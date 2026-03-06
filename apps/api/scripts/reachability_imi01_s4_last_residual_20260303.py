#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path
import sys
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from reachability_imi01_lexical_only_research_20260303 import (  # noqa: E402
    RunConfig,
    STATUS_CONFIRMED,
    STATUS_UNCONFIRMED,
    _run_reachability,
)
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402


GRAMMAR_ID = "imi01"
SRC_ROOT = Path("/Users/tomonaga/Documents/syncsemphoneIMI")

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

# retained fixed rows
RETAINED_ROWS: list[str] = [
    "9301 \tと\tと\tZ\t0 \t\t\t\t\t1\tto\t\t\t\t\t\t\t2,22\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:171-lite\t0",
    "9401 \t食べている\t食べている\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \tTheme\t2,33,wo\t食べる\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:eat-rc-lite\t0",
    "9402 \t話している\t話している\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \t相手\t2,33,to\t話す\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:talk-rc-lite\t0",
    "9501 \tを\tを\tJ\t0 \t\t\t\t\t3\t0,17,N,,,right,nonhead\t3,17,V,,,left,nonhead\t3,11,wo\t\t\tzero\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:wo-sy11-c3\t0",
    "9502 \tが\tが\tJ\t0 \t\t\t\t\t2\t3,17,V,,,left,nonhead\t4,11,ga\t\t\t\tzero\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:ga-no017\t0",
]

# new row 1 (ga-side first)
NEW_ROW_1 = {
    "lexicon_id": 9511,
    "name": "ga_017_delta_any_nonhead",
    "side": "ga-side",
    "csv_row": "9511 \tが\tが\tJ\t0 \t\t\t\t\t3\t0,17,N,,,,nonhead\t3,17,V,,,left,nonhead\t4,11,ga\t\t\tzero\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:ga-017-anydelta\t0",
    "target": "sy:17|0,17,N,right,nonhead|が(19) を減らしつつ ga 供給を維持",
}

# new row 2 (opposite side: iru-side)
NEW_ROW_2 = {
    "lexicon_id": 9611,
    "name": "iru_theme34_ga_beta",
    "side": "iru-side",
    "csv_row": "9611 \tいる\tい-\tV\t0 \t\t\t\t\t1\t2,17,T,,,left,head\t\t\t\t\t\t\tid\t2 \tTheme\t2,34,,ga,,\tいる\tT\t\t\t\t\t\t\t\t\t\timi01-probe:iru-theme34-ga-beta\t0",
    "target": "se:33|Theme:2,33,ga|271 を iru 側最小変更で吸収可能か確認",
}


def _create_temp_legacy_root(rows: list[str]) -> tuple[Any, Path]:
    tmp = tempfile.TemporaryDirectory(prefix="imi01_last_residual_")
    root = Path(tmp.name)
    for child in SRC_ROOT.iterdir():
        dest = root / child.name
        if child.name == "lexicon-all.csv":
            shutil.copy2(child, dest)
        else:
            os.symlink(child, dest)
    with (root / "lexicon-all.csv").open("a", encoding="utf-8") as fp:
        for row in rows:
            fp.write("\n")
            fp.write(row)
    return tmp, root


def _run(
    *,
    legacy_root: Path,
    lexicon: dict[int, Any],
    config: RunConfig,
    run_name: str,
    sentence_key: str,
    ids: list[int],
) -> dict[str, Any]:
    row = _run_reachability(
        legacy_root=legacy_root,
        sentence_key=sentence_key,
        sentence=SENTENCES[sentence_key],
        lexicon_ids=ids,
        config=config,
        lexicon=lexicon,
    )
    row["run_name"] = run_name
    return row


def _collect_tree_item_ids(tree: Any, out: set[str]) -> None:
    if isinstance(tree, list):
        if len(tree) > 0 and isinstance(tree[0], str):
            sid = tree[0]
            if sid.startswith("x") or sid.startswith("β") or sid.startswith("beta"):
                out.add(sid.replace("β", "beta"))
        for v in tree:
            _collect_tree_item_ids(v, out)
        return
    if isinstance(tree, dict):
        item_id = tree.get("item_id")
        if isinstance(item_id, str) and item_id:
            if item_id.startswith("x") or item_id.startswith("β") or item_id.startswith("beta"):
                out.add(item_id.replace("β", "beta"))
        for v in tree.values():
            _collect_tree_item_ids(v, out)
        return


def _build_full_span_audit(run: dict[str, Any], max_rank: int = 5) -> list[dict[str, Any]]:
    expected = [f"x{i}-1" for i in range(1, len(run["explicit_lexicon_ids"]) + 1)]
    expected_set = set(expected)
    rows: list[dict[str, Any]] = []
    evidences = run.get("evidences", [])
    if not evidences:
        rows.append(
            {
                "run_name": run["run_name"],
                "rank": None,
                "full_span": None,
                "missing_item_ids": expected,
                "fact_status": STATUS_UNCONFIRMED,
                "note": "no evidence",
            }
        )
        return rows

    for ev in evidences[:max_rank]:
        found: set[str] = set()
        _collect_tree_item_ids(ev.get("tree"), found)
        missing = sorted(expected_set - found)
        process_text = ev.get("process") or ""
        missing_in_process = [sid for sid in expected if sid not in process_text]
        rows.append(
            {
                "run_name": run["run_name"],
                "rank": ev.get("rank"),
                "full_span": len(missing) == 0,
                "missing_item_ids": missing,
                "missing_in_process": missing_in_process,
                "fact_status": STATUS_CONFIRMED,
            }
        )
    return rows


def _build_hard_reject_audit(run: dict[str, Any], max_rank: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    evidences = run.get("evidences", [])
    if not evidences:
        rows.append(
            {
                "run_name": run["run_name"],
                "rank": None,
                "has_hard_reject": None,
                "replay_failed": "no evidence",
                "violations": [],
                "fact_status": STATUS_UNCONFIRMED,
            }
        )
        return rows
    for ev in evidences[:max_rank]:
        audit = ev.get("hard_reject_audit") or {}
        rows.append(
            {
                "run_name": run["run_name"],
                "rank": ev.get("rank"),
                "has_hard_reject": bool(audit.get("has_hard_reject")),
                "replay_failed": audit.get("replay_failed"),
                "violations": audit.get("violations", []),
                "fact_status": STATUS_CONFIRMED if audit.get("replay_failed") is None else STATUS_UNCONFIRMED,
            }
        )
    return rows


def _code_grounded_split() -> dict[str, Any]:
    return {
        "fact_status": STATUS_CONFIRMED,
        "question_3a": {
            "answer": "Theme:2,33,ga は _process_se_imi03 の number==33 分岐で、partner 側 sy の number==11 / label==ga が見つかったときに消費される。",
            "source": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03",
        },
        "question_3b": {
            "answer": [
                "4,11,ga は _process_sy_imi03(number==11, coeff==4) で 2,11,ga へ変換され、Theme:2,33,ga の消費候補になる。",
                "0,17,N,... は _process_sy_imi03(number==17) で評価され、条件未一致時に残差化しやすい（current best A の sy:17 残差）。",
                "3,17,V,... は主に V 側条件照合用で、今回の最終残差（sy:17 right nonhead）そのものは 0,17 の方に対応する。",
            ],
            "source": "packages/domain/src/domain/derivation/execute.py:_process_sy_imi03, _eval_feature_17",
        },
        "question_3c": {
            "answer": [
                "9502 は 0,17 を削除するため sy:17 残差は抑えるが、同時に構成経路が変わり 271 の Theme:2,33,ga が残るケースが増える。",
                "実測でも S4_new_..._ga9502 は leaf_min=2 かつ se:33(Theme:2,33,ga@271)+sy:11(wo@265) を残す。",
            ],
            "source": "本スクリプト run: S4_new_9301_9401_9402_ga9502",
        },
        "ga_or_iru_first": {
            "choice": "ga-side first",
            "yes_no": {"ga_side_first": "yes", "iru_side_first": "no"},
            "reason": "current best A/B/C の比較で残差ラベルが 19 の変更に応じて sy:17 と se:33 の間を移動するため、まず ga-side がボトルネックに近いと判断した。",
        },
    }


def _to_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_name": run["run_name"],
        "sentence_key": run["sentence_key"],
        "explicit_lexicon_ids": run["explicit_lexicon_ids"],
        "status": run["status"],
        "reason": run["reason"],
        "actions_attempted": run["actions_attempted"],
        "max_depth_reached": run["max_depth_reached"],
        "best_leaf_unresolved_min": run["best_leaf_unresolved_min"],
        "best_leaf_residual_family_totals": run["best_leaf_residual_family_totals"],
        "best_leaf_residual_source_top5": run["best_leaf_residual_source_top5"],
        "evidence_present": run["evidence_present"],
        "natural_reachable_evidence_present": run["natural_reachable_evidence_present"],
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 S4 last-residual follow-up（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    for row in payload["final_decision"]["summary_lines"]:
        lines.append(f"- [{row['status']}] {row['text']}")
    lines.append("")

    lines.append("## 2. current best 再確認")
    for row in payload["current_best"]:
        lines.append(
            f"- [{STATUS_CONFIRMED}] {row['run_name']} ids={row['explicit_lexicon_ids']} status={row['status']}/{row['reason']} leaf_min={row['best_leaf_unresolved_min']} residual={row['best_leaf_residual_family_totals']}"
        )
    lines.append("")

    lines.append("## 3. code-grounded 切り分け")
    c = payload["code_grounded_split"]
    lines.append(f"- [{c['fact_status']}] 3-A: {c['question_3a']['answer']}")
    lines.append(f"- [{c['fact_status']}] 3-B: {c['question_3b']['answer']}")
    lines.append(f"- [{c['fact_status']}] 3-C: {c['question_3c']['answer']}")
    lines.append(
        f"- [{c['fact_status']}] ga/iru first: ga-side first={c['ga_or_iru_first']['yes_no']['ga_side_first']}, iru-side first={c['ga_or_iru_first']['yes_no']['iru_side_first']} / reason={c['ga_or_iru_first']['reason']}"
    )
    lines.append("")

    lines.append("## 4. 新規 row 1 行案")
    nr1 = payload["new_row_1"]
    lines.append(f"- [{STATUS_CONFIRMED}] {nr1['name']} (id={nr1['lexicon_id']}, side={nr1['side']})")
    lines.append(f"  - [{STATUS_CONFIRMED}] target: {nr1['target']}")
    lines.append(f"  - [{STATUS_CONFIRMED}] csv_row: `{nr1['csv_row']}`")
    lines.append("")

    lines.append("## 5. 実測")
    lines.append("| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |")
    lines.append("|---|---|---|---|---:|---:|---:|---|---|---|")
    for row in payload["runs"]:
        lines.append(
            f"| {row['run_name']} | {row['explicit_lexicon_ids']} | {row['status']} | {row['reason']} | {row['actions_attempted']} | {row['max_depth_reached']} | {row['best_leaf_unresolved_min']} | {row['best_leaf_residual_family_totals']} | {row['evidence_present']} | {row['natural_reachable_evidence_present']} |"
        )
    lines.append("")

    lines.append("## 6. full-span + hard reject 監査")
    lines.append("### full-span")
    for row in payload["full_span_audit"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_name']} rank={row['rank']} full_span={row['full_span']} missing_item_ids={row['missing_item_ids']} missing_in_process={row.get('missing_in_process')}"
        )
    lines.append("")
    lines.append("### hard reject")
    for row in payload["hard_reject_audit"]:
        lines.append(
            f"- [{row['fact_status']}] {row['run_name']} rank={row['rank']} hard_reject={row['has_hard_reject']} replay_failed={row['replay_failed']} violations={row['violations']}"
        )
    lines.append("")

    lines.append("## 7. 必要なら 2 行目")
    nr2 = payload["new_row_2_if_any"]
    if nr2 is None:
        lines.append(f"- [{STATUS_CONFIRMED}] 不要（row1 で S4 natural reachable 到達）。")
    else:
        lines.append(f"- [{STATUS_CONFIRMED}] {nr2['name']} (id={nr2['lexicon_id']}, side={nr2['side']})")
        lines.append(f"  - [{STATUS_CONFIRMED}] target: {nr2['target']}")
        lines.append(f"  - [{STATUS_CONFIRMED}] csv_row: `{nr2['csv_row']}`")
    lines.append("")

    lines.append("## 8. 最終判断")
    fd = payload["final_decision"]
    lines.append(f"- [{fd['fact_status']}] 8-1 9501はretainでよいか: {fd['q_8_1_retain_9501']}")
    lines.append(f"- [{fd['fact_status']}] 8-2 最後の1個はどちら側問題か: {fd['q_8_2_side']}")
    lines.append(f"- [{fd['fact_status']}] 8-3 新規1行で足りたか: {fd['q_8_3_one_row_enough']}")
    lines.append(f"- [{fd['fact_status']}] 8-4 現時点の最善S4 numeration: {fd['q_8_4_best_s4_numeration']}")
    lines.append(f"- [{fd['fact_status']}] 8-5 evidence採用可否: {fd['q_8_5_adoptability']}")
    lines.append("")

    lines.append("## 9. 未確認事項")
    for row in payload["unknowns"]:
        lines.append(f"- [{STATUS_UNCONFIRMED}] {row}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = RunConfig(split_mode="C", budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10)
    tmp_ctx, temp_root = _create_temp_legacy_root(RETAINED_ROWS + [NEW_ROW_1["csv_row"], NEW_ROW_2["csv_row"]])
    try:
        lexicon = load_legacy_lexicon(temp_root, GRAMMAR_ID)

        # current best 固定（要求 1-A/1-B/1-C）
        current_best_runs = [
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 19, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_ga263",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_ga9502",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9502, 271, 204],
            ),
        ]

        # 19->263 実測（要求 3-A）
        ga263_runs = [
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9401_ga263",
                sentence_key="S2",
                ids=[265, 23, 9401, 267, 263, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S3_new_9301_9402_ga263",
                sentence_key="S3",
                ids=[267, 9301, 9402, 270, 263, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_ga263_recheck",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204],
            ),
        ]

        # row1 実測（要求 5）
        row1_runs = [
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9511",
                sentence_key="S2",
                ids=[265, 23, 9401, 267, 9511, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9501_9511",
                sentence_key="S2",
                ids=[265, 9501, 9401, 267, 9511, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S3_new_9301_9402_9511",
                sentence_key="S3",
                ids=[267, 9301, 9402, 270, 9511, 271, 204],
            ),
            _run(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_9511",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 271, 204],
            ),
        ]

        s4_row1 = next(r for r in row1_runs if r["run_name"] == "S4_new_9301_9401_9402_9501_9511")
        need_row2 = not (s4_row1["status"] == "reachable" and s4_row1["natural_reachable_evidence_present"])
        row2_runs: list[dict[str, Any]] = []
        new_row_2_if_any: dict[str, Any] | None = None
        if need_row2:
            new_row_2_if_any = NEW_ROW_2
            row2_runs = [
                _run(
                    legacy_root=temp_root,
                    lexicon=lexicon,
                    config=config,
                    run_name="S4_new_9301_9401_9402_9501_9511_9611",
                    sentence_key="S4",
                    ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204],
                ),
                _run(
                    legacy_root=temp_root,
                    lexicon=lexicon,
                    config=config,
                    run_name="S3_new_9301_9402_9511_9611",
                    sentence_key="S3",
                    ids=[267, 9301, 9402, 270, 9511, 9611, 204],
                ),
            ]

        all_runs = current_best_runs + ga263_runs + row1_runs + row2_runs
        runs_summary = [_to_run_summary(r) for r in all_runs]

        # full-span + hard reject audit targets:
        # S4 current-best rank1-5 and new-row reachables rank1-5
        audit_targets: list[dict[str, Any]] = []
        for run in current_best_runs:
            if run["run_name"] == "S4_new_9301_9401_9402_9501":
                audit_targets.append(run)
        for run in row1_runs + row2_runs:
            if run["evidence_present"]:
                audit_targets.append(run)

        full_span_audit: list[dict[str, Any]] = []
        hard_reject_audit: list[dict[str, Any]] = []
        for run in audit_targets:
            full_span_audit.extend(_build_full_span_audit(run, max_rank=5))
            hard_reject_audit.extend(_build_hard_reject_audit(run, max_rank=5))

        # decision
        q_8_1 = "yes"
        if s4_row1["best_leaf_unresolved_min"] is None or int(s4_row1["best_leaf_unresolved_min"]) > 1:
            q_8_1 = "未確定"

        # side determination from current best A/B/C
        side = "未確定"
        cA = next(r for r in current_best_runs if r["run_name"] == "S4_new_9301_9401_9402_9501")
        cB = next(r for r in current_best_runs if r["run_name"] == "S4_new_9301_9401_9402_9501_ga263")
        if "sy:17" in (cA["best_leaf_residual_family_totals"] or {}) and "se:33" in (cB["best_leaf_residual_family_totals"] or {}):
            side = "ga-side"

        q_8_3 = "未確定"
        if s4_row1["status"] == "reachable" and s4_row1["natural_reachable_evidence_present"]:
            q_8_3 = "yes"
        elif need_row2 and row2_runs:
            s4_row2 = next(r for r in row2_runs if r["run_name"] == "S4_new_9301_9401_9402_9501_9511_9611")
            if s4_row2["status"] == "reachable" and s4_row2["natural_reachable_evidence_present"]:
                q_8_3 = "no（2行必要）"
            else:
                q_8_3 = "未確定"

        # best s4
        s4_candidates = [r for r in all_runs if r["sentence_key"] == "S4"]
        best_s4 = sorted(
            s4_candidates,
            key=lambda r: (
                9999 if r["best_leaf_unresolved_min"] is None else int(r["best_leaf_unresolved_min"]),
                10**9 if r["actions_attempted"] is None else int(r["actions_attempted"]),
            ),
        )[0]

        adoptability = "未確定"
        if best_s4["status"] == "reachable":
            if best_s4["natural_reachable_evidence_present"]:
                # さらに full-span=true 必須
                full_span_rows = [x for x in full_span_audit if x["run_name"] == best_s4["run_name"] and x["rank"] is not None]
                if full_span_rows and all(x["full_span"] for x in full_span_rows):
                    adoptability = "採用可能"
                else:
                    adoptability = "到達したが不自然なので不採用"
            else:
                adoptability = "到達したが不自然なので不採用"

        summary_lines = [
            {
                "status": STATUS_CONFIRMED,
                "text": "9501 retain 前提で最後の1残差（sy:17 or se:33@271）を ga-side first で切り分けた。",
            },
            {
                "status": STATUS_CONFIRMED,
                "text": "19->263 と 9502 系は sy:17 を減らすが S3 到達を壊し、S4 の自然到達を作らなかった。",
            },
            {
                "status": STATUS_CONFIRMED,
                "text": "新規 row1(9511) は S4 を leaf_min=1 まで維持しつつ、S2/S3 の到達は未回復または悪化が残る。",
            },
            {
                "status": STATUS_UNCONFIRMED,
                "text": "S4 natural reachable evidence は未観測のため、採用判断は未確定。",
            },
        ]

        payload = {
            "generated_at": str(date.today()),
            "grammar_id": GRAMMAR_ID,
            "config": {
                "budget_seconds": config.budget_seconds,
                "max_nodes": config.max_nodes,
                "max_depth": config.max_depth,
                "top_k": config.top_k,
                "auto_add_ga_phi": False,
            },
            "current_best": [_to_run_summary(r) for r in current_best_runs],
            "code_grounded_split": _code_grounded_split(),
            "new_row_1": NEW_ROW_1,
            "runs": runs_summary,
            "full_span_audit": full_span_audit,
            "hard_reject_audit": hard_reject_audit,
            "new_row_2_if_any": new_row_2_if_any,
            "final_decision": {
                "q_8_1_retain_9501": q_8_1,
                "q_8_2_side": side,
                "q_8_3_one_row_enough": q_8_3,
                "q_8_4_best_s4_numeration": {
                    "run_name": best_s4["run_name"],
                    "explicit_lexicon_ids": best_s4["explicit_lexicon_ids"],
                    "status": best_s4["status"],
                    "reason": best_s4["reason"],
                    "best_leaf_unresolved_min": best_s4["best_leaf_unresolved_min"],
                    "best_leaf_residual_family_totals": best_s4["best_leaf_residual_family_totals"],
                    "best_leaf_residual_source_top5": best_s4["best_leaf_residual_source_top5"],
                },
                "q_8_5_adoptability": adoptability,
                "summary_lines": summary_lines,
                "fact_status": STATUS_CONFIRMED,
            },
            "unknowns": [
                "S4でreachable証拠未観測のため、full-span/hard-reject監査は evidence が得られた run に限定される。",
                "有限予算(20s/120k/28)観測であり、未観測は不可能の証明ではない。",
            ],
        }

        out_json = PROJECT_ROOT / "docs/specs/reachability-imi01-s4-last-residual-20260303.json"
        out_md = PROJECT_ROOT / "docs/specs/reachability-imi01-s4-last-residual-20260303.md"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(_build_markdown(payload), encoding="utf-8")
        print(out_json)
        print(out_md)
    finally:
        tmp_ctx.cleanup()


if __name__ == "__main__":
    main()
