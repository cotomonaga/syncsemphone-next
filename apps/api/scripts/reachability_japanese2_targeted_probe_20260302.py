#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_SRC = PROJECT_ROOT / "packages" / "domain" / "src"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(DOMAIN_SRC) not in sys.path:
    sys.path.insert(0, str(DOMAIN_SRC))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _search_reachability,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.lexicon.models import LexiconEntry  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402

STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"

GRAMMAR_ID = "japanese2"

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

BASELINE = {
    "S2": [265, 23, 266, 267, 19, 271, 204],
    "S3": [267, 268, 269, 270, 19, 271, 204],
    "S4": [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204],
}

TARGETED_PROBES = [
    {"probe_group": "1-A", "sentence_key": "S2", "label": "S2-A", "old_id": 266, "surface": "食べている"},
    {"probe_group": "1-B", "sentence_key": "S3", "label": "S3-B", "old_id": 268, "surface": "と"},
    {"probe_group": "1-B", "sentence_key": "S4", "label": "S4-B", "old_id": 268, "surface": "と"},
    {"probe_group": "1-C", "sentence_key": "S3", "label": "S3-C", "old_id": 269, "surface": "話している"},
    {"probe_group": "1-C", "sentence_key": "S4", "label": "S4-C", "old_id": 269, "surface": "話している"},
    {"probe_group": "1-D", "sentence_key": "S3", "label": "S3-D", "old_id": 271, "surface": "いる"},
    {"probe_group": "1-D", "sentence_key": "S4", "label": "S4-D", "old_id": 271, "surface": "いる"},
]


@dataclass(frozen=True)
class RunConfig:
    budget_seconds: float = 20.0
    max_nodes: int = 120000
    max_depth: int = 28
    top_k: int = 10


def _normalize_token(token: str) -> str:
    return token.strip().replace("　", "").replace(" ", "")


def _phono_variants(phono: str) -> list[str]:
    out: list[str] = []
    normalized = _normalize_token(phono)
    if normalized:
        out.append(normalized)
    stripped = normalized.strip("-")
    if stripped and stripped != normalized:
        out.append(stripped)
    return out


def _line_map_by_id(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        try:
            lid = int(cols[0].strip())
        except Exception:
            continue
        out[lid] = line
    return out


def _build_temp_legacy_root_for_explicit(*, legacy_root: Path, required_ids: set[int]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_targeted_probe_"))

    for child in legacy_root.iterdir():
        dst = tmp_root / child.name
        if child.name == "japanese2":
            continue
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    src_j2 = legacy_root / "japanese2"
    dst_j2 = tmp_root / "japanese2"
    dst_j2.mkdir(parents=True, exist_ok=True)
    for child in src_j2.iterdir():
        if child.name == "japanese2.csv":
            continue
        dst = dst_j2 / child.name
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")

    lines: list[str] = []
    for lid in sorted(required_ids):
        if lid in j2_map:
            lines.append(j2_map[lid])
        elif lid in all_map:
            lines.append(all_map[lid])
    (dst_j2 / "japanese2.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_root


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = defaultdict(list)
    for lid, entry in lexicon.items():
        seen: set[str] = set()
        entry_norm = _normalize_token(entry.entry)
        if entry_norm:
            seen.add(entry_norm)
        for v in _phono_variants(entry.phono):
            if v:
                seen.add(v)
        for s in sorted(seen):
            idx[s].append(lid)
    return dict(idx)


def _build_numeration_text(memo: str, lexicon_ids: list[int]) -> str:
    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    for i, lid in enumerate(lexicon_ids, start=1):
        if i > NUMERATION_SLOT_COUNT:
            break
        line1[i] = str(lid)
        line3[i] = str(i)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _aggregate_residual_families(samples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for sample in samples:
        for key, value in (sample.get("residual_family_counts") or {}).items():
            counter[key] += int(value)
    return dict(sorted(counter.items(), key=lambda row: (-row[1], row[0])))


def _build_initial_item_map(*, state: Any, lexicon_ids: list[int], lexicon: dict[int, LexiconEntry]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for slot_index in range(1, state.basenum + 1):
        item = state.base[slot_index]
        if item == "zero" or not isinstance(item, list):
            continue
        item_id = str(item[0]) if len(item) > 0 else ""
        lid = lexicon_ids[slot_index - 1] if slot_index - 1 < len(lexicon_ids) else None
        entry = lexicon.get(lid) if lid is not None else None
        mapping[item_id] = {
            "initial_slot": slot_index,
            "lexicon_id": lid,
            "surface": entry.entry if entry is not None else "",
            "phono": entry.phono if entry is not None else "",
            "category": entry.category if entry is not None else "",
        }
    return mapping


def _flatten_exact_sources_top(
    *,
    samples: list[dict[str, Any]],
    initial_item_map: dict[str, dict[str, Any]],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    attrs: dict[str, dict[str, Any]] = {}
    for sample in samples[:5]:
        for family, rows in (sample.get("residual_family_sources") or {}).items():
            for row in rows:
                item_id = str(row.get("item_id", ""))
                init = initial_item_map.get(item_id, {})
                key = "|".join(
                    [
                        family,
                        str(row.get("raw", "")),
                        item_id,
                        str(init.get("initial_slot", "")),
                        str(init.get("surface", "")),
                    ]
                )
                counter[key] += 1
                attrs[key] = {
                    "family": family,
                    "exact_label": str(row.get("raw", "")),
                    "item_id": item_id,
                    "surface": str(init.get("surface", row.get("phono", ""))),
                    "initial_slot": init.get("initial_slot"),
                    "current_slot": str(row.get("slot_index", "")),
                    "lexicon_id": init.get("lexicon_id"),
                }
    out: list[dict[str, Any]] = []
    for key, count in counter.most_common(top_n):
        row = dict(attrs[key])
        row["count_in_top5_samples"] = int(count)
        out.append(row)
    return out


def _run_case(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    lexicon_ids: list[int],
    config: RunConfig,
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:{proposal_id}", lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    initial_item_map = _build_initial_item_map(state=state, lexicon_ids=lexicon_ids, lexicon=lexicon)

    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    req = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=req,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[: config.top_k]
    best_mid_samples = (internal.leaf_stats.get("best_mid_state_samples") or [])[: config.top_k]

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "proposal_id": proposal_id,
        "explicit_lexicon_ids": list(lexicon_ids),
        "metrics": {
            "status": internal.status,
            "reason": internal.reason,
            "actions_attempted": internal.actions_attempted,
            "max_depth_reached": internal.max_depth_reached,
            "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
            "best_leaf_residual_family_totals": _aggregate_residual_families(best_leaf_samples),
            "best_mid_residual_family_totals": _aggregate_residual_families(best_mid_samples),
            "best_leaf_exact_source_top5": _flatten_exact_sources_top(
                samples=best_leaf_samples,
                initial_item_map=initial_item_map,
                top_n=5,
            ),
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _replace_one_slot(ids: list[int], old_id: int, new_id: int) -> list[int]:
    out = list(ids)
    replaced = False
    for i, lid in enumerate(out):
        if lid == old_id:
            out[i] = new_id
            replaced = True
            break
    if not replaced:
        raise ValueError(f"old_id={old_id} not found in {ids}")
    return out


def _build_probe_inventory(
    *,
    legacy_root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], set[int]]:
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    all_idx = _build_surface_index(all_lex)
    j2_idx = _build_surface_index(j2_lex)

    inventory: dict[str, list[dict[str, Any]]] = {}
    required_ids: set[int] = set()
    for sk in BASELINE:
        required_ids.update(BASELINE[sk])

    for probe in TARGETED_PROBES:
        key = f"{probe['label']}-{probe['old_id']}"
        surface = _normalize_token(str(probe["surface"]))
        all_ids = set(all_idx.get(surface, []))
        j2_ids = set(j2_idx.get(surface, []))
        shared_ids = sorted(all_ids & j2_ids)
        rows: list[dict[str, Any]] = []
        for lid in shared_ids:
            entry = j2_lex[lid]
            rows.append(
                {
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "phono": entry.phono,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                }
            )
            required_ids.add(lid)
        inventory[key] = rows
    return inventory, required_ids


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 Targeted Lexical Probe ({payload['generated_at']})")
    lines.append("")
    cfg = payload["config"]
    lines.append(f"- [確認済み事実] 固定条件: grammar_id={cfg['grammar_id']}, explicit numeration, auto_add_ga_phi={cfg['auto_add_ga_phi']}")
    lines.append(
        f"- [確認済み事実] 予算: budget_seconds={cfg['budget_seconds']}, max_nodes={cfg['max_nodes']}, max_depth={cfg['max_depth']}, top_k={cfg['top_k']}"
    )
    lines.append("")
    lines.append("## 0. Baseline")
    lines.append("")
    lines.append("| sentence | explicit_lexicon_ids | status | reason | actions | depth | leaf_min |")
    lines.append("|---|---|---|---|---:|---:|---:|")
    for sk in ("S2", "S3", "S4"):
        row = payload["runs"][sk]["baseline"]
        m = row["metrics"]
        lines.append(
            f"| {sk} | `{','.join(str(x) for x in row['explicit_lexicon_ids'])}` | {m['status']} | {m['reason']} | {m['actions_attempted']} | {m['max_depth_reached']} | {m['best_leaf_unresolved_min']} |"
        )
    lines.append("")

    lines.append("## 1. Candidate Inventory (lexicon-all.csv ∩ japanese2.csv)")
    lines.append("")
    for probe in TARGETED_PROBES:
        inv_key = f"{probe['label']}-{probe['old_id']}"
        lines.append(f"### {probe['label']} old_id={probe['old_id']} surface={probe['surface']}")
        candidates = payload["inventory"].get(inv_key, [])
        if not candidates:
            lines.append("- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）")
            lines.append("")
            continue
        lines.append("| lexicon_id | entry | phono | category | idslot |")
        lines.append("|---:|---|---|---|---|")
        for c in candidates:
            lines.append(f"| {c['lexicon_id']} | {c['entry']} | {c['phono']} | {c['category']} | {c['idslot']} |")
        lines.append("")

    lines.append("## 2. Targeted Probe Results")
    lines.append("")
    for sk in ("S2", "S3", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        base = payload["runs"][sk]["baseline"]
        lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in base['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] baseline residual totals: {base['metrics']['best_leaf_residual_family_totals']}")
        lines.append(f"- [確認済み事実] baseline residual source top5: {base['metrics']['best_leaf_exact_source_top5']}")
        for p in payload["runs"][sk]["probes"]:
            if p.get("not_run"):
                lines.append(
                    f"- [確認済み事実] {p['proposal_id']}: not_run ({p['reason']})"
                )
                continue
            m = p["metrics"]
            lines.append(
                f"- [確認済み事実] {p['proposal_id']} IDs: `{','.join(str(x) for x in p['explicit_lexicon_ids'])}` "
                f"status={m['status']} reason={m['reason']} actions={m['actions_attempted']} depth={m['max_depth_reached']} leaf_min={m['best_leaf_unresolved_min']}"
            )
            lines.append(
                f"  residual totals={m['best_leaf_residual_family_totals']}; source_top5={m['best_leaf_exact_source_top5']}"
            )
        lines.append("")

    lines.append("## 3. 未確認")
    lines.append("")
    lines.append("- [未確認] 各runは有限予算観測であり、unknown を unreachable と断定できない。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    inventory, required_ids = _build_probe_inventory(legacy_root=legacy_root)
    temp_root = _build_temp_legacy_root_for_explicit(legacy_root=legacy_root, required_ids=required_ids)

    runs: dict[str, dict[str, Any]] = {}
    for sk in ("S2", "S3", "S4"):
        sentence = SENTENCES[sk]
        baseline_ids = BASELINE[sk]
        baseline = _run_case(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="baseline",
            lexicon_ids=baseline_ids,
            config=config,
        )
        probe_rows: list[dict[str, Any]] = []
        for probe in [p for p in TARGETED_PROBES if p["sentence_key"] == sk]:
            inv_key = f"{probe['label']}-{probe['old_id']}"
            candidates = [c for c in inventory.get(inv_key, []) if int(c["lexicon_id"]) != int(probe["old_id"])]
            if not candidates:
                probe_rows.append(
                    {
                        "proposal_id": f"{probe['label']}-no-candidate",
                        "probe_group": probe["probe_group"],
                        "target_surface": probe["surface"],
                        "old_id": probe["old_id"],
                        "not_run": True,
                        "reason": "no_candidate_in_both_sources",
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
                continue
            for idx, cand in enumerate(candidates, start=1):
                cand_id = int(cand["lexicon_id"])
                proposal_id = f"{probe['label']}{idx}:{probe['old_id']}->{cand_id}"
                explicit_ids = _replace_one_slot(baseline_ids, int(probe["old_id"]), cand_id)
                if explicit_ids == baseline_ids:
                    probe_rows.append(
                        {
                            "proposal_id": proposal_id,
                            "probe_group": probe["probe_group"],
                            "target_surface": probe["surface"],
                            "old_id": probe["old_id"],
                            "new_id": cand_id,
                            "not_run": True,
                            "reason": "invalid_same_as_baseline",
                            "fact_status": STATUS_CONFIRMED,
                        }
                    )
                    continue
                result = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id=proposal_id,
                    lexicon_ids=explicit_ids,
                    config=config,
                )
                result["probe_group"] = probe["probe_group"]
                result["target_surface"] = probe["surface"]
                result["old_id"] = probe["old_id"]
                result["new_id"] = cand_id
                probe_rows.append(result)
        runs[sk] = {"baseline": baseline, "probes": probe_rows}

    payload = {
        "generated_at": date.today().isoformat(),
        "config": {
            "grammar_id": GRAMMAR_ID,
            "auto_add_ga_phi": False,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "fact_status": STATUS_CONFIRMED,
        },
        "sentences": SENTENCES,
        "baseline": BASELINE,
        "inventory": inventory,
        "temp_legacy_root": str(temp_root),
        "runs": runs,
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-targeted-probe-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-targeted-probe-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
