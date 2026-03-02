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

P0 = {
    "S2": [265, 23, 266, 267, 19, 271, 125],
    "S3": [267, 268, 269, 270, 19, 271, 125],
    "S4": [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 125],
}

P0_SWAP_125_TO_204 = {
    sk: [204 if lid == 125 else lid for lid in ids]
    for sk, ids in P0.items()
}


@dataclass(frozen=True)
class RunConfig:
    budget_seconds: float = 20.0
    max_nodes: int = 120000
    max_depth: int = 28
    top_k: int = 10


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


def _make_temp_legacy_root_for_explicit(*, legacy_root: Path, required_ids: set[int]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_p0_125to204_"))

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


def _aggregate_residual_families(samples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for sample in samples:
        for key, value in (sample.get("residual_family_counts") or {}).items():
            counter[key] += int(value)
    return dict(sorted(counter.items(), key=lambda row: (-row[1], row[0])))


def _aggregate_residual_sources(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_family: dict[str, Counter[str]] = {}
    attrs: dict[str, dict[str, str]] = {}
    for sample in samples:
        source_map = sample.get("residual_family_sources") or {}
        for family, rows in source_map.items():
            fam_counter = by_family.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        str(row.get("item_id", "")),
                        str(row.get("category", "")),
                        str(row.get("phono", "")),
                        str(row.get("raw", "")),
                        str(row.get("slot_index", "")),
                    ]
                )
                fam_counter[key] += 1
                attrs[key] = {
                    "item_id": str(row.get("item_id", "")),
                    "category": str(row.get("category", "")),
                    "phono": str(row.get("phono", "")),
                    "raw": str(row.get("raw", "")),
                    "slot_index": str(row.get("slot_index", "")),
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, counter in sorted(by_family.items(), key=lambda row: row[0]):
        items: list[dict[str, Any]] = []
        for key, count in counter.most_common(10):
            a = attrs[key]
            items.append(
                {
                    "count": int(count),
                    "item_id": a["item_id"],
                    "category": a["category"],
                    "phono": a["phono"],
                    "raw": a["raw"],
                    "slot_index": a["slot_index"],
                }
            )
        out[family] = items
    return out


def _run(*, legacy_root: Path, sentence_key: str, sentence: str, proposal_id: str, lexicon_ids: list[int], config: RunConfig) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:{proposal_id}", lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
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
        "explicit_lexicon_ids": lexicon_ids,
        "metrics": {
            "status": internal.status,
            "reason": internal.reason,
            "actions_attempted": internal.actions_attempted,
            "max_depth_reached": internal.max_depth_reached,
            "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
            "best_leaf_residual_family_totals": _aggregate_residual_families(best_leaf_samples),
            "best_mid_residual_family_totals": _aggregate_residual_families(best_mid_samples),
            "persistent_residual_source_top": _aggregate_residual_sources(best_leaf_samples),
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    b = before["metrics"]
    a = after["metrics"]
    fam_keys = sorted(set((b.get("best_leaf_residual_family_totals") or {}).keys()) | set((a.get("best_leaf_residual_family_totals") or {}).keys()))
    fam_diff = {
        k: int((a.get("best_leaf_residual_family_totals") or {}).get(k, 0)) - int((b.get("best_leaf_residual_family_totals") or {}).get(k, 0))
        for k in fam_keys
    }
    return {
        "best_leaf_unresolved_min_before": b.get("best_leaf_unresolved_min"),
        "best_leaf_unresolved_min_after": a.get("best_leaf_unresolved_min"),
        "best_leaf_unresolved_min_delta": (
            (a.get("best_leaf_unresolved_min") - b.get("best_leaf_unresolved_min"))
            if isinstance(a.get("best_leaf_unresolved_min"), int) and isinstance(b.get("best_leaf_unresolved_min"), int)
            else None
        ),
        "best_leaf_residual_family_totals_delta": fam_diff,
        "fact_status": STATUS_CONFIRMED,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 P0 125->204 Explicit Experiment ({payload['generated_at']})")
    lines.append("")
    lines.append("- [確認済み事実] 条件: grammar_id=japanese2, explicit numeration, P0固定, 125->204のみ差し替え")
    lines.append(f"- [確認済み事実] budget_seconds={payload['config']['budget_seconds']}, max_nodes={payload['config']['max_nodes']}, max_depth={payload['config']['max_depth']}, top_k={payload['config']['top_k']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| sentence | P0 unresolved_min | P0(125->204) unresolved_min | delta |")
    lines.append("|---|---:|---:|---:|")
    for sk in ("S2", "S3", "S4"):
        d = payload["diff"][sk]
        lines.append(f"| {sk} | {d['best_leaf_unresolved_min_before']} | {d['best_leaf_unresolved_min_after']} | {d['best_leaf_unresolved_min_delta']} |")
    lines.append("")
    lines.append("## Details")
    lines.append("")
    for sk in ("S2", "S3", "S4"):
        sentence = payload["sentences"][sk]
        base = payload["sentence"][sk]["P0_baseline"]
        swap = payload["sentence"][sk]["P0_swap_125_to_204"]
        d = payload["diff"][sk]
        lines.append(f"### {sk}: {sentence}")
        lines.append(f"- [確認済み事実] P0 IDs: {base['explicit_lexicon_ids']}")
        lines.append(f"- [確認済み事実] P0_swap IDs: {swap['explicit_lexicon_ids']}")
        lines.append(f"- [確認済み事実] P0 metrics: status={base['metrics']['status']}, reason={base['metrics']['reason']}, actions={base['metrics']['actions_attempted']}, depth={base['metrics']['max_depth_reached']}, leaf_min={base['metrics']['best_leaf_unresolved_min']}")
        lines.append(f"- [確認済み事実] P0 residual totals: {base['metrics']['best_leaf_residual_family_totals']}")
        lines.append(f"- [確認済み事実] P0 residual source top: {base['metrics']['persistent_residual_source_top']}")
        lines.append(f"- [確認済み事実] P0_swap metrics: status={swap['metrics']['status']}, reason={swap['metrics']['reason']}, actions={swap['metrics']['actions_attempted']}, depth={swap['metrics']['max_depth_reached']}, leaf_min={swap['metrics']['best_leaf_unresolved_min']}")
        lines.append(f"- [確認済み事実] P0_swap residual totals: {swap['metrics']['best_leaf_residual_family_totals']}")
        lines.append(f"- [確認済み事実] P0_swap residual source top: {swap['metrics']['persistent_residual_source_top']}")
        lines.append(f"- [確認済み事実] delta: {d}")
        lines.append("")
    lines.append("## 未確認")
    lines.append("")
    lines.append("- [未確認] 各ケースは budget 上限内観測であり、unknown を unreachable と断定できない。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    required_ids: set[int] = set()
    for ids in P0.values():
        required_ids.update(ids)
    for ids in P0_SWAP_125_TO_204.values():
        required_ids.update(ids)

    temp_root = _make_temp_legacy_root_for_explicit(legacy_root=legacy_root, required_ids=required_ids)

    sentence_results: dict[str, dict[str, Any]] = defaultdict(dict)
    diff_results: dict[str, Any] = {}
    for sk in ("S2", "S3", "S4"):
        sentence = SENTENCES[sk]
        base = _run(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="P0_baseline",
            lexicon_ids=P0[sk],
            config=config,
        )
        swap = _run(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="P0_swap_125_to_204",
            lexicon_ids=P0_SWAP_125_TO_204[sk],
            config=config,
        )
        sentence_results[sk]["P0_baseline"] = base
        sentence_results[sk]["P0_swap_125_to_204"] = swap
        diff_results[sk] = _diff(base, swap)

    payload = {
        "generated_at": date.today().isoformat(),
        "config": {
            "grammar_id": GRAMMAR_ID,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "auto_add_ga_phi": False,
            "experiment": "P0 keep, swap only 125->204",
            "fact_status": STATUS_CONFIRMED,
        },
        "sentences": SENTENCES,
        "temp_legacy_root": str(temp_root),
        "sentence": sentence_results,
        "diff": diff_results,
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-p0-125to204-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-p0-125to204-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")

    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
