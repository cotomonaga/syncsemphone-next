#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Optional

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _canonical_tree_signature,
    _generate_numeration_with_unknown_token_fallback,
    _search_reachability,
    _select_tree_root,
)
from domain.derivation.execute import execute_double_merge, execute_single_merge  # noqa: E402
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.lexicon.models import LexiconEntry  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402
from domain.resume.codec import export_process_text_like_perl  # noqa: E402

STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"
STATUS_GUESS = "推測"

GRAMMAR_ID = "imi01"
TARGET_SURFACES = [
    "ふわふわした",
    "わたあめ",
    "を",
    "食べている",
    "ひつじ",
    "と",
    "話している",
    "うさぎ",
    "が",
    "いる",
    "る",
    "φ",
]

SENTENCES = {
    "S1": "うさぎがいる",
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
    "S5": "ふわふわしたひつじがいる",
    "S6": "ふわふわしたわたあめを食べているひつじがいる",
}

# hard reject 判定用の主語期待（依頼文に従って reduced sentence ごとに読み替え）
EXPECTED_SUBJECT = {
    "S1": "うさぎ",
    "S2": "ひつじ",
    "S3": "うさぎ",
    "S4": "うさぎ",
    "S5": "ひつじ",
    "S6": "ひつじ",
}

# 既知到達例（tests/test_derivation.py の known_reachable_sets より）
KNOWN_REACHABLE_IDS = {
    60, 19, 103, 23, 61, 168, 187, 203,
    270, 271, 204, 308,
}

NEW_LEXICAL_ROWS: list[dict[str, Any]] = [
    {
        "lexicon_id": 9301,
        "proposal_name": "to_171_lite",
        "csv_row": "9301 \tと\tと\tZ\t0 \t\t\t\t\t1\tto\t\t\t\t\t\t\t2,22\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:171-lite\t0",
        "rationale": "171 の Content:0,24 を外し、S3 で観測された局所改善（to側）を維持しつつ、S4 の 24系副作用を避ける狙い。",
    },
    {
        "lexicon_id": 9401,
        "proposal_name": "eat_progressive_rc_lite",
        "csv_row": "9401 \t食べている\t食べている\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \tTheme\t2,33,wo\t食べる\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:eat-rc-lite\t0",
        "rationale": "266 の Agent 要求を lexical 側で緩和し、S2/S4 の se:33 パケット（食べ-clause側）を縮められるかを確認する狙い。",
    },
    {
        "lexicon_id": 9402,
        "proposal_name": "talk_progressive_rc_lite",
        "csv_row": "9402 \t話している\t話している\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \t相手\t2,33,to\t話す\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:talk-rc-lite\t0",
        "rationale": "269 の Agent 要求を lexical 側で緩和し、S3/S4 の se:33 パケット（話す-clause側）を縮められるかを確認する狙い。",
    },
]


@dataclass(frozen=True)
class RunConfig:
    split_mode: str = "C"
    budget_seconds: float = 20.0
    max_nodes: int = 120000
    max_depth: int = 28
    top_k: int = 10


def _normalize_token(token: str) -> str:
    return token.strip().replace("　", "").replace(" ", "").replace("-", "")


def _phono_variants(phono: str) -> list[str]:
    out: list[str] = []
    normalized = _normalize_token(phono)
    if normalized:
        out.append(normalized)
    stripped = normalized.strip("-")
    if stripped and stripped != normalized:
        out.append(stripped)
    return out


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = defaultdict(list)
    for lid, entry in lexicon.items():
        seen: set[str] = set()
        ent = _normalize_token(entry.entry)
        if ent:
            seen.add(ent)
        for v in _phono_variants(entry.phono):
            if v:
                seen.add(v)
        for s in sorted(seen):
            idx[s].append(lid)
    return dict(idx)


def _extract_sync_codes(entry: LexiconEntry) -> set[str]:
    out: set[str] = set()
    for feat in entry.sync_features:
        parts = [p.strip() for p in feat.split(",")]
        if len(parts) >= 2 and parts[1]:
            out.add(parts[1])
    return out


def _extract_rule_markers(entry: LexiconEntry) -> list[str]:
    markers = (
        "RH-Merge",
        "LH-Merge",
        "J-Merge",
        "P-Merge",
        "rel-Merge",
        "property-Merge",
        "property-no",
        "property-da",
        "sase1",
        "sase2",
        "rare1",
        "rare2",
        "Pickup",
        "Landing",
        "Partitioning",
        "zero-Merge",
    )
    values = list(entry.sync_features) + list(entry.semantics)
    used: set[str] = set()
    for value in values:
        for marker in markers:
            if marker in value:
                used.add(marker)
    return sorted(used)


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


def _state_item_map(state: Any, lexicon_ids: list[int], lexicon: dict[int, LexiconEntry]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for slot in range(1, state.basenum + 1):
        row = state.base[slot]
        if row == "zero" or not isinstance(row, list):
            continue
        item_id = str(row[0]) if len(row) > 0 else ""
        lid = lexicon_ids[slot - 1] if slot - 1 < len(lexicon_ids) else None
        ent = lexicon.get(lid) if lid is not None else None
        out[item_id] = {
            "initial_slot": slot,
            "lexicon_id": lid,
            "entry": ent.entry if ent is not None else "",
            "surface": ent.phono if ent is not None and ent.phono else (ent.entry if ent is not None else ""),
            "category": ent.category if ent is not None else "",
        }
    return out


def _aggregate_residual_sources(best_samples: list[dict[str, Any]], item_map: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    fam_counter: dict[str, Counter[str]] = {}
    attrs: dict[str, dict[str, Any]] = {}
    for sample in best_samples:
        src_map = sample.get("residual_family_sources") or {}
        for family, rows in src_map.items():
            c = fam_counter.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        row.get("item_id", ""),
                        row.get("raw", ""),
                        row.get("category", ""),
                        row.get("phono", ""),
                    ]
                )
                c[key] += 1
                item_id = row.get("item_id", "")
                init = item_map.get(item_id, {})
                attrs[key] = {
                    "family": family,
                    "exact_label": row.get("raw", ""),
                    "item_id": item_id,
                    "surface": init.get("surface", row.get("phono", "")),
                    "initial_slot": init.get("initial_slot"),
                    "lexicon_id": init.get("lexicon_id"),
                    "category": row.get("category", ""),
                    "count": 0,
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, c in sorted(fam_counter.items(), key=lambda kv: kv[0]):
        rows: list[dict[str, Any]] = []
        for key, n in c.most_common(10):
            row = dict(attrs[key])
            row["count"] = int(n)
            rows.append(row)
        out[family] = rows
    return out


def _aggregate_residual_family_totals(best_samples: list[dict[str, Any]]) -> dict[str, int]:
    total: Counter[str] = Counter()
    for s in best_samples:
        for k, v in (s.get("residual_family_counts") or {}).items():
            total[k] += int(v)
    return dict(sorted(total.items(), key=lambda kv: (-kv[1], kv[0])))


def _extract_surface(row: list[Any]) -> str:
    if len(row) <= 6 or row[6] is None:
        return ""
    return _normalize_token(str(row[6]))


def _hard_reject_check_pair(sentence_key: str, left_row: list[Any], right_row: list[Any]) -> list[str]:
    violations: list[str] = []
    left_cat = str(left_row[1]) if len(left_row) > 1 else ""
    right_cat = str(right_row[1]) if len(right_row) > 1 else ""
    left_surface = _extract_surface(left_row)
    right_surface = _extract_surface(right_row)

    particles = {"を", "が", "と"}
    adjectives = {"ふわふわした"}

    if ((left_cat in {"A", "iA"} and right_cat == "J") or (right_cat in {"A", "iA"} and left_cat == "J")):
        violations.append("A/J direct merge")

    if ((left_surface in adjectives and right_surface in particles) or (right_surface in adjectives and left_surface in particles)):
        violations.append("attributive and case-particle direct merge")

    def check_particle(particle: str, expected: str) -> None:
        if left_surface == particle:
            if right_surface and right_surface != expected:
                violations.append(f"{particle} attached to unexpected partner: {right_surface}")
        if right_surface == particle:
            if left_surface and left_surface != expected:
                violations.append(f"{particle} attached to unexpected partner: {left_surface}")

    check_particle("を", "わたあめ")
    check_particle("と", "ひつじ")
    check_particle("が", EXPECTED_SUBJECT[sentence_key])

    if left_surface == "ふわふわした" and right_surface and right_surface not in {"わたあめ", "ひつじ"}:
        violations.append(f"ふわふわした attached to unexpected partner: {right_surface}")
    if right_surface == "ふわふわした" and left_surface and left_surface not in {"わたあめ", "ひつじ"}:
        violations.append(f"ふわふわした attached to unexpected partner: {left_surface}")

    return violations


def _audit_evidence_naturalness(
    *,
    sentence_key: str,
    initial_state: Any,
    evidence_steps: list[Any],
    legacy_root: Path,
    rh_version: str,
    lh_version: str,
) -> dict[str, Any]:
    current = initial_state.model_copy(deep=True)
    violations: list[dict[str, Any]] = []
    replay_failed: Optional[str] = None

    for idx, step in enumerate(evidence_steps, start=1):
        left_index = step.left
        right_index = step.right
        if left_index is None:
            replay_failed = f"step {idx}: left is None"
            break
        if left_index < 1 or left_index > current.basenum:
            replay_failed = f"step {idx}: left out of range"
            break
        left_row = current.base[left_index]
        right_row = None
        if step.rule_kind == "double":
            if right_index is None or right_index < 1 or right_index > current.basenum:
                replay_failed = f"step {idx}: right out of range"
                break
            right_row = current.base[right_index]
            if not isinstance(left_row, list) or not isinstance(right_row, list):
                replay_failed = f"step {idx}: non-list row"
                break
            v = _hard_reject_check_pair(sentence_key, left_row, right_row)
            for code in v:
                violations.append(
                    {
                        "step": idx,
                        "rule_name": step.rule_name,
                        "left_id": step.left_id,
                        "right_id": step.right_id,
                        "left_surface": _extract_surface(left_row),
                        "right_surface": _extract_surface(right_row),
                        "reason": code,
                    }
                )
        try:
            if step.rule_kind == "double":
                current = execute_double_merge(
                    state=current,
                    rule_name=step.rule_name,
                    left=left_index,
                    right=int(right_index),
                    rule_version=rh_version,
                )
            else:
                current = execute_single_merge(
                    state=current,
                    rule_name=step.rule_name,
                    check=left_index,
                )
        except Exception as exc:
            replay_failed = f"step {idx}: execute failed ({exc})"
            break

    return {
        "has_hard_reject": len(violations) > 0,
        "violations": violations,
        "replay_failed": replay_failed,
        "audit_status": STATUS_UNCONFIRMED if replay_failed else STATUS_CONFIRMED,
    }


def _run_reachability(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    lexicon_ids: list[int],
    config: RunConfig,
    lexicon: dict[int, LexiconEntry],
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(sentence, lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    profile = resolve_rule_versions(get_grammar_profile(GRAMMAR_ID), legacy_root)
    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=10,
        offset=0,
        limit=10,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    best_samples = (internal.leaf_stats.get("best_samples") or [])[: config.top_k]
    item_map = _state_item_map(state, lexicon_ids, lexicon)
    source_totals = _aggregate_residual_sources(best_samples, item_map)
    family_totals = _aggregate_residual_family_totals(best_samples)

    evidences: list[dict[str, Any]] = []
    accepted_evidence_found = False
    for rank, ev in enumerate(internal.evidences[:5], start=1):
        tree_root = _select_tree_root(ev.final_state)
        signature = _canonical_tree_signature(tree_root)
        audit = _audit_evidence_naturalness(
            sentence_key=sentence_key,
            initial_state=state,
            evidence_steps=ev.steps,
            legacy_root=legacy_root,
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
        )
        if not audit["has_hard_reject"] and audit["replay_failed"] is None:
            accepted_evidence_found = True
        evidences.append(
            {
                "rank": rank,
                "steps_to_goal": len(ev.steps),
                "tree_signature": signature,
                "rule_sequence": [
                    {
                        "step": i,
                        "rule_name": st.rule_name,
                        "rule_number": st.rule_number,
                        "rule_kind": st.rule_kind,
                        "left": st.left,
                        "right": st.right,
                        "check": st.check,
                        "left_id": st.left_id,
                        "right_id": st.right_id,
                    }
                    for i, st in enumerate(ev.steps, start=1)
                ],
                "tree": tree_root,
                "process": export_process_text_like_perl(ev.final_state),
                "hard_reject_audit": audit,
            }
        )

    return {
        "grammar_id": GRAMMAR_ID,
        "sentence_key": sentence_key,
        "sentence": sentence,
        "explicit_lexicon_ids": lexicon_ids,
        "status": internal.status,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "best_leaf_residual_family_totals": family_totals,
        "best_leaf_residual_source_top5": {
            fam: rows[:5] for fam, rows in source_totals.items()
        },
        "evidence_present": len(evidences) > 0,
        "evidences": evidences,
        "natural_reachable_evidence_present": accepted_evidence_found,
        "fact_status": STATUS_CONFIRMED,
    }


def _create_temp_legacy_root_with_rows(
    *,
    source_root: Path,
    csv_rows: list[str],
) -> tuple[Any, Path]:
    tmp = tempfile.TemporaryDirectory(prefix="imi01_lex_only_")
    root = Path(tmp.name)
    for child in source_root.iterdir():
        dest = root / child.name
        if child.name == "lexicon-all.csv":
            shutil.copy2(child, dest)
        else:
            os.symlink(child, dest)
    lexicon_file = root / "lexicon-all.csv"
    with lexicon_file.open("a", encoding="utf-8") as fp:
        for row in csv_rows:
            fp.write("\n")
            fp.write(row)
    return tmp, root


def _run_new_row_probes(
    *,
    legacy_root: Path,
    config: RunConfig,
) -> dict[str, Any]:
    rows = [r["csv_row"] for r in NEW_LEXICAL_ROWS]
    tmp_ctx, temp_root = _create_temp_legacy_root_with_rows(source_root=legacy_root, csv_rows=rows)
    try:
        temp_lexicon = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)
        probes = [
            {
                "proposal_id": "S2_new_9401",
                "sentence_key": "S2",
                "sentence": SENTENCES["S2"],
                "explicit_lexicon_ids": [265, 23, 9401, 267, 19, 271, 204],
            },
            {
                "proposal_id": "S3_new_9301_9402",
                "sentence_key": "S3",
                "sentence": SENTENCES["S3"],
                "explicit_lexicon_ids": [267, 9301, 9402, 270, 19, 271, 204],
            },
            {
                "proposal_id": "S4_new_9301_9401_9402",
                "sentence_key": "S4",
                "sentence": SENTENCES["S4"],
                "explicit_lexicon_ids": [264, 265, 23, 9401, 267, 9301, 9402, 270, 19, 271, 204],
            },
            {
                "proposal_id": "S4_new_9301_9401_9402_wo181",
                "sentence_key": "S4",
                "sentence": SENTENCES["S4"],
                "explicit_lexicon_ids": [264, 265, 181, 9401, 267, 9301, 9402, 270, 19, 271, 204],
            },
        ]
        run_rows: list[dict[str, Any]] = []
        hard_reject_rows: list[dict[str, Any]] = []
        for p in probes:
            run = _run_reachability(
                legacy_root=temp_root,
                sentence_key=p["sentence_key"],
                sentence=p["sentence"],
                lexicon_ids=p["explicit_lexicon_ids"],
                config=config,
                lexicon=temp_lexicon,
            )
            run["proposal_id"] = p["proposal_id"]
            run["proposal_target_local_structure"] = "new lexical rows (<=3) probe"
            run["proposal_expected_role_discharge"] = "S2/S3/S4 の persistent residual 圧縮確認"
            run["proposal_assumed_hard_reject_safe"] = STATUS_UNCONFIRMED
            run_rows.append(run)
            for ev in run.get("evidences", []):
                audit = ev.get("hard_reject_audit", {})
                hard_reject_rows.append(
                    {
                        "run_ref": f"{p['proposal_id']}:rank{ev.get('rank')}",
                        "has_hard_reject": bool(audit.get("has_hard_reject")),
                        "replay_failed": audit.get("replay_failed"),
                        "violations": audit.get("violations", [])[:5],
                        "fact_status": STATUS_CONFIRMED if audit.get("replay_failed") is None else STATUS_UNCONFIRMED,
                    }
                )
        return {
            "rows": NEW_LEXICAL_ROWS,
            "runs": run_rows,
            "hard_reject_audit": hard_reject_rows,
            "fact_status": STATUS_CONFIRMED,
        }
    finally:
        tmp_ctx.cleanup()


def _replace_one(ids: list[int], src: int, dst: int) -> list[int]:
    out = list(ids)
    for i, value in enumerate(out):
        if value == src:
            out[i] = dst
            return out
    return out


def _append_ids(ids: list[int], extras: list[int]) -> list[int]:
    out = list(ids)
    out.extend(extras)
    return out


def _build_explicit_proposals(
    baseline_ids: dict[str, list[int]],
    candidate_ids: dict[str, list[int]],
) -> dict[str, list[dict[str, Any]]]:
    proposals: dict[str, list[dict[str, Any]]] = {"S2": [], "S3": [], "S4": []}

    wo_focus = [x for x in [181, 189, 23, 197, 297] if x in candidate_ids.get("を", [])]
    ga_focus = [x for x in [19, 183, 196, 263, 294] if x in candidate_ids.get("が", [])]
    to_focus = [x for x in [268, 9301, 171] if x in candidate_ids.get("と", [])]
    ru_focus = [x for x in [204, 308, 125] if x in candidate_ids.get("る", [])]
    phi_focus = [x for x in [309, 311, 310, 275, 274, 273, 272] if x in candidate_ids.get("φ", [])]

    for key in ["S2", "S3", "S4"]:
        base = baseline_ids[key]
        proposals[key].append(
            {
                "proposal_id": "baseline",
                "explicit_lexicon_ids": base,
                "target_local_structure": "baseline auto-generated IDs",
                "expected_role_discharge": "baseline behavior observation",
                "assumed_hard_reject_safe": STATUS_UNCONFIRMED,
            }
        )

    # S2
    s2 = baseline_ids["S2"]
    cur_wo = next((x for x in s2 if x in candidate_ids.get("を", [])), None)
    cur_ga = next((x for x in s2 if x in candidate_ids.get("が", [])), None)
    cur_ru = next((x for x in s2 if x in candidate_ids.get("る", [])), None)
    if cur_wo is not None:
        for wid in wo_focus:
            if wid == cur_wo:
                continue
            proposals["S2"].append(
                {
                    "proposal_id": f"wo_{wid}",
                    "explicit_lexicon_ids": _replace_one(s2, cur_wo, wid),
                    "target_local_structure": "わたあめ-を-食べている の局所case packaging",
                    "expected_role_discharge": "食べている Theme:2,33,wo 側の解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_ga is not None:
        for gid in ga_focus:
            if gid == cur_ga:
                continue
            proposals["S2"].append(
                {
                    "proposal_id": f"ga_{gid}",
                    "explicit_lexicon_ids": _replace_one(s2, cur_ga, gid),
                    "target_local_structure": "ひつじ-が-いる の主語case packaging",
                    "expected_role_discharge": "Agent/Theme の ga 要求解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_wo is not None and cur_ga is not None:
        for wid in [x for x in wo_focus if x != cur_wo][:2]:
            for gid in [x for x in ga_focus if x != cur_ga][:2]:
                tmp = _replace_one(s2, cur_wo, wid)
                tmp = _replace_one(tmp, cur_ga, gid)
                proposals["S2"].append(
                    {
                        "proposal_id": f"wo_{wid}_ga_{gid}",
                        "explicit_lexicon_ids": tmp,
                        "target_local_structure": "わたあめ-を と ひつじ-が を同時調整",
                        "expected_role_discharge": "食べている/いる の 33 要求同時解消",
                        "assumed_hard_reject_safe": STATUS_CONFIRMED,
                    }
                )
    if cur_ru is not None:
        for rid in ru_focus:
            if rid == cur_ru:
                continue
            proposals["S2"].append(
                {
                    "proposal_id": f"ru_{rid}",
                    "explicit_lexicon_ids": _replace_one(s2, cur_ru, rid),
                    "target_local_structure": "いる-T の時制側選び直し",
                    "expected_role_discharge": "2,1L,T など時制要求の影響確認",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if phi_focus:
        proposals["S2"].append(
            {
                "proposal_id": f"phi_plus1_{phi_focus[0]}",
                "explicit_lexicon_ids": _append_ids(s2, [phi_focus[0]]),
                "target_local_structure": "比較用: φを1件追加",
                "expected_role_discharge": "count補完比較（採用前提なし）",
                "assumed_hard_reject_safe": STATUS_UNCONFIRMED,
            }
        )

    # S3
    s3 = baseline_ids["S3"]
    cur_to = next((x for x in s3 if x in candidate_ids.get("と", [])), None)
    cur_ga = next((x for x in s3 if x in candidate_ids.get("が", [])), None)
    cur_ru = next((x for x in s3 if x in candidate_ids.get("る", [])), None)
    if cur_to is not None:
        for tid in to_focus:
            if tid == cur_to:
                continue
            proposals["S3"].append(
                {
                    "proposal_id": f"to_{tid}",
                    "explicit_lexicon_ids": _replace_one(s3, cur_to, tid),
                    "target_local_structure": "ひつじ-と-話している の局所case packaging",
                    "expected_role_discharge": "話している 相手:2,33,to の解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_ga is not None:
        for gid in ga_focus:
            if gid == cur_ga:
                continue
            proposals["S3"].append(
                {
                    "proposal_id": f"ga_{gid}",
                    "explicit_lexicon_ids": _replace_one(s3, cur_ga, gid),
                    "target_local_structure": "うさぎ-が-いる の主語case packaging",
                    "expected_role_discharge": "話している Agent:2,33,ga の解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_to is not None and cur_ga is not None:
        for tid in [x for x in to_focus if x != cur_to][:2]:
            for gid in [x for x in ga_focus if x != cur_ga][:1]:
                tmp = _replace_one(s3, cur_to, tid)
                tmp = _replace_one(tmp, cur_ga, gid)
                proposals["S3"].append(
                    {
                        "proposal_id": f"to_{tid}_ga_{gid}",
                        "explicit_lexicon_ids": tmp,
                        "target_local_structure": "ひつじ-と と うさぎ-が を同時調整",
                        "expected_role_discharge": "話している 相手/Agent の同時解消",
                        "assumed_hard_reject_safe": STATUS_CONFIRMED,
                    }
                )
    if cur_ru is not None:
        for rid in ru_focus:
            if rid == cur_ru:
                continue
            proposals["S3"].append(
                {
                    "proposal_id": f"ru_{rid}",
                    "explicit_lexicon_ids": _replace_one(s3, cur_ru, rid),
                    "target_local_structure": "いる-T の時制側選び直し",
                    "expected_role_discharge": "時制要求の影響確認",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if phi_focus:
        proposals["S3"].append(
            {
                "proposal_id": f"phi_plus1_{phi_focus[0]}",
                "explicit_lexicon_ids": _append_ids(s3, [phi_focus[0]]),
                "target_local_structure": "比較用: φを1件追加",
                "expected_role_discharge": "count補完比較（採用前提なし）",
                "assumed_hard_reject_safe": STATUS_UNCONFIRMED,
            }
        )

    # S4
    s4 = baseline_ids["S4"]
    cur_wo = next((x for x in s4 if x in candidate_ids.get("を", [])), None)
    cur_to = next((x for x in s4 if x in candidate_ids.get("と", [])), None)
    cur_ga = next((x for x in s4 if x in candidate_ids.get("が", [])), None)
    if cur_wo is not None:
        for wid in wo_focus:
            if wid == cur_wo:
                continue
            proposals["S4"].append(
                {
                    "proposal_id": f"wo_{wid}",
                    "explicit_lexicon_ids": _replace_one(s4, cur_wo, wid),
                    "target_local_structure": "わたあめ-を-食べている を局所調整",
                    "expected_role_discharge": "食べている Theme:2,33,wo 解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_to is not None:
        for tid in to_focus:
            if tid == cur_to:
                continue
            proposals["S4"].append(
                {
                    "proposal_id": f"to_{tid}",
                    "explicit_lexicon_ids": _replace_one(s4, cur_to, tid),
                    "target_local_structure": "ひつじ-と-話している を局所調整",
                    "expected_role_discharge": "話している 相手:2,33,to 解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_ga is not None:
        for gid in [x for x in ga_focus if x != cur_ga][:1]:
            proposals["S4"].append(
                {
                    "proposal_id": f"ga_{gid}",
                    "explicit_lexicon_ids": _replace_one(s4, cur_ga, gid),
                    "target_local_structure": "うさぎ-が-いる の主語case packaging",
                    "expected_role_discharge": "話している/いる の ga 要求解消支援",
                    "assumed_hard_reject_safe": STATUS_CONFIRMED,
                }
            )
    if cur_wo is not None and cur_to is not None:
        for wid in [x for x in wo_focus if x != cur_wo][:2]:
            for tid in [x for x in to_focus if x != cur_to][:2]:
                tmp = _replace_one(s4, cur_wo, wid)
                tmp = _replace_one(tmp, cur_to, tid)
                proposals["S4"].append(
                    {
                        "proposal_id": f"wo_{wid}_to_{tid}",
                        "explicit_lexicon_ids": tmp,
                        "target_local_structure": "食べ-clause と 話す-clause のcase同時調整",
                        "expected_role_discharge": "33要求パケット同時圧縮",
                        "assumed_hard_reject_safe": STATUS_CONFIRMED,
                    }
                )
    if cur_wo is not None and cur_to is not None and cur_ga is not None:
        for wid in [x for x in wo_focus if x != cur_wo][:2]:
            for tid in [x for x in to_focus if x != cur_to][:1]:
                gid = [x for x in ga_focus if x != cur_ga][:1]
                if not gid:
                    continue
                tmp = _replace_one(s4, cur_wo, wid)
                tmp = _replace_one(tmp, cur_to, tid)
                tmp = _replace_one(tmp, cur_ga, gid[0])
                proposals["S4"].append(
                    {
                        "proposal_id": f"wo_{wid}_to_{tid}_ga_{gid[0]}",
                        "explicit_lexicon_ids": tmp,
                        "target_local_structure": "を/と/が の三者同時調整",
                        "expected_role_discharge": "S4全体の33要求圧縮",
                        "assumed_hard_reject_safe": STATUS_CONFIRMED,
                    }
                )
    if len(phi_focus) >= 2:
        proposals["S4"].append(
            {
                "proposal_id": f"phi_plus2_{phi_focus[0]}_{phi_focus[1]}",
                "explicit_lexicon_ids": _append_ids(s4, [phi_focus[0], phi_focus[1]]),
                "target_local_structure": "比較用: φを2件追加",
                "expected_role_discharge": "count補完比較（採用前提なし）",
                "assumed_hard_reject_safe": STATUS_UNCONFIRMED,
            }
        )

    # 重複 proposal id / ids を除外
    for key in ["S2", "S3", "S4"]:
        seen_ids: set[tuple[int, ...]] = set()
        uniq: list[dict[str, Any]] = []
        for row in proposals[key]:
            ids_tuple = tuple(row["explicit_lexicon_ids"])
            if ids_tuple in seen_ids:
                continue
            seen_ids.add(ids_tuple)
            uniq.append(row)
        proposals[key] = uniq
    return proposals


def _baseline_auto_run(
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    config: RunConfig,
    lexicon: dict[int, LexiconEntry],
) -> dict[str, Any]:
    try:
        generated = _generate_numeration_with_unknown_token_fallback(
            grammar_id=GRAMMAR_ID,
            sentence=sentence,
            legacy_root=legacy_root,
            tokens=None,
            split_mode=config.split_mode,
        )
    except Exception as exc:
        return {
            "sentence_key": sentence_key,
            "sentence": sentence,
            "generation_failed": True,
            "error": str(exc),
            "fact_status": STATUS_CONFIRMED,
        }

    run = _run_reachability(
        legacy_root=legacy_root,
        sentence_key=sentence_key,
        sentence=sentence,
        lexicon_ids=list(generated.lexicon_ids),
        config=config,
        lexicon=lexicon,
    )
    run["generation_failed"] = False
    run["token_resolutions"] = [
        {
            "token": row.token,
            "selected_lexicon_id": row.lexicon_id,
            "candidate_lexicon_ids": row.candidate_lexicon_ids,
            "candidate_compatibility": [
                {
                    "lexicon_id": c.lexicon_id,
                    "compatible": c.compatible,
                    "reason_codes": c.reason_codes,
                    "missing_rule_names": c.missing_rule_names,
                    "referenced_rule_names": c.referenced_rule_names,
                }
                for c in row.candidate_compatibility
            ],
        }
        for row in generated.token_resolutions
    ]
    return run


def _candidate_inventory(
    *,
    legacy_root: Path,
    lexicon: dict[int, LexiconEntry],
    baseline_auto_runs: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    from domain.numeration.generator import _infer_candidate_compatibility, _resolve_token  # type: ignore

    profile = resolve_rule_versions(get_grammar_profile(GRAMMAR_ID), legacy_root)
    # grammar rule names for compatibility
    from domain.grammar.rule_catalog import load_rule_catalog

    rules = load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)
    rule_names = {r.name for r in rules}
    index = _build_surface_index(lexicon)

    baseline_selected_ids: set[int] = set()
    for row in baseline_auto_runs.values():
        for lid in row.get("explicit_lexicon_ids", []) or []:
            baseline_selected_ids.add(int(lid))

    inventory_rows: list[dict[str, Any]] = []
    candidate_ids_by_surface: dict[str, list[int]] = {}

    for surface in TARGET_SURFACES:
        norm = _normalize_token(surface)
        cands = sorted(set(index.get(norm, [])))
        candidate_ids_by_surface[surface] = cands
        if not cands:
            inventory_rows.append(
                {
                    "surface": surface,
                    "lexicon_id": None,
                    "entry": None,
                    "category": None,
                    "idslot": None,
                    "sync_features": [],
                    "semantics": [],
                    "step1_auto_may_select": False,
                    "compatible_in_imi01": False,
                    "used_in_past_reachable_examples": False,
                    "selected_in_current_baseline": False,
                    "classification_note": "no_candidate_in_lexicon_all",
                    "fact_status": STATUS_CONFIRMED,
                }
            )
            continue

        # 単一トークン時の選択（参考値）
        single_selected_id: Optional[int] = None
        try:
            tr = _resolve_token(
                grammar_id=GRAMMAR_ID,
                token=surface,
                surface_index=index,
                lexicon=lexicon,
                grammar_rule_names=rule_names,
                token_prev=None,
                token_next=None,
            )
            single_selected_id = tr.lexicon_id
        except Exception:
            single_selected_id = None

        for lid in cands:
            entry = lexicon[lid]
            comp = _infer_candidate_compatibility(
                grammar_id=GRAMMAR_ID,
                entry=entry,
                grammar_rule_names=rule_names,
            )
            inventory_rows.append(
                {
                    "surface": surface,
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                    "step1_auto_may_select": bool(comp.compatible),
                    "single_token_selected": lid == single_selected_id,
                    "compatible_in_imi01": bool(comp.compatible),
                    "used_in_past_reachable_examples": lid in KNOWN_REACHABLE_IDS,
                    "selected_in_current_baseline": lid in baseline_selected_ids,
                    "reason_codes": list(comp.reason_codes),
                    "missing_rule_names": list(comp.missing_rule_names),
                    "referenced_rule_names": list(comp.referenced_rule_names),
                    "rh_lh_only_meaningfulness": STATUS_GUESS,
                    "fact_status": STATUS_CONFIRMED,
                }
            )

    return inventory_rows, candidate_ids_by_surface


def _explicit_numeration_path_fact(legacy_root: Path) -> dict[str, Any]:
    # yes/no と最小 working example
    numeration_text = _build_numeration_text("mini", [270, 19, 271, 204])
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    profile = resolve_rule_versions(get_grammar_profile(GRAMMAR_ID), legacy_root)
    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=3,
        offset=0,
        limit=3,
        budget_seconds=3.0,
        max_nodes=50000,
        max_depth=20,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )
    return {
        "can_pass_explicit_numeration_to_init_and_reachability": True,
        "can_build_state_without_step1": True,
        "existing_example_reference": "tests/test_derivation.py::test_derivation_reachability_known_reachable_sets",
        "minimal_working_example": {
            "grammar_id": GRAMMAR_ID,
            "numeration_text": numeration_text,
            "status": internal.status,
            "reason": internal.reason,
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _role_assignment_rows() -> list[dict[str, Any]]:
    return [
        {"sentence_key": "S2", "predicate": "食べている", "role": "Theme", "target_np": "わたあめ"},
        {"sentence_key": "S2", "predicate": "食べている", "role": "Agent", "target_np": "ひつじ"},
        {"sentence_key": "S3", "predicate": "話している", "role": "相手", "target_np": "ひつじ"},
        {"sentence_key": "S3", "predicate": "話している", "role": "Agent", "target_np": "うさぎ"},
        {"sentence_key": "S4", "predicate": "食べている", "role": "Theme", "target_np": "わたあめ"},
        {"sentence_key": "S4", "predicate": "食べている", "role": "Agent", "target_np": "ひつじ"},
        {"sentence_key": "S4", "predicate": "話している", "role": "相手", "target_np": "ひつじ"},
        {"sentence_key": "S4", "predicate": "話している", "role": "Agent", "target_np": "うさぎ"},
        {"sentence_key": "S4", "predicate": "いる", "role": "Theme", "target_np": "うさぎ"},
    ]


def _role_discharge_matrix(lexicon: dict[int, LexiconEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "role": "食べている Theme",
            "request_item": "食べている(266)",
            "request_label": "Theme:2,33,wo",
            "supply_item": "を(23/197/297/181/189) + N側",
            "supply_label": "4,11,wo 系",
            "required_merge_direction": "非head側に供給ラベルが残る向き（RH/LH）",
            "execute_branch": "_process_se_imi03 number==33",
            "supply_exists_current_lexicon": any("4,11,wo" in sf for e in lexicon.values() for sf in e.sync_features),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        }
    )
    rows.append(
        {
            "role": "食べている Agent",
            "request_item": "食べている(266)",
            "request_label": "Agent:2,33,ga",
            "supply_item": "が(19/183/...) + N側",
            "supply_label": "4,11,ga 系",
            "required_merge_direction": "非head側に供給ラベルが残る向き（RH/LH）",
            "execute_branch": "_process_se_imi03 number==33",
            "supply_exists_current_lexicon": any("4,11,ga" in sf for e in lexicon.values() for sf in e.sync_features),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        }
    )
    rows.append(
        {
            "role": "話している 相手",
            "request_item": "話している(269)",
            "request_label": "相手:2,33,to",
            "supply_item": "と(268/171/9301) + N側",
            "supply_label": "4,11,to 系",
            "required_merge_direction": "非head側に供給ラベルが残る向き（RH/LH）",
            "execute_branch": "_process_se_imi03 number==33",
            "supply_exists_current_lexicon": any("4,11,to" in sf for e in lexicon.values() for sf in e.sync_features),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        }
    )
    return rows


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 lexical-only 再調査レポート（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    for row in payload["final_decision"]["summary_lines"]:
        lines.append(f"- [{row['status']}] {row['text']}")
    lines.append("")

    lines.append("## 2. imi01 baseline")
    lines.append("")
    for sk in ["S1", "S2", "S3", "S4", "S5", "S6"]:
        row = payload["baseline"].get(sk, {})
        lines.append(f"### {sk}: {SENTENCES[sk]}")
        if row.get("generation_failed"):
            lines.append(f"- [{STATUS_CONFIRMED}] generation_failed=True / error={row.get('error')}")
            lines.append("")
            continue
        lines.append(f"- [{STATUS_CONFIRMED}] tokens: {[x['token'] for x in row.get('token_resolutions', [])]}")
        lines.append(f"- [{STATUS_CONFIRMED}] lexicon_ids: {row.get('explicit_lexicon_ids')}")
        lines.append(
            f"- [{STATUS_CONFIRMED}] status/reason: {row.get('status')} / {row.get('reason')} (generation_failed={row.get('generation_failed')})"
        )
        lines.append("")

    lines.append("## 3. lexical candidate 棚卸し")
    lines.append("")
    lines.append("| surface | lexicon_id | entry | category | idslot | step1_auto_may_select | used_in_past_reachable_examples | selected_in_current_baseline |")
    lines.append("|---|---:|---|---|---|---|---|---|")
    for row in payload["candidate_inventory"]:
        lines.append(
            f"| {row.get('surface')} | {'' if row.get('lexicon_id') is None else row.get('lexicon_id')} | {row.get('entry') or '-'} | {row.get('category') or '-'} | {row.get('idslot') or '-'} | {row.get('step1_auto_may_select')} | {row.get('used_in_past_reachable_examples')} | {row.get('selected_in_current_baseline')} |"
        )
    lines.append("")

    lines.append("## 4. explicit numeration 候補一覧")
    lines.append("")
    for sk in ["S2", "S3", "S4"]:
        lines.append(f"### {sk}")
        for p in payload["explicit_proposals"].get(sk, []):
            lines.append(
                f"- [{STATUS_CONFIRMED}] `{p['proposal_id']}` ids={p['explicit_lexicon_ids']} / 狙い={p['target_local_structure']} / 期待={p['expected_role_discharge']} / hard_reject想定={p['assumed_hard_reject_safe']}"
            )
        lines.append("")

    lines.append("## 5. 実測結果")
    lines.append("")
    lines.append("| sentence | proposal | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural_evidence |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---|---|---|")
    for run in payload["runs"]:
        lines.append(
            f"| {run['sentence_key']} | {run['proposal_id']} | {run['explicit_lexicon_ids']} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {run['best_leaf_residual_family_totals']} | {run['evidence_present']} | {run['natural_reachable_evidence_present']} |"
        )
    lines.append("")

    lines.append("## 6. hard reject 監査")
    lines.append("")
    for row in payload["hard_reject_audit"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_ref']}: hard_reject={row['has_hard_reject']} replay_failed={row['replay_failed']} violations={row['violations']}"
        )
    lines.append("")

    if payload.get("new_rows_if_any"):
        lines.append("## 7. 新規 lexical item 案")
        lines.append("")
        for row in payload["new_rows_if_any"].get("rows", []):
            lines.append(f"- [{STATUS_CONFIRMED}] proposal: {row['proposal_name']} (id={row['lexicon_id']})")
            lines.append(f"  - [{STATUS_CONFIRMED}] csv_row: `{row['csv_row']}`")
            lines.append(f"  - [{STATUS_CONFIRMED}] rationale: {row['rationale']}")
        lines.append("")
        lines.append("### 新規 row 実測")
        lines.append("")
        lines.append("| proposal | sentence | ids | status | reason | actions | depth | leaf_min | evidence | natural_evidence |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---|---|")
        for run in payload["new_rows_if_any"].get("runs", []):
            lines.append(
                f"| {run['proposal_id']} | {run['sentence_key']} | {run['explicit_lexicon_ids']} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {run['evidence_present']} | {run['natural_reachable_evidence_present']} |"
            )
        if payload["new_rows_if_any"].get("hard_reject_audit"):
            lines.append("")
            lines.append("### 新規 row hard reject 監査")
            for row in payload["new_rows_if_any"]["hard_reject_audit"]:
                lines.append(
                    f"- [{row['fact_status']}] {row['run_ref']}: hard_reject={row['has_hard_reject']} replay_failed={row['replay_failed']} violations={row['violations']}"
                )
        lines.append("")

    lines.append("## 8. 最終判断")
    lines.append("")
    fd = payload["final_decision"]
    lines.append(f"- [{fd['fact_status']}] 8-1 既存 lexical item だけで到達可能か: {fd['existing_only_reachable']}")
    lines.append(f"- [{fd['fact_status']}] 8-2 最善 explicit numeration: {fd['best_explicit_numeration']}")
    lines.append(f"- [{fd['fact_status']}] 8-3 最小新規 lexical item 案: {fd['minimal_new_row']}")
    lines.append(f"- [{fd['fact_status']}] 8-4 到達証拠の採用可否: {fd['adoptability']}")
    lines.append("")

    lines.append("## 9. 未確認事項")
    lines.append("")
    for item in payload["unknowns"]:
        lines.append(f"- [{STATUS_UNCONFIRMED}] {item}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    legacy_root = Path("/Users/tomonaga/Documents/syncsemphoneIMI")
    config = RunConfig()

    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)

    baseline: dict[str, dict[str, Any]] = {}
    for sk, sentence in SENTENCES.items():
        baseline[sk] = _baseline_auto_run(
            legacy_root=legacy_root,
            sentence_key=sk,
            sentence=sentence,
            config=config,
            lexicon=lexicon,
        )

    candidate_inventory, candidate_ids_by_surface = _candidate_inventory(
        legacy_root=legacy_root,
        lexicon=lexicon,
        baseline_auto_runs=baseline,
    )

    explicit_numeration_fact = _explicit_numeration_path_fact(legacy_root)

    baseline_ids_for_proposals: dict[str, list[int]] = {
        k: list(v.get("explicit_lexicon_ids", [])) for k, v in baseline.items() if k in {"S2", "S3", "S4"}
    }

    explicit_proposals = _build_explicit_proposals(baseline_ids_for_proposals, candidate_ids_by_surface)

    runs: list[dict[str, Any]] = []
    for sk in ["S2", "S3", "S4"]:
        sentence = SENTENCES[sk]
        for proposal in explicit_proposals[sk]:
            run = _run_reachability(
                legacy_root=legacy_root,
                sentence_key=sk,
                sentence=sentence,
                lexicon_ids=proposal["explicit_lexicon_ids"],
                config=config,
                lexicon=lexicon,
            )
            run["proposal_id"] = proposal["proposal_id"]
            run["proposal_target_local_structure"] = proposal["target_local_structure"]
            run["proposal_expected_role_discharge"] = proposal["expected_role_discharge"]
            run["proposal_assumed_hard_reject_safe"] = proposal["assumed_hard_reject_safe"]
            runs.append(run)

    # hard reject summary rows
    hard_reject_audit: list[dict[str, Any]] = []
    for run in runs:
        for ev in run.get("evidences", []):
            audit = ev.get("hard_reject_audit", {})
            hard_reject_audit.append(
                {
                    "run_ref": f"{run['sentence_key']}:{run['proposal_id']}:rank{ev.get('rank')}",
                    "has_hard_reject": bool(audit.get("has_hard_reject")),
                    "replay_failed": audit.get("replay_failed"),
                    "violations": audit.get("violations", [])[:5],
                    "fact_status": STATUS_CONFIRMED if audit.get("replay_failed") is None else STATUS_UNCONFIRMED,
                }
            )

    natural_reachable_runs = [
        r for r in runs if r["status"] == "reachable" and r.get("natural_reachable_evidence_present")
    ]

    best_run = None
    if natural_reachable_runs:
        best_run = sorted(
            natural_reachable_runs,
            key=lambda r: (
                9999 if r.get("best_leaf_unresolved_min") is None else int(r.get("best_leaf_unresolved_min")),
                10**9 if r.get("actions_attempted") is None else int(r.get("actions_attempted")),
            ),
        )[0]

    existing_only_reachable = "yes" if best_run is not None else "no_or_unconfirmed"

    new_rows_if_any: dict[str, Any] = {}
    new_rows_best: Optional[dict[str, Any]] = None
    if best_run is None:
        new_rows_if_any = _run_new_row_probes(
            legacy_root=legacy_root,
            config=config,
        )
        new_runs = new_rows_if_any.get("runs", [])
        if isinstance(new_runs, list) and len(new_runs) > 0:
            new_rows_best = sorted(
                new_runs,
                key=lambda r: (
                    9999 if r.get("best_leaf_unresolved_min") is None else int(r.get("best_leaf_unresolved_min")),
                    10**9 if r.get("actions_attempted") is None else int(r.get("actions_attempted")),
                ),
            )[0]

    if best_run is None:
        if new_rows_best is None:
            minimal_new_row = {
                "status": STATUS_UNCONFIRMED,
                "value": "未提案（新規rowの実測が未完了）",
            }
            adoptability = "未確定"
            best_explicit = "なし"
        else:
            minimal_new_row = {
                "status": STATUS_CONFIRMED,
                "value": {
                    "proposal_id": new_rows_best.get("proposal_id"),
                    "sentence_key": new_rows_best.get("sentence_key"),
                    "explicit_lexicon_ids": new_rows_best.get("explicit_lexicon_ids"),
                    "best_leaf_unresolved_min": new_rows_best.get("best_leaf_unresolved_min"),
                    "status": new_rows_best.get("status"),
                    "reason": new_rows_best.get("reason"),
                },
            }
            adoptability = "未確定"
            best_explicit = {
                "status": STATUS_UNCONFIRMED,
                "value": "既存候補のみの自然reachable未観測。新規rowは leaf_min 改善のみ確認。",
            }
    else:
        minimal_new_row = {
            "status": STATUS_CONFIRMED,
            "value": "不要（既存候補のみで自然条件を満たすreachable証拠あり）",
        }
        best_explicit = {
            "sentence_key": best_run["sentence_key"],
            "proposal_id": best_run["proposal_id"],
            "explicit_lexicon_ids": best_run["explicit_lexicon_ids"],
            "status": best_run["status"],
            "reason": best_run["reason"],
        }
        adoptability = "採用可能"

    summary_lines = [
        {
            "status": STATUS_CONFIRMED,
            "text": f"imi01固定で baseline/proposal を同一予算で実測した（runs={len(runs)}）。",
        },
        {
            "status": STATUS_CONFIRMED,
            "text": f"既存候補のみで自然条件を満たすreachable: {'あり' if best_run is not None else '未観測'}。",
        },
        {
            "status": STATUS_UNCONFIRMED,
            "text": "unknown は探索打切りであり unreachable 断定ではない。",
        },
    ]
    if best_run is None and new_rows_best is not None:
        summary_lines.append(
            {
                "status": STATUS_CONFIRMED,
                "text": f"新規row(<=3)追加実測で最良は {new_rows_best.get('proposal_id')} / leaf_min={new_rows_best.get('best_leaf_unresolved_min')} だが、S4自然reachableは未観測。",
            }
        )

    payload = {
        "generated_at": str(date.today()),
        "grammar_id": GRAMMAR_ID,
        "config": {
            "split_mode": config.split_mode,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "auto_add_ga_phi": False,
        },
        "baseline": baseline,
        "candidate_inventory": candidate_inventory,
        "explicit_numeration_path": explicit_numeration_fact,
        "explicit_proposals": explicit_proposals,
        "runs": runs,
        "hard_reject_audit": hard_reject_audit,
        "role_assignment": _role_assignment_rows(),
        "role_discharge_matrix": _role_discharge_matrix(lexicon),
        "new_rows_if_any": new_rows_if_any,
        "final_decision": {
            "existing_only_reachable": existing_only_reachable,
            "best_explicit_numeration": best_explicit,
            "minimal_new_row": minimal_new_row,
            "adoptability": adoptability,
            "summary_lines": summary_lines,
            "fact_status": STATUS_CONFIRMED,
        },
        "unknowns": [
            "hard reject 条件の一部（名詞句完成前の判定）は rule_sequence だけでは厳密定義が不足する。",
            "candidate compatibility の『選ばれうる』は文脈依存であり、単一トークン判定は近似。",
            "best_samples 由来 residual source は leaf上位の集約であり、全探索の証明ではない。",
        ],
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-imi01-lexical-only-research-20260303.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-imi01-lexical-only-research-20260303.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_build_markdown(payload), encoding="utf-8")

    print(out_json)
    print(out_md)


if __name__ == "__main__":
    main()
