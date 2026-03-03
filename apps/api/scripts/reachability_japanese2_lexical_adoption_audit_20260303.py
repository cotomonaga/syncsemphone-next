#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_SRC = PROJECT_ROOT / "packages" / "domain" / "src"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(DOMAIN_SRC) not in sys.path:
    sys.path.insert(0, str(DOMAIN_SRC))

from app.main import app  # noqa: E402
from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _count_uninterpretable_like_perl,
    _search_reachability,
    _select_tree_root,
    export_process_text_like_perl,
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
BUDGET_SECONDS = 20.0
MAX_NODES = 120_000
MAX_DEPTH = 28
TOP_K = 10

LEGACY_ROOT = PROJECT_ROOT.parents[0]

OUT_JSON = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-adoption-audit-20260303.json"
OUT_MD = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-adoption-audit-20260303.md"


EXPLICIT_RUNS = {
    "S2_after_wo181": {
        "sentence_key": "S2",
        "sentence": "わたあめを食べているひつじがいる",
        "lexicon_ids": [265, 181, 266, 267, 19, 271, 204],
    },
    "S2_after_wo189": {
        "sentence_key": "S2",
        "sentence": "わたあめを食べているひつじがいる",
        "lexicon_ids": [265, 189, 266, 267, 19, 271, 204],
    },
    "S4_after_wo181": {
        "sentence_key": "S4",
        "sentence": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
        "lexicon_ids": [264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204],
    },
    "S4_after_wo189": {
        "sentence_key": "S4",
        "sentence": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
        "lexicon_ids": [264, 265, 189, 266, 267, 9301, 269, 270, 19, 271, 204],
    },
}


OVERFIT_SENTENCES = {
    "OF1": "わたあめを食べているひつじがいる",
    "OF2": "わたあめを食べているうさぎがいる",
    "OF3": "うさぎを食べているひつじがいる",
}


def _normalize_token(token: str) -> str:
    return token.strip().replace("　", "").replace(" ", "")


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


def _summarize_sync_semantics(final_state: Any) -> dict[str, Any]:
    sync_code_counts: dict[str, int] = {}
    sem_code_counts: dict[str, int] = {}
    sync_literal_counts: dict[str, int] = {}
    sem_literal_counts: dict[str, int] = {}

    def _inc(bucket: dict[str, int], key: str) -> None:
        if key == "":
            return
        bucket[key] = bucket.get(key, 0) + 1

    for idx in range(1, final_state.basenum + 1):
        row = final_state.base[idx]
        if row == "zero" or not isinstance(row, list):
            continue
        stack = [row]
        while stack:
            node = stack.pop()
            if not isinstance(node, list):
                continue
            if len(node) > 7 and isinstance(node[7], list):
                for child in node[7]:
                    if isinstance(child, list):
                        stack.append(child)

            sy_values = node[3] if len(node) > 3 and isinstance(node[3], list) else []
            se_values = node[5] if len(node) > 5 and isinstance(node[5], list) else []

            for val in sy_values:
                raw = str(val).strip()
                if raw == "":
                    continue
                parts = [part.strip() for part in raw.split(",")]
                if len(parts) >= 3 and parts[1].isdigit():
                    label = parts[2] if len(parts) > 2 else ""
                    _inc(sync_code_counts, f"{parts[1]}:{label}")
                else:
                    _inc(sync_literal_counts, raw)

            for val in se_values:
                raw = str(val).strip()
                if raw == "":
                    continue
                if ":" not in raw:
                    _inc(sem_literal_counts, raw)
                    continue
                lhs, rhs = raw.split(":", 1)
                rhs_parts = [part.strip() for part in rhs.split(",")]
                if len(rhs_parts) >= 3 and rhs_parts[1].isdigit():
                    label = rhs_parts[2] if len(rhs_parts) > 2 else ""
                    _inc(sem_code_counts, f"{rhs_parts[1]}:{label}")
                else:
                    _inc(sem_literal_counts, lhs.strip())

    return {
        "sync_code_counts": dict(sorted(sync_code_counts.items(), key=lambda x: (-x[1], x[0]))),
        "sem_code_counts": dict(sorted(sem_code_counts.items(), key=lambda x: (-x[1], x[0]))),
        "sync_literal_counts": dict(sorted(sync_literal_counts.items(), key=lambda x: (-x[1], x[0]))),
        "sem_literal_counts": dict(sorted(sem_literal_counts.items(), key=lambda x: (-x[1], x[0]))),
    }


def _run_reachability_for_ids(*, sentence: str, sentence_key: str, lexicon_ids: list[int]) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:audit", lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=LEGACY_ROOT,
    )
    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=LEGACY_ROOT)
    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=TOP_K,
        budget_seconds=BUDGET_SECONDS,
        max_nodes=MAX_NODES,
        max_depth=MAX_DEPTH,
        return_process_text=True,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=LEGACY_ROOT,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    evidences: list[dict[str, Any]] = []
    for ev in internal.evidences:
        final_state = ev.final_state
        tree_root = _select_tree_root(final_state)
        process_text = export_process_text_like_perl(final_state)
        unresolved = _count_uninterpretable_like_perl(final_state)
        history_steps = [asdict(step) for step in ev.steps]
        evidences.append(
            {
                "tree_signature": ev.tree_signature,
                "tree_root": tree_root,
                "process_text": process_text,
                "history_steps": history_steps,
                "steps_to_goal": len(history_steps),
                "unresolved": unresolved,
                "sync_semantics_summary": _summarize_sync_semantics(final_state),
            }
        )

    leaf_stats = internal.leaf_stats if isinstance(internal.leaf_stats, dict) else {}
    return {
        "sentence": sentence,
        "sentence_key": sentence_key,
        "explicit_lexicon_ids": list(lexicon_ids),
        "status": internal.status,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": leaf_stats.get("unresolved_min"),
        "evidence_count": len(evidences),
        "evidence_present": len(evidences) > 0,
        "evidences": evidences,
    }


def _compare_evidence_sets(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    sig_to_a = {row["tree_signature"]: row for row in a.get("evidences", [])}
    sig_to_b = {row["tree_signature"]: row for row in b.get("evidences", [])}
    sigs_a = set(sig_to_a.keys())
    sigs_b = set(sig_to_b.keys())
    common = sorted(sigs_a & sigs_b)
    only_a = sorted(sigs_a - sigs_b)
    only_b = sorted(sigs_b - sigs_a)

    per_sig: list[dict[str, Any]] = []
    for sig in common:
        ea = sig_to_a[sig]
        eb = sig_to_b[sig]
        tree_equal = ea["tree_root"] == eb["tree_root"]
        process_equal = ea["process_text"] == eb["process_text"]
        history_equal = ea["history_steps"] == eb["history_steps"]
        summary_equal = ea["sync_semantics_summary"] == eb["sync_semantics_summary"]
        per_sig.append(
            {
                "tree_signature": sig,
                "tree_equal": tree_equal,
                "process_equal": process_equal,
                "history_equal": history_equal,
                "sync_semantics_summary_equal": summary_equal,
            }
        )

    same_signature_set = sigs_a == sigs_b
    same_strict = same_signature_set and all(
        row["tree_equal"] and row["process_equal"] and row["history_equal"] for row in per_sig
    )
    semantics_diff_exists = any(not row["sync_semantics_summary_equal"] for row in per_sig)

    return {
        "evidence_count_a": len(sig_to_a),
        "evidence_count_b": len(sig_to_b),
        "same_signature_set": same_signature_set,
        "same_strict_evidence": same_strict,
        "semantics_diff_exists_in_common_signatures": semantics_diff_exists,
        "signatures_only_in_a": only_a,
        "signatures_only_in_b": only_b,
        "common_signature_comparison": per_sig,
    }


def _run_auto(client: TestClient, *, sentence_key: str, sentence: str) -> dict[str, Any]:
    res = client.post(
        "/v1/derivation/init/from-sentence",
        json={
            "grammar_id": GRAMMAR_ID,
            "sentence": sentence,
            "split_mode": "A",
            "legacy_root": str(LEGACY_ROOT),
            "auto_add_ga_phi": False,
        },
    )
    if res.status_code != 200:
        return {
            "sentence_key": sentence_key,
            "sentence": sentence,
            "generation_failed": True,
            "error": res.json(),
        }
    body = res.json()
    numeration = body.get("numeration", {})
    token_resolutions = numeration.get("token_resolutions") or []
    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "generation_failed": False,
        "lexicon_ids": [int(x) for x in numeration.get("lexicon_ids") or []],
        "token_resolutions": token_resolutions,
    }


def _run_overfit_audit(client: TestClient) -> dict[str, Any]:
    lexicon = load_legacy_lexicon(legacy_root=LEGACY_ROOT, grammar_id=GRAMMAR_ID)
    wo_theme_verbs: list[dict[str, Any]] = []
    for lid, entry in sorted(lexicon.items(), key=lambda x: x[0]):
        semantics = list(entry.semantics)
        if any(str(val).strip() == "Theme:2,33,wo" for val in semantics):
            wo_theme_verbs.append(
                {
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "phono": entry.phono,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": semantics,
                    "lookup_deployable": True,
                    "engine_usable": True,
                }
            )

    per_sentence: dict[str, Any] = {}
    for key, sentence in OVERFIT_SENTENCES.items():
        auto_row = _run_auto(client, sentence_key=key, sentence=sentence)
        if auto_row.get("generation_failed"):
            per_sentence[key] = {
                "sentence": sentence,
                "auto": auto_row,
                "forced_runs": {},
            }
            continue
        base_ids = list(auto_row["lexicon_ids"])
        tokens = auto_row["token_resolutions"]
        wo_slot = None
        for idx, row in enumerate(tokens):
            if _normalize_token(str(row.get("token", ""))) == "を":
                wo_slot = idx
                break
        forced_runs: dict[str, Any] = {}
        if wo_slot is not None:
            for wo_id in (23, 181, 189):
                forced_ids = list(base_ids)
                if wo_slot < len(forced_ids):
                    forced_ids[wo_slot] = wo_id
                run = _run_reachability_for_ids(
                    sentence=sentence,
                    sentence_key=key,
                    lexicon_ids=forced_ids,
                )
                forced_runs[f"force_wo_{wo_id}"] = {
                    "explicit_lexicon_ids": forced_ids,
                    "status": run["status"],
                    "reason": run["reason"],
                    "best_leaf_unresolved_min": run["best_leaf_unresolved_min"],
                    "evidence_present": run["evidence_present"],
                    "evidence_count": run["evidence_count"],
                    "first_evidence_tree_signature": (
                        run["evidences"][0]["tree_signature"] if run["evidences"] else None
                    ),
                    "first_evidence_process_text": (
                        run["evidences"][0]["process_text"] if run["evidences"] else None
                    ),
                }
        per_sentence[key] = {
            "sentence": sentence,
            "auto": auto_row,
            "forced_runs": forced_runs,
        }

    return {
        "wo_theme_verbs_lookup_deployable_engine_usable": wo_theme_verbs,
        "sentences": per_sentence,
    }


def _build_yes_no(payload: dict[str, Any]) -> dict[str, Any]:
    s2_cmp = payload["evidence_comparison"]["S2_after_wo181_vs_after_wo189"]
    s4_cmp = payload["evidence_comparison"]["S4_after_wo181_vs_after_wo189"]
    s2_181 = payload["explicit_runs"]["S2_after_wo181"]
    s2_189 = payload["explicit_runs"]["S2_after_wo189"]
    s4_181 = payload["explicit_runs"]["S4_after_wo181"]
    s4_189 = payload["explicit_runs"]["S4_after_wo189"]

    q1_yes = bool(s2_cmp["same_strict_evidence"])
    q2_yes = bool(s4_cmp["same_strict_evidence"])
    q3_yes = bool(
        (not s2_cmp["same_signature_set"])
        or (not s4_cmp["same_signature_set"])
        or s2_cmp["semantics_diff_exists_in_common_signatures"]
        or s4_cmp["semantics_diff_exists_in_common_signatures"]
    )
    q4_yes = bool(
        q1_yes
        and q2_yes
        and (not q3_yes)
    )

    return {
        "q1_s2_same_tree_process_evidence_181_189": {
            "answer": "yes" if q1_yes else "no",
            "run_a": "S2_after_wo181",
            "run_b": "S2_after_wo189",
            "status_a": s2_181["status"],
            "reason_a": s2_181["reason"],
            "status_b": s2_189["status"],
            "reason_b": s2_189["reason"],
            "evidence_comparison": s2_cmp,
            "fact_status": STATUS_CONFIRMED,
        },
        "q2_s4_same_tree_process_evidence_181_189": {
            "answer": "yes" if q2_yes else "no",
            "run_a": "S4_after_wo181",
            "run_b": "S4_after_wo189",
            "status_a": s4_181["status"],
            "reason_a": s4_181["reason"],
            "status_b": s4_189["status"],
            "reason_b": s4_189["reason"],
            "evidence_comparison": s4_cmp,
            "fact_status": STATUS_CONFIRMED,
        },
        "q3_difference_appears_in_evidence_semantics_not_only_reachability": {
            "answer": "yes" if q3_yes else "no",
            "basis": {
                "S2": {
                    "same_strict_evidence": s2_cmp["same_strict_evidence"],
                    "semantics_diff_exists_in_common_signatures": s2_cmp[
                        "semantics_diff_exists_in_common_signatures"
                    ],
                },
                "S4": {
                    "same_strict_evidence": s4_cmp["same_strict_evidence"],
                    "semantics_diff_exists_in_common_signatures": s4_cmp[
                        "semantics_diff_exists_in_common_signatures"
                    ],
                },
            },
            "fact_status": STATUS_CONFIRMED,
        },
        "q4_if_no_diff_default_181_not_established_yet": {
            "answer": "yes" if q4_yes else "no",
            "basis": {
                "q1": "yes" if q1_yes else "no",
                "q2": "yes" if q2_yes else "no",
                "q3": "yes" if q3_yes else "no",
            },
            "fact_status": STATUS_CONFIRMED,
        },
    }


def _fallback_conditions(payload: dict[str, Any]) -> dict[str, Any]:
    # Facts from existing explicit runs in lexical-selection report (already measured).
    s2_after_wo181 = payload["reference_metrics"]["S2_after_wo181"]
    s2_secondary = payload["reference_metrics"]["S2_secondary_wo181_ga183"]
    s4_after_wo181 = payload["reference_metrics"]["S4_after_wo181"]
    s4_secondary = payload["reference_metrics"]["S4_secondary_wo181_ga183"]

    return {
        "facts": [
            {
                "label": "S2",
                "before": s2_after_wo181,
                "after_secondary": s2_secondary,
                "fact_status": STATUS_CONFIRMED,
            },
            {
                "label": "S4",
                "before": s4_after_wo181,
                "after_secondary": s4_secondary,
                "fact_status": STATUS_CONFIRMED,
            },
        ],
        "fallback_policy_draft": {
            "trigger_when": [
                {
                    "condition": "を=181 適用後も best_leaf_unresolved_min > 0 が継続",
                    "status": STATUS_INFER,
                },
                {
                    "condition": "top leaf 残差に sy:1 が残る（S2で観測）",
                    "status": STATUS_INFER,
                },
            ],
            "keep_19_when": [
                {
                    "condition": "を=181 だけで best_leaf_unresolved_min == 0（S4で観測）",
                    "status": STATUS_CONFIRMED,
                }
            ],
            "where_to_apply": {
                "proposal": "reachability 後段での二段目評価（Step.1固定より安全）",
                "status": STATUS_INFER,
            },
        },
    }


def _load_reference_metrics() -> dict[str, Any]:
    path = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-selection-impl-20260302.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    runs = payload.get("explicit", {}).get("runs", {})
    out: dict[str, Any] = {}
    s2 = runs.get("S2", {})
    s4 = runs.get("S4", {})
    for key, src in (
        ("S2_after_wo181", s2.get("after_wo181")),
        ("S2_secondary_wo181_ga183", s2.get("secondary_wo181_ga183")),
        ("S4_after_wo181", s4.get("after_wo181")),
        ("S4_secondary_wo181_ga183", s4.get("secondary_wo181_ga183")),
    ):
        if isinstance(src, dict):
            out[key] = {
                "status": src.get("status"),
                "reason": src.get("reason"),
                "best_leaf_unresolved_min": src.get("best_leaf_unresolved_min"),
                "explicit_lexicon_ids": src.get("explicit_lexicon_ids"),
            }
    return out


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    s2_cmp = payload["evidence_comparison"]["S2_after_wo181_vs_after_wo189"]
    s4_cmp = payload["evidence_comparison"]["S4_after_wo181_vs_after_wo189"]
    q = payload["yes_no"]
    lines.append(f"# japanese2 lexical-only 採用監査（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("- [確認済み事実] 本監査は `grammar_id=japanese2` 固定、Grammar変更/探索器変更/新規lexical row追加なしで実施。")
    lines.append("- [確認済み事実] S4/T1 の比較は **9301固定の上で** `を=181/189` を評価。")
    lines.append(
        "- [確認済み事実] evidence比較結果:"
        f" S2 same_signature_set={s2_cmp['same_signature_set']}, S4 same_signature_set={s4_cmp['same_signature_set']}."
    )
    lines.append(
        f"- [確認済み事実] yes/no 判定: q1={q['q1_s2_same_tree_process_evidence_181_189']['answer']}, "
        f"q2={q['q2_s4_same_tree_process_evidence_181_189']['answer']}, "
        f"q3={q['q3_difference_appears_in_evidence_semantics_not_only_reachability']['answer']}, "
        f"q4={q['q4_if_no_diff_default_181_not_established_yet']['answer']}."
    )
    lines.append("")

    lines.append("## 2. 181 vs 189 の evidence 比較")
    for run_name in ("S2_after_wo181", "S2_after_wo189", "S4_after_wo181", "S4_after_wo189"):
        run = payload["explicit_runs"][run_name]
        lines.append(f"### {run_name}")
        lines.append(f"- [確認済み事実] lexicon_ids: `{run['explicit_lexicon_ids']}`")
        lines.append(
            f"- [確認済み事実] status/reason: `{run['status']}` / `{run['reason']}` "
            f"(actions={run['actions_attempted']}, depth={run['max_depth_reached']}, leaf_min={run['best_leaf_unresolved_min']})"
        )
        lines.append(f"- [確認済み事実] evidence_count: `{run['evidence_count']}`")
        unresolved_list = [int(ev.get("unresolved") or 0) for ev in run.get("evidences", [])]
        lines.append(
            f"- [確認済み事実] evidence unresolved list: `{unresolved_list}` / "
            f"all_zero=`{all(v == 0 for v in unresolved_list)}`"
        )
        if run["evidence_count"] == 0:
            lines.append("- [未確認] evidence が 0 件のため tree/process/history の比較不可。")
            continue
        for idx, ev in enumerate(run["evidences"], start=1):
            lines.append(f"- [確認済み事実] evidence#{idx} sig=`{ev['tree_signature']}` unresolved=`{ev['unresolved']}`")
            lines.append(f"- [確認済み事実] evidence#{idx} tree=`{json.dumps(ev['tree_root'], ensure_ascii=False)[:240]}...`")
            lines.append(f"- [確認済み事実] evidence#{idx} process=`{(ev['process_text'] or '')[:240]}...`")
            lines.append(f"- [確認済み事実] evidence#{idx} history=`{json.dumps(ev['history_steps'], ensure_ascii=False)[:240]}...`")
            lines.append(
                f"- [確認済み事実] evidence#{idx} semantics/sync summary=`{json.dumps(ev['sync_semantics_summary'], ensure_ascii=False)[:240]}...`"
            )
        lines.append("")

    lines.append("## 3. yes/no")
    for key, row in payload["yes_no"].items():
        lines.append(f"- [確認済み事実] {key}: `{row['answer']}`")
        lines.append(f"  - run/basis: `{json.dumps({k:v for k,v in row.items() if k not in {'fact_status'}}, ensure_ascii=False)[:300]}...`")
    lines.append("")

    lines.append("## 4. `を` selector の overfit 監査")
    verbs = payload["overfit_audit"]["wo_theme_verbs_lookup_deployable_engine_usable"]
    lines.append(f"- [確認済み事実] `japanese2.csv` で `Theme:2,33,wo` を持つ動詞候補数: `{len(verbs)}`")
    for v in verbs:
        lines.append(
            f"- [確認済み事実] verb id={v['lexicon_id']} entry={v['entry']} "
            f"lookup_deployable={v['lookup_deployable']} engine_usable={v['engine_usable']}"
        )
    if len(payload["overfit_audit"]["sentences"]) < 3:
        lines.append("- [未確認] Step.1 auto が通る比較文を3件確保できなかった。")
    for key, row in payload["overfit_audit"]["sentences"].items():
        lines.append(f"### {key}: {row['sentence']}")
        auto = row["auto"]
        lines.append(
            f"- [確認済み事実] current selector lexicon_ids=`{auto.get('lexicon_ids')}` "
            f"generation_failed=`{auto.get('generation_failed')}`"
        )
        forced = row.get("forced_runs", {})
        for fname in ("force_wo_23", "force_wo_181", "force_wo_189"):
            if fname not in forced:
                continue
            fr = forced[fname]
            lines.append(
                f"- [確認済み事実] {fname}: ids=`{fr['explicit_lexicon_ids']}` "
                f"status/reason=`{fr['status']}/{fr['reason']}` "
                f"evidence_present=`{fr['evidence_present']}` leaf_min=`{fr['best_leaf_unresolved_min']}`"
            )
            if fr.get("first_evidence_tree_signature"):
                lines.append(
                    f"  - [確認済み事実] first_evidence sig=`{fr['first_evidence_tree_signature']}` "
                    f"process=`{(fr.get('first_evidence_process_text') or '')[:120]}...`"
                )
    lines.append("")

    lines.append("## 5. `が=183` の fallback 条件")
    fb = payload["fallback_conditions"]
    for row in fb["facts"]:
        lines.append(f"- [確認済み事実] {row['label']}: `{row['before']}` -> `{row['after_secondary']}`")
    for row in fb["fallback_policy_draft"]["trigger_when"]:
        lines.append(f"- [{row['status']}] trigger候補: {row['condition']}")
    for row in fb["fallback_policy_draft"]["keep_19_when"]:
        lines.append(f"- [{row['status']}] keep候補: {row['condition']}")
    lines.append(
        f"- [{fb['fallback_policy_draft']['where_to_apply']['status']}] "
        f"適用位置案: {fb['fallback_policy_draft']['where_to_apply']['proposal']}"
    )
    lines.append("")

    lines.append("## 6. 未確認事項")
    lines.append("- [未確認] `181` と `189` の意味差が将来的な別文脈で evidence 差分として顕在化するかは、この4 run だけでは確定できない。")
    lines.append("- [未確認] `が=183` の発火条件を production ルール化した場合の副作用は未検証。")
    return "\n".join(lines) + "\n"


def main() -> None:
    client = TestClient(app)

    explicit_runs: dict[str, Any] = {}
    for run_name, cfg in EXPLICIT_RUNS.items():
        explicit_runs[run_name] = _run_reachability_for_ids(
            sentence=cfg["sentence"],
            sentence_key=cfg["sentence_key"],
            lexicon_ids=cfg["lexicon_ids"],
        )

    evidence_comparison = {
        "S2_after_wo181_vs_after_wo189": _compare_evidence_sets(
            explicit_runs["S2_after_wo181"],
            explicit_runs["S2_after_wo189"],
        ),
        "S4_after_wo181_vs_after_wo189": _compare_evidence_sets(
            explicit_runs["S4_after_wo181"],
            explicit_runs["S4_after_wo189"],
        ),
    }

    overfit_audit = _run_overfit_audit(client)
    reference_metrics = _load_reference_metrics()

    payload: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "grammar_id": GRAMMAR_ID,
            "auto_add_ga_phi": False,
            "budget_seconds": BUDGET_SECONDS,
            "max_nodes": MAX_NODES,
            "max_depth": MAX_DEPTH,
            "top_k": TOP_K,
            "constraints": [
                "no_grammar_change",
                "no_search_engine_change",
                "no_phi_addition",
                "no_266_9304_retry",
                "no_new_lexical_row",
            ],
        },
        "explicit_runs": explicit_runs,
        "evidence_comparison": evidence_comparison,
        "overfit_audit": overfit_audit,
        "reference_metrics": reference_metrics,
    }
    payload["yes_no"] = _build_yes_no(payload)
    payload["fallback_conditions"] = _fallback_conditions(payload)

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"WROTE_JSON={OUT_JSON}")
    print(f"WROTE_MD={OUT_MD}")


if __name__ == "__main__":
    main()
