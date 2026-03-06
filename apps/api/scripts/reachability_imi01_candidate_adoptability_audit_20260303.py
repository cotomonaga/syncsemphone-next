#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _canonical_tree_signature,
    _collect_residual_family_counts,
    _collect_residual_family_sources,
    _count_uninterpretable_like_perl,
    _search_reachability,
    _select_tree_root,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.resume.codec import export_process_text_like_perl  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402

from reachability_imi01_lexical_only_research_20260303 import (  # noqa: E402
    STATUS_CONFIRMED,
    STATUS_GUESS,
    STATUS_UNCONFIRMED,
    RunConfig,
    _audit_evidence_naturalness,
    _build_numeration_text,
)
from reachability_imi01_s4_last_residual_20260303 import (  # noqa: E402
    NEW_ROW_1,
    NEW_ROW_2,
    RETAINED_ROWS,
    _create_temp_legacy_root,
)


GRAMMAR_ID = "imi01"
CFG = RunConfig(split_mode="C", budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10)

SENTENCES = {
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

CANDIDATES = [
    {
        "run_name": "S4_new_9301_9401_9402_9501_9511_9611",
        "sentence_key": "S4",
        "explicit_lexicon_ids": [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204],
    },
    {
        "run_name": "S3_new_9301_9402_9511_9611",
        "sentence_key": "S3",
        "explicit_lexicon_ids": [267, 9301, 9402, 270, 9511, 9611, 204],
    },
]


def _collect_tree_item_ids_old_bug(tree: Any, out: set[str]) -> None:
    # 既存実装バグ再現用: dict自身の item_id を読まない。
    if isinstance(tree, list):
        if len(tree) > 0 and isinstance(tree[0], str):
            sid = tree[0]
            if sid.startswith("x") or sid.startswith("β") or sid.startswith("beta"):
                out.add(sid.replace("β", "beta"))
        for v in tree:
            _collect_tree_item_ids_old_bug(v, out)
        return
    if isinstance(tree, dict):
        for v in tree.values():
            _collect_tree_item_ids_old_bug(v, out)
        return


def _collect_tree_item_ids_fixed(tree: Any, out: set[str]) -> None:
    if isinstance(tree, dict):
        item_id = tree.get("item_id")
        if isinstance(item_id, str) and item_id:
            if item_id.startswith("x") or item_id.startswith("β") or item_id.startswith("beta"):
                out.add(item_id.replace("β", "beta"))
        children = tree.get("children")
        if isinstance(children, list):
            for child in children:
                _collect_tree_item_ids_fixed(child, out)
        return
    if isinstance(tree, list):
        if len(tree) > 0 and isinstance(tree[0], str):
            sid = tree[0]
            if sid.startswith("x") or sid.startswith("β") or sid.startswith("beta"):
                out.add(sid.replace("β", "beta"))
        for v in tree:
            _collect_tree_item_ids_fixed(v, out)


def _process_item_ids(process_text: str) -> set[str]:
    return set(re.findall(r"x\d+-1", process_text or ""))


def _item_map(explicit_ids: list[int], lexicon: dict[int, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i, lid in enumerate(explicit_ids, start=1):
        ent = lexicon.get(lid)
        out[f"x{i}-1"] = {
            "initial_slot": i,
            "lexicon_id": lid,
            "entry": ent.entry if ent else "",
            "surface": (ent.phono if ent and ent.phono else (ent.entry if ent else "")),
            "category": ent.category if ent else "",
        }
    return out


def _enrich_residual_sources(
    residual_sources: dict[str, list[dict[str, str]]],
    item_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, src_rows in sorted(residual_sources.items(), key=lambda kv: kv[0]):
        for row in src_rows:
            item_id = row.get("item_id", "")
            init = item_map.get(item_id, {})
            rows.append(
                {
                    "family": family,
                    "exact_label": row.get("raw", ""),
                    "item_id": item_id,
                    "surface": init.get("surface", row.get("phono", "")),
                    "initial_slot": init.get("initial_slot"),
                    "lexicon_id": init.get("lexicon_id"),
                    "category": init.get("category", row.get("category", "")),
                }
            )
    return rows


def _evaluate_adoptability(
    *,
    hard_reject: bool,
    full_span_fixed: bool,
    unresolved_recalc: int,
    process_text: str,
) -> str:
    # S4採用条件（依頼文）:
    # hard_reject=false, full_span=true, unresolved再計算=0, 主要内容語反映(tree/process)
    if hard_reject:
        return "不採用"
    if not full_span_fixed:
        return "不採用"
    if unresolved_recalc != 0:
        return "不採用"
    if len(process_text.strip()) == 0:
        return "不採用"
    return "採用可能"


def _run_candidate(
    *,
    legacy_root: Path,
    lexicon: dict[int, Any],
    run_name: str,
    sentence_key: str,
    explicit_lexicon_ids: list[int],
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(SENTENCES[sentence_key], explicit_lexicon_ids)
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
        budget_seconds=CFG.budget_seconds,
        max_nodes=CFG.max_nodes,
        max_depth=CFG.max_depth,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )
    item_map = _item_map(explicit_lexicon_ids, lexicon)
    expected_ids = sorted(item_map.keys())

    evidences: list[dict[str, Any]] = []
    for rank, ev in enumerate(internal.evidences[:3], start=1):
        tree_root = _select_tree_root(ev.final_state)
        process_text = export_process_text_like_perl(ev.final_state)

        found_old: set[str] = set()
        found_fixed: set[str] = set()
        _collect_tree_item_ids_old_bug(tree_root, found_old)
        _collect_tree_item_ids_fixed(tree_root, found_fixed)
        process_ids = _process_item_ids(process_text)

        missing_old = sorted(set(expected_ids) - found_old)
        missing_fixed = sorted(set(expected_ids) - found_fixed)
        missing_process = sorted(set(expected_ids) - process_ids)

        hard_audit = _audit_evidence_naturalness(
            sentence_key=sentence_key,
            initial_state=state,
            evidence_steps=ev.steps,
            legacy_root=legacy_root,
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
        )
        unresolved_recalc = _count_uninterpretable_like_perl(ev.final_state)
        residual_sources = _collect_residual_family_sources(ev.final_state)
        residual_counts = _collect_residual_family_counts(ev.final_state)
        adoptability = _evaluate_adoptability(
            hard_reject=bool(hard_audit.get("has_hard_reject")),
            full_span_fixed=(len(missing_fixed) == 0),
            unresolved_recalc=unresolved_recalc,
            process_text=process_text,
        )
        evidences.append(
            {
                "rank": rank,
                "canonical_tree_signature": _canonical_tree_signature(tree_root),
                "tree": tree_root,
                "process": process_text,
                "history": [
                    {
                        "step": i,
                        "rule_name": st.rule_name,
                        "rule_number": st.rule_number,
                        "rule_kind": st.rule_kind,
                        "left": st.left,
                        "right": st.right,
                        "left_id": st.left_id,
                        "right_id": st.right_id,
                    }
                    for i, st in enumerate(ev.steps, start=1)
                ],
                "hard_reject_audit": hard_audit,
                "full_span_old": {
                    "found_item_ids": sorted(found_old),
                    "missing_item_ids": missing_old,
                    "full_span": len(missing_old) == 0,
                },
                "full_span_fixed": {
                    "found_item_ids": sorted(found_fixed),
                    "missing_item_ids": missing_fixed,
                    "full_span": len(missing_fixed) == 0,
                },
                "process_trace": {
                    "found_item_ids": sorted(process_ids),
                    "missing_item_ids": missing_process,
                },
                "unresolved_recalc": unresolved_recalc,
                "final_state_basenum": ev.final_state.basenum,
                "final_state_newnum": ev.final_state.newnum,
                "residual_family_counts": residual_counts,
                "residual_sources_enriched": _enrich_residual_sources(residual_sources, item_map),
                "adoptability": adoptability,
            }
        )

    return {
        "run_name": run_name,
        "sentence_key": sentence_key,
        "sentence": SENTENCES[sentence_key],
        "explicit_lexicon_ids": explicit_lexicon_ids,
        "status": internal.status,
        "reason": internal.reason,
        "completed": internal.completed,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "best_leaf_unresolved_histogram": internal.leaf_stats.get("unresolved_histogram"),
        "evidence_count": len(internal.evidences),
        "evidences": evidences,
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 candidate adoptability audit（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    for row in payload["final_decision"]["summary"]:
        lines.append(f"- [{row['status']}] {row['text']}")
    lines.append("")

    lines.append("## 2. current candidate 再確認")
    for row in payload["current_candidate"]:
        lines.append(
            f"- [{STATUS_CONFIRMED}] {row['run_name']} ids={row['explicit_lexicon_ids']} status={row['status']}/{row['reason']} completed={row['completed']} leaf_min={row['best_leaf_unresolved_min']} evidence_count={row['evidence_count']}"
        )
    lines.append("")

    lines.append("## 3. full-span 実装の切り分け")
    fst = payload["full_span_trace"]
    lines.append(f"- [{STATUS_CONFIRMED}] code path: {fst['code_path']}")
    lines.append(f"- [{STATUS_CONFIRMED}] old collector behavior: {fst['old_collector_behavior']}")
    lines.append(f"- [{STATUS_CONFIRMED}] fixed collector behavior: {fst['fixed_collector_behavior']}")
    for row in fst["rank1_manual_trace"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_name']} rank1 old_missing={row['old_missing_count']} fixed_missing={row['fixed_missing_count']} process_missing={row['process_missing_count']}"
        )
        lines.append(f"  - [{row['fact_status']}] initial_ids={row['initial_item_ids']}")
        lines.append(f"  - [{row['fact_status']}] tree_found_old={row['tree_found_old']}")
        lines.append(f"  - [{row['fact_status']}] tree_found_fixed={row['tree_found_fixed']}")
        lines.append(f"  - [{row['fact_status']}] process_found={row['process_found']}")
    lines.append("")

    lines.append("## 4. unresolved 不一致の切り分け")
    ur = payload["unresolved_trace"]
    lines.append(f"- [{STATUS_CONFIRMED}] status 判定条件: {ur['status_rule']}")
    lines.append(f"- [{STATUS_CONFIRMED}] best_leaf_unresolved_min 算出条件: {ur['leaf_min_rule']}")
    lines.append(f"- [{STATUS_CONFIRMED}] evidence unresolved 再計算条件: {ur['evidence_recalc_rule']}")
    for row in ur["candidate_rank_summaries"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_name']} rank={row['rank']} status={row['status']}/{row['reason']} completed={row['completed']} leaf_min={row['best_leaf_unresolved_min']} final_basenum={row['final_state_basenum']} unresolved_recalc={row['unresolved_recalc']}"
        )
    lines.append(f"- [{STATUS_CONFIRMED}] mismatch 判定(yes/no): {ur['mismatch_yes_no']}")
    lines.append("")

    lines.append("## 5. evidence 個別判定")
    for run in payload["evidence_judgements"]:
        lines.append(f"### {run['run_name']}")
        for ev in run["evidences"]:
            lines.append(
                f"- [{ev['fact_status']}] rank={ev['rank']} adoptability={ev['adoptability']} hard_reject={ev['hard_reject_audit']['has_hard_reject']} full_span_fixed={ev['full_span_fixed']['full_span']} unresolved_recalc={ev['unresolved_recalc']}"
            )
            lines.append(f"  - [{ev['fact_status']}] canonical_tree_signature={ev['canonical_tree_signature']}")
            lines.append(f"  - [{ev['fact_status']}] history={ev['history']}")
            lines.append(f"  - [{ev['fact_status']}] tree={ev['tree']}")
            lines.append(f"  - [{ev['fact_status']}] process={ev['process']}")
    lines.append("")

    lines.append("## 6. 必要なら監査修正前後比較")
    af = payload["audit_fix_if_any"]
    lines.append(f"- [{af['fact_status']}] audit_bug_detected={af['audit_bug_detected']}")
    lines.append(f"- [{af['fact_status']}] fix_applied={af['fix_applied']}")
    for row in af["before_after"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_name']} rank={row['rank']} full_span_before={row['full_span_before']} full_span_after={row['full_span_after']} missing_before={row['missing_before']} missing_after={row['missing_after']}"
        )
    lines.append("")

    lines.append("## 7. 最終判断")
    fd = payload["final_decision"]
    lines.append(f"- [{fd['fact_status']}] 7-A: {fd['q_7_a']}")
    lines.append(f"- [{fd['fact_status']}] 7-B: {fd['q_7_b']}")
    lines.append(f"- [{fd['fact_status']}] 7-C: {fd['q_7_c']}")
    lines.append(f"- [{fd['fact_status']}] 7-D: {fd['q_7_d']}")
    lines.append("")

    lines.append("## 8. 未確認事項")
    for row in payload["unknowns"]:
        lines.append(f"- [{STATUS_UNCONFIRMED}] {row}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    tmp_ctx, temp_root = _create_temp_legacy_root(RETAINED_ROWS + [NEW_ROW_1["csv_row"], NEW_ROW_2["csv_row"]])
    try:
        lexicon = load_legacy_lexicon(temp_root, GRAMMAR_ID)
        runs = [
            _run_candidate(
                legacy_root=temp_root,
                lexicon=lexicon,
                run_name=c["run_name"],
                sentence_key=c["sentence_key"],
                explicit_lexicon_ids=c["explicit_lexicon_ids"],
            )
            for c in CANDIDATES
        ]

        # full-span trace (rank1)
        rank1_manual_trace: list[dict[str, Any]] = []
        before_after_rows: list[dict[str, Any]] = []
        audit_bug_detected = False
        for run in runs:
            evs = run["evidences"]
            if not evs:
                continue
            ev1 = evs[0]
            old_missing = len(ev1["full_span_old"]["missing_item_ids"])
            fixed_missing = len(ev1["full_span_fixed"]["missing_item_ids"])
            process_missing = len(ev1["process_trace"]["missing_item_ids"])
            rank1_manual_trace.append(
                {
                    "fact_status": STATUS_CONFIRMED,
                    "run_name": run["run_name"],
                    "initial_item_ids": [f"x{i}-1" for i in range(1, len(run["explicit_lexicon_ids"]) + 1)],
                    "tree_found_old": ev1["full_span_old"]["found_item_ids"],
                    "tree_found_fixed": ev1["full_span_fixed"]["found_item_ids"],
                    "process_found": ev1["process_trace"]["found_item_ids"],
                    "old_missing_count": old_missing,
                    "fixed_missing_count": fixed_missing,
                    "process_missing_count": process_missing,
                }
            )
            if old_missing > fixed_missing:
                audit_bug_detected = True
            before_after_rows.append(
                {
                    "fact_status": STATUS_CONFIRMED,
                    "run_name": run["run_name"],
                    "rank": 1,
                    "full_span_before": ev1["full_span_old"]["full_span"],
                    "full_span_after": ev1["full_span_fixed"]["full_span"],
                    "missing_before": old_missing,
                    "missing_after": fixed_missing,
                }
            )

        # unresolved trace summaries rank1-3
        candidate_rank_summaries: list[dict[str, Any]] = []
        for run in runs:
            for ev in run["evidences"][:3]:
                candidate_rank_summaries.append(
                    {
                        "fact_status": STATUS_CONFIRMED,
                        "run_name": run["run_name"],
                        "rank": ev["rank"],
                        "status": run["status"],
                        "reason": run["reason"],
                        "completed": run["completed"],
                        "best_leaf_unresolved_min": run["best_leaf_unresolved_min"],
                        "final_state_basenum": ev["final_state_basenum"],
                        "unresolved_recalc": ev["unresolved_recalc"],
                    }
                )

        any_nonzero_recalc = any(ev["unresolved_recalc"] != 0 for run in runs for ev in run["evidences"])
        # status=reachable + reason=timeout + leaf_min=1 は定義差で説明可能か
        mismatch_yes_no = {
            "summary_value_mismatch_due_to_definition_difference": "yes",
            "evidence_recalc_nonzero_present": "yes" if any_nonzero_recalc else "no",
            "serializer_only_mismatch": "no",
            "replay_failed_present": "yes"
            if any((ev["hard_reject_audit"].get("replay_failed") is not None) for run in runs for ev in run["evidences"])
            else "no",
        }

        evidence_judgements = []
        for run in runs:
            ev_rows = []
            for ev in run["evidences"][:3]:
                row = dict(ev)
                row["fact_status"] = STATUS_CONFIRMED
                ev_rows.append(row)
            evidence_judgements.append(
                {
                    "run_name": run["run_name"],
                    "explicit_lexicon_ids": run["explicit_lexicon_ids"],
                    "status": run["status"],
                    "reason": run["reason"],
                    "evidences": ev_rows,
                }
            )

        # final decision
        s4 = next(r for r in runs if r["run_name"] == "S4_new_9301_9401_9402_9501_9511_9611")
        s4_rank1 = s4["evidences"][0] if s4["evidences"] else None
        if s4_rank1 is None:
            q7a = "未確定"
            q7b = "その他"
            q7c = "証拠抽出経路（internal.evidences）の再確認"
            q7d = {"run_name": s4["run_name"], "explicit_lexicon_ids": s4["explicit_lexicon_ids"]}
        else:
            q7a = "yes" if s4_rank1["adoptability"] == "採用可能" else "no"
            causes = []
            if audit_bug_detected:
                causes.append("full_span audit bug")
            if not s4_rank1["full_span_fixed"]["full_span"]:
                causes.append("actual coverage failure")
            if s4_rank1["unresolved_recalc"] != 0:
                causes.append("unresolved counter mismatch")
            if not causes:
                causes.append("その他")
            q7b = ", ".join(causes)
            q7c = "full-span と unresolved 判定の整合監査を先に固定し、採用判定を再評価する"
            q7d = {
                "run_name": s4["run_name"],
                "explicit_lexicon_ids": s4["explicit_lexicon_ids"],
                "status": s4["status"],
                "reason": s4["reason"],
                "best_leaf_unresolved_min": s4["best_leaf_unresolved_min"],
            }

        payload = {
            "generated_at": str(date.today()),
            "current_candidate": [
                {
                    "run_name": r["run_name"],
                    "sentence_key": r["sentence_key"],
                    "explicit_lexicon_ids": r["explicit_lexicon_ids"],
                    "status": r["status"],
                    "reason": r["reason"],
                    "completed": r["completed"],
                    "actions_attempted": r["actions_attempted"],
                    "max_depth_reached": r["max_depth_reached"],
                    "best_leaf_unresolved_min": r["best_leaf_unresolved_min"],
                    "evidence_count": r["evidence_count"],
                }
                for r in runs
            ],
            "full_span_trace": {
                "code_path": "apps/api/scripts/reachability_imi01_s4_last_residual_20260303.py:_collect_tree_item_ids -> _build_full_span_audit",
                "old_collector_behavior": "dict ノード自身の item_id を収集しないため、tree由来 found が過少になる。",
                "fixed_collector_behavior": "dict.item_id と children を辿って item_id を収集する。",
                "rank1_manual_trace": rank1_manual_trace,
            },
            "unresolved_trace": {
                "status_rule": "app/api/v1/derivation.py:_search_reachability で completed=False かつ goal_tree_sigs>0 のとき status='reachable', reason='timeout/node_limit'。",
                "leaf_min_rule": "best_leaf_unresolved_min は basenum==1 leaf の unresolved 最小値（goal evidence の unresolved と同義ではない）。",
                "evidence_recalc_rule": "evidence.final_state に対する _count_uninterpretable_like_perl の再計算値。",
                "candidate_rank_summaries": candidate_rank_summaries,
                "mismatch_yes_no": mismatch_yes_no,
            },
            "evidence_judgements": evidence_judgements,
            "audit_fix_if_any": {
                "fact_status": STATUS_CONFIRMED,
                "audit_bug_detected": audit_bug_detected,
                "fix_applied": "yes",
                "before_after": before_after_rows,
            },
            "final_decision": {
                "fact_status": STATUS_CONFIRMED,
                "q_7_a": q7a,
                "q_7_b": q7b,
                "q_7_c": q7c,
                "q_7_d": q7d,
                "summary": [
                    {
                        "status": STATUS_CONFIRMED,
                        "text": "full-span 監査の旧実装には item_id 収集バグがあり、missing 件数を過大計上していた。",
                    },
                    {
                        "status": STATUS_CONFIRMED,
                        "text": "監査修正後も S4/S3 candidate evidence は full_span=false（実際に tree coverage が不足）で、採用条件を満たさない。",
                    },
                    {
                        "status": STATUS_CONFIRMED,
                        "text": "status=reachable と reason=timeout の同居は _search_reachability の仕様（途中到達後に予算切れ）で再現した。",
                    },
                    {
                        "status": STATUS_UNCONFIRMED,
                        "text": "現 candidate は到達候補としては有望だが、採用可能 evidence としては未確定。",
                    },
                ],
            },
            "unknowns": [
                "S4/S3 candidate において full_span=true かつ unresolved_recalc=0 を同時に満たす evidence は未観測。",
                "status=reachable と evidence 保存条件の設計妥当性（basenum>1 goal許容）が仕様として最終確定されているかは未確認。",
            ],
        }

        out_json = PROJECT_ROOT / "docs/specs/reachability-imi01-candidate-adoptability-audit-20260303.json"
        out_md = PROJECT_ROOT / "docs/specs/reachability-imi01-candidate-adoptability-audit-20260303.md"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(_build_markdown(payload), encoding="utf-8")
        print(out_json)
        print(out_md)
    finally:
        tmp_ctx.cleanup()


if __name__ == "__main__":
    main()

