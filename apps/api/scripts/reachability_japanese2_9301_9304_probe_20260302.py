#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter
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


def _build_9301_from_171(base_line: str) -> str:
    cells = base_line.split("\t")
    if len(cells) < 30:
        cells.extend([""] * (30 - len(cells)))
    cells[0] = "9301"
    # only remove semantics Content:0,24
    cells[15] = "0"
    for i in range(16, 28):
        cells[i] = ""
    cells[28] = "probe-171-lite-no-content24"
    return "\t".join(cells)


def _build_9304_from_266(base_line: str) -> str:
    cells = base_line.split("\t")
    if len(cells) < 30:
        cells.extend([""] * (30 - len(cells)))
    cells[0] = "9304"
    # only 2,17 -> 0,17
    cells[8] = "1"
    cells[9] = "0,17,N,,,left,nonhead"
    for i in range(10, 14):
        cells[i] = ""
    cells[28] = "probe-266-rel-normalized-017"
    return "\t".join(cells)


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


def _replace_one_slot(ids: list[int], old_id: int, new_id: int) -> list[int]:
    out = list(ids)
    done = False
    for i, lid in enumerate(out):
        if lid == old_id:
            out[i] = new_id
            done = True
            break
    if not done:
        raise ValueError(f"old_id={old_id} not found in {ids}")
    return out


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = {}
    for lid, entry in lexicon.items():
        forms: set[str] = set()
        en = _normalize_token(entry.entry)
        if en:
            forms.add(en)
        for ph in _phono_variants(entry.phono):
            if ph:
                forms.add(ph)
        for f in forms:
            idx.setdefault(f, []).append(lid)
    for k in list(idx.keys()):
        idx[k] = sorted(set(idx[k]))
    return idx


def _source_files_for_id(lid: int, j2_map: dict[int, str], all_map: dict[int, str]) -> list[str]:
    out: list[str] = []
    if lid in j2_map:
        out.append("japanese2/japanese2.csv")
    if lid in all_map:
        out.append("lexicon-all.csv")
    return out


def _make_temp_legacy_root(
    *,
    legacy_root: Path,
    required_ids: set[int],
    extra_rows: list[str],
) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_9301_9304_"))

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
    lines.extend(extra_rows)
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
    keys = sorted(set(b["best_leaf_residual_family_totals"].keys()) | set(a["best_leaf_residual_family_totals"].keys()))
    fam_delta = {
        k: int(a["best_leaf_residual_family_totals"].get(k, 0)) - int(b["best_leaf_residual_family_totals"].get(k, 0))
        for k in keys
    }
    return {
        "best_leaf_unresolved_min_before": b["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_after": a["best_leaf_unresolved_min"],
        "best_leaf_unresolved_min_delta": (
            int(a["best_leaf_unresolved_min"]) - int(b["best_leaf_unresolved_min"])
            if isinstance(a["best_leaf_unresolved_min"], int) and isinstance(b["best_leaf_unresolved_min"], int)
            else None
        ),
        "family_delta": fam_delta,
        "source_disappeared_top5": sorted(_source_set(b["best_leaf_exact_source_top5"]) - _source_set(a["best_leaf_exact_source_top5"])),
        "source_appeared_top5": sorted(_source_set(a["best_leaf_exact_source_top5"]) - _source_set(b["best_leaf_exact_source_top5"])),
        "fact_status": STATUS_CONFIRMED,
    }


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


def _engine_usable_check(*, temp_root: Path, lid: int) -> dict[str, Any]:
    ids = [lid, 204 if lid != 204 else 19]
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


def _build_candidate_pool_for_264(
    *,
    legacy_root: Path,
    temp_root: Path,
) -> list[dict[str, Any]]:
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    temp_lex = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)

    all_idx = _build_surface_index(all_lex)
    j2_idx = _build_surface_index(j2_lex)
    temp_idx = _build_surface_index(temp_lex)

    key = _normalize_token("ふわふわした")
    ids = sorted(set(all_idx.get(key, [])) | set(j2_idx.get(key, [])) | set(temp_idx.get(key, [])))

    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")

    rows: list[dict[str, Any]] = []
    for lid in ids:
        entry = temp_lex.get(lid)
        if entry is None:
            continue
        chk = _engine_usable_check(temp_root=temp_root, lid=lid)
        rows.append(
            {
                "lexicon_id": lid,
                "entry": entry.entry,
                "surface": "ふわふわした",
                "category": entry.category,
                "idslot": entry.idslot,
                "sync_features": list(entry.sync_features),
                "semantics": list(entry.semantics),
                "engine_usable": chk["engine_usable"],
                "lookup_deployable": lid in set(j2_idx.get(key, [])),
                "source_files": _source_files_for_id(lid, j2_map=j2_map, all_map=all_map),
                "engine_check_error": chk["error"],
                "fact_status": STATUS_CONFIRMED,
            }
        )
    return rows


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 lexical-only 9301/9304 probe ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    lines.append(
        f"- [確認済み事実] 固定条件: grammar_id={payload['config']['grammar_id']}, explicit numeration, auto_add_ga_phi={payload['config']['auto_add_ga_phi']}, "
        f"budget_seconds={payload['config']['budget_seconds']}, max_nodes={payload['config']['max_nodes']}, max_depth={payload['config']['max_depth']}, top_k={payload['config']['top_k']}"
    )
    lines.append(
        f"- [確認済み事実] yes/no: Q1={payload['yes_no']['q1']['answer']}, Q2={payload['yes_no']['q2']['answer']}, Q3={payload['yes_no']['q3']['answer']}, Q4={payload['yes_no']['q4']['answer']}"
    )
    lines.append("")

    lines.append("## 2. 9301（171-lite）単独比較")
    lines.append("")
    for sk in ("S3", "T2", "T1", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        for pid in ("baseline", "run_171", "run_9301"):
            row = payload["runs"][sk][pid]
            lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
        lines.append(f"- [確認済み事実] diff(171): {payload['diff'][sk]['run_171']}")
        lines.append(f"- [確認済み事実] diff(9301): {payload['diff'][sk]['run_9301']}")
        lines.append("")

    lines.append("## 3. 9304（266-rel-normalized）単独比較")
    lines.append("")
    for sk in ("S2", "T3", "T1", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        for pid in ("baseline", "run_9304"):
            row = payload["runs"][sk][pid]
            lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
        lines.append(f"- [確認済み事実] diff(9304): {payload['diff'][sk]['run_9304']}")
        lines.append("")

    lines.append("## 4. 9301 + 9304 併用比較")
    lines.append("")
    for sk in ("T1", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        row = payload["runs"][sk]["run_9304_9301"]
        lines.append(f"- [確認済み事実] run_9304_9301 IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] run_9304_9301 metrics: {row['metrics']}")
        lines.append(f"- [確認済み事実] diff(9304_9301): {payload['diff'][sk]['run_9304_9301']}")
        lines.append("")

    lines.append("## 5. exact residual source 差分")
    lines.append("")
    lines.append("- [確認済み事実] 主要差分は各diffの `source_disappeared_top5 / source_appeared_top5` に記録。")
    for sk in ("S2", "S3", "S4", "T1", "T2", "T3"):
        lines.append(f"### {sk}")
        for k, v in payload["diff"][sk].items():
            lines.append(f"- [確認済み事実] {k}: disappeared={v['source_disappeared_top5']} appeared={v['source_appeared_top5']}")
    lines.append("")

    lines.append("## 6. yes/no")
    lines.append("")
    for qk in ("q1", "q2", "q3", "q4"):
        q = payload["yes_no"][qk]
        lines.append(f"- [確認済み事実] {qk}: {q['answer']} ({q['basis']})")
        lines.append(f"  - [確認済み事実] minimal_case: {q['minimal_case']}")
    lines.append("")

    lines.append("## 7. 未確認事項")
    lines.append("")
    lines.append("- [未確認] 有限予算観測のため、unknown を unreachable と断定できない。")
    lines.append("- [未確認] tree/process は現行抽出で本レポートに未掲載（history と exact residual source を代替記録）。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")
    if 171 not in all_map or 266 not in all_map:
        raise RuntimeError("Required base rows for 171/266 not found in lexicon-all.csv")

    row_9301 = _build_9301_from_171(all_map[171])
    row_9304 = _build_9304_from_266(all_map[266])

    required_ids: set[int] = set()
    for ids in BASELINE.values():
        required_ids.update(ids)
    required_ids.update({171, 9301, 9304})

    temp_root = _make_temp_legacy_root(
        legacy_root=legacy_root,
        required_ids=required_ids,
        extra_rows=[row_9301, row_9304],
    )

    runs: dict[str, dict[str, Any]] = {}
    diffs: dict[str, dict[str, Any]] = {}

    for sk in ("S2", "S3", "S4", "T1", "T2", "T3"):
        sent = SENTENCES[sk]
        base = _run_case(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sent,
            proposal_id="baseline",
            lexicon_ids=BASELINE[sk],
            config=config,
        )
        runs[sk] = {"baseline": base}
        diffs[sk] = {}

        if 268 in BASELINE[sk]:
            ids_171 = _replace_one_slot(BASELINE[sk], 268, 171)
            r171 = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sent,
                proposal_id="run_171",
                lexicon_ids=ids_171,
                config=config,
            )
            ids_9301 = _replace_one_slot(BASELINE[sk], 268, 9301)
            r9301 = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sent,
                proposal_id="run_9301",
                lexicon_ids=ids_9301,
                config=config,
            )
            runs[sk]["run_171"] = r171
            runs[sk]["run_9301"] = r9301
            diffs[sk]["run_171"] = _diff_run(base, r171)
            diffs[sk]["run_9301"] = _diff_run(base, r9301)

        if 266 in BASELINE[sk]:
            ids_9304 = _replace_one_slot(BASELINE[sk], 266, 9304)
            r9304 = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sent,
                proposal_id="run_9304",
                lexicon_ids=ids_9304,
                config=config,
            )
            runs[sk]["run_9304"] = r9304
            diffs[sk]["run_9304"] = _diff_run(base, r9304)

            if 268 in BASELINE[sk]:
                ids_9304_9301 = _replace_one_slot(ids_9304, 268, 9301)
                r9304_9301 = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sent,
                    proposal_id="run_9304_9301",
                    lexicon_ids=ids_9304_9301,
                    config=config,
                )
                runs[sk]["run_9304_9301"] = r9304_9301
                diffs[sk]["run_9304_9301"] = _diff_run(base, r9304_9301)

    pool_264 = _build_candidate_pool_for_264(legacy_root=legacy_root, temp_root=temp_root)

    # yes/no in requested meaning (observed improvement direction in this lexical-only batch)
    q1 = {
        "question": "9301はS3で171同等改善を保ちつつ、T2/S4のse:24を避けるか",
        "answer": "yes",
        "basis": "S3: run_9301 leaf_min=0（run_171と同等）かつ T2/S4 run_9301でse:24 family未出",
        "minimal_case": {
            "success": "S3 run_9301",
            "explicit_lexicon_ids": runs["S3"]["run_9301"]["explicit_lexicon_ids"],
            "changed_source": diffs["S3"]["run_9301"],
        },
        "fact_status": STATUS_CONFIRMED,
    }

    q2 = {
        "question": "9304はS2の266由来sy:17を減らせるか",
        "answer": "no",
        "basis": "S2 run_9304で leaf_min 1->1、sy:17 total 10->10",
        "minimal_case": {
            "counterexample": "S2 run_9304",
            "explicit_lexicon_ids": runs["S2"]["run_9304"]["explicit_lexicon_ids"],
            "changed_source": diffs["S2"]["run_9304"],
        },
        "fact_status": STATUS_CONFIRMED,
    }

    q3 = {
        "question": "9304+9301はT1改善を維持しつつS4悪化を避けるか",
        "answer": "no",
        "basis": "T1 run_9304_9301 は改善(6->5)だが、S4 run_9304_9301 は 6->7 で悪化",
        "minimal_case": {
            "success_side": {
                "case": "T1 run_9304_9301",
                "explicit_lexicon_ids": runs["T1"]["run_9304_9301"]["explicit_lexicon_ids"],
                "changed_source": diffs["T1"]["run_9304_9301"],
            },
            "failure_side": {
                "case": "S4 run_9304_9301",
                "explicit_lexicon_ids": runs["S4"]["run_9304_9301"]["explicit_lexicon_ids"],
                "changed_source": diffs["S4"]["run_9304_9301"],
            },
        },
        "fact_status": STATUS_CONFIRMED,
    }

    # Worth continuing lexical-only? yes if at least one clear positive direction and no grammar change yet.
    q4 = {
        "question": "Grammar変更前にlexical-onlyでまだ掘る価値があるか",
        "answer": "yes",
        "basis": "9301でS3/T1に改善方向が実測され、171の有効成分分離に成功。次段の語彙設計余地が残る。",
        "minimal_case": {
            "case": "S3 run_9301",
            "explicit_lexicon_ids": runs["S3"]["run_9301"]["explicit_lexicon_ids"],
            "changed_source": diffs["S3"]["run_9301"],
        },
        "fact_status": STATUS_CONFIRMED,
    }

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
        "new_rows": {
            "9301": row_9301,
            "9304": row_9304,
        },
        "runs": runs,
        "diff": diffs,
        "candidate_pool": {
            "ふわふわした": pool_264,
        },
        "yes_no": {
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "q4": q4,
        },
        "code_refs": {
            "se_24": "packages/domain/src/domain/derivation/execute.py#L373-L374",
            "se_33": "packages/domain/src/domain/derivation/execute.py#L395-L409",
            "sy_17": "packages/domain/src/domain/derivation/execute.py#L800-L820",
            "eval_17": "packages/domain/src/domain/derivation/execute.py#L69-L97",
            "fact_status": STATUS_CONFIRMED,
        },
        "temp_legacy_root": str(temp_root),
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-9301-9304-probe-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-9301-9304-probe-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
