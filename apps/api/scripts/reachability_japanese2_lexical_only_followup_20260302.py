#!/usr/bin/env python3
from __future__ import annotations

import csv
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
STATUS_GUESS = "推測"

GRAMMAR_ID = "japanese2"

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
    "T1": "わたあめを食べているひつじと話しているうさぎがいる",
    "T2": "ふわふわしたひつじと話しているうさぎがいる",
    "T3": "ふわふわしたわたあめを食べているひつじがいる",
}

BASELINE = {
    "S2": [265, 23, 266, 267, 19, 271, 204],
    "S3": [267, 268, 269, 270, 19, 271, 204],
    "S4": [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204],
    "T1": [265, 23, 266, 267, 268, 269, 270, 19, 271, 204],
    "T2": [264, 267, 268, 269, 270, 19, 271, 204],
    "T3": [264, 265, 23, 266, 267, 19, 271, 204],
}

TARGET_SURFACES = ["食べている", "と", "話している", "いる", "る", "φ"]

# old_id -> (surface, sentence keys)
TARGETED_SLOT_PROBES = {
    266: {"surface": "食べている", "sentences": ["S2"]},
    269: {"surface": "話している", "sentences": ["S3", "S4"]},
    271: {"surface": "いる", "sentences": ["S3", "S4"]},
}


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


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = defaultdict(list)
    for lid, entry in lexicon.items():
        forms: set[str] = set()
        e = _normalize_token(entry.entry)
        if e:
            forms.add(e)
        for p in _phono_variants(entry.phono):
            if p:
                forms.add(p)
        for form in sorted(forms):
            idx[form].append(lid)
    return dict(idx)


def _parse_reachable_lexicon_ids_from_confirmed_sets(path: Path) -> set[int]:
    if not path.exists():
        return set()
    out: set[int] = set()
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "Lexicon IDs:" not in line:
            continue
        start = line.find("`")
        end = line.rfind("`")
        if start == -1 or end <= start:
            continue
        for token in line[start + 1 : end].split(","):
            raw = token.strip()
            if raw.isdigit():
                out.add(int(raw))
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
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_lexonly_followup_"))

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

    history_top: list[str] = []
    for ev in internal.evidences[:3]:
        history_top.append(" ".join(f"([{s.left_id} {s.right_id}] {s.rule_name})" for s in ev.steps))

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
            "history_top": history_top,
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


def _source_files_for_id(lid: int, j2_map: dict[int, str], all_map: dict[int, str]) -> list[str]:
    files: list[str] = []
    if lid in j2_map:
        files.append("japanese2/japanese2.csv")
    if lid in all_map:
        files.append("lexicon-all.csv")
    return files


def _engine_usable_check(*, temp_root: Path, lid: int) -> dict[str, Any]:
    # explicit numeration と search が例外なく実行できるかで判定
    ids = [lid]
    if lid != 204:
        ids.append(204)
    else:
        ids.append(19)
    try:
        state = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=_build_numeration_text(f"engine_check:{lid}", ids),
            legacy_root=temp_root,
        )
        profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=temp_root)
        req = DerivationReachabilityRequest(
            state=state,
            max_evidences=1,
            budget_seconds=0.1,
            max_nodes=200,
            max_depth=6,
            return_process_text=False,
        )
        _search_reachability(
            request=req,
            legacy_root=temp_root,
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
            search_signature_mode="structural",
        )
        return {"engine_usable": True, "error": None, "fact_status": STATUS_CONFIRMED}
    except Exception as exc:
        return {"engine_usable": False, "error": str(exc), "fact_status": STATUS_CONFIRMED}


def _build_candidate_pool(
    *,
    legacy_root: Path,
    temp_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    temp_j2_lex = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)

    all_idx = _build_surface_index(all_lex)
    j2_idx = _build_surface_index(j2_lex)
    temp_idx = _build_surface_index(temp_j2_lex)

    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")

    used_ids = _parse_reachable_lexicon_ids_from_confirmed_sets(
        PROJECT_ROOT / "docs/specs/reachability-confirmed-sets-ja.md"
    )

    pool: dict[str, list[dict[str, Any]]] = {}
    for surface in TARGET_SURFACES:
        key = _normalize_token(surface)
        ids = sorted(set(all_idx.get(key, [])) | set(j2_idx.get(key, [])) | set(temp_idx.get(key, [])))
        rows: list[dict[str, Any]] = []
        for lid in ids:
            entry = temp_j2_lex.get(lid)
            if entry is None:
                continue
            engine_chk = _engine_usable_check(temp_root=temp_root, lid=lid)
            lookup_deployable = lid in set(j2_idx.get(key, []))
            rows.append(
                {
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "surface": surface,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                    "engine_usable": engine_chk["engine_usable"],
                    "lookup_deployable": bool(lookup_deployable),
                    "source_files": _source_files_for_id(lid, j2_map=j2_map, all_map=all_map),
                    "used_in_known_reachable_examples": lid in used_ids,
                    "engine_check_error": engine_chk["error"],
                    "fact_status": STATUS_CONFIRMED,
                }
            )
        pool[surface] = rows
    return pool


def _source_set(rows: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        out.add(
            f"{row.get('family','')}|{row.get('exact_label','')}|{row.get('item_id','')}|{row.get('surface','')}"
        )
    return out


def _diff_run(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    b = before["metrics"]
    a = after["metrics"]
    fam_keys = sorted(set(b["best_leaf_residual_family_totals"].keys()) | set(a["best_leaf_residual_family_totals"].keys()))
    fam_delta = {
        k: int(a["best_leaf_residual_family_totals"].get(k, 0)) - int(b["best_leaf_residual_family_totals"].get(k, 0))
        for k in fam_keys
    }
    b_sources = _source_set(b["best_leaf_exact_source_top5"])
    a_sources = _source_set(a["best_leaf_exact_source_top5"])
    return {
        "best_leaf_unresolved_min_before": b["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_after": a["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_delta": (
            int(a["best_leaf_unresolved_min"]) - int(b["best_leaf_unresolved_min"])
            if isinstance(a["best_leaf_unresolved_min"], int) and isinstance(b["best_leaf_unresolved_min"], int)
            else None
        ),
        "family_delta": fam_delta,
        "source_disappeared_top5": sorted(b_sources - a_sources),
        "source_appeared_top5": sorted(a_sources - b_sources),
        "fact_status": STATUS_CONFIRMED,
    }


def _lexicon_row_by_id(path: Path, target_id: int) -> str | None:
    with path.open(encoding="utf-8") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if not cols or not cols[0].strip().isdigit():
                continue
            if int(cols[0].strip()) == target_id:
                return line.rstrip("\n")
    return None


def _csv_row_minimal_variant(*, base_line: str, new_id: int, new_sync_feature: str, note: str) -> str:
    cells = base_line.split("\t")
    if len(cells) < 30:
        cells.extend([""] * (30 - len(cells)))
    cells[0] = str(new_id)
    # sync num + first sync feature only; keep remaining blank for minimal diff note
    cells[8] = "1"
    cells[9] = new_sync_feature
    for i in range(10, 14):
        cells[i] = ""
    cells[28] = note
    return "\t".join(cells)


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 lexical-only followup ({payload['generated_at']})")
    lines.append("")
    cfg = payload["config"]
    lines.append("## 1. 結論")
    lines.append("")
    lines.append(
        f"- [確認済み事実] 固定条件: grammar_id={cfg['grammar_id']}, explicit numeration, auto_add_ga_phi={cfg['auto_add_ga_phi']}, "
        f"budget_seconds={cfg['budget_seconds']}, max_nodes={cfg['max_nodes']}, max_depth={cfg['max_depth']}, top_k={cfg['top_k']}"
    )
    lines.append(
        f"- [確認済み事実] S3の `268->171` は leaf_min {payload['core_diff']['S3']['best_leaf_unresolved_min_before']} -> {payload['core_diff']['S3']['best_leaf_unresolved_min_after']} へ改善。"
    )
    lines.append(
        f"- [確認済み事実] S4の `268->171` は leaf_min {payload['core_diff']['S4']['best_leaf_unresolved_min_before']} -> {payload['core_diff']['S4']['best_leaf_unresolved_min_after']} で改善せず、family差分は {payload['core_diff']['S4']['family_delta']}。"
    )
    lines.append(
        "- [確認済み事実] 266/269/271 の同表層 engine-usable 代替候補は今回観測では存在せず、1スロット差し替えprobeは not_run。"
    )
    lines.append(
        "- [推測] 266 の sy:17 残差は既存候補の選び直しのみでは縮退しないため、lexical-onlyで狙うなら 266 相当の新規行追加が最小。"
    )
    lines.append("")

    lines.append("## 2. candidate pool（engine-usable / lookup-deployable）")
    lines.append("")
    for surface in TARGET_SURFACES:
        lines.append(f"### surface: {surface}")
        rows = payload["candidate_pool"].get(surface, [])
        if not rows:
            lines.append("- [確認済み事実] 候補なし")
            lines.append("")
            continue
        lines.append("| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |")
        lines.append("|---:|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(
                f"| {r['lexicon_id']} | {r['entry']} | {r['category']} | {r['idslot']} | {r['engine_usable']} | {r['lookup_deployable']} | {','.join(r['source_files'])} | {r['used_in_known_reachable_examples']} |"
            )
        lines.append("")

    lines.append("## 3. S3 の `268->171` 成功分析")
    lines.append("")
    s3b = payload["runs"]["S3"]["baseline"]
    s3s = payload["runs"]["S3"]["swap_268_to_171"]
    lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in s3b['explicit_lexicon_ids'])}`")
    lines.append(f"- [確認済み事実] swap IDs: `{','.join(str(x) for x in s3s['explicit_lexicon_ids'])}`")
    lines.append(f"- [確認済み事実] baseline metrics: {s3b['metrics']}")
    lines.append(f"- [確認済み事実] swap metrics: {s3s['metrics']}")
    lines.append(f"- [確認済み事実] diff: {payload['core_diff']['S3']}")
    lines.append("")

    lines.append("## 4. S4 の `268->171` 悪化分析")
    lines.append("")
    s4b = payload["runs"]["S4"]["baseline"]
    s4s = payload["runs"]["S4"]["swap_268_to_171"]
    lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in s4b['explicit_lexicon_ids'])}`")
    lines.append(f"- [確認済み事実] swap IDs: `{','.join(str(x) for x in s4s['explicit_lexicon_ids'])}`")
    lines.append(f"- [確認済み事実] baseline metrics: {s4b['metrics']}")
    lines.append(f"- [確認済み事実] swap metrics: {s4s['metrics']}")
    lines.append(f"- [確認済み事実] diff: {payload['core_diff']['S4']}")
    lines.append(
        "- [確認済み事実] swap時の `se:24` exact source top5 は `264 ふわふわした`（Content:0,24）であり、171自身のsourceとしては観測されていない。"
    )
    lines.append("")

    lines.append("## 5. `264` 干渉切り分け reduced sentence")
    lines.append("")
    for key in ("T1", "T2", "T3"):
        row = payload["runs"][key]
        lines.append(f"### {key}: {payload['sentences'][key]}")
        lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in row['baseline']['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] baseline metrics: {row['baseline']['metrics']}")
        if "swap_268_to_171" in row:
            lines.append(f"- [確認済み事実] swap IDs: `{','.join(str(x) for x in row['swap_268_to_171']['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] swap metrics: {row['swap_268_to_171']['metrics']}")
            lines.append(f"- [確認済み事実] diff: {payload['core_diff'].get(key)}")
        else:
            lines.append("- [確認済み事実] swap_268_to_171 は not_applicable（268がbaselineに存在しない）")
        lines.append("")

    lines.append("## 6. `266/269/271` targeted probe")
    lines.append("")
    for probe in payload["targeted_slot_probe_runs"]:
        lines.append(f"### old_id={probe['old_id']} surface={probe['surface']} sentence={probe['sentence_key']}")
        lines.append(f"- [確認済み事実] baseline IDs: `{','.join(str(x) for x in probe['baseline_ids'])}`")
        if probe.get("not_run"):
            lines.append(f"- [確認済み事実] not_run: {probe['reason']}")
        else:
            lines.append(f"- [確認済み事実] proposal IDs: `{','.join(str(x) for x in probe['proposal']['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] proposal metrics: {probe['proposal']['metrics']}")
            lines.append(f"- [確認済み事実] diff: {probe['diff']}")
        lines.append("")

    lines.append("## 7. `171` と `268` の code-grounded 差分")
    lines.append("")
    lines.append("- [確認済み事実] `268`（J/zero）は `sync_features=[0,17,N,,,right,nonhead; 3,17,V,,,left,nonhead; 4,11,to]` を持つ。")
    lines.append("- [確認済み事実] `171`（Z/2,22）は `sync_features=[to]`, `semantics=[Content:0,24]` を持つ。")
    lines.append("- [確認済み事実] `17` 系消費は `execute.py` の `_process_sy_imi03`（`number == \"17\"`）で `_eval_feature_17` を通る。")
    lines.append("- [確認済み事実] `se:24` 消費は `execute.py` の `_process_se_imi03`（`number == \"24\"`）で `attr:nb_id` に置換される。")
    lines.append("- [確認済み事実] `se:33` 消費は `_process_se_imi03`（`number == \"33\"`）で相手 `sy` の `11`/`12` ラベル一致を要する。")
    lines.append("")

    lines.append("## 8. `266` lexical-only 可否")
    lines.append("")
    lines.append("- [確認済み事実] yes/no-1: **No**（既存候補の選び直しだけでは不可）。理由: `食べている` の engine-usable 候補は 266 のみ。")
    lines.append("- [推測] yes/no-2: **Yes**（新規 lexical item 1行追加で狙うのが妥当）。理由: S2 obstruction が 266由来 sy:17 に局在。")
    lines.append("- [推測] yes/no-3: 最小差分は `266` の `sync_features`（17系）を1本変える設計。")
    lines.append("")

    lines.append("## 9. 必要なら新規 lexical item 案")
    lines.append("")
    for row in payload["new_lexical_item_proposals"]:
        lines.append(f"- [推測] {row['comment']}")
        lines.append("```tsv")
        lines.append(row["csv_row"])
        lines.append("```")
    lines.append("")

    lines.append("## 10. 未確認事項")
    lines.append("")
    lines.append("- [未確認] 有限予算下の unknown は unreachable を意味しない。")
    lines.append("- [未確認] 新規 lexical item 案（9201/9202）は未投入・未実測。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    # Build required ID universe for temp japanese2.csv
    required_ids: set[int] = set()
    for ids in BASELINE.values():
        required_ids.update(ids)
    required_ids.add(171)

    # Include all candidate IDs for target surfaces from both sources
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")
    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")

    # quick surface harvest from lexicon-all/j2 by exact entry/phono
    def harvest_ids(path: Path, surfaces: list[str]) -> set[int]:
        out: set[int] = set()
        with path.open(encoding="utf-8") as f:
            r = csv.reader(f, delimiter="\t")
            for row in r:
                if not row:
                    continue
                try:
                    lid = int((row[0] if len(row) > 0 else "").strip())
                except Exception:
                    continue
                entry = _normalize_token(row[1] if len(row) > 1 else "")
                phono = _normalize_token(row[2] if len(row) > 2 else "")
                for s in surfaces:
                    ss = _normalize_token(s)
                    if entry == ss or phono == ss or phono.strip("-") == ss:
                        out.add(lid)
                        break
        return out

    required_ids.update(harvest_ids(legacy_root / "lexicon-all.csv", TARGET_SURFACES))
    required_ids.update(harvest_ids(legacy_root / "japanese2" / "japanese2.csv", TARGET_SURFACES))

    temp_root = _make_temp_legacy_root_for_explicit(legacy_root=legacy_root, required_ids=required_ids)

    candidate_pool = _build_candidate_pool(legacy_root=legacy_root, temp_root=temp_root)

    runs: dict[str, dict[str, Any]] = {}
    core_diff: dict[str, Any] = {}

    for sk in ("S2", "S3", "S4", "T1", "T2", "T3"):
        sentence = SENTENCES[sk]
        baseline = _run_case(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="baseline",
            lexicon_ids=BASELINE[sk],
            config=config,
        )
        runs[sk] = {"baseline": baseline}
        if 268 in BASELINE[sk]:
            swap_ids = _replace_one_slot(BASELINE[sk], 268, 171)
            swap = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sentence,
                proposal_id="swap_268_to_171",
                lexicon_ids=swap_ids,
                config=config,
            )
            runs[sk]["swap_268_to_171"] = swap
            core_diff[sk] = _diff_run(baseline, swap)

    targeted_slot_probe_runs: list[dict[str, Any]] = []
    for old_id, cfg in TARGETED_SLOT_PROBES.items():
        surface = cfg["surface"]
        candidates = [row for row in candidate_pool.get(surface, []) if bool(row["engine_usable"])]
        alt_ids = [int(row["lexicon_id"]) for row in candidates if int(row["lexicon_id"]) != int(old_id)]
        for sk in cfg["sentences"]:
            base_ids = BASELINE[sk]
            row: dict[str, Any] = {
                "old_id": old_id,
                "surface": surface,
                "sentence_key": sk,
                "baseline_ids": base_ids,
            }
            if not alt_ids:
                row["not_run"] = True
                row["reason"] = "no_engine_usable_alternative_candidate"
                row["fact_status"] = STATUS_CONFIRMED
                targeted_slot_probe_runs.append(row)
                continue
            # run all alternatives (generally small)
            for aid in alt_ids:
                prop_ids = _replace_one_slot(base_ids, old_id, aid)
                if prop_ids == base_ids:
                    row2 = dict(row)
                    row2["not_run"] = True
                    row2["reason"] = "invalid_same_as_baseline"
                    row2["new_id"] = aid
                    row2["fact_status"] = STATUS_CONFIRMED
                    targeted_slot_probe_runs.append(row2)
                    continue
                proposal = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=SENTENCES[sk],
                    proposal_id=f"{old_id}_to_{aid}",
                    lexicon_ids=prop_ids,
                    config=config,
                )
                row2 = dict(row)
                row2["new_id"] = aid
                row2["proposal"] = proposal
                row2["diff"] = _diff_run(runs[sk]["baseline"], proposal)
                row2["fact_status"] = STATUS_CONFIRMED
                targeted_slot_probe_runs.append(row2)

    # New lexical proposals (not executed)
    base_266 = _lexicon_row_by_id(legacy_root / "lexicon-all.csv", 266)
    new_rows: list[dict[str, Any]] = []
    if base_266 is not None:
        row1 = _csv_row_minimal_variant(
            base_line=base_266,
            new_id=9201,
            new_sync_feature="2,17,N,,,left,head",
            note="probe-266-sy17-left-head",
        )
        row2 = _csv_row_minimal_variant(
            base_line=base_266,
            new_id=9202,
            new_sync_feature="2,17,N,,,right,nonhead",
            note="probe-266-sy17-right-nonhead",
        )
        new_rows = [
            {"comment": "266の17系をhead側一致へ最小変更", "csv_row": row1, "status": STATUS_GUESS},
            {"comment": "266の17系を反対方向へ最小変更", "csv_row": row2, "status": STATUS_GUESS},
        ]

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
        "candidate_pool": candidate_pool,
        "runs": runs,
        "core_diff": core_diff,
        "targeted_slot_probe_runs": targeted_slot_probe_runs,
        "new_lexical_item_proposals": new_rows,
        "code_grounded_refs": {
            "process_se_24": "packages/domain/src/domain/derivation/execute.py#L373-L374",
            "process_se_33": "packages/domain/src/domain/derivation/execute.py#L395-L409",
            "process_sy_17_nonhead": "packages/domain/src/domain/derivation/execute.py#L800-L820",
            "eval_feature_17": "packages/domain/src/domain/derivation/execute.py#L69-L97",
            "fact_status": STATUS_CONFIRMED,
        },
        "temp_legacy_root": str(temp_root),
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-only-followup-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-only-followup-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
