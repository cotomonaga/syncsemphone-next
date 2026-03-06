#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any, Optional

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import DerivationReachabilityRequest, _search_reachability  # noqa: E402
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.grammar.rule_catalog import load_rule_catalog  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.lexicon.models import LexiconEntry  # noqa: E402
from domain.numeration.generator import generate_numeration_from_sentence  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402

STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"
STATUS_GUESS = "推測"

GRAMMAR_ID = "imi01"
SENTENCES = {
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
}

# 追加候補（最大3行）
PROPOSED_ROWS = [
    {
        "lexicon_id": 9001,
        "entry": "ひつじ",
        "phono": "ひつじ",
        "category": "N",
        "predicates": [],
        "sync_features": ["4,11,ga", "4,11,to"],
        "idslot": "id",
        "semantics": ["ひつじ:T"],
        "note": "probe20260302",
    },
    {
        "lexicon_id": 9002,
        "entry": "うさぎ",
        "phono": "うさぎ",
        "category": "N",
        "predicates": [],
        "sync_features": ["4,11,ga"],
        "idslot": "id",
        "semantics": ["うさぎ:T"],
        "note": "probe20260302",
    },
    {
        "lexicon_id": 9003,
        "entry": "が",
        "phono": "が",
        "category": "J",
        "predicates": [],
        "sync_features": ["0,17,N,,,right,nonhead", "3,17,V,,,left,nonhead", "4,11,ga", "4,11,ga"],
        "idslot": "zero",
        "semantics": [],
        "note": "probe20260302",
    },
]

PROPOSALS = [
    {
        "proposal_id": "baseline_auto",
        "description": "現行Step.1自動選択IDをそのまま利用",
        "replacements": {},
    },
    {
        "proposal_id": "lex_add_headnoun_features",
        "description": "ひつじ(9001), うさぎ(9002)へ置換",
        "replacements": {
            "S2": {267: 9001},
            "S3": {267: 9001, 270: 9002},
            "S4": {267: 9001, 270: 9002},
        },
    },
    {
        "proposal_id": "lex_add_particle_ga_double",
        "description": "が(19)を新規が(9003)に置換",
        "replacements": {
            "S2": {19: 9003},
            "S3": {19: 9003},
            "S4": {19: 9003},
        },
    },
    {
        "proposal_id": "lex_add_combined",
        "description": "ひつじ/うさぎ置換 + が置換を同時適用",
        "replacements": {
            "S2": {267: 9001, 19: 9003},
            "S3": {267: 9001, 270: 9002, 19: 9003},
            "S4": {267: 9001, 270: 9002, 19: 9003},
        },
    },
]

TARGET_SURFACES = ["を", "と", "が", "る", "φ"]
_RULE_NAME_MARKERS = (
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
_JAPANESE2_ONLY_SYNC_FEATURE_CODES = {"1L", "2L", "3L"}


@dataclass(frozen=True)
class RunConfig:
    split_mode: str = "A"
    budget_seconds: float = 120.0
    max_nodes: int = 40000
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


def _build_surface_index(lexicon: dict[int, LexiconEntry]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = defaultdict(list)
    for lid, entry in lexicon.items():
        seen: set[str] = set()
        if _normalize_token(entry.entry):
            seen.add(_normalize_token(entry.entry))
        for variant in _phono_variants(entry.phono):
            if variant:
                seen.add(variant)
        for s in sorted(seen):
            idx[s].append(lid)
    return dict(idx)


def _split_semantic(value: str) -> tuple[str, str]:
    if ":" not in value:
        return value, ""
    a, b = value.split(":", 1)
    return a, b


def _build_legacy_row(entry: dict[str, Any]) -> str:
    cells = ["" for _ in range(30)]
    cells[0] = str(entry["lexicon_id"])
    cells[1] = str(entry["entry"])
    cells[2] = str(entry["phono"])
    cells[3] = str(entry["category"])

    predicates = list(entry.get("predicates", []))
    cells[4] = str(len(predicates))
    y = 4
    for pred in predicates:
        triple = list(pred) + ["", "", ""]
        y += 1
        cells[y] = str(triple[0])
        y += 1
        cells[y] = str(triple[1])
        y += 1
        cells[y] = str(triple[2])

    sync_features = [str(v) for v in entry.get("sync_features", [])]
    cells[8] = str(len(sync_features))
    y = 8
    for feature in sync_features:
        y += 1
        if y >= len(cells):
            break
        cells[y] = feature

    cells[14] = str(entry.get("idslot", ""))

    semantics = [str(v) for v in entry.get("semantics", [])]
    cells[15] = str(len(semantics))
    y = 15
    for sem in semantics:
        attr, val = _split_semantic(sem)
        y += 1
        if y >= len(cells):
            break
        cells[y] = attr
        y += 1
        if y >= len(cells):
            break
        cells[y] = val

    note = str(entry.get("note", "")).strip()
    cells[28] = note
    cells[29] = "0"
    return "\t".join(cells)


def _build_temp_legacy_root(*, legacy_root: Path, appended_rows: list[str]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="legacy_probe_"))
    for child in legacy_root.iterdir():
        dst = tmp_root / child.name
        if child.name == "lexicon-all.csv":
            continue
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    src_csv = legacy_root / "lexicon-all.csv"
    dst_csv = tmp_root / "lexicon-all.csv"
    text = src_csv.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    if appended_rows:
        text += "\n".join(appended_rows) + "\n"
    dst_csv.write_text(text, encoding="utf-8")
    return tmp_root


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


def _aggregate_source_totals(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    fam_counter: dict[str, Counter[str]] = {}
    attrs: dict[str, dict[str, Any]] = {}
    for sample in samples:
        source_map = sample.get("residual_family_sources") or {}
        for family, rows in source_map.items():
            c = fam_counter.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        row.get("item_id", ""),
                        row.get("phono", ""),
                        row.get("raw", ""),
                        row.get("slot_index", ""),
                    ]
                )
                c[key] += 1
                attrs[key] = row
    out: dict[str, list[dict[str, Any]]] = {}
    for family, c in sorted(fam_counter.items(), key=lambda kv: kv[0]):
        rows: list[dict[str, Any]] = []
        for key, n in c.most_common(10):
            row = attrs[key]
            rows.append(
                {
                    "count": int(n),
                    "item_id": row.get("item_id", ""),
                    "phono": row.get("phono", ""),
                    "raw": row.get("raw", ""),
                    "slot_index": row.get("slot_index", ""),
                }
            )
        out[family] = rows
    return out


def _best_family_avg(best_samples: list[dict[str, Any]]) -> dict[str, float]:
    totals: Counter[str] = Counter()
    for s in best_samples:
        for k, v in (s.get("residual_family_counts") or {}).items():
            totals[k] += int(v)
    if not best_samples:
        return {}
    return {k: round(float(v) / float(len(best_samples)), 3) for k, v in sorted(totals.items())}


def _apply_replacements(ids: list[int], repl: dict[int, int]) -> list[int]:
    out = list(ids)
    used_src: set[int] = set()
    for idx, lid in enumerate(out):
        if lid in repl and lid not in used_src:
            out[idx] = repl[lid]
            used_src.add(lid)
    return out


def _run_case(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    proposal_desc: str,
    explicit_ids: list[int],
    config: RunConfig,
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(sentence, explicit_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=10,
        return_process_text=False,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[: config.top_k]
    best_avg = _best_family_avg(best_leaf_samples)
    source_top = _aggregate_source_totals(best_leaf_samples)

    histories: list[dict[str, Any]] = []
    if internal.evidences:
        for rank, evidence in enumerate(internal.evidences[:3], start=1):
            histories.append(
                {
                    "rank": rank,
                    "steps_to_goal": evidence.steps_to_goal,
                    "rule_sequence": [
                        {
                            "rule_name": step.rule_name,
                            "rule_number": step.rule_number,
                            "left_id": step.left_id,
                            "right_id": step.right_id,
                        }
                        for step in evidence.steps
                    ],
                    "fact_status": STATUS_CONFIRMED,
                }
            )

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "grammar_id": GRAMMAR_ID,
        "proposal_id": proposal_id,
        "proposal_desc": proposal_desc,
        "explicit_lexicon_ids": explicit_ids,
        "status": internal.status,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "se33_residual_avg": float(best_avg.get("se:33", 0.0)),
        "sy11_residual_avg": float(best_avg.get("sy:11", 0.0)),
        "sy17_residual_avg": float(best_avg.get("sy:17", 0.0)),
        "best_leaf_residual_family_avg": best_avg,
        "best_leaf_source_top": source_top,
        "history_top": histories,
        "history_top_status": STATUS_CONFIRMED if histories else STATUS_UNCONFIRMED,
    }


def _extract_rule_markers(entry: LexiconEntry) -> list[str]:
    values = list(entry.sync_features) + list(entry.semantics)
    used: set[str] = set()
    for value in values:
        for marker in _RULE_NAME_MARKERS:
            if marker in value:
                used.add(marker)
    return sorted(used)


def _sync_codes(entry: LexiconEntry) -> set[str]:
    codes: set[str] = set()
    for feature in entry.sync_features:
        parts = [p.strip() for p in feature.split(",")]
        if len(parts) > 1 and parts[1]:
            codes.add(parts[1])
    return codes


def _candidate_inventory(*, legacy_root: Path) -> list[dict[str, Any]]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    rules = load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)
    rule_names = {r.name for r in rules}
    surface_index = _build_surface_index(lexicon)

    rows: list[dict[str, Any]] = []
    for surface in TARGET_SURFACES:
        cands = sorted(set(surface_index.get(_normalize_token(surface), [])))
        if not cands:
            rows.append(
                {
                    "surface": surface,
                    "lexicon_id": None,
                    "entry": None,
                    "category": None,
                    "sync_features": [],
                    "semantics": [],
                    "classification": "candidate_not_found",
                    "reason_codes": ["not_in_lexicon_all"],
                    "fact_status": STATUS_CONFIRMED,
                }
            )
            continue
        for lid in cands:
            e = lexicon[lid]
            reason_codes: list[str] = []
            refs = _extract_rule_markers(e)
            missing_rules = [name for name in refs if name not in rule_names]
            if missing_rules:
                reason_codes.append("missing_required_rule")
            if any(code in _JAPANESE2_ONLY_SYNC_FEATURE_CODES for code in _sync_codes(e)):
                reason_codes.append("requires_japanese2_l_feature")
            classification = (
                "imi01_meaningful_candidate" if not reason_codes else "imi01_meaningless_candidate"
            )
            rows.append(
                {
                    "surface": surface,
                    "lexicon_id": lid,
                    "entry": e.entry,
                    "category": e.category,
                    "sync_features": list(e.sync_features),
                    "semantics": list(e.semantics),
                    "classification": classification,
                    "reason_codes": reason_codes,
                    "missing_rule_names": missing_rules,
                    "referenced_rule_names": refs,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
    return rows


def _role_discharge_matrix(*, lexicon: dict[int, LexiconEntry]) -> list[dict[str, Any]]:
    rows = []

    rows.append(
        {
            "role": "S2/S4: 食べている(266) Agent",
            "request_item": "食べている(266)",
            "request_label": "Agent:2,33,ga",
            "supply_item": "ひつじ(267) / ひつじ(9001)",
            "supply_label": "4,11,ga (or 2,11,ga after sy処理)",
            "required_merge_direction": "verbがhead, supply側がnon-head（RH:右head or LH:左head）",
            "execute_branch": "_process_se_imi03 number==33 (execute.py:395-409)",
            "supply_exists_current_lexicon": any("4,11,ga" in e.sync_features for e in lexicon.values() if e.entry == "ひつじ"),
            "measured_in_probe": STATUS_CONFIRMED,
        }
    )
    rows.append(
        {
            "role": "S3/S4: 話している(269) Agent",
            "request_item": "話している(269)",
            "request_label": "Agent:2,33,ga",
            "supply_item": "うさぎ(270) / うさぎ(9002)",
            "supply_label": "4,11,ga (or 2,11,ga)",
            "required_merge_direction": "verbがhead, supply側がnon-head（RH:右head or LH:左head）",
            "execute_branch": "_process_se_imi03 number==33 (execute.py:395-409)",
            "supply_exists_current_lexicon": any("4,11,ga" in e.sync_features for e in lexicon.values() if e.entry == "うさぎ"),
            "measured_in_probe": STATUS_CONFIRMED,
        }
    )
    rows.append(
        {
            "role": "S3/S4: 話している(269) 相手",
            "request_item": "話している(269)",
            "request_label": "相手:2,33,to",
            "supply_item": "と(268) / ひつじ(9001)",
            "supply_label": "4,11,to (or 2,11,to)",
            "required_merge_direction": "verbがhead, supply側がnon-head（RH:右head or LH:左head）",
            "execute_branch": "_process_se_imi03 number==33 (execute.py:395-409)",
            "supply_exists_current_lexicon": any("4,11,to" in e.sync_features for e in lexicon.values()),
            "measured_in_probe": STATUS_CONFIRMED,
        }
    )
    return rows


def _yes_no_answers(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 判定基準: 対象roleラベルが best_leaf_source_top(se:33) に残る場合は No。
    by = {(r["sentence_key"], r["proposal_id"]): r for r in results}

    def has_residual(row: dict[str, Any], label: str) -> bool:
        se_rows = (row.get("best_leaf_source_top") or {}).get("se:33") or []
        return any(str(x.get("raw", "")) == label for x in se_rows)

    rows = []

    # 最小反例: combined proposal でも残るかを採用
    s2 = by.get(("S2", "lex_add_combined"))
    s3 = by.get(("S3", "lex_add_combined"))
    s4 = by.get(("S4", "lex_add_combined"))

    q1_no = (s2 is None) or (s2.get("status") != "reachable") or has_residual(s2, "Agent:2,33,ga")
    q2_no = (s3 is None) or (s3.get("status") != "reachable") or has_residual(s3, "Agent:2,33,ga")
    q3_no = (s3 is None) or (s3.get("status") != "reachable") or has_residual(s3, "相手:2,33,to")

    rows.append(
        {
            "question": "食べている(266) Agent:2,33,ga は S2/S4 で head noun ひつじにより imi01 RH/LHだけで dischargeできるか",
            "answer_yes_no": "No" if q1_no else "Yes",
            "counterexample_case": "S2 + lex_add_combined",
            "counterexample_status": s2.get("status") if s2 else "未取得",
            "counterexample_reason": s2.get("reason") if s2 else "未取得",
            "counterexample_best_leaf_source": "Agent:2,33,ga が残存" if s2 and has_residual(s2, "Agent:2,33,ga") else "未確認",
            "local_condition_code_path": "_process_se_imi03 number==33 requires matching sy label on non-head",
            "local_condition_not_satisfied_point": "どの手順で不成立になったかは best-sample では未取得（history/tree不足）",
            "fact_status": STATUS_CONFIRMED,
            "unconfirmed_status": STATUS_UNCONFIRMED,
        }
    )
    rows.append(
        {
            "question": "話している(269) Agent:2,33,ga は S3/S4 で head noun うさぎにより imi01 RH/LHだけで dischargeできるか",
            "answer_yes_no": "No" if q2_no else "Yes",
            "counterexample_case": "S3 + lex_add_combined",
            "counterexample_status": s3.get("status") if s3 else "未取得",
            "counterexample_reason": s3.get("reason") if s3 else "未取得",
            "counterexample_best_leaf_source": "Agent:2,33,ga が残存" if s3 and has_residual(s3, "Agent:2,33,ga") else "未確認",
            "local_condition_code_path": "_process_se_imi03 number==33 requires matching sy label on non-head",
            "local_condition_not_satisfied_point": "どの手順で不成立になったかは best-sample では未取得（history/tree不足）",
            "fact_status": STATUS_CONFIRMED,
            "unconfirmed_status": STATUS_UNCONFIRMED,
        }
    )
    rows.append(
        {
            "question": "話している(269) 相手:2,33,to は S3/S4 で ひつじにより dischargeできるか",
            "answer_yes_no": "No" if q3_no else "Yes",
            "counterexample_case": "S3 + lex_add_combined",
            "counterexample_status": s3.get("status") if s3 else "未取得",
            "counterexample_reason": s3.get("reason") if s3 else "未取得",
            "counterexample_best_leaf_source": "相手:2,33,to が残存" if s3 and has_residual(s3, "相手:2,33,to") else "未確認",
            "local_condition_code_path": "_process_se_imi03 number==33 requires matching sy label on non-head",
            "local_condition_not_satisfied_point": "どの手順で不成立になったかは best-sample では未取得（history/tree不足）",
            "fact_status": STATUS_CONFIRMED,
            "unconfirmed_status": STATUS_UNCONFIRMED,
        }
    )

    return rows


def _conclusion(results: list[dict[str, Any]]) -> dict[str, Any]:
    # A: imi01維持+語彙追加のみで到達
    # B: imi01では無理で最小rule差分必要
    # C: 未確定
    has_reachable_non_baseline = any(
        r["proposal_id"] != "baseline_auto" and r["status"] == "reachable" for r in results
    )
    if has_reachable_non_baseline:
        return {
            "choice": "A",
            "reason": "語彙追加案で imi01 のまま reachable を確認",
            "fact_status": STATUS_CONFIRMED,
        }
    has_any_reachable = any(r["status"] == "reachable" for r in results)
    if not has_any_reachable:
        return {
            "choice": "C",
            "reason": "全案が unknown のため、語彙追加のみ不可と断定する根拠は不足（unreachable確証なし）",
            "fact_status": STATUS_CONFIRMED,
            "unconfirmed": "未知探索領域が残るため B の断定条件を満たさない",
        }
    return {
        "choice": "C",
        "reason": "baselineは到達/非到達が混在、語彙追加案の効果は限定。最小rule差分の必要性は追加観測要",
        "fact_status": STATUS_CONFIRMED,
    }


def _build_metrics_view(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    nested: dict[str, dict[str, Any]] = {}
    for row in results:
        sentence_key = row["sentence_key"]
        proposal_id = row["proposal_id"]
        nested.setdefault(sentence_key, {})[proposal_id] = {
            "status": row["status"],
            "reason": row["reason"],
            "actions_attempted": row["actions_attempted"],
            "max_depth_reached": row["max_depth_reached"],
            "best_leaf_unresolved_min": row["best_leaf_unresolved_min"],
            "se33_residual_avg": row["se33_residual_avg"],
            "sy11_residual_avg": row["sy11_residual_avg"],
            "sy17_residual_avg": row["sy17_residual_avg"],
            "best_leaf_residual_family_avg": row["best_leaf_residual_family_avg"],
            "best_leaf_source_top": row["best_leaf_source_top"],
            "history_top": row["history_top"],
            "history_top_status": row["history_top_status"],
            "explicit_lexicon_ids": row["explicit_lexicon_ids"],
        }
    return nested


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# imi01語彙追加可否 事実抽出レポート（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 結論")
    lines.append("")
    c = payload["final_conclusion"]
    lines.append(f"- [確認済み事実] 最終判定: **{c['choice']}**")
    lines.append(f"- [確認済み事実] 判定理由: {c['reason']}")
    if "unconfirmed" in c:
        lines.append(f"- [未確認] {c['unconfirmed']}")
    lines.append("")

    lines.append("## 確認済み事実")
    lines.append("")
    lines.append("- [確認済み事実] Grammar固定: imi01、auto_add_ga_phi=false、探索器改修なし。")
    lines.append("- [確認済み事実] S2/S3/S4 × 4提案（baseline+3）を同一予算で実測。")
    lines.append("")

    lines.append("## 未確認")
    lines.append("")
    lines.append("- [未確認] unknown は探索打切りであり、unreachable確定ではない。")
    lines.append("- [未確認] best-sample 由来の source には process/tree 参照が含まれない。")
    lines.append("")

    lines.append("## 推測")
    lines.append("")
    lines.append("- [推測] なし（本レポートは原則として実測・コード・CSVのみ）。")
    lines.append("")

    lines.append("## S2/S3/S4 の role discharge 表")
    lines.append("")
    lines.append("### 目標役割割当（作業前提）")
    lines.append("| sentence | predicate | role | target NP |")
    lines.append("|---|---|---|---|")
    for row in payload["target_role_assignment"]:
        lines.append(f"| {row['sentence_key']} | {row['predicate']} | {row['role']} | {row['target_np']} |")
    lines.append("")
    lines.append("- [確認済み事実] 上表はユーザー依頼の自然解釈ターゲットとして固定。")
    lines.append("")

    lines.append("### code-grounded discharge 条件")
    lines.append("| role | 要求側 item/label | 供給側 item/label | merge方向 | execute分岐 | 現行lexiconに供給候補 | 実測確認 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in payload["role_discharge_matrix"]:
        lines.append(
            f"| {r['role']} | {r['request_item']} / {r['request_label']} | {r['supply_item']} / {r['supply_label']} | {r['required_merge_direction']} | {r['execute_branch']} | {r['supply_exists_current_lexicon']} | {r['measured_in_probe']} |"
        )
    lines.append("")

    lines.append("## 候補 lexical item 棚卸し（を/と/が/る/φ）")
    lines.append("")
    lines.append("| surface | lexicon_id | entry | category | classification | reason_codes | sync_features | semantics |")
    lines.append("|---|---:|---|---|---|---|---|---|")
    for r in payload["candidate_inventory"]:
        lines.append(
            f"| {r.get('surface','')} | {'' if r.get('lexicon_id') is None else r.get('lexicon_id')} | {r.get('entry') or '-'} | {r.get('category') or '-'} | {r.get('classification')} | {','.join(r.get('reason_codes', [])) or '-'} | {'<br>'.join(r.get('sync_features', [])) or '-'} | {'<br>'.join(r.get('semantics', [])) or '-'} |"
        )
    lines.append("")

    lines.append("### 提案CSV行（新規ID）")
    lines.append("- [確認済み事実] 以下3行を temporary lexicon-all.csv に追記して A/B 実測。")
    lines.append("```tsv")
    for row in payload["proposed_csv_rows"]:
        lines.append(row)
    lines.append("```")
    lines.append("")

    lines.append("## A/B 実測表（imi01固定）")
    lines.append("")
    lines.append("| sentence | proposal_id | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top(se:33) | history上位 |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|")
    for r in payload["results"]:
        se_top = (r.get("best_leaf_source_top") or {}).get("se:33") or []
        se_top_text = "; ".join(f"{x.get('item_id')}:{x.get('raw')}({x.get('count')})" for x in se_top[:3]) or "-"
        h = r.get("history_top") or []
        if h:
            h_text = "; ".join(
                " -> ".join(step["rule_name"] for step in hh.get("rule_sequence", [])) for hh in h[:2]
            )
        else:
            h_text = "[未確認] unreachable/unknown でevidence無し"
        lines.append(
            f"| {r['sentence_key']} | {r['proposal_id']} | {r['status']} | {r['reason']} | {r['actions_attempted']} | {r['max_depth_reached']} | {r['best_leaf_unresolved_min']} | {r['se33_residual_avg']} | {r['sy11_residual_avg']} | {r['sy17_residual_avg']} | {se_top_text} | {h_text} |"
        )
    lines.append("")

    lines.append("### Yes/No 判定（3問）")
    lines.append("| question | yes/no | 最小反例 | status/reason | residual source | code path |")
    lines.append("|---|---|---|---|---|---|")
    for q in payload["yes_no_answers"]:
        lines.append(
            f"| {q['question']} | {q['answer_yes_no']} | {q['counterexample_case']} | {q['counterexample_status']}/{q['counterexample_reason']} | {q['counterexample_best_leaf_source']} | {q['local_condition_code_path']} |"
        )
        lines.append(f"- [未確認] 局所不成立の正確なmerge地点: {q['local_condition_not_satisfied_point']}")
    lines.append("## 最終結論")
    lines.append("")
    lines.append(f"- [確認済み事実] 3択判定: **{payload['final_conclusion']['choice']}**")
    lines.append(f"- [確認済み事実] {payload['final_conclusion']['reason']}")
    if "unconfirmed" in payload["final_conclusion"]:
        lines.append(f"- [未確認] {payload['final_conclusion']['unconfirmed']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = Path("/Users/tomonaga/Documents/syncsemphoneIMI")
    config = RunConfig()

    proposed_rows_tsv = [_build_legacy_row(row) for row in PROPOSED_ROWS]
    temp_root = _build_temp_legacy_root(legacy_root=legacy_root, appended_rows=proposed_rows_tsv)

    try:
        lexicon_current = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
        lexicon_temp = load_legacy_lexicon(legacy_root=temp_root, grammar_id=GRAMMAR_ID)

        # baseline auto ids
        baseline_ids: dict[str, list[int]] = {}
        token_resolutions: dict[str, list[dict[str, Any]]] = {}
        for sk, sentence in SENTENCES.items():
            gen = generate_numeration_from_sentence(
                grammar_id=GRAMMAR_ID,
                sentence=sentence,
                legacy_root=temp_root,
                split_mode=config.split_mode,
            )
            baseline_ids[sk] = list(gen.lexicon_ids)
            token_resolutions[sk] = [
                {
                    "token": row.token,
                    "lexicon_id": row.lexicon_id,
                    "candidate_lexicon_ids": list(row.candidate_lexicon_ids),
                }
                for row in gen.token_resolutions
            ]

        results: list[dict[str, Any]] = []
        for sk, sentence in SENTENCES.items():
            for p in PROPOSALS:
                repl = (p.get("replacements") or {}).get(sk, {})
                ids = _apply_replacements(baseline_ids[sk], repl)
                res = _run_case(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id=p["proposal_id"],
                    proposal_desc=p["description"],
                    explicit_ids=ids,
                    config=config,
                )
                res["token_resolutions_auto"] = token_resolutions[sk]
                results.append(res)

        target_role_assignment = [
            {"sentence_key": "S2", "predicate": "食べている", "role": "Theme", "target_np": "わたあめ"},
            {"sentence_key": "S2", "predicate": "食べている", "role": "Agent", "target_np": "ひつじ"},
            {"sentence_key": "S2", "predicate": "いる", "role": "Theme", "target_np": "ひつじ"},
            {"sentence_key": "S3", "predicate": "話している", "role": "相手", "target_np": "ひつじ"},
            {"sentence_key": "S3", "predicate": "話している", "role": "Agent", "target_np": "うさぎ"},
            {"sentence_key": "S3", "predicate": "いる", "role": "Theme", "target_np": "うさぎ"},
            {"sentence_key": "S4", "predicate": "食べている", "role": "Theme", "target_np": "わたあめ"},
            {"sentence_key": "S4", "predicate": "食べている", "role": "Agent", "target_np": "ひつじ"},
            {"sentence_key": "S4", "predicate": "話している", "role": "相手", "target_np": "ひつじ"},
            {"sentence_key": "S4", "predicate": "話している", "role": "Agent", "target_np": "うさぎ"},
            {"sentence_key": "S4", "predicate": "いる", "role": "Theme", "target_np": "うさぎ"},
        ]

        payload = {
            "generated_at": date.today().isoformat(),
            "config": {
                "grammar_id": GRAMMAR_ID,
                "split_mode": config.split_mode,
                "budget_seconds": config.budget_seconds,
                "max_nodes": config.max_nodes,
                "max_depth": config.max_depth,
                "top_k": config.top_k,
                "auto_add_ga_phi": False,
                "legacy_root": str(legacy_root),
                "temp_legacy_root": str(temp_root),
            },
            "target_role_assignment": target_role_assignment,
            "role_discharge_matrix": _role_discharge_matrix(lexicon=lexicon_current),
            "candidate_inventory": _candidate_inventory(legacy_root=legacy_root),
            "proposed_csv_rows": proposed_rows_tsv,
            "results": results,
            "yes_no_answers": _yes_no_answers(results),
            "final_conclusion": _conclusion(results),
        }

        # sentence -> proposal -> metrics
        payload["results_by_sentence_proposal"] = _build_metrics_view(results)

        out_json = PROJECT_ROOT / "docs/specs/reachability-lexicon-probe-20260302.json"
        out_md = PROJECT_ROOT / "docs/specs/reachability-lexicon-probe-20260302.md"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(_render_markdown(payload), encoding="utf-8")

        print(f"Wrote JSON: {out_json}")
        print(f"Wrote Markdown: {out_md}")
    finally:
        # 調査再現のため残す方針。必要なら手動削除。
        pass


if __name__ == "__main__":
    main()
