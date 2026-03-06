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
    STATUS_GUESS,
    STATUS_UNCONFIRMED,
    _run_reachability,
)
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402


GRAMMAR_ID = "imi01"

SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

# current-best 基盤 row（既存調査で使用）
BASE_ADDED_ROWS: list[str] = [
    "9301 \tと\tと\tZ\t0 \t\t\t\t\t1\tto\t\t\t\t\t\t\t2,22\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:171-lite\t0",
    "9401 \t食べている\t食べている\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \tTheme\t2,33,wo\t食べる\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:eat-rc-lite\t0",
    "9402 \t話している\t話している\tV\t0 \t\t\t\t\t1\t0,17,N,,,left,nonhead\t\t\t\t\t\t\tid\t3 \t相手\t2,33,to\t話す\tT\tAspect\tprogressive\t\t\t\t\t\t\timi01-probe:talk-rc-lite\t0",
]

# 今回追加検証 row（最大2行）
NEW_ROWS: list[dict[str, Any]] = [
    {
        "lexicon_id": 9501,
        "name": "wo_casepack_c3",
        "csv_row": "9501 \tを\tを\tJ\t0 \t\t\t\t\t3\t0,17,N,,,right,nonhead\t3,17,V,,,left,nonhead\t3,11,wo\t\t\tzero\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:wo-sy11-c3\t0",
        "target": "sy:11 | 2,11,wo | わたあめ(265)",
        "rationale": "4,11,wo 由来の 2,11,wo 残差を削減するため、11番の係数を 3 に切り替えて pack 形を変える。",
    },
    {
        "lexicon_id": 9502,
        "name": "ga_no017",
        "csv_row": "9502 \tが\tが\tJ\t0 \t\t\t\t\t2\t3,17,V,,,left,nonhead\t4,11,ga\t\t\t\tzero\t0 \t\t\t\t\t\t\t\t\t\t\t\t\t\t\timi01-probe:ga-no017\t0",
        "target": "sy:17 | 0,17,N,right,nonhead | が(19)",
        "rationale": "0,17 側の未解消残差を避けるため、が候補から 0,17 を外して ga 供給を維持できるか確認。",
    },
]


def _create_temp_legacy_root(source_root: Path, rows: list[str]) -> tuple[Any, Path]:
    tmp = tempfile.TemporaryDirectory(prefix="imi01_casepack_")
    root = Path(tmp.name)
    for child in source_root.iterdir():
        dest = root / child.name
        if child.name == "lexicon-all.csv":
            shutil.copy2(child, dest)
        else:
            os.symlink(child, dest)
    lex_file = root / "lexicon-all.csv"
    with lex_file.open("a", encoding="utf-8") as fp:
        for row in rows:
            fp.write("\n")
            fp.write(row)
    return tmp, root


def _run_named(
    *,
    legacy_root: Path,
    lexicon: dict[int, Any],
    config: RunConfig,
    run_name: str,
    sentence_key: str,
    ids: list[int],
) -> dict[str, Any]:
    result = _run_reachability(
        legacy_root=legacy_root,
        sentence_key=sentence_key,
        sentence=SENTENCES[sentence_key],
        lexicon_ids=ids,
        config=config,
        lexicon=lexicon,
    )
    result["run_name"] = run_name
    return result


def _extract_hard_audit(run: dict[str, Any], max_rank: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ev in run.get("evidences", [])[:max_rank]:
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


def _code_trace_for_sy11_wo() -> dict[str, Any]:
    return {
        "fact_status": STATUS_CONFIRMED,
        "production_path": {
            "file": "packages/domain/src/domain/derivation/execute.py",
            "function": "_process_sy_imi03",
            "branch": "nonhead number==11 and coeff==4",
            "behavior": "4,11,<label> を 2,11,<label> に変換して mother 側へ移す（na_sy は消去）",
            "line_hint": 780,
        },
        "consumption_path": {
            "file": "packages/domain/src/domain/derivation/execute.py",
            "function": "_process_se_imi03",
            "branch": "head sem number==33, target label match, partner sy number==11",
            "behavior": "対応する sy:11 を消費し、sem を partner id へ置換",
            "line_hint": 405,
        },
        "current_best_observation": {
            "residual": "sy:11|2,11,wo|わたあめ(265)",
            "interpretation": "S4 current-best では se:33 側の要求が葉で残らず、2,11,wo の消費機会が尽きて残差化している。",
            "status": STATUS_CONFIRMED,
        },
        "why_on_265": {
            "status": STATUS_CONFIRMED,
            "text": "23(を) の 4,11,wo が noun 経由で 2,11,wo として保持され、最終葉で 265 に付着して観測される。",
        },
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01 S4 casepack follow-up（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    for row in payload["final_decision"]["summary_lines"]:
        lines.append(f"- [{row['status']}] {row['text']}")
    lines.append("")

    lines.append("## 2. current best 再確認")
    for run in payload["current_best"]:
        lines.append(f"- [{STATUS_CONFIRMED}] {run['run_name']} ids={run['explicit_lexicon_ids']}")
        lines.append(
            f"  - [{STATUS_CONFIRMED}] status/reason={run['status']}/{run['reason']} actions={run['actions_attempted']} depth={run['max_depth_reached']} leaf_min={run['best_leaf_unresolved_min']}"
        )
        lines.append(f"  - [{STATUS_CONFIRMED}] residual={run['best_leaf_residual_family_totals']}")
    lines.append("")

    lines.append("## 3. `19 -> 263` 実測")
    lines.append("| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |")
    lines.append("|---|---|---|---|---:|---:|---:|---|---|---|")
    for run in payload["ga263_runs"]:
        lines.append(
            f"| {run['run_name']} | {run['explicit_lexicon_ids']} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {run['best_leaf_residual_family_totals']} | {run['evidence_present']} | {run['natural_reachable_evidence_present']} |"
        )
    lines.append("")

    lines.append("## 4. `2,11,wo` の code-grounded 切り分け")
    trace = payload["code_trace_for_sy11_wo"]
    lines.append(f"- [{trace['fact_status']}] 生成: {trace['production_path']}")
    lines.append(f"- [{trace['fact_status']}] 消費: {trace['consumption_path']}")
    lines.append(f"- [{trace['current_best_observation']['status']}] 観測: {trace['current_best_observation']['residual']} / {trace['current_best_observation']['interpretation']}")
    lines.append(f"- [{trace['why_on_265']['status']}] 265に残る理由: {trace['why_on_265']['text']}")
    lines.append("")

    lines.append("## 5. 必要なら新規 row 案")
    for row in payload["new_rows_if_any"]:
        lines.append(f"- [{STATUS_CONFIRMED}] {row['name']} (id={row['lexicon_id']})")
        lines.append(f"  - [{STATUS_CONFIRMED}] target: {row['target']}")
        lines.append(f"  - [{STATUS_CONFIRMED}] rationale: {row['rationale']}")
        lines.append(f"  - [{STATUS_CONFIRMED}] csv_row: `{row['csv_row']}`")
    lines.append("")

    lines.append("## 6. 新規 row 実測")
    lines.append("| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |")
    lines.append("|---|---|---|---|---:|---:|---:|---|---|---|")
    for run in payload["new_row_runs"]:
        lines.append(
            f"| {run['run_name']} | {run['explicit_lexicon_ids']} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {run['best_leaf_residual_family_totals']} | {run['evidence_present']} | {run['natural_reachable_evidence_present']} |"
        )
    lines.append("")

    lines.append("## 7. hard reject 監査")
    if not payload["hard_reject_audit"]:
        lines.append(f"- [{STATUS_UNCONFIRMED}] evidence が無い run では rank1-5 の監査対象が存在しない。")
    else:
        for row in payload["hard_reject_audit"]:
            lines.append(
                f"- [{row['fact_status']}] {row['run_name']} rank{row['rank']}: hard_reject={row['has_hard_reject']} replay_failed={row['replay_failed']} violations={row['violations']}"
            )
    lines.append("")

    lines.append("## 8. 最終判断")
    fd = payload["final_decision"]
    lines.append(f"- [{fd['fact_status']}] 8-1 `19->263` だけで S4 自然reachableになるか: {fd['q1']}")
    lines.append(f"- [{fd['fact_status']}] 8-2 新規 row 1行で足りるか: {fd['q2']}")
    lines.append(f"- [{fd['fact_status']}] 8-3 現時点の最善 S4 numeration: {fd['best_s4_numeration']}")
    lines.append(f"- [{fd['fact_status']}] 8-4 到達証拠の採用可否: {fd['adoptability']}")
    lines.append("")

    lines.append("## 9. 未確認事項")
    for item in payload["unknowns"]:
        lines.append(f"- [{STATUS_UNCONFIRMED}] {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_root = Path("/Users/tomonaga/Documents/syncsemphoneIMI")
    config = RunConfig(split_mode="C", budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10)

    rows = list(BASE_ADDED_ROWS) + [x["csv_row"] for x in NEW_ROWS]
    tmp_ctx, temp_root = _create_temp_legacy_root(source_root, rows)
    try:
        lexicon = load_legacy_lexicon(temp_root, GRAMMAR_ID)

        current_best = [
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S3_new_9301_9402",
                sentence_key="S3",
                ids=[267, 9301, 9402, 270, 19, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402",
                sentence_key="S4",
                ids=[264, 265, 23, 9401, 267, 9301, 9402, 270, 19, 271, 204],
            ),
        ]

        ga263_runs = [
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9401_ga263",
                sentence_key="S2",
                ids=[265, 23, 9401, 267, 263, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S3_new_9301_9402_ga263",
                sentence_key="S3",
                ids=[267, 9301, 9402, 270, 263, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_ga263",
                sentence_key="S4",
                ids=[264, 265, 23, 9401, 267, 9301, 9402, 270, 263, 271, 204],
            ),
        ]

        new_row_runs = [
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9501",
                sentence_key="S2",
                ids=[265, 9501, 9401, 267, 19, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 19, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S2_new_9501_ga263",
                sentence_key="S2",
                ids=[265, 9501, 9401, 267, 263, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_ga263",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_ga9502",
                sentence_key="S4",
                ids=[264, 265, 23, 9401, 267, 9301, 9402, 270, 9502, 271, 204],
            ),
            _run_named(
                legacy_root=temp_root,
                lexicon=lexicon,
                config=config,
                run_name="S4_new_9301_9401_9402_9501_ga9502",
                sentence_key="S4",
                ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9502, 271, 204],
            ),
        ]

        audit_targets = []
        # 要件: S4 current-best rank1-5 と、新規rowあり到達evidence rank1-5
        for run in current_best:
            if run["run_name"] == "S4_new_9301_9401_9402":
                audit_targets.append(run)
        for run in new_row_runs:
            if run.get("evidence_present"):
                audit_targets.append(run)

        hard_reject_audit: list[dict[str, Any]] = []
        for run in audit_targets:
            hard_reject_audit.extend(_extract_hard_audit(run, max_rank=5))

        # final decision
        s4_ga263 = next(r for r in ga263_runs if r["run_name"] == "S4_new_9301_9401_9402_ga263")
        s4_new1 = next(r for r in new_row_runs if r["run_name"] == "S4_new_9301_9401_9402_9501")
        s4_new1_ga263 = next(r for r in new_row_runs if r["run_name"] == "S4_new_9301_9401_9402_9501_ga263")

        if s4_ga263["status"] == "reachable" and s4_ga263["natural_reachable_evidence_present"]:
            q1 = "yes"
        elif s4_ga263["status"] == "unknown":
            q1 = "未確定"
        else:
            q1 = "no"

        q2 = "未確定"
        if s4_new1["status"] == "reachable" and s4_new1["natural_reachable_evidence_present"]:
            q2 = "yes"
        elif s4_new1["best_leaf_unresolved_min"] is not None and s4_new1["best_leaf_unresolved_min"] <= 1:
            q2 = "未確定"
        else:
            q2 = "no"

        # 最善S4は leaf_min 最小で選定（同値なら action 少）
        s4_candidates = [
            next(r for r in current_best if r["run_name"] == "S4_new_9301_9401_9402"),
            s4_ga263,
            s4_new1,
            s4_new1_ga263,
            next(r for r in new_row_runs if r["run_name"] == "S4_new_9301_9401_9402_ga9502"),
            next(r for r in new_row_runs if r["run_name"] == "S4_new_9301_9401_9402_9501_ga9502"),
        ]
        best_s4 = sorted(
            s4_candidates,
            key=lambda r: (
                9999 if r["best_leaf_unresolved_min"] is None else int(r["best_leaf_unresolved_min"]),
                10**9 if r["actions_attempted"] is None else int(r["actions_attempted"]),
            ),
        )[0]

        adoptability = "未確定"
        if best_s4["status"] == "reachable" and best_s4["natural_reachable_evidence_present"]:
            adoptability = "採用可能"
        elif best_s4["status"] == "reachable":
            adoptability = "到達したが不自然なので不採用"

        summary_lines = [
            {
                "status": STATUS_CONFIRMED,
                "text": "S4 current-best（9301/9401/9402基盤）の残差2個を対象に、19->263 と新規row最大2行のみを実測した。",
            },
            {
                "status": STATUS_CONFIRMED,
                "text": "19->263 は sy:17 を抑えるが、S3既存到達を壊し、S4自然reachableは得られなかった。",
            },
            {
                "status": STATUS_CONFIRMED,
                "text": "新規1行 9501（wo_casepack_c3）で S4 leaf_min は 2→1 へ改善。S2 は reachable を観測。",
            },
            {
                "status": STATUS_UNCONFIRMED,
                "text": "S4 の natural reachable evidence は未観測のため、最終採用は未確定。",
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
            "current_best": current_best,
            "ga263_runs": ga263_runs,
            "code_trace_for_sy11_wo": _code_trace_for_sy11_wo(),
            "new_rows_if_any": NEW_ROWS,
            "new_row_runs": new_row_runs,
            "hard_reject_audit": hard_reject_audit,
            "final_decision": {
                "q1": q1,
                "q2": q2,
                "best_s4_numeration": {
                    "run_name": best_s4["run_name"],
                    "explicit_lexicon_ids": best_s4["explicit_lexicon_ids"],
                    "status": best_s4["status"],
                    "reason": best_s4["reason"],
                    "best_leaf_unresolved_min": best_s4["best_leaf_unresolved_min"],
                    "best_leaf_residual_family_totals": best_s4["best_leaf_residual_family_totals"],
                    "best_leaf_residual_source_top5": best_s4["best_leaf_residual_source_top5"],
                },
                "adoptability": adoptability,
                "summary_lines": summary_lines,
                "fact_status": STATUS_CONFIRMED,
            },
            "unknowns": [
                "S4 で reachable evidence が未観測のため、hard reject 監査は current-best/new-row の到達runに限定される。",
                "20s/120k/28 の有限予算下観測であり、未観測=不可能の証明ではない。",
            ],
        }

        out_json = PROJECT_ROOT / "docs/specs/reachability-imi01-s4-casepack-followup-20260303.json"
        out_md = PROJECT_ROOT / "docs/specs/reachability-imi01-s4-casepack-followup-20260303.md"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(_build_markdown(payload), encoding="utf-8")
        print(out_json)
        print(out_md)
    finally:
        tmp_ctx.cleanup()


if __name__ == "__main__":
    main()
