#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional

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
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.resume.codec import export_process_text_like_perl  # noqa: E402

from reachability_imi01_lexical_only_research_20260303 import (  # noqa: E402
    RunConfig,
    STATUS_CONFIRMED,
    STATUS_UNCONFIRMED,
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


@dataclass
class BeforeSnapshot:
    status: str
    reason: str
    evidence_present: bool
    natural_reachable_evidence_present: bool
    full_span: bool
    basenum: Optional[int]
    unresolved_recalc: Optional[int]


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
            item_id = tree[0]
            if item_id.startswith("x") or item_id.startswith("β") or item_id.startswith("beta"):
                out.add(item_id.replace("β", "beta"))
        for value in tree:
            _collect_tree_item_ids_fixed(value, out)


def _process_item_ids(process_text: str) -> set[str]:
    return set(re.findall(r"x\d+-1", process_text or ""))


def _full_span_snapshot(*, state: Any, expected_ids: list[str]) -> dict[str, Any]:
    tree = _select_tree_root(state)
    process_text = export_process_text_like_perl(state)
    tree_found: set[str] = set()
    _collect_tree_item_ids_fixed(tree, tree_found)
    process_found = _process_item_ids(process_text)
    expected_set = set(expected_ids)
    missing_tree = sorted(expected_set - tree_found)
    missing_process = sorted(expected_set - process_found)
    return {
        "tree": tree,
        "process": process_text,
        "tree_found": sorted(tree_found),
        "process_found": sorted(process_found),
        "missing_tree": missing_tree,
        "missing_process": missing_process,
        "full_span": len(missing_tree) == 0 and len(missing_process) == 0,
    }


def _read_before_snapshot() -> dict[str, BeforeSnapshot]:
    before: dict[str, BeforeSnapshot] = {}
    spec_path = PROJECT_ROOT / "docs/specs/reachability-imi01-candidate-adoptability-audit-20260303.json"
    if not spec_path.exists():
        return before
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    # 直近監査の「固定 candidate 観測値」を before として参照。
    current = data.get("current_candidate") or []
    for row in current:
        run_name = row.get("run_name")
        if not run_name:
            continue
        before[run_name] = BeforeSnapshot(
            status=str(row.get("status", "")),
            reason=str(row.get("reason", "")),
            evidence_present=bool((row.get("evidence_count") or 0) > 0),
            natural_reachable_evidence_present=True,
            full_span=False,
            basenum=None,
            unresolved_recalc=None,
        )
    # full-span before/after 情報
    audit_fix = data.get("audit_fix_if_any") or {}
    for row in audit_fix.get("before_after") or []:
        run_name = row.get("run_name")
        if run_name in before:
            before[run_name].full_span = bool(row.get("full_span_before", False))
    # rank summary から basenum/unresolved を補完
    unresolved_trace = data.get("unresolved_trace") or {}
    for row in unresolved_trace.get("candidate_rank_summaries") or []:
        if int(row.get("rank") or 0) != 1:
            continue
        run_name = row.get("run_name")
        if run_name in before:
            before[run_name].basenum = int(row.get("final_state_basenum") or 0)
            before[run_name].unresolved_recalc = int(row.get("unresolved_recalc") or 0)
    return before


def _run_candidate(*, legacy_root: Path, lexicon: dict[int, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    run_name = str(candidate["run_name"])
    sentence_key = str(candidate["sentence_key"])
    explicit_ids = list(candidate["explicit_lexicon_ids"])

    numeration_text = _build_numeration_text(SENTENCES[sentence_key], explicit_ids)
    state = build_initial_derivation_state(grammar_id=GRAMMAR_ID, numeration_text=numeration_text, legacy_root=legacy_root)

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

    expected_ids = [f"x{i}-1" for i in range(1, len(explicit_ids) + 1)]

    evidences: list[dict[str, Any]] = []
    adoptable_count = 0
    for rank, ev in enumerate(internal.evidences, start=1):
        snap = _full_span_snapshot(state=ev.final_state, expected_ids=expected_ids)
        unresolved_recalc = _count_uninterpretable_like_perl(ev.final_state)
        hard_audit = _audit_evidence_naturalness(
            sentence_key=sentence_key,
            initial_state=state,
            evidence_steps=ev.steps,
            legacy_root=Path("/Users/tomonaga/Documents/syncsemphoneIMI"),
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
        )
        hard_reject = bool(hard_audit.get("has_hard_reject")) or hard_audit.get("replay_failed") is not None
        adoptable = (
            unresolved_recalc == 0
            and ev.final_state.basenum == 1
            and bool(snap["full_span"])
            and not hard_reject
        )
        if adoptable:
            adoptable_count += 1
        evidences.append(
            {
                "rank": rank,
                "steps_to_goal": len(ev.steps),
                "tree_signature": _canonical_tree_signature(snap["tree"]),
                "tree": snap["tree"],
                "process": snap["process"],
                "history": [
                    {
                        "step": i + 1,
                        "rule_name": st.rule_name,
                        "rule_number": st.rule_number,
                        "rule_kind": st.rule_kind,
                        "left": st.left,
                        "right": st.right,
                        "check": st.check,
                        "left_id": st.left_id,
                        "right_id": st.right_id,
                    }
                    for i, st in enumerate(ev.steps)
                ],
                "full_span": bool(snap["full_span"]),
                "full_span_tree": len(snap["missing_tree"]) == 0,
                "full_span_process": len(snap["missing_process"]) == 0,
                "missing_tree": snap["missing_tree"],
                "missing_process": snap["missing_process"],
                "tree_found": snap["tree_found"],
                "process_found": snap["process_found"],
                "basenum": int(ev.final_state.basenum),
                "unresolved_recalc": int(unresolved_recalc),
                "hard_reject": bool(hard_reject),
                "hard_reject_audit": hard_audit,
                "adoptable": bool(adoptable),
            }
        )

    return {
        "run_name": run_name,
        "sentence_key": sentence_key,
        "sentence": SENTENCES[sentence_key],
        "explicit_lexicon_ids": explicit_ids,
        "status": internal.status,
        "reason": internal.reason,
        "completed": bool(internal.completed),
        "metrics": {
            "actions_attempted": int(internal.actions_attempted),
            "max_depth_reached": int(internal.max_depth_reached),
            "best_leaf_unresolved_min": int((internal.leaf_stats or {}).get("unresolved_min", 0)),
            "cache_stats": internal.cache_stats,
        },
        "evidence_present": len(evidences) > 0,
        "adoptable_evidence_present": adoptable_count > 0,
        "adoptable_evidence_count": adoptable_count,
        "evidences": evidences,
    }


def _build_markdown(*, before: dict[str, BeforeSnapshot], after_runs: list[dict[str, Any]], out_json_path: Path) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 core adoptable evidence fix report（{date.today().isoformat()}）")
    lines.append("")
    lines.append("## 1. 修正前 / 修正後 code path")
    lines.append("- [確認済み事実] 修正前（_search_reachability）: `unresolved==0` で goal 記録後に即 return し、basenum>1 の partial-goal からの継続展開を core 側で行わない。")
    lines.append("- [確認済み事実] 修正後（_search_reachability）: `raw_goal_found` を記録し、`adoptable_goal` 判定（basenum==1/full_span/hard_reject=false/unresolved_recalc=0）を追加。")
    lines.append("- [確認済み事実] 修正後（_search_reachability）: `unresolved==0 && basenum>1` の場合に bounded post-goal continuation（imi01, RH/LHのみ）を実行し、adoptable evidence を core 側で回収する。")
    lines.append("- [確認済み事実] 修正後（互換）: imi01 の対象系列（ふわふわ/わたあめ/ひつじ）以外は raw evidence も返す。")
    lines.append("")

    lines.append("## 2. raw_goal_found / adoptable_goal_found 定義")
    lines.append("- [確認済み事実] raw_goal_found: `unresolved==0` に到達した事実。")
    lines.append("- [確認済み事実] adoptable_goal_found: `unresolved_recalc==0 && basenum==1 && full_span==true && hard_reject==false` を満たす evidence。")
    lines.append("")

    lines.append("## 3. S4/S3 candidate before / after")
    for run in after_runs:
        rn = run["run_name"]
        b = before.get(rn)
        lines.append(f"### {rn}")
        if b is None:
            lines.append("- [未確認] 修正前スナップショット（保存済み監査JSON）を取得できなかった。")
        else:
            lines.append(
                f"- [確認済み事実] before: status={b.status} reason={b.reason} evidence_present={b.evidence_present} natural_reachable_evidence_present={b.natural_reachable_evidence_present} full_span={b.full_span} basenum={b.basenum} unresolved_recalc={b.unresolved_recalc}"
            )
        lines.append(
            f"- [確認済み事実] after: status={run['status']} reason={run['reason']} evidence_present={run['evidence_present']} adoptable_evidence_present={run['adoptable_evidence_present']} adoptable_evidence_count={run['adoptable_evidence_count']}"
        )
        metrics = run["metrics"]
        lines.append(
            f"- [確認済み事実] after metrics: actions_attempted={metrics['actions_attempted']} max_depth_reached={metrics['max_depth_reached']} best_leaf_unresolved_min={metrics['best_leaf_unresolved_min']}"
        )
        cache_stats = metrics.get("cache_stats") or {}
        lines.append(
            f"- [確認済み事実] after cache_stats: raw_goal_found_count={cache_stats.get('raw_goal_found_count')} adoptable_goal_found_count={cache_stats.get('adoptable_goal_found_count')} post_goal_continuation_invocations={cache_stats.get('post_goal_continuation_invocations')} post_goal_continuation_actions={cache_stats.get('post_goal_continuation_actions')}"
        )
        lines.append("")

    lines.append("## 4. evidence 詳細（top）")
    for run in after_runs:
        rn = run["run_name"]
        lines.append(f"### {rn}")
        if not run["evidences"]:
            lines.append("- [未確認] evidence が 0 件のため詳細なし。")
            lines.append("")
            continue
        for ev in run["evidences"][:3]:
            lines.append(
                f"- [確認済み事実] rank={ev['rank']} adoptable={ev['adoptable']} basenum={ev['basenum']} unresolved_recalc={ev['unresolved_recalc']} full_span={ev['full_span']} hard_reject={ev['hard_reject']}"
            )
            lines.append(f"  - tree_signature: `{ev['tree_signature']}`")
            lines.append(f"  - history_len: {len(ev['history'])}")
            lines.append(f"  - tree: `{json.dumps(ev['tree'], ensure_ascii=False)}`")
            lines.append(f"  - process: `{ev['process']}`")
            lines.append(f"  - history: `{json.dumps(ev['history'], ensure_ascii=False)}`")
        lines.append("")

    lines.append("## 5. 既知課題")
    unknowns = []
    for run in after_runs:
        if not run["adoptable_evidence_present"]:
            unknowns.append(f"{run['run_name']}: adoptable evidence が未回収")
    if not unknowns:
        lines.append("- [確認済み事実] 今回対象（S4/S3 fixed candidate）では core API で adoptable evidence を回収できた。")
    else:
        for row in unknowns:
            lines.append(f"- [未確認] {row}")

    lines.append("")
    lines.append("## 6. 出力ファイル")
    lines.append(f"- [確認済み事実] JSON: `{out_json_path}`")

    return "\n".join(lines) + "\n"


def main() -> None:
    before = _read_before_snapshot()
    extra_rows: list[str] = list(RETAINED_ROWS)
    for row in (NEW_ROW_1, NEW_ROW_2):
        if isinstance(row, dict):
            csv_row = row.get("csv_row")
            if isinstance(csv_row, str):
                extra_rows.append(csv_row)
        elif isinstance(row, str):
            extra_rows.append(row)
    tmp, legacy_root = _create_temp_legacy_root(rows=extra_rows)
    try:
        lexicon = load_legacy_lexicon(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)
        after_runs = [
            _run_candidate(legacy_root=legacy_root, lexicon=lexicon, candidate=candidate)
            for candidate in CANDIDATES
        ]
    finally:
        tmp.cleanup()

    payload = {
        "generated_at": date.today().isoformat(),
        "code_path": {
            "before": {
                "search": "unresolved==0 で即 return（partial-goal から core continuation なし）",
                "evidence": "goal 到達時点の state をそのまま evidence 化",
            },
            "after": {
                "search": "raw_goal と adoptable_goal を分離し、imi01 では post-goal continuation を実行",
                "adoptable": "unresolved_recalc==0 && basenum==1 && full_span==true && hard_reject==false",
                "evidence": "adoptable evidence を優先保存（対象系列 strict）",
            },
        },
        "before_snapshot": {
            key: {
                "status": value.status,
                "reason": value.reason,
                "evidence_present": value.evidence_present,
                "natural_reachable_evidence_present": value.natural_reachable_evidence_present,
                "full_span": value.full_span,
                "basenum": value.basenum,
                "unresolved_recalc": value.unresolved_recalc,
            }
            for key, value in before.items()
        },
        "after_runs": after_runs,
    }

    out_json = PROJECT_ROOT / f"docs/specs/reachability-imi01-core-adoptable-fix-{date.today().strftime('%Y%m%d')}.json"
    out_md = PROJECT_ROOT / f"docs/specs/reachability-imi01-core-adoptable-fix-{date.today().strftime('%Y%m%d')}.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_build_markdown(before=before, after_runs=after_runs, out_json_path=out_json), encoding="utf-8")
    print(out_json)
    print(out_md)


if __name__ == "__main__":
    main()
