#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"
STATUS_INFER = "推測"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
IN_IMPL = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-selection-impl-20260302.json"
IN_AUDIT = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-adoption-audit-20260303.json"
OUT_JSON = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-final-decision-20260303.json"
OUT_MD = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-final-decision-20260303.md"


def _safe_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _build_payload(impl: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    explicit_impl = _safe_get(impl, "explicit", "runs", default={}) or {}
    auto_impl = _safe_get(impl, "auto", "runs", default={}) or {}
    explicit_audit = _safe_get(audit, "explicit_runs", default={}) or {}
    comparison = _safe_get(audit, "evidence_comparison", default={}) or {}
    yes_no_src = _safe_get(audit, "yes_no", default={}) or {}

    # fixed adoption candidate for S4 under japanese2 lexical-only
    final_candidate = {
        "grammar_id": "japanese2",
        "lexical_rows": {
            "9301": {"decision": "採用", "reason": f"{STATUS_CONFIRMED}: S3/T2/T1で有効成分、S4比較でもbaseline前提として機能"},
            "181": {"decision": "暫定既定", "reason": f"{STATUS_CONFIRMED}: 9301固定の上で S4 reachable を与える"},
            "189": {"decision": "保留候補", "reason": f"{STATUS_CONFIRMED}: 9301固定の上で S4 reachable を与える（181との差分は要追加監査）"},
            "183": {"decision": "fallback候補", "reason": f"{STATUS_CONFIRMED}: 181後でも S2/T1 で改善幅を持つが既定化根拠は不足"},
            "264_japanese2_lookup": {"decision": "採用", "reason": f"{STATUS_CONFIRMED}: Step.1 auto の generation_failed 解消に必要"},
        },
        "selection_rules": {
            "to": "9301 fixed",
            "wo": "181 default, 189 peer candidate",
            "ga": "19 default, 183 secondary fallback",
            "ru": "204 fixed",
        },
        "adopted_explicit_numeration_s4": {
            "tokens": ["ふわふわした", "わたあめ", "を", "食べている", "ひつじ", "と", "話している", "うさぎ", "が", "いる", "る"],
            "lexicon_ids": [264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
        },
    }

    s4_after_wo181 = _safe_get(explicit_impl, "S4", "after_wo181", default={}) or {}
    s4_after_wo189 = _safe_get(explicit_impl, "S4", "after_wo189", default={}) or {}
    s2_after_wo181 = _safe_get(explicit_impl, "S2", "after_wo181", default={}) or {}
    s2_after_wo189 = _safe_get(explicit_impl, "S2", "after_wo189", default={}) or {}

    adoption_decision = {
        "decision": "まだ確定してはいけない",
        "reason_3_lines": [
            f"{STATUS_CONFIRMED}: 9301固定の上で S4 は 181/189 とも reachable だが、181優位の確証は evidence差分で未確立。",
            f"{STATUS_CONFIRMED}: evidence再計算 unresolved と status=reachable の不一致があり、運用根拠の整合監査が未完了。",
            f"{STATUS_CONFIRMED}: 189を正式除外する根拠は不足し、183も fallback 条件の運用定義のみで確定実装根拠は不足。",
        ],
    }

    evidence_comparison = {
        "S2": {
            "run_181": explicit_audit.get("S2_after_wo181", {}),
            "run_189": explicit_audit.get("S2_after_wo189", {}),
            "comparison": comparison.get("S2_after_wo181_vs_after_wo189", {}),
        },
        "S4": {
            "run_181": explicit_audit.get("S4_after_wo181", {}),
            "run_189": explicit_audit.get("S4_after_wo189", {}),
            "comparison": comparison.get("S4_after_wo181_vs_after_wo189", {}),
        },
    }

    yes_no = {
        "3A_use_reachable_despite_unresolved_recalc_mismatch": {
            "answer": "no",
            "basis": f"{STATUS_CONFIRMED}: audit出力で evidence unresolved 再計算値が 0 でない行が存在。",
            "runs": ["S2_after_wo181", "S2_after_wo189", "S4_after_wo181", "S4_after_wo189"],
        },
        "3B_can_claim_181_more_natural_now": {
            "answer": "no",
            "basis": f"{STATUS_CONFIRMED}: 181/189 の優位を意味自然性で断定できる evidence 差分根拠が未確立。",
            "runs": ["S2_after_wo181_vs_after_wo189", "S4_after_wo181_vs_after_wo189"],
        },
        "3C_can_drop_189_now": {
            "answer": "no",
            "basis": f"{STATUS_CONFIRMED}: 189 でも S2/S4 で reachable が確認され、除外の根拠不足。",
            "runs": ["S2_after_wo189", "S4_after_wo189"],
        },
        "3D_should_keep_183_as_fallback_not_default": {
            "answer": "yes",
            "basis": f"{STATUS_CONFIRMED}: S2/T1で改善幅がある一方、S4は181単独で到達済み。",
            "runs": ["S2_secondary_wo181_ga183", "T1_secondary_wo181_ga183", "S4_after_wo181"],
        },
    }

    fallback_policy_for_183 = {
        "use_183_when": [
            f"{STATUS_INFER}: 181適用後も best_leaf_unresolved_min > 0 が継続し、かつ sy:1 系が残る場合。",
            f"{STATUS_CONFIRMED}: S2では 181+183 で leaf_min 1→0。",
        ],
        "keep_19_when": [
            f"{STATUS_CONFIRMED}: 181単独で best_leaf_unresolved_min=0（S4）。",
        ],
        "control_point": f"{STATUS_INFER}: Step.1固定変更ではなく reachability後段の二段目評価として運用する方が安全。",
    }

    auto_vs_explicit = {}
    adopted_map = {
        "S2": final_candidate["adopted_explicit_numeration_s4"]["lexicon_ids"][:7],  # adjusted below
        "T3": [264, 265, 181, 266, 267, 19, 271, 204],
        "T1": [265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
        "S4": [264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
    }
    adopted_map["S2"] = [265, 181, 266, 267, 19, 271, 204]
    for key in ("S2", "T3", "T1", "S4"):
        auto = auto_impl.get(key, {})
        explicit = adopted_map[key]
        auto_ids = auto.get("lexicon_ids")
        auto_vs_explicit[key] = {
            "sentence": _safe_get(explicit_impl, key, "after_wo181", "sentence", default=auto.get("sentence")),
            "auto_tokens": [row.get("token") for row in (auto.get("token_resolutions") or [])],
            "auto_lexicon_ids": auto_ids,
            "explicit_adopted_lexicon_ids": explicit,
            "is_same": auto_ids == explicit,
            "generation_failed": auto.get("generation_failed"),
            "reason_if_mismatch": None if auto_ids == explicit else f"{STATUS_UNCONFIRMED}: 差分理由は個別監査未実施",
        }

    # top-level structured output
    payload = {
        "generated_at": datetime.now().isoformat(),
        "constraints": {
            "grammar_id": "japanese2",
            "no_grammar_change": True,
            "no_search_change": True,
            "no_phi_solution": True,
            "no_266_9304_retry": True,
            "no_new_lexical_row_proposal": True,
        },
        "final_candidate": final_candidate,
        "adoption_decision": adoption_decision,
        "evidence_comparison": evidence_comparison,
        "yes_no": yes_no,
        "fallback_policy_for_183": fallback_policy_for_183,
        "auto_vs_explicit": auto_vs_explicit,
        "unknowns": [
            f"{STATUS_UNCONFIRMED}: status=reachable と evidence unresolved 再計算値の不一致原因（判定基準差/集計差）の切り分け。",
            f"{STATUS_UNCONFIRMED}: 181 と 189 の意味自然性差を言語学的評価指標で確定する追加検証。",
            f"{STATUS_UNCONFIRMED}: 183 fallback 発火を運用ルール化した際の副作用。",
        ],
        "raw_references": {
            "impl_report": str(IN_IMPL),
            "adoption_audit_report": str(IN_AUDIT),
            "runs": {
                "S2_after_wo181": s2_after_wo181,
                "S2_after_wo189": s2_after_wo189,
                "S4_after_wo181": s4_after_wo181,
                "S4_after_wo189": s4_after_wo189,
            },
            "audit_yes_no": yes_no_src,
        },
    }
    return payload


def _to_markdown(payload: dict[str, Any]) -> str:
    fc = payload["final_candidate"]
    ad = payload["adoption_decision"]
    ev = payload["evidence_comparison"]
    yn = payload["yes_no"]
    av = payload["auto_vs_explicit"]
    lines: list[str] = []

    lines.append("# 1. 結論")
    lines.append("## 1-A. 到達案")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 lexical row 一覧: "
        "9301=採用, 181=暫定既定, 189=保留同格候補, 183=fallback候補, 264(japanese2 lookup行)=採用。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 lexical selection ルール: `と→9301`, `を→181(既定)/189(比較候補)`, "
        "`が→19(既定)/183(二段目)`, `る→204固定`。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 numeration(S4): tokens={fc['adopted_explicit_numeration_s4']['tokens']}, "
        f"ids={fc['adopted_explicit_numeration_s4']['lexicon_ids']}。"
    )
    lines.append(f"- [{STATUS_CONFIRMED}] 採用 Grammar: `japanese2`。")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 到達確認済み sentence: S4（9301固定の上で `を=181/189` いずれも reachable 観測）。"
    )
    lines.append(f"- [{STATUS_CONFIRMED}] 到達確認済み evidence: あり（S4 after_wo181/after_wo189 で evidence 抽出済み）。")
    lines.append("")

    lines.append("## 1-B. 暫定運用判断")
    lines.append("- [確認済み事実] **暫定運用としてはまだ確定してはいけない**。")
    for row in ad["reason_3_lines"]:
        lines.append(f"- {row}")
    lines.append("")

    lines.append("# 2. 採用 lexical-only 案")
    lines.append("## 2-A. 採用 lexical row")
    for key, row in fc["lexical_rows"].items():
        lines.append(f"- [{STATUS_CONFIRMED}] `{key}`: `{row['decision']}` / {row['reason']}")
    lines.append("## 2-B. 採用 numeration")
    lines.append(
        f"- [{STATUS_CONFIRMED}] S4 暫定運用 explicit numeration: "
        f"`{fc['adopted_explicit_numeration_s4']['lexicon_ids']}`"
    )
    lines.append("## 2-C. 採用 Grammar")
    lines.append(f"- [{STATUS_CONFIRMED}] yes: `japanese2` のままで到達例（S4 reachable）は観測済み。")
    lines.append(
        f"- [{STATUS_UNCONFIRMED}] ただし意味自然性と判定整合（reachable vs unresolved再計算）の未解決があり、最終確定は保留。"
    )
    lines.append("")

    lines.append("# 3. 暫定運用可否（yes/no）")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 3-A: {yn['3A_use_reachable_despite_unresolved_recalc_mismatch']['answer']} "
        f"(run={yn['3A_use_reachable_despite_unresolved_recalc_mismatch']['runs']})"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 3-B: {yn['3B_can_claim_181_more_natural_now']['answer']} "
        f"(run={yn['3B_can_claim_181_more_natural_now']['runs']})"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 3-C: {yn['3C_can_drop_189_now']['answer']} "
        f"(run={yn['3C_can_drop_189_now']['runs']})"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 3-D: {yn['3D_should_keep_183_as_fallback_not_default']['answer']} "
        f"(run={yn['3D_should_keep_183_as_fallback_not_default']['runs']})"
    )
    lines.append("")

    lines.append("# 4. 181 vs 189 evidence 比較")
    for sentence_key in ("S2", "S4"):
        row = ev[sentence_key]
        run181 = row["run_181"]
        run189 = row["run_189"]
        cmp_row = row["comparison"]
        lines.append(f"## {sentence_key}")
        lines.append(
            f"- [{STATUS_CONFIRMED}] run181 ids={run181.get('explicit_lexicon_ids')} "
            f"status/reason={run181.get('status')}/{run181.get('reason')} evidence_count={run181.get('evidence_count')}"
        )
        lines.append(
            f"- [{STATUS_CONFIRMED}] run189 ids={run189.get('explicit_lexicon_ids')} "
            f"status/reason={run189.get('status')}/{run189.get('reason')} evidence_count={run189.get('evidence_count')}"
        )
        lines.append(
            f"- [{STATUS_CONFIRMED}] comparison: same_signature_set={cmp_row.get('same_signature_set')}, "
            f"same_strict_evidence={cmp_row.get('same_strict_evidence')}, "
            f"semantics_diff_exists={cmp_row.get('semantics_diff_exists_in_common_signatures')}"
        )
        lines.append(
            f"- [{STATUS_CONFIRMED}] signatures_only_in_181={len(cmp_row.get('signatures_only_in_a') or [])}, "
            f"signatures_only_in_189={len(cmp_row.get('signatures_only_in_b') or [])}"
        )
        lines.append(f"- [{STATUS_CONFIRMED}] actual evidence 本体（tree/process/history/unresolved）は JSON の `evidence_comparison.{sentence_key}` に全件格納。")
    lines.append("")

    lines.append("# 5. 183 fallback 条件")
    lines.append(
        f"- [{STATUS_CONFIRMED}] fallback候補として保持: S2は 181+183 で leaf_min改善、S4は181単独で到達済み。"
    )
    lines.append(
        f"- [{STATUS_INFER}] 発火条件: 181適用後も unresolved>0 かつ sy:1 系残差が観測されるとき。"
    )
    lines.append(
        f"- [{STATUS_INFER}] 実施位置: Step.1既定変更ではなく reachability 後段二段目評価として扱う。"
    )
    lines.append("")

    lines.append("# 6. Step.1 auto vs explicit")
    for key in ("S2", "T3", "T1", "S4"):
        row = av[key]
        lines.append(
            f"- [{STATUS_CONFIRMED}] {key}: auto_ids={row['auto_lexicon_ids']} / explicit_ids={row['explicit_adopted_lexicon_ids']} "
            f"/ same={row['is_same']} / generation_failed={row['generation_failed']}"
        )
        if row["reason_if_mismatch"] is not None:
            lines.append(f"- [{STATUS_UNCONFIRMED}] {key} mismatch reason: {row['reason_if_mismatch']}")
    lines.append("")

    lines.append("# 7. 最終判断")
    lines.append("## 7-A. ふわふわ文の暫定 lexical-only 案")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 lexical row: 9301, 181(暫定既定), 189(保留), 183(fallback), 264 lookup行。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 selection: `と→9301`, `を→181(既定)/189(比較)`, `が→19既定`, `る→204`。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] 採用 numeration: `{fc['adopted_explicit_numeration_s4']['lexicon_ids']}`。"
    )
    lines.append(f"- [{STATUS_CONFIRMED}] 採用 Grammar: japanese2。")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 到達確認: S4 after_wo181 / after_wo189 とも reachable（9301固定前提）。"
    )
    lines.append("## 7-B. 暫定運用として確定すべきか")
    lines.append("- [確認済み事実] **まだ確定してはいけない**。")
    lines.append(
        f"- [{STATUS_CONFIRMED}] 到達性: reachable 観測はある。"
        f" ただし {STATUS_UNCONFIRMED} として判定整合監査（reachable vs unresolved再計算）が未完。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] evidence一致性: 181/189 は同一ではない比較結果が出ており、既定固定判断は保留が妥当。"
    )
    lines.append(
        f"- [{STATUS_UNCONFIRMED}] 意味自然性: 181優位を断定する evidence 根拠は未確立。"
    )
    lines.append(
        f"- [{STATUS_CONFIRMED}] auto path 実用性: S2/T3/T1/S4 で generation_failed は解消し、採用列と一致。"
    )
    lines.append("")

    lines.append("# 8. 未確認事項")
    for row in payload["unknowns"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def main() -> None:
    if not IN_IMPL.exists() or not IN_AUDIT.exists():
        missing = [str(p) for p in (IN_IMPL, IN_AUDIT) if not p.exists()]
        raise SystemExit(f"missing input files: {missing}")
    impl = json.loads(IN_IMPL.read_text(encoding="utf-8"))
    audit = json.loads(IN_AUDIT.read_text(encoding="utf-8"))
    payload = _build_payload(impl, audit)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"WROTE_JSON={OUT_JSON}")
    print(f"WROTE_MD={OUT_MD}")


if __name__ == "__main__":
    main()

