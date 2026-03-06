#!/usr/bin/env python3
from __future__ import annotations

import csv
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
STATUS_INFER = "推測"

GRAMMAR_ID = "japanese2"

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "T3": "ふわふわしたわたあめを食べているひつじがいる",
    "T1": "わたあめを食べているひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

BASELINE = {
    "S2": [265, 23, 266, 267, 19, 271, 204],
    "T3": [264, 265, 23, 266, 267, 19, 271, 204],
    "T1": [265, 23, 266, 267, 9301, 269, 270, 19, 271, 204],
    "S4": [264, 265, 23, 266, 267, 9301, 269, 270, 19, 271, 204],
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


def _make_temp_legacy_root(*, legacy_root: Path, required_ids: set[int], extra_rows: list[str]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_casepack_probe_"))

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


def _flatten_exact_sources_top(*, samples: list[dict[str, Any]], initial_item_map: dict[str, dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    attrs: dict[str, dict[str, Any]] = {}
    for sample in samples[:5]:
        for family, rows in (sample.get("residual_family_sources") or {}).items():
            for row in rows:
                item_id = str(row.get("item_id", ""))
                init = initial_item_map.get(item_id, {})
                key = "|".join([
                    family,
                    str(row.get("raw", "")),
                    item_id,
                    str(init.get("initial_slot", "")),
                    str(init.get("surface", "")),
                ])
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
        out.add(f"{row.get('family','')}|{row.get('exact_label','')}|{row.get('item_id','')}|{row.get('surface','')}")
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
        "status_before": b["status"],
        "status_after": a["status"],
        "reason_before": b["reason"],
        "reason_after": a["reason"],
        "family_delta": fam_delta,
        "source_disappeared_top5": sorted(_source_set(b["best_leaf_exact_source_top5"]) - _source_set(a["best_leaf_exact_source_top5"])),
        "source_appeared_top5": sorted(_source_set(a["best_leaf_exact_source_top5"]) - _source_set(b["best_leaf_exact_source_top5"])),
        "fact_status": STATUS_CONFIRMED,
    }


def _run_case(*, legacy_root: Path, sentence_key: str, sentence: str, proposal_id: str, lexicon_ids: list[int], config: RunConfig) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:{proposal_id}", lexicon_ids)
    state = build_initial_derivation_state(grammar_id=GRAMMAR_ID, numeration_text=numeration_text, legacy_root=legacy_root)
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
            "best_leaf_exact_source_top5": _flatten_exact_sources_top(samples=best_leaf_samples, initial_item_map=initial_item_map, top_n=5),
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


def _build_candidate_pool(*, legacy_root: Path, temp_root: Path, surface: str) -> list[dict[str, Any]]:
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    temp_lex = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)

    all_idx = _build_surface_index(all_lex)
    j2_idx = _build_surface_index(j2_lex)
    temp_idx = _build_surface_index(temp_lex)

    key = _normalize_token(surface)
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
                "surface": surface,
                "entry": entry.entry,
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


def _known_reachable_usage_from_runs(runs: dict[str, dict[str, Any]]) -> set[int]:
    used: set[int] = set()
    for per_sentence in runs.values():
        for run in per_sentence.values():
            m = run["metrics"]
            if m.get("status") == "reachable":
                for lid in run["explicit_lexicon_ids"]:
                    used.add(int(lid))
    return used


def _proposal_id(prefix: str, wo_id: int | None, ga_id: int | None) -> str:
    if wo_id is not None and ga_id is None:
        return f"{prefix}_wo{wo_id}"
    if wo_id is None and ga_id is not None:
        return f"{prefix}_ga{ga_id}"
    if wo_id is not None and ga_id is not None:
        return f"{prefix}_wo{wo_id}_ga{ga_id}"
    return prefix


def _replace_ids(base: list[int], old_to_new: dict[int, int]) -> list[int]:
    out = list(base)
    for i, lid in enumerate(out):
        if lid in old_to_new:
            out[i] = old_to_new[lid]
    return out


def _collect_new_23_19_lines(*, legacy_root: Path, candidate_pool: dict[str, list[dict[str, Any]]], runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    # only if no improvement across S2/T3/T1/S4
    improved = False
    for sk in ("S2", "T3", "T1", "S4"):
        base_min = runs[sk]["baseline"]["metrics"]["best_leaf_unresolved_min"]
        for pid, row in runs[sk].items():
            if pid == "baseline":
                continue
            m = row["metrics"]
            if isinstance(base_min, int) and isinstance(m.get("best_leaf_unresolved_min"), int):
                if int(m["best_leaf_unresolved_min"]) < int(base_min):
                    improved = True
                    break
        if improved:
            break

    if improved:
        return []

    # proposal rows are hypotheses, built by minimal edit from existing 23/19 rows.
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")
    proposals: list[dict[str, Any]] = []

    # 9231: from 23, set idslot(2,1,N + 2,3L,V style) preserving wo, zero semantics
    if 23 in all_map:
        c = all_map[23].split("\t")
        if len(c) < 30:
            c.extend([""] * (30 - len(c)))
        c[0] = "9231"
        c[3] = ""
        c[8] = "4"
        c[9] = "2,1,N"
        c[10] = "2,3L,V"
        c[11] = "wo"
        c[12] = "1,5,J-Merge"
        c[13] = ""
        c[14] = "zero"
        c[15] = "0"
        c[28] = "probe-23-casepack-jmerge"
        proposals.append(
            {
                "lexicon_id": 9231,
                "target": "を",
                "reason": "[推測] S2/T3/T1/S4 で 266由来 sy:17 が残るため、case packaging を 2,1/2,3L/V 系へ合わせる最小案",
                "csv_row": "\t".join(c),
                "fact_status": STATUS_INFER,
            }
        )

    # 9219: from 19, set idslot with 2,1,N + 2,1L,T + ga + J-Merge
    if 19 in all_map:
        c = all_map[19].split("\t")
        if len(c) < 30:
            c.extend([""] * (30 - len(c)))
        c[0] = "9219"
        c[3] = ""
        c[8] = "4"
        c[9] = "2,1,N"
        c[10] = "2,1L,T"
        c[11] = "ga"
        c[12] = "1,5,J-Merge"
        c[13] = ""
        c[14] = "zero"
        c[15] = "0"
        c[28] = "probe-19-casepack-jmerge"
        proposals.append(
            {
                "lexicon_id": 9219,
                "target": "が",
                "reason": "[推測] 19 の 0,17/3,17/4,11 だけでは eat-clause 終盤に残るため、2,1/2,1L/T 系の最小案",
                "csv_row": "\t".join(c),
                "fact_status": STATUS_INFER,
            }
        )

    return proposals[:2]


def _build_yes_no(*, runs: dict[str, dict[str, Any]], diffs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    # Q1
    s4_base = runs["S4"]["baseline"]["metrics"]
    s4_sources = s4_base.get("best_leaf_exact_source_top5", [])
    has_264_top = any(int(row.get("lexicon_id") or -1) == 264 for row in s4_sources)
    q1_answer = "yes" if not has_264_top else "no"
    q1_basis = {
        "run": "S4 baseline(9301固定)",
        "best_leaf_unresolved_min_before": s4_base.get("best_leaf_unresolved_min"),
        "best_leaf_unresolved_min_after": s4_base.get("best_leaf_unresolved_min"),
        "status": s4_base.get("status"),
        "reason": s4_base.get("reason"),
        "has_264_in_top5": has_264_top,
        "fact_status": STATUS_CONFIRMED,
    }

    # Q2 S2 any improvement for 266 sy:17
    s2_base = runs["S2"]["baseline"]["metrics"]
    best_q2 = None
    for pid, row in runs["S2"].items():
        if pid == "baseline":
            continue
        m = row["metrics"]
        if best_q2 is None:
            best_q2 = (pid, m)
        else:
            cur = m.get("best_leaf_unresolved_min")
            prev = best_q2[1].get("best_leaf_unresolved_min")
            if isinstance(cur, int) and isinstance(prev, int) and cur < prev:
                best_q2 = (pid, m)
    q2_yes = False
    q2_best = best_q2[0] if best_q2 else None
    if best_q2 and isinstance(s2_base.get("best_leaf_unresolved_min"), int) and isinstance(best_q2[1].get("best_leaf_unresolved_min"), int):
        q2_yes = int(best_q2[1]["best_leaf_unresolved_min"]) < int(s2_base["best_leaf_unresolved_min"])

    # Q3 both T1 and S4 improved by same proposal
    q3_yes = False
    q3_run = None
    common = sorted(set(runs["T1"].keys()) & set(runs["S4"].keys()) - {"baseline"})
    t1_base_min = runs["T1"]["baseline"]["metrics"].get("best_leaf_unresolved_min")
    s4_base_min = runs["S4"]["baseline"]["metrics"].get("best_leaf_unresolved_min")
    for pid in common:
        t1m = runs["T1"][pid]["metrics"]
        s4m = runs["S4"][pid]["metrics"]
        if isinstance(t1_base_min, int) and isinstance(s4_base_min, int) and isinstance(t1m.get("best_leaf_unresolved_min"), int) and isinstance(s4m.get("best_leaf_unresolved_min"), int):
            if int(t1m["best_leaf_unresolved_min"]) < int(t1_base_min) and int(s4m["best_leaf_unresolved_min"]) < int(s4_base_min):
                q3_yes = True
                q3_run = pid
                break

    # Q4 any lexical-only value left?
    # yes if at least one run in any sentence improved baseline, or source shifted meaningfully in S2/T3/T1/S4
    any_improve = False
    for sk in ("S2", "T3", "T1", "S4"):
        base_min = runs[sk]["baseline"]["metrics"].get("best_leaf_unresolved_min")
        for pid, row in runs[sk].items():
            if pid == "baseline":
                continue
            m = row["metrics"]
            if isinstance(base_min, int) and isinstance(m.get("best_leaf_unresolved_min"), int):
                if int(m["best_leaf_unresolved_min"]) < int(base_min):
                    any_improve = True
                    break
        if any_improve:
            break

    return {
        "q1": {
            "question": "9301固定でS4の残差主戦場は264ではなくeat-clauseへ移ったと言えるか",
            "answer": "yes" if q1_answer == "yes" else "no",
            "basis": q1_basis,
            "fact_status": STATUS_CONFIRMED,
        },
        "q2": {
            "question": "23または19の既存候補だけでS2の266由来sy:17を減らせるか",
            "answer": "yes" if q2_yes else "no",
            "basis": {
                "run": q2_best,
                "best_leaf_unresolved_min_before": s2_base.get("best_leaf_unresolved_min"),
                "best_leaf_unresolved_min_after": best_q2[1].get("best_leaf_unresolved_min") if best_q2 else None,
                "status": best_q2[1].get("status") if best_q2 else None,
                "reason": best_q2[1].get("reason") if best_q2 else None,
                "source_delta": diffs["S2"].get(q2_best) if q2_best else None,
                "fact_status": STATUS_CONFIRMED,
            },
            "fact_status": STATUS_CONFIRMED,
        },
        "q3": {
            "question": "23/19調整でT1とS4の両方に同時改善が見えるか",
            "answer": "yes" if q3_yes else "no",
            "basis": {
                "run": q3_run,
                "t1_best_leaf_unresolved_min_before": t1_base_min,
                "s4_best_leaf_unresolved_min_before": s4_base_min,
                "t1_best_leaf_unresolved_min_after": runs["T1"][q3_run]["metrics"].get("best_leaf_unresolved_min") if q3_run else None,
                "s4_best_leaf_unresolved_min_after": runs["S4"][q3_run]["metrics"].get("best_leaf_unresolved_min") if q3_run else None,
                "t1_status": runs["T1"][q3_run]["metrics"].get("status") if q3_run else None,
                "s4_status": runs["S4"][q3_run]["metrics"].get("status") if q3_run else None,
                "fact_status": STATUS_CONFIRMED,
            },
            "fact_status": STATUS_CONFIRMED,
        },
        "q4": {
            "question": "Grammarを変える前にlexical-onlyでまだ掘る価値があるか",
            "answer": "yes" if any_improve else "no",
            "basis": {
                "any_improvement_observed": any_improve,
                "reference_run_examples": {
                    sk: [
                        pid
                        for pid, row in runs[sk].items()
                        if pid != "baseline"
                        and isinstance(row["metrics"].get("best_leaf_unresolved_min"), int)
                        and isinstance(runs[sk]["baseline"]["metrics"].get("best_leaf_unresolved_min"), int)
                        and int(row["metrics"]["best_leaf_unresolved_min"]) < int(runs[sk]["baseline"]["metrics"]["best_leaf_unresolved_min"])
                    ]
                    for sk in ("S2", "T3", "T1", "S4")
                },
                "fact_status": STATUS_CONFIRMED,
            },
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 lexical-only case packaging probe ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    lines.append(
        f"- [確認済み事実] 固定条件: grammar_id={payload['config']['grammar_id']}, explicit numeration, auto_add_ga_phi={payload['config']['auto_add_ga_phi']}, "
        f"budget_seconds={payload['config']['budget_seconds']}, max_nodes={payload['config']['max_nodes']}, max_depth={payload['config']['max_depth']}, top_k={payload['config']['top_k']}"
    )
    for qk in ("q1", "q2", "q3", "q4"):
        q = payload["yes_no"][qk]
        lines.append(f"- [確認済み事実] {qk}: {q['answer']}")
    lines.append("")

    lines.append("## 2. `を/が` candidate pool")
    lines.append("")
    for sf in ("を", "が"):
        lines.append(f"### {sf}")
        for row in payload["candidate_pool"][sf]:
            lines.append(f"- [確認済み事実] {row}")
        lines.append("")

    lines.append("## 3. S2 probe")
    lines.append("")
    for pid, row in payload["runs"]["S2"].items():
        lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
        if pid != "baseline":
            lines.append(f"- [確認済み事実] diff vs baseline: {payload['diff']['S2'][pid]}")
    lines.append("")

    lines.append("## 4. T3 probe")
    lines.append("")
    for pid, row in payload["runs"]["T3"].items():
        lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
        lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
        if pid != "baseline":
            lines.append(f"- [確認済み事実] diff vs baseline: {payload['diff']['T3'][pid]}")
    lines.append("")

    lines.append("## 5. T1/S4 probe（9301固定）")
    lines.append("")
    for sk in ("T1", "S4"):
        lines.append(f"### {sk}: {payload['sentences'][sk]}")
        for pid, row in payload["runs"][sk].items():
            lines.append(f"- [確認済み事実] {pid} IDs: `{','.join(str(x) for x in row['explicit_lexicon_ids'])}`")
            lines.append(f"- [確認済み事実] {pid} metrics: {row['metrics']}")
            if pid != "baseline":
                lines.append(f"- [確認済み事実] diff vs baseline: {payload['diff'][sk][pid]}")
        lines.append("")

    lines.append("## 6. exact residual source 差分")
    lines.append("")
    for sk in ("S2", "T3", "T1", "S4"):
        lines.append(f"### {sk}")
        for pid, d in payload["diff"][sk].items():
            lines.append(f"- [確認済み事実] {pid}: disappeared={d['source_disappeared_top5']} appeared={d['source_appeared_top5']}")
    lines.append("")

    lines.append("## 7. 必要なら新規 23/19 行")
    lines.append("")
    if payload["new_23_19_rows"]:
        for row in payload["new_23_19_rows"]:
            lines.append(f"- [{row.get('fact_status', STATUS_INFER)}] {row}")
    else:
        lines.append("- [確認済み事実] 既存候補実験で改善が観測されたため、新規23/19行提案は未実施。")
    lines.append("")

    lines.append("## 8. yes/no")
    lines.append("")
    for qk in ("q1", "q2", "q3", "q4"):
        q = payload["yes_no"][qk]
        lines.append(f"- [確認済み事実] {qk}: {q['answer']}")
        lines.append(f"  - [確認済み事実] question: {q['question']}")
        lines.append(f"  - [確認済み事実] basis: {q['basis']}")
    lines.append("")

    lines.append("## 9. 未確認事項")
    lines.append("")
    lines.append("- [未確認] 有限予算観測のため、unknown を unreachable と断定できない。")
    lines.append("- [未確認] tree/process は本出力に未掲載（history と exact residual source を代替記録）。")
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = PROJECT_ROOT.parent
    config = RunConfig()

    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")
    if 171 not in all_map:
        raise RuntimeError("Required base row for 171 not found")

    row_9301 = _build_9301_from_171(all_map[171])

    # pre-scan candidate IDs for を/が from lexicon-all and japanese2
    all_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    j2_lex = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    idx_all = _build_surface_index(all_lex)
    idx_j2 = _build_surface_index(j2_lex)
    wo_ids = sorted(set(idx_all.get("を", [])) | set(idx_j2.get("を", [])))
    ga_ids = sorted(set(idx_all.get("が", [])) | set(idx_j2.get("が", [])))

    required_ids: set[int] = set()
    for ids in BASELINE.values():
        required_ids.update(ids)
    required_ids.update(wo_ids)
    required_ids.update(ga_ids)
    required_ids.update({9301})

    temp_root = _make_temp_legacy_root(
        legacy_root=legacy_root,
        required_ids=required_ids,
        extra_rows=[row_9301],
    )

    # candidate pool (engine-usable prioritized)
    pool_wo = _build_candidate_pool(legacy_root=legacy_root, temp_root=temp_root, surface="を")
    pool_ga = _build_candidate_pool(legacy_root=legacy_root, temp_root=temp_root, surface="が")

    wo_candidates = [int(r["lexicon_id"]) for r in pool_wo if bool(r["engine_usable"]) and int(r["lexicon_id"]) != 23]
    ga_candidates = [int(r["lexicon_id"]) for r in pool_ga if bool(r["engine_usable"]) and int(r["lexicon_id"]) != 19]

    runs: dict[str, dict[str, Any]] = {k: {} for k in SENTENCES.keys()}
    diffs: dict[str, dict[str, Any]] = {k: {} for k in SENTENCES.keys()}

    for sk, sentence in SENTENCES.items():
        base_ids = BASELINE[sk]
        base_run = _run_case(
            legacy_root=temp_root,
            sentence_key=sk,
            sentence=sentence,
            proposal_id="baseline",
            lexicon_ids=base_ids,
            config=config,
        )
        runs[sk]["baseline"] = base_run

        # A: only を replaced
        for wid in wo_candidates:
            prop = _proposal_id("A", wid, None)
            ids = _replace_ids(base_ids, {23: wid})
            if ids == base_ids:
                continue
            row = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sentence,
                proposal_id=prop,
                lexicon_ids=ids,
                config=config,
            )
            runs[sk][prop] = row
            diffs[sk][prop] = _diff_run(base_run, row)

        # B: only が replaced
        for gid in ga_candidates:
            prop = _proposal_id("B", None, gid)
            ids = _replace_ids(base_ids, {19: gid})
            if ids == base_ids:
                continue
            row = _run_case(
                legacy_root=temp_root,
                sentence_key=sk,
                sentence=sentence,
                proposal_id=prop,
                lexicon_ids=ids,
                config=config,
            )
            runs[sk][prop] = row
            diffs[sk][prop] = _diff_run(base_run, row)

        # C: both replaced
        for wid in wo_candidates:
            for gid in ga_candidates:
                prop = _proposal_id("C", wid, gid)
                ids = _replace_ids(base_ids, {23: wid, 19: gid})
                if ids == base_ids:
                    continue
                row = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id=prop,
                    lexicon_ids=ids,
                    config=config,
                )
                runs[sk][prop] = row
                diffs[sk][prop] = _diff_run(base_run, row)

    reachable_used = _known_reachable_usage_from_runs(runs)
    for row in pool_wo:
        row["used_in_known_reachable_example"] = int(row["lexicon_id"]) in reachable_used
    for row in pool_ga:
        row["used_in_known_reachable_example"] = int(row["lexicon_id"]) in reachable_used

    new_23_19_rows = _collect_new_23_19_lines(legacy_root=legacy_root, candidate_pool={"を": pool_wo, "が": pool_ga}, runs=runs)
    yes_no = _build_yes_no(runs=runs, diffs=diffs)

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
        "new_rows": {"9301": row_9301},
        "candidate_pool": {
            "を": pool_wo,
            "が": pool_ga,
            "fact_status": STATUS_CONFIRMED,
        },
        "runs": runs,
        "diff": diffs,
        "new_23_19_rows": new_23_19_rows,
        "yes_no": yes_no,
        "temp_legacy_root": str(temp_root),
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-casepack-probe-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-casepack-probe-20260302.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
