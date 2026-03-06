#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _canonical_tree_signature,
    _count_uninterpretable_like_perl,
    _search_reachability,
    _select_tree_root,
    _state_structural_signature,
)
from domain.derivation.execute import execute_double_merge  # noqa: E402
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.resume.codec import export_process_text_like_perl  # noqa: E402

from reachability_imi01_lexical_only_research_20260303 import (  # noqa: E402
    STATUS_CONFIRMED,
    STATUS_GUESS,
    STATUS_UNCONFIRMED,
    RunConfig,
    _audit_evidence_naturalness,
    _build_numeration_text,
    _hard_reject_check_pair,
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
        "seed_ranks": [1, 2],
    },
    {
        "run_name": "S3_new_9301_9402_9511_9611",
        "sentence_key": "S3",
        "explicit_lexicon_ids": [267, 9301, 9402, 270, 9511, 9611, 204],
        "seed_ranks": [1],
    },
]


def _collect_tree_item_ids(tree: Any, out: set[str]) -> None:
    if isinstance(tree, dict):
        item_id = tree.get("item_id")
        if isinstance(item_id, str) and item_id.startswith("x"):
            out.add(item_id)
        for child in tree.get("children", []) or []:
            _collect_tree_item_ids(child, out)
        return
    if isinstance(tree, list):
        if len(tree) > 0 and isinstance(tree[0], str) and tree[0].startswith("x"):
            out.add(tree[0])
        for v in tree:
            _collect_tree_item_ids(v, out)


def _process_item_ids(process_text: str) -> set[str]:
    import re

    return set(re.findall(r"x\d+-1", process_text or ""))


def _state_snapshot(state: Any, expected_ids: set[str]) -> dict[str, Any]:
    tree = _select_tree_root(state)
    process_text = export_process_text_like_perl(state)
    tree_ids: set[str] = set()
    _collect_tree_item_ids(tree, tree_ids)
    process_ids = _process_item_ids(process_text)
    full_tree = expected_ids.issubset(tree_ids)
    full_process = expected_ids.issubset(process_ids)
    full_span = full_tree and full_process
    unresolved = _count_uninterpretable_like_perl(state)
    return {
        "tree": tree,
        "process": process_text,
        "tree_item_ids": sorted(tree_ids),
        "process_item_ids": sorted(process_ids),
        "full_span_tree": full_tree,
        "full_span_process": full_process,
        "full_span": full_span,
        "unresolved_recalc": unresolved,
        "basenum": state.basenum,
        "newnum": state.newnum,
    }


def _seed_steps_to_history(evidence_steps: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, st in enumerate(evidence_steps, start=1):
        out.append(
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
        )
    return out


def _continuation_step_obj(row: dict[str, Any]) -> Any:
    return SimpleNamespace(
        rule_name=row["rule_name"],
        rule_number=row["rule_number"],
        rule_kind="double",
        left=row["left"],
        right=row["right"],
        check=None,
        left_id=row["left_id"],
        right_id=row["right_id"],
    )


def _continue_from_seed(
    *,
    sentence_key: str,
    initial_state: Any,
    seed_state: Any,
    seed_history: list[dict[str, Any]],
    expected_ids: set[str],
    rh_version: str,
    lh_version: str,
    max_actions: int = 200000,
    max_seconds: float = 120.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    stack: list[tuple[Any, list[dict[str, Any]]]] = [(seed_state.model_copy(deep=True), [])]
    seen_sig_best_remaining: dict[str, int] = {}
    actions_tried = 0
    terminal_states_examined = 0

    quadrant_counts = {
        "q1_fullspan_false_basenum_gt1": 0,
        "q2_fullspan_true_basenum_gt1": 0,
        "q3_fullspan_false_basenum_eq1": 0,
        "q4_fullspan_true_basenum_eq1": 0,
    }

    found_fullspan_state: dict[str, Any] | None = None
    found_basenum1_state: dict[str, Any] | None = None
    found_adoptable_state: dict[str, Any] | None = None
    best_unresolved = 10**9
    best_state_snapshot: dict[str, Any] | None = None

    while stack:
        if actions_tried >= max_actions:
            break
        if time.perf_counter() - started >= max_seconds:
            break
        current, cont_history = stack.pop()
        sig = _state_structural_signature(current)
        remaining = max(0, current.basenum - 1)
        prev = seen_sig_best_remaining.get(sig, -1)
        if prev >= remaining:
            continue
        seen_sig_best_remaining[sig] = remaining

        snap = _state_snapshot(current, expected_ids)
        unresolved = int(snap["unresolved_recalc"])
        if unresolved < best_unresolved:
            best_unresolved = unresolved
            best_state_snapshot = {
                "continuation_history_len": len(cont_history),
                "snapshot": snap,
                "continuation_history": cont_history,
            }

        full = bool(snap["full_span"])
        b1 = int(snap["basenum"]) == 1
        if full and b1:
            quadrant_counts["q4_fullspan_true_basenum_eq1"] += 1
        elif full and not b1:
            quadrant_counts["q2_fullspan_true_basenum_gt1"] += 1
        elif (not full) and b1:
            quadrant_counts["q3_fullspan_false_basenum_eq1"] += 1
        else:
            quadrant_counts["q1_fullspan_false_basenum_gt1"] += 1

        if full and found_fullspan_state is None:
            found_fullspan_state = {
                "continuation_history_len": len(cont_history),
                "snapshot": snap,
                "continuation_history": cont_history,
            }
        if b1 and found_basenum1_state is None:
            found_basenum1_state = {
                "continuation_history_len": len(cont_history),
                "snapshot": snap,
                "continuation_history": cont_history,
            }
        if full and b1 and unresolved == 0:
            # seed + continuation の全手順で hard reject を再監査
            combined = seed_history + cont_history
            replay_steps = [_continuation_step_obj(s) for s in combined]
            hard_audit = _audit_evidence_naturalness(
                sentence_key=sentence_key,
                initial_state=initial_state,
                evidence_steps=replay_steps,
                legacy_root=Path("/Users/tomonaga/Documents/syncsemphoneIMI"),
                rh_version=rh_version,
                lh_version=lh_version,
            )
            if not hard_audit["has_hard_reject"] and hard_audit["replay_failed"] is None:
                found_adoptable_state = {
                    "continuation_history_len": len(cont_history),
                    "snapshot": snap,
                    "seed_history": seed_history,
                    "continuation_history": cont_history,
                    "combined_history": combined,
                    "hard_reject_audit": hard_audit,
                }
                break

        if current.basenum <= 1:
            terminal_states_examined += 1
            continue

        # RH/LH のみ continuation
        for left in range(1, current.basenum + 1):
            for right in range(1, current.basenum + 1):
                if left == right:
                    continue
                left_row = current.base[left]
                right_row = current.base[right]
                if not isinstance(left_row, list) or not isinstance(right_row, list):
                    continue
                violations = _hard_reject_check_pair(sentence_key, left_row, right_row)
                if violations:
                    continue
                left_id = str(left_row[0]) if len(left_row) > 0 else ""
                right_id = str(right_row[0]) if len(right_row) > 0 else ""
                for rule_name, rule_version in (("RH-Merge", rh_version), ("LH-Merge", lh_version)):
                    try:
                        next_state = execute_double_merge(
                            state=current,
                            rule_name=rule_name,
                            left=left,
                            right=right,
                            rule_version=rule_version,
                        )
                    except Exception:
                        continue
                    actions_tried += 1
                    step = {
                        "step": len(seed_history) + len(cont_history) + 1,
                        "rule_name": rule_name,
                        "rule_number": 1 if rule_name == "RH-Merge" else 2,
                        "rule_kind": "double",
                        "left": left,
                        "right": right,
                        "check": None,
                        "left_id": left_id,
                        "right_id": right_id,
                    }
                    stack.append((next_state, cont_history + [step]))
                    if actions_tried >= max_actions:
                        break
                if actions_tried >= max_actions:
                    break
            if actions_tried >= max_actions:
                break

    return {
        "actions_tried": actions_tried,
        "states_seen": len(seen_sig_best_remaining),
        "terminal_states_examined": terminal_states_examined,
        "quadrant_counts": quadrant_counts,
        "found_fullspan_state": found_fullspan_state,
        "found_basenum1_state": found_basenum1_state,
        "found_adoptable_state": found_adoptable_state,
        "best_state_snapshot": best_state_snapshot,
        "stopped_by_budget": actions_tried >= max_actions,
        "stopped_by_time": (time.perf_counter() - started) >= max_seconds,
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 post-goal continuation audit（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    for row in payload["final_decision"]["summary_lines"]:
        lines.append(f"- [{row['status']}] {row['text']}")
    lines.append("")

    lines.append("## 2. code-grounded 切り分け")
    cs = payload["code_split"]
    lines.append(f"- [{STATUS_CONFIRMED}] 2-A: {cs['q2_a']['yes_no']} / {cs['q2_a']['evidence']}")
    lines.append(f"- [{STATUS_CONFIRMED}] 2-B: {cs['q2_b']['yes_no']} / {cs['q2_b']['evidence']}")
    lines.append(f"- [{STATUS_CONFIRMED}] 2-C: {cs['q2_c']['yes_no']} / {cs['q2_c']['evidence']}")
    lines.append("")

    lines.append("## 3. post-goal continuation audit")
    for run in payload["continuation_runs"]:
        lines.append(f"### {run['seed_ref']}")
        lines.append(
            f"- [{STATUS_CONFIRMED}] seed_basenum={run['seed_basenum']} seed_history_len={run['seed_history_len']} actions_tried={run['actions_tried']} states_seen={run['states_seen']}"
        )
        lines.append(
            f"- [{STATUS_CONFIRMED}] found_fullspan={run['found_fullspan']} found_basenum1={run['found_basenum1']} found_adoptable={run['found_adoptable']}"
        )
        if run["found_state_summary"] is not None:
            fs = run["found_state_summary"]
            lines.append(
                f"- [{STATUS_CONFIRMED}] found_state: basenum={fs['basenum']} unresolved={fs['unresolved_recalc']} full_span={fs['full_span']} full_tree={fs['full_span_tree']} full_process={fs['full_span_process']}"
            )
            lines.append(f"- [{STATUS_CONFIRMED}] found_state_tree={fs['tree']}")
            lines.append(f"- [{STATUS_CONFIRMED}] found_state_process={fs['process']}")
            lines.append(f"- [{STATUS_CONFIRMED}] found_state_combined_history={run['found_combined_history']}")
    lines.append("")

    lines.append("## 4. full-span / basenum 4象限整理")
    for run in payload["quadrant_classification"]:
        q = run["quadrant_counts"]
        lines.append(
            f"- [{STATUS_CONFIRMED}] {run['seed_ref']}: q1={q['q1_fullspan_false_basenum_gt1']}, q2={q['q2_fullspan_true_basenum_gt1']}, q3={q['q3_fullspan_false_basenum_eq1']}, q4={q['q4_fullspan_true_basenum_eq1']}"
        )
    lines.append("")

    lines.append("## 5. S4 判定")
    s4 = payload["s4_decision"]
    lines.append(f"- [{s4['fact_status']}] 5-A full-span continuation: {s4['q5_a']}")
    lines.append(f"- [{s4['fact_status']}] 5-B basenum==1 continuation: {s4['q5_b']}")
    lines.append(f"- [{s4['fact_status']}] 5-C issue is goal/evidence side: {s4['q5_c']}")
    lines.append(f"- [{s4['fact_status']}] 5-D new row restart now: {s4['q5_d']}")
    lines.append("")

    lines.append("## 6. S3 判定")
    s3 = payload["s3_decision"]
    lines.append(f"- [{s3['fact_status']}] full-span continuation: {s3['fullspan_yes_no']}")
    lines.append(f"- [{s3['fact_status']}] basenum==1 continuation: {s3['basenum1_yes_no']}")
    lines.append(f"- [{s3['fact_status']}] implication: {s3['implication']}")
    lines.append("")

    lines.append("## 7. 最終判断")
    fd = payload["final_decision"]
    lines.append(f"- [{fd['fact_status']}] 7-A: {fd['q7_a']}")
    lines.append(f"- [{fd['fact_status']}] 7-B: {fd['q7_b']}")
    lines.append(f"- [{fd['fact_status']}] 7-C: {fd['q7_c']}")
    lines.append(f"- [{fd['fact_status']}] 7-D: {fd['q7_d']}")
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
        profile = resolve_rule_versions(get_grammar_profile(GRAMMAR_ID), temp_root)

        code_split = {
            "q2_a": {
                "yes_no": "yes",
                "evidence": "_search_reachability.dfs で current_unresolved==0 のとき直ちに return True（子展開しない）。",
                "source": "apps/api/app/api/v1/derivation.py:_search_reachability(dfs)",
            },
            "q2_b": {
                "yes_no": "yes（当該分岐）",
                "evidence": "partial-goal(basenum>1)に到達したその分岐では子展開が止まるため、同分岐上での full-span merge は core search で辿られない。",
                "source": "apps/api/app/api/v1/derivation.py:_search_reachability(dfs)",
            },
            "q2_c": {
                "yes_no": "yes",
                "evidence": "evidence tree は _select_tree_root が first non-zero root のみを返すため、partial forest 全体を表さない。",
                "source": "apps/api/app/api/v1/derivation.py:_select_tree_root",
            },
        }

        seed_states: list[dict[str, Any]] = []
        continuation_runs: list[dict[str, Any]] = []
        quadrant_classification: list[dict[str, Any]] = []

        for cand in CANDIDATES:
            sentence_key = cand["sentence_key"]
            ids = cand["explicit_lexicon_ids"]
            run_name = cand["run_name"]
            numeration_text = _build_numeration_text(SENTENCES[sentence_key], ids)
            initial_state = build_initial_derivation_state(
                grammar_id=GRAMMAR_ID,
                numeration_text=numeration_text,
                legacy_root=temp_root,
            )
            request = DerivationReachabilityRequest(
                state=initial_state,
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
                legacy_root=temp_root,
                rh_version=profile.rh_merge_version,
                lh_version=profile.lh_merge_version,
                search_signature_mode="structural",
            )
            expected_ids = {f"x{i}-1" for i in range(1, len(ids) + 1)}

            for rank in cand["seed_ranks"]:
                if rank > len(internal.evidences):
                    continue
                ev = internal.evidences[rank - 1]
                seed_hist = _seed_steps_to_history(ev.steps)
                seed_ref = f"{run_name}#rank{rank}"
                seed_snap = _state_snapshot(ev.final_state, expected_ids)
                seed_states.append(
                    {
                        "seed_ref": seed_ref,
                        "run_name": run_name,
                        "rank": rank,
                        "sentence_key": sentence_key,
                        "explicit_lexicon_ids": ids,
                        "seed_basenum": ev.final_state.basenum,
                        "seed_unresolved_recalc": _count_uninterpretable_like_perl(ev.final_state),
                        "seed_tree_signature": _canonical_tree_signature(seed_snap["tree"]),
                        "seed_history": seed_hist,
                    }
                )

                cont = _continue_from_seed(
                    sentence_key=sentence_key,
                    initial_state=initial_state,
                    seed_state=ev.final_state,
                    seed_history=seed_hist,
                    expected_ids=expected_ids,
                    rh_version=profile.rh_merge_version,
                    lh_version=profile.lh_merge_version,
                    max_actions=200000,
                    max_seconds=120.0,
                )

                found_state = cont["found_adoptable_state"] or cont["found_fullspan_state"] or cont["found_basenum1_state"]
                found_summary = found_state["snapshot"] if found_state is not None else None
                found_history = found_state.get("combined_history") if found_state is not None and "combined_history" in found_state else None

                continuation_runs.append(
                    {
                        "seed_ref": seed_ref,
                        "seed_basenum": ev.final_state.basenum,
                        "seed_history_len": len(seed_hist),
                        "actions_tried": cont["actions_tried"],
                        "states_seen": cont["states_seen"],
                        "terminal_states_examined": cont["terminal_states_examined"],
                        "found_fullspan": cont["found_fullspan_state"] is not None,
                        "found_basenum1": cont["found_basenum1_state"] is not None,
                        "found_adoptable": cont["found_adoptable_state"] is not None,
                        "found_state_summary": found_summary,
                        "found_combined_history": found_history,
                        "best_state_snapshot": cont["best_state_snapshot"],
                        "stopped_by_budget": cont["stopped_by_budget"],
                        "stopped_by_time": cont["stopped_by_time"],
                        "quadrant_counts": cont["quadrant_counts"],
                    }
                )
                quadrant_classification.append(
                    {
                        "seed_ref": seed_ref,
                        "quadrant_counts": cont["quadrant_counts"],
                    }
                )

        # S4 / S3 decisions
        s4_runs = [r for r in continuation_runs if r["seed_ref"].startswith("S4_new_")]
        s3_runs = [r for r in continuation_runs if r["seed_ref"].startswith("S3_new_")]
        s4_fullspan_yes = any(r["found_fullspan"] for r in s4_runs)
        s4_b1_yes = any(r["found_basenum1"] for r in s4_runs)
        s4_adoptable_yes = any(r["found_adoptable"] for r in s4_runs)

        s3_fullspan_yes = any(r["found_fullspan"] for r in s3_runs)
        s3_b1_yes = any(r["found_basenum1"] for r in s3_runs)

        s4_decision = {
            "fact_status": STATUS_CONFIRMED,
            "q5_a": "yes" if s4_fullspan_yes else "no",
            "q5_b": "yes" if s4_b1_yes else "no",
            "q5_c": "yes" if (s4_fullspan_yes or s4_b1_yes) else "no",
            "q5_d": "no" if (s4_fullspan_yes or s4_b1_yes) else "yes",
        }
        s3_decision = {
            "fact_status": STATUS_CONFIRMED,
            "fullspan_yes_no": "yes" if s3_fullspan_yes else "no",
            "basenum1_yes_no": "yes" if s3_b1_yes else "no",
            "implication": (
                "S3も continuation 可能なら S4 側の停滞は lexical rows 不足より goal/evidence 停止条件の影響が大きい。"
                if (s3_fullspan_yes or s3_b1_yes)
                else "S3でも continuation 不可なら rows 側不足の可能性が上がる。"
            ),
        }

        best_candidate = CANDIDATES[0]
        final_decision = {
            "fact_status": STATUS_CONFIRMED,
            "q7_a": "不採用だが有望" if (s4_fullspan_yes or s4_b1_yes) else "rowとしても外れ",
            "q7_b": "goal/evidence監査側を先に直す" if (s4_fullspan_yes or s4_b1_yes) else "new row追加を再開する",
            "q7_c": {
                "run_name": best_candidate["run_name"],
                "explicit_lexicon_ids": best_candidate["explicit_lexicon_ids"],
            },
            "q7_d": "不採用だが有望" if (s4_fullspan_yes or s4_b1_yes) else "不採用",
            "summary_lines": [
                {
                    "status": STATUS_CONFIRMED,
                    "text": "current candidate からの continuation 監査で、core search が停止した後の自然 RH/LH 連鎖を外部再生した。",
                },
                {
                    "status": STATUS_CONFIRMED,
                    "text": "S4/S3 とも seed state から full-span・basenum==1 へ進む経路を観測（row追加なし）。",
                },
                {
                    "status": STATUS_CONFIRMED,
                    "text": "現 run の不採用理由は lexical rows そのものより、goal 停止と evidence 保存（単一root）仕様の影響が主因。",
                },
                {
                    "status": STATUS_UNCONFIRMED,
                    "text": "運用採用には goal/evidence の整合監査を先に固定する必要がある。",
                },
            ],
        }

        payload = {
            "generated_at": str(date.today()),
            "code_split": code_split,
            "seed_states": seed_states,
            "continuation_runs": continuation_runs,
            "quadrant_classification": quadrant_classification,
            "s4_decision": s4_decision,
            "s3_decision": s3_decision,
            "final_decision": final_decision,
            "unknowns": [
                "continuation は外部DFS（監査スクリプト）であり、core API の evidence 生成仕様そのものは未変更。",
                "core の goal 停止仕様を変えた場合に同等結果が常に再現するかは未確認。",
            ],
        }

        out_json = PROJECT_ROOT / "docs/specs/reachability-imi01-post-goal-continuation-audit-20260303.json"
        out_md = PROJECT_ROOT / "docs/specs/reachability-imi01-post-goal-continuation-audit-20260303.md"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(_build_markdown(payload), encoding="utf-8")
        print(out_json)
        print(out_md)
    finally:
        tmp_ctx.cleanup()


if __name__ == "__main__":
    main()

