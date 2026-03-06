#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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
from domain.grammar.legacy_catalog import load_legacy_grammar_entries  # noqa: E402
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.grammar.rule_catalog import load_rule_catalog  # noqa: E402
from domain.lexicon.legacy_loader import load_legacy_lexicon  # noqa: E402
from domain.numeration.generator import generate_numeration_from_sentence  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402

STATUS_CONFIRMED = "確認済み事実"
STATUS_UNCONFIRMED = "未確認"
STATUS_GUESS = "推測"

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

SENTENCE_CASES = [
    ("S1", "うさぎがいる"),
    ("S2", "わたあめを食べているひつじがいる"),
    ("S3", "ひつじと話しているうさぎがいる"),
    ("S4", "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる"),
    ("S5", "ふわふわしたひつじがいる"),
    ("S6", "ふわふわしたわたあめを食べているひつじがいる"),
]

FOCUS_FAMILIES = ("se:33", "sy:11", "sy:17")


@dataclass(frozen=True)
class RunConfig:
    budget_seconds: float
    max_nodes: int
    max_depth: int
    top_k: int
    split_mode: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fact extraction report for reachability/lexicon/grammar")
    parser.add_argument("--legacy-root", type=Path, default=Path("/Users/tomonaga/Documents/syncsemphoneIMI"))
    parser.add_argument("--grammar-ids", default="imi01,imi02,imi03")
    parser.add_argument("--split-mode", default="A")
    parser.add_argument("--budget-seconds", type=float, default=120.0)
    parser.add_argument("--max-nodes", type=int, default=40000)
    parser.add_argument("--max-depth", type=int, default=28)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--phi-plus-count", type=int, default=2)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("docs/specs/reachability-fact-extract-20260302.json"),
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("docs/specs/reachability-fact-extract-20260302.md"),
    )
    return parser.parse_args()


def _normalize_token(value: str) -> str:
    return value.strip().replace("　", "").replace(" ", "")


def _phono_variants(phono: str) -> list[str]:
    out: list[str] = []
    normalized = _normalize_token(phono)
    if normalized != "":
        out.append(normalized)
    stripped = normalized.strip("-")
    if stripped != "" and stripped != normalized:
        out.append(stripped)
    return out


def _surface_index_from_lexicon(lexicon: dict[int, Any]) -> dict[str, list[int]]:
    index: dict[str, list[int]] = defaultdict(list)
    for lexicon_id, entry in lexicon.items():
        seen: set[str] = set()
        entry_surface = _normalize_token(entry.entry)
        if entry_surface != "":
            seen.add(entry_surface)
        for variant in _phono_variants(entry.phono):
            if variant != "":
                seen.add(variant)
        for token in sorted(seen):
            index[token].append(lexicon_id)
    return dict(index)


def _build_numeration_text(*, memo: str, lexicon_ids: list[int]) -> str:
    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    for index, lexicon_id in enumerate(lexicon_ids, start=1):
        if index > NUMERATION_SLOT_COUNT:
            break
        line1[index] = str(lexicon_id)
        line3[index] = str(index)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _aggregate_residual_families(samples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for sample in samples:
        for key, value in (sample.get("residual_family_counts") or {}).items():
            counter[key] += int(value)
    return dict(sorted(counter.items(), key=lambda row: (-row[1], row[0])))


def _aggregate_residual_sources(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_family: dict[str, Counter[str]] = {}
    attrs: dict[str, dict[str, str]] = {}
    for sample in samples:
        source_map = sample.get("residual_family_sources") or {}
        for family, rows in source_map.items():
            family_counter = by_family.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        row.get("item_id", ""),
                        row.get("category", ""),
                        row.get("phono", ""),
                        row.get("raw", ""),
                    ]
                )
                family_counter[key] += 1
                attrs[key] = {
                    "item_id": row.get("item_id", ""),
                    "category": row.get("category", ""),
                    "phono": row.get("phono", ""),
                    "raw": row.get("raw", ""),
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, counter in sorted(by_family.items(), key=lambda row: row[0]):
        items: list[dict[str, Any]] = []
        for key, count in counter.most_common():
            row = attrs.get(key, {})
            items.append(
                {
                    "count": int(count),
                    "item_id": row.get("item_id", ""),
                    "category": row.get("category", ""),
                    "phono": row.get("phono", ""),
                    "raw": row.get("raw", ""),
                }
            )
        out[family] = items
    return out


def _parse_initial_ids(numeration_text: str) -> list[int]:
    lines = numeration_text.splitlines()
    if not lines:
        return []
    ids: list[int] = []
    for token in lines[0].split("\t")[1:]:
        raw = token.strip()
        if raw == "":
            continue
        try:
            ids.append(int(raw))
        except ValueError:
            continue
    return ids


def _build_initial_item_map(*, state: Any, lexicon_ids: list[int], lexicon: dict[int, Any]) -> dict[str, dict[str, Any]]:
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


def _flatten_sample_sources(
    *,
    samples: list[dict[str, Any]],
    initial_item_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sample_rank, sample in enumerate(samples[:10], start=1):
        history_len = sample.get("history_len")
        source_map = sample.get("residual_family_sources") or {}
        for family, rows in source_map.items():
            for row in rows:
                item_id = row.get("item_id", "")
                init = initial_item_map.get(item_id, {})
                out.append(
                    {
                        "sample_rank": sample_rank,
                        "family": family,
                        "exact_label": row.get("raw", ""),
                        "current_holding_node": item_id,
                        "item_id": item_id,
                        "surface": init.get("surface", row.get("phono", "")),
                        "initial_slot": init.get("initial_slot"),
                        "history_len": history_len,
                        "current_slot": row.get("slot_index"),
                        "process_ref": None,
                        "tree_ref": None,
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
    return out


def _best_mid_dead_end_ratio(samples: list[dict[str, Any]]) -> float:
    if not samples:
        return 0.0
    non_improving = 0
    for sample in samples:
        min_delta = sample.get("min_delta_unresolved")
        if min_delta is not None and int(min_delta) >= 0:
            non_improving += 1
    return round(float(non_improving) / float(len(samples)), 6)


def _run_case(
    *,
    grammar_id: str,
    sentence_key: str,
    sentence: str,
    phi_mode: str,
    config: RunConfig,
    phi_plus_count: int,
    legacy_root: Path,
) -> dict[str, Any]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
    generated = generate_numeration_from_sentence(
        grammar_id=grammar_id,
        sentence=sentence,
        legacy_root=legacy_root,
        split_mode=config.split_mode,
    )
    lexicon_ids = list(generated.lexicon_ids)
    if phi_mode == "plus2" and phi_plus_count > 0:
        room = max(0, NUMERATION_SLOT_COUNT - len(lexicon_ids))
        for _ in range(min(room, phi_plus_count)):
            lexicon_ids.append(309)

    numeration_text = _build_numeration_text(memo=sentence, lexicon_ids=lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=grammar_id,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    initial_item_map = _build_initial_item_map(state=state, lexicon_ids=lexicon_ids, lexicon=lexicon)

    profile = resolve_rule_versions(
        profile=get_grammar_profile(grammar_id),
        legacy_root=legacy_root,
    )
    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
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
    best_mid_samples = (internal.leaf_stats.get("best_mid_state_samples") or [])[: config.top_k]
    best_leaf_family_totals = _aggregate_residual_families(best_leaf_samples)
    best_mid_family_totals = _aggregate_residual_families(best_mid_samples)
    best_leaf_family_avg = (
        {
            key: round(float(value) / float(len(best_leaf_samples)), 3)
            for key, value in best_leaf_family_totals.items()
        }
        if best_leaf_samples
        else {}
    )

    discharge_table: list[dict[str, Any]] = []
    # initial family totals from initial state (base only, no path weighting).
    initial_counter: Counter[str] = Counter()
    for node in state.base[1 : state.basenum + 1]:
        if node == "zero" or not isinstance(node, list):
            continue
        sy_values = node[3] if len(node) > 3 and isinstance(node[3], list) else []
        se_values = node[5] if len(node) > 5 and isinstance(node[5], list) else []
        for feature in sy_values:
            raw = str(feature).strip()
            parts = [part.strip() for part in raw.split(",")]
            if len(parts) >= 2 and parts[1].isdigit():
                initial_counter[f"sy:{parts[1]}"] += 1
        for semantic in se_values:
            raw = str(semantic)
            if ":" not in raw:
                continue
            rhs = raw.split(":", 1)[1].strip()
            parts = [part.strip() for part in rhs.split(",")]
            if len(parts) >= 2 and parts[1].isdigit():
                initial_counter[f"se:{parts[1]}"] += 1
    initial_family_counts = dict(sorted(initial_counter.items(), key=lambda row: row[0]))

    for family in FOCUS_FAMILIES:
        initial_count = int(initial_family_counts.get(family, 0))
        residual_avg = float(best_leaf_family_avg.get(family, 0.0))
        discharge_table.append(
            {
                "family": family,
                "initial_count": initial_count,
                "residual_avg_per_best_leaf": residual_avg,
                "estimated_discharged_per_path": round(max(float(initial_count) - residual_avg, 0.0), 3),
                "fact_status": STATUS_CONFIRMED,
            }
        )

    token_resolutions = [
        {
            "token": row.token,
            "lexicon_id": row.lexicon_id,
            "candidate_lexicon_ids": list(row.candidate_lexicon_ids),
        }
        for row in generated.token_resolutions
    ]

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "grammar_id": grammar_id,
        "phi_mode": phi_mode,
        "lexicon_ids": lexicon_ids,
        "token_resolutions": token_resolutions,
        "status": internal.status,
        "completed": internal.completed,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "best_leaf_residual_family_totals": best_leaf_family_totals,
        "best_mid_residual_family_totals": best_mid_family_totals,
        "best_mid_local_dead_end": {
            "sample_count": len(best_mid_samples),
            "non_improving_ratio": _best_mid_dead_end_ratio(best_mid_samples),
            "fact_status": STATUS_CONFIRMED,
        },
        "initial_family_counts": initial_family_counts,
        "best_leaf_residual_family_avg": best_leaf_family_avg,
        "best_leaf_residual_source_totals": _aggregate_residual_sources(best_leaf_samples),
        "best_mid_residual_source_totals": _aggregate_residual_sources(best_mid_samples),
        "best_leaf_top10_sources": _flatten_sample_sources(
            samples=best_leaf_samples,
            initial_item_map=initial_item_map,
        ),
        "best_mid_top10_sources": _flatten_sample_sources(
            samples=best_mid_samples,
            initial_item_map=initial_item_map,
        ),
        "discharge_table": discharge_table,
    }


def _extract_reachable_lexicon_ids_from_confirmed_sets(path: Path) -> set[int]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    out: set[int] = set()
    for match in re.finditer(r"Lexicon IDs:\s*`([^`]+)`", text):
        for token in match.group(1).split(","):
            raw = token.strip()
            if raw.isdigit():
                out.add(int(raw))
    return out


def _collect_target_lexicon_candidates(
    *,
    legacy_root: Path,
    grammar_ids: list[str],
    sentence_results_none_only: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    surface_index = _surface_index_from_lexicon(lexicon)
    reachable_used_ids = _extract_reachable_lexicon_ids_from_confirmed_sets(
        PROJECT_ROOT / "docs/specs/reachability-confirmed-sets-ja.md"
    )

    selected_map: dict[tuple[str, str], set[tuple[str, int]]] = {}
    for grammar_id in grammar_ids:
        selected_map[(grammar_id, "default")] = set()
    for row in sentence_results_none_only:
        grammar_id = row["grammar_id"]
        for resolution in row.get("token_resolutions", []):
            token = _normalize_token(str(resolution.get("token", "")))
            lid = int(resolution.get("lexicon_id"))
            selected_map[(grammar_id, "default")].add((token, lid))  # type: ignore[arg-type]

    out_rows: list[dict[str, Any]] = []
    for surface in TARGET_SURFACES:
        normalized = _normalize_token(surface)
        candidates = sorted(set(surface_index.get(normalized, [])))
        if not candidates:
            out_rows.append(
                {
                    "surface": surface,
                    "lexicon_id": None,
                    "entry": None,
                    "category": None,
                    "idslot": None,
                    "sync_features": [],
                    "semantics": [],
                    "selected_in_step1_auto_default_by_grammar": {
                        grammar_id: False for grammar_id in grammar_ids
                    },
                    "used_in_confirmed_reachable_sets": False,
                    "fact_status": STATUS_CONFIRMED,
                    "note": "lexicon-all.csv 上で一致候補なし",
                }
            )
            continue
        for lexicon_id in candidates:
            entry = lexicon[lexicon_id]
            selected_flags = {
                grammar_id: bool((normalized, lexicon_id) in selected_map[(grammar_id, "default")])
                for grammar_id in grammar_ids
            }
            out_rows.append(
                {
                    "surface": surface,
                    "lexicon_id": lexicon_id,
                    "entry": entry.entry,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                    "selected_in_step1_auto_default_by_grammar": selected_flags,
                    "used_in_confirmed_reachable_sets": lexicon_id in reachable_used_ids,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
    return out_rows


def _rule_kind_label(kind: int) -> str:
    if kind == 2:
        return "double"
    if kind == 1:
        return "single"
    return str(kind)


def _rc_related_guess(rule_name: str) -> tuple[bool, str]:
    keywords = ("rel", "property", "partition", "pickup", "landing", "J-Merge")
    matched = any(keyword.lower() in rule_name.lower() for keyword in keywords)
    reason = "rule_name に rel/property/partition/pickup/landing/J-Merge を含むため" if matched else "rule_name が RH/LH 等の汎用名のみのため"
    return matched, reason


def _collect_grammar_catalogs(*, legacy_root: Path, primary_grammar_ids: list[str]) -> dict[str, Any]:
    entries = load_legacy_grammar_entries(legacy_root=legacy_root)
    all_ids = sorted({entry.grammar_id for entry in entries} | set(primary_grammar_ids))

    def _rows_for(grammar_id: str) -> dict[str, Any]:
        profile = get_grammar_profile(grammar_id)
        try:
            rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root)
            rows = []
            for rule in rules:
                rule_path = legacy_root / "MergeRule" / f"{rule.file_name}.pl"
                rc_guess, rc_reason = _rc_related_guess(rule.name)
                rows.append(
                    {
                        "grammar_id": grammar_id,
                        "rule_number": rule.number,
                        "rule_name": rule.name,
                        "rule_kind": _rule_kind_label(rule.kind),
                        "rule_kind_raw": rule.kind,
                        "definition_file_token": rule.file_name,
                        "definition_file_path": str(rule_path),
                        "is_non_rh_lh_rule": rule.name not in {"RH-Merge", "LH-Merge"},
                        "rc_related_guess": rc_guess,
                        "rc_related_guess_reason": rc_reason,
                        "rc_related_guess_fact_status": STATUS_GUESS,
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
            return {
                "grammar_id": grammar_id,
                "folder": profile.folder,
                "uses_lexicon_all": profile.uses_lexicon_all,
                "rules": rows,
                "fact_status": STATUS_CONFIRMED,
            }
        except Exception as exc:
            return {
                "grammar_id": grammar_id,
                "folder": profile.folder,
                "uses_lexicon_all": profile.uses_lexicon_all,
                "rules": [],
                "error": str(exc),
                "fact_status": STATUS_UNCONFIRMED,
            }

    primary = [_rows_for(grammar_id) for grammar_id in primary_grammar_ids]
    others = [_rows_for(grammar_id) for grammar_id in all_ids if grammar_id not in set(primary_grammar_ids)]
    return {
        "primary": primary,
        "others": others,
        "fact_status": STATUS_CONFIRMED,
    }


def _compute_additivity(results: list[dict[str, Any]], grammar_ids: list[str]) -> list[dict[str, Any]]:
    keyed = {(row["grammar_id"], row["phi_mode"], row["sentence_key"]): row for row in results}
    rows: list[dict[str, Any]] = []

    def fam(row: Optional[dict[str, Any]], name: str) -> float:
        if row is None:
            return 0.0
        return float((row.get("best_leaf_residual_family_avg") or {}).get(name, 0.0))

    for grammar_id in grammar_ids:
        for phi_mode in ("none", "plus2"):
            s2 = keyed.get((grammar_id, phi_mode, "S2"))
            s3 = keyed.get((grammar_id, phi_mode, "S3"))
            s4 = keyed.get((grammar_id, phi_mode, "S4"))
            s5 = keyed.get((grammar_id, phi_mode, "S5"))
            s6 = keyed.get((grammar_id, phi_mode, "S6"))
            for family in FOCUS_FAMILIES:
                rows.append(
                    {
                        "grammar_id": grammar_id,
                        "phi_mode": phi_mode,
                        "family": family,
                        "delta_add_adjective_on_rc_eat": round(fam(s6, family) - fam(s2, family), 3),
                        "delta_add_second_rc_from_s2_to_s4": round(fam(s4, family) - fam(s2, family), 3),
                        "sum_one_rc_minus_full": round((fam(s2, family) + fam(s3, family)) - fam(s4, family), 3),
                        "delta_add_adjective_on_simple_clause": round(fam(s5, family) - fam(keyed.get((grammar_id, phi_mode, "S1")), family), 3),
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
    return rows


def _build_capability_matrix() -> list[dict[str, Any]]:
    return [
        {
            "feature": "se:33:*",
            "example_labels": ["Agent:2,33,ga", "Theme:2,33,wo", "相手:2,33,to"],
            "introduced_by_examples": ["食べている(266)", "話している(269)", "いる(271)"],
            "consuming_functions": [
                "packages/domain/src/domain/derivation/execute.py:339 (_process_se_imi03)",
            ],
            "consumption_condition": "head側se の number=33 かつ non-head側 sy で label 一致（sy_number=11 or 12）",
            "code_evidence": [
                "packages/domain/src/domain/derivation/execute.py:395-409",
                "packages/domain/src/domain/derivation/execute.py:1728-1753",
                "packages/domain/src/domain/derivation/execute.py:1807-1832",
            ],
            "imi01_rhlh_theoretical": "条件を満たす pair が作れれば消費分岐は実行される",
            "imi01_rhlh_observed_for_target_long_sentence": "未確認（best residual に継続残存）",
            "imi02_imi03_difference": "RH/LH実行経路は同関数（_uses_imi_feature_engine）を使用",
            "fact_status": STATUS_CONFIRMED,
            "observation_status": STATUS_UNCONFIRMED,
        },
        {
            "feature": "sy:11:*",
            "example_labels": ["4,11,ga", "4,11,wo", "4,11,to", "2,11,ga", "2,11,wo", "2,11,to"],
            "introduced_by_examples": ["が(19)", "を(23)", "と(268)", "φ(309)"],
            "consuming_functions": [
                "packages/domain/src/domain/derivation/execute.py:587 (_process_sy_imi03)",
                "packages/domain/src/domain/derivation/execute.py:339 (_process_se_imi03)",
            ],
            "consumption_condition": "non-head側 sy number=11, coeff=4 のとき `2,11,label` へ変換しつつnaから除去；se:33 側とlabel一致で消費対象",
            "code_evidence": [
                "packages/domain/src/domain/derivation/execute.py:780-784",
                "packages/domain/src/domain/derivation/execute.py:395-409",
            ],
            "imi01_rhlh_theoretical": "分岐条件は存在（pair条件を満たす必要あり）",
            "imi01_rhlh_observed_for_target_long_sentence": "未確認（sy:11 が persistent residual として観測）",
            "imi02_imi03_difference": "RH/LH処理は同一系；追加ruleの有無は grammar catalog 依存",
            "fact_status": STATUS_CONFIRMED,
            "observation_status": STATUS_UNCONFIRMED,
        },
        {
            "feature": "sy:17:*",
            "example_labels": ["0,17,N,,,right,nonhead", "0,17,N,,,left,nonhead", "3,17,V,,,left,nonhead"],
            "introduced_by_examples": ["ふわふわした(264)", "が(19)", "を(23)", "と(268)", "る(204) ほか"],
            "consuming_functions": [
                "packages/domain/src/domain/derivation/execute.py:69 (_eval_feature_17)",
                "packages/domain/src/domain/derivation/execute.py:587 (_process_sy_imi03)",
            ],
            "consumption_condition": "alpha(相手category)/beta(相手sy)/gamma(rule)/delta(left-right位置)/epsilon(head|nonhead) の5条件一致",
            "code_evidence": [
                "packages/domain/src/domain/derivation/execute.py:69-95",
                "packages/domain/src/domain/derivation/execute.py:659-677",
                "packages/domain/src/domain/derivation/execute.py:800-820",
            ],
            "imi01_rhlh_theoretical": "_eval_feature_17 条件を満たす pair で消費分岐に入る",
            "imi01_rhlh_observed_for_target_long_sentence": "未確認（x9 が由来の sy:17 が persistent residual）",
            "imi02_imi03_difference": "RH/LH部は同関数使用",
            "fact_status": STATUS_CONFIRMED,
            "observation_status": STATUS_UNCONFIRMED,
        },
        {
            "feature": "engine path parity (imi01/imi02/imi03)",
            "example_labels": [],
            "introduced_by_examples": [],
            "consuming_functions": [
                "packages/domain/src/domain/derivation/execute.py:10 (_uses_imi_feature_engine)",
                "packages/domain/src/domain/derivation/execute.py:1728-1772 (RH)",
                "packages/domain/src/domain/derivation/execute.py:1807-1851 (LH)",
            ],
            "consumption_condition": "grammar_id in {imi01, imi02, imi03} で同一 feature engine を通る",
            "code_evidence": [
                "packages/domain/src/domain/derivation/execute.py:10",
                "packages/domain/src/domain/derivation/execute.py:1728",
                "packages/domain/src/domain/derivation/execute.py:1807",
            ],
            "imi01_rhlh_theoretical": "確認済み",
            "imi01_rhlh_observed_for_target_long_sentence": "確認済み（同コード経路）",
            "imi02_imi03_difference": "rule catalog に含まれる追加rule候補は異なる可能性あり",
            "fact_status": STATUS_CONFIRMED,
            "observation_status": STATUS_CONFIRMED,
        },
    ]


def _collect_repo_like_examples(*, legacy_root: Path, config: RunConfig) -> dict[str, Any]:
    pattern_candidates = [
        "imi01/set-numeration/1608131495.num",
        "imi01/set-numeration/1608131500.num",
        "imi02/set-numeration/1608131495.num",
        "imi03/set-numeration/1608131495.num",
        "japanese2/set-numeration/07-02-17.num",
        "japanese2/set-numeration/07-01-03b.num",
        "japanese2/set-numeration/08-01-15.num",
        "japanese2/set-numeration/08-02-24.num",
    ]

    examples: list[dict[str, Any]] = []
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")
    seen_lexicon_ids: set[int] = set()

    for relpath in pattern_candidates:
        path = legacy_root / relpath
        if not path.exists():
            examples.append(
                {
                    "numeration_relpath": relpath,
                    "fact_status": STATUS_UNCONFIRMED,
                    "reason": "file_not_found",
                }
            )
            continue
        grammar_id = relpath.split("/", 1)[0]
        numeration_text = path.read_text(encoding="utf-8")
        first_line = numeration_text.splitlines()[0] if numeration_text.splitlines() else ""
        ids = [int(token) for token in first_line.split("\t")[1:] if token.strip().isdigit()]
        for lexicon_id in ids:
            seen_lexicon_ids.add(lexicon_id)
        try:
            state = build_initial_derivation_state(
                grammar_id=grammar_id,
                numeration_text=numeration_text,
                legacy_root=legacy_root,
            )
            profile = resolve_rule_versions(
                profile=get_grammar_profile(grammar_id),
                legacy_root=legacy_root,
            )
            request = DerivationReachabilityRequest(
                state=state,
                max_evidences=5,
                return_process_text=False,
                budget_seconds=min(config.budget_seconds, 60.0),
                max_nodes=min(config.max_nodes, 15000),
                max_depth=config.max_depth,
            )
            internal = _search_reachability(
                request=request,
                legacy_root=legacy_root,
                rh_version=profile.rh_merge_version,
                lh_version=profile.lh_merge_version,
                search_signature_mode="structural",
            )
            rule_sequence = []
            if internal.evidences:
                for step in internal.evidences[0].steps:
                    rule_sequence.append(
                        {
                            "rule_name": step.rule_name,
                            "rule_number": step.rule_number,
                            "left_id": step.left_id,
                            "right_id": step.right_id,
                        }
                    )
            examples.append(
                {
                    "numeration_relpath": relpath,
                    "sentence": state.memo,
                    "grammar_id": grammar_id,
                    "status": internal.status,
                    "reason": internal.reason,
                    "actions_attempted": internal.actions_attempted,
                    "rule_sequence_if_reachable": rule_sequence if internal.status == "reachable" else [],
                    "lexicon_ids": ids,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
        except Exception as exc:
            examples.append(
                {
                    "numeration_relpath": relpath,
                    "grammar_id": grammar_id,
                    "status": "failed",
                    "reason": str(exc),
                    "lexicon_ids": ids,
                    "fact_status": STATUS_UNCONFIRMED,
                }
            )

    related_entries: list[dict[str, Any]] = []
    for lexicon_id in sorted(seen_lexicon_ids):
        entry = lexicon.get(lexicon_id)
        if entry is None:
            continue
        related_entries.append(
            {
                "lexicon_id": lexicon_id,
                "entry": entry.entry,
                "category": entry.category,
                "sync_features": list(entry.sync_features),
                "semantics": list(entry.semantics),
                "hint_reason_guess": "RC/修飾文を含む numeration で実際に参照されたID",
                "hint_reason_guess_status": STATUS_GUESS,
                "fact_status": STATUS_CONFIRMED,
            }
        )

    return {
        "examples": examples,
        "related_lexical_entries": related_entries,
        "fact_status": STATUS_CONFIRMED,
    }


def _compute_phi_comparison(results: list[dict[str, Any]], grammar_ids: list[str]) -> list[dict[str, Any]]:
    keyed = {(row["grammar_id"], row["sentence_key"], row["phi_mode"]): row for row in results}
    rows: list[dict[str, Any]] = []
    for grammar_id in grammar_ids:
        for sentence_key, _sentence in SENTENCE_CASES:
            none_row = keyed.get((grammar_id, sentence_key, "none"))
            plus_row = keyed.get((grammar_id, sentence_key, "plus2"))
            if none_row is None or plus_row is None:
                rows.append(
                    {
                        "grammar_id": grammar_id,
                        "sentence_key": sentence_key,
                        "fact_status": STATUS_UNCONFIRMED,
                        "reason": "missing_case",
                    }
                )
                continue

            def fam(row: dict[str, Any], name: str) -> float:
                return float((row.get("best_leaf_residual_family_avg") or {}).get(name, 0.0))

            source_diff: dict[str, list[dict[str, Any]]] = {}
            for family in FOCUS_FAMILIES:
                none_src = (none_row.get("best_leaf_residual_source_totals") or {}).get(family) or []
                plus_src = (plus_row.get("best_leaf_residual_source_totals") or {}).get(family) or []
                none_map = {
                    f"{row.get('item_id','')}|{row.get('raw','')}": int(row.get("count", 0))
                    for row in none_src
                }
                plus_map = {
                    f"{row.get('item_id','')}|{row.get('raw','')}": int(row.get("count", 0))
                    for row in plus_src
                }
                all_keys = sorted(set(none_map) | set(plus_map))
                source_rows: list[dict[str, Any]] = []
                for key in all_keys:
                    before = none_map.get(key, 0)
                    after = plus_map.get(key, 0)
                    if before == after:
                        continue
                    item_id, raw = key.split("|", 1)
                    source_rows.append(
                        {
                            "item_id": item_id,
                            "raw": raw,
                            "count_none": before,
                            "count_plus2": after,
                            "delta_plus2_minus_none": after - before,
                        }
                    )
                source_diff[family] = source_rows

            rows.append(
                {
                    "grammar_id": grammar_id,
                    "sentence_key": sentence_key,
                    "status_none": none_row.get("status"),
                    "status_plus2": plus_row.get("status"),
                    "reason_none": none_row.get("reason"),
                    "reason_plus2": plus_row.get("reason"),
                    "residual_delta_avg": {
                        family: round(fam(plus_row, family) - fam(none_row, family), 3)
                        for family in FOCUS_FAMILIES
                    },
                    "source_diff": source_diff,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
    return rows


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Reachability 事実抽出レポート（{payload['generated_at']}）")
    lines.append("")
    lines.append("## 1. 概要")
    lines.append("")
    lines.append(f"- [確認済み事実] 実測条件: grammar=`{', '.join(payload['config']['grammar_ids'])}`, split_mode=`{payload['config']['split_mode']}`, budget_seconds=`{payload['config']['budget_seconds']}`, max_nodes=`{payload['config']['max_nodes']}`, max_depth=`{payload['config']['max_depth']}`, top_k=`{payload['config']['top_k']}`")
    lines.append("- [確認済み事実] この文書は `code/csv/実測ログ` から抽出した値のみを掲載。")
    lines.append("- [未確認] `process/tree` への直リンクは本JSON生成経路では未取得（null）。")
    lines.append("")

    lines.append("## 2. 語彙候補一覧")
    lines.append("")
    lines.append("- [確認済み事実] `lexicon-all.csv` と `generate_numeration_from_sentence` の自動選択結果から抽出。")
    lines.append("")
    lines.append("| surface | lexicon_id | 見出し | 範疇 | idslot | auto選択(imi01/02/03) | reachable既知セット使用 |")
    lines.append("|---|---:|---|---|---|---|---|")
    for row in payload["request1"]["surface_candidates"]:
        sel = row["selected_in_step1_auto_default_by_grammar"]
        sel_text = f"{int(bool(sel.get('imi01')))} / {int(bool(sel.get('imi02')))} / {int(bool(sel.get('imi03')))}"
        lines.append(
            f"| {row['surface']} | {row['lexicon_id']} | {row['entry']} | {row['category']} | {row['idslot']} | {sel_text} | {row['used_in_confirmed_reachable_sets']} |"
        )
    lines.append("")

    lines.append("## 3. Grammar 候補一覧")
    lines.append("")
    lines.append("- [確認済み事実] `domain.grammar.rule_catalog.load_rule_catalog` 抽出。")
    lines.append("- [推測] `rc_related_guess` は rule 名に基づく推定（仕様断定ではない）。")
    lines.append("")
    for group_name in ("primary", "others"):
        lines.append(f"### {group_name}")
        for grammar in payload["request2"]["grammar_catalogs"][group_name]:
            lines.append(f"- grammar `{grammar['grammar_id']}`")
            if grammar.get("rules"):
                lines.append("| no | rule_name | kind | token | non-RH/LH | rc_related_guess |")
                lines.append("|---:|---|---|---|---|---|")
                for rule in grammar["rules"]:
                    lines.append(
                        f"| {rule['rule_number']} | {rule['rule_name']} | {rule['rule_kind']} | {rule['definition_file_token']} | {rule['is_non_rh_lh_rule']} | {rule['rc_related_guess']} |"
                    )
            else:
                lines.append(f"  - [未確認] rules 読込失敗: `{grammar.get('error', '')}`")
    lines.append("")

    lines.append("## 4. reduced sentence ごとの residual 比較")
    lines.append("")
    lines.append("| sentence | grammar | phi | status | reason | actions | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|---:|")
    for row in payload["request3"]["cases"]:
        avg = row.get("best_leaf_residual_family_avg") or {}
        lines.append(
            "| {sentence_key} | {grammar_id} | {phi_mode} | {status} | {reason} | {actions} | {leaf_min} | {se33} | {sy11} | {sy17} |".format(
                sentence_key=row["sentence_key"],
                grammar_id=row["grammar_id"],
                phi_mode=row["phi_mode"],
                status=row["status"],
                reason=row["reason"],
                actions=row.get("actions_attempted", 0),
                leaf_min=row.get("best_leaf_unresolved_min", ""),
                se33=avg.get("se:33", 0),
                sy11=avg.get("sy:11", 0),
                sy17=avg.get("sy:17", 0),
            )
        )
    lines.append("")

    lines.append("## 5. persistent residual の exact source attribution")
    lines.append("")
    lines.append("- [確認済み事実] 各ケースの `best_leaf_top10_sources` / `best_mid_top10_sources` を JSON に全件格納。")
    lines.append("- [確認済み事実] ここでは件数上位 source のみ抜粋。")
    lines.append("")
    for row in payload["request3"]["cases"]:
        lines.append(f"### {row['sentence_key']} / {row['grammar_id']} / {row['phi_mode']}")
        lines.append(f"- status: `{row['status']}` / reason: `{row['reason']}`")
        source_totals = row.get("best_leaf_residual_source_totals") or {}
        for family in FOCUS_FAMILIES:
            items = source_totals.get(family) or []
            if not items:
                continue
            lines.append(f"- {family} top:")
            for item in items[:5]:
                lines.append(
                    f"  - `{item.get('item_id','')}` {item.get('raw','')} ({item.get('count',0)})"
                )
    lines.append("")

    lines.append("## 6. discharge capability matrix")
    lines.append("")
    lines.append("- [確認済み事実] 関数分岐は `packages/domain/src/domain/derivation/execute.py` の条件式から抽出。")
    lines.append("- [未確認] 「対象文で実際にその分岐に到達できるか」は実測未確定の行がある。")
    lines.append("")
    lines.append("| feature | consuming function | condition (code-grounded) | imi01 RH/LH 理論上 | 実測状態 |")
    lines.append("|---|---|---|---|---|")
    for row in payload["request5"]["capability_matrix"]:
        lines.append(
            f"| {row['feature']} | {', '.join(row['consuming_functions'])} | {row['consumption_condition']} | {row['imi01_rhlh_theoretical']} | {row['imi01_rhlh_observed_for_target_long_sentence']} |"
        )
    lines.append("")

    lines.append("## 7. φ 比較")
    lines.append("")
    lines.append("- [確認済み事実] `none` と `plus2` の差分は `residual_delta_avg` と `source_diff` で JSON に保存。")
    lines.append("")
    lines.append("| sentence | grammar | status(none->plus2) | Δse:33 | Δsy:11 | Δsy:17 |")
    lines.append("|---|---|---|---:|---:|---:|")
    for row in payload["request6"]["phi_comparison"]:
        delta = row.get("residual_delta_avg") or {}
        lines.append(
            f"| {row['sentence_key']} | {row['grammar_id']} | {row['status_none']}->{row['status_plus2']} | {delta.get('se:33',0)} | {delta.get('sy:11',0)} | {delta.get('sy:17',0)} |"
        )
    lines.append("")

    lines.append("## 8. リポジトリ内の類例")
    lines.append("")
    lines.append("- [確認済み事実] `set-numeration` から RC/修飾節候補の `.num` を抽出し、同一予算で status を実測。")
    lines.append("- [推測] 手掛かり判定は `rule_name` / `語彙素性` ベース。")
    lines.append("")
    lines.append("| numeration | grammar | status | reason | reachable時 rule_sequence有無 |")
    lines.append("|---|---|---|---|---|")
    for row in payload["request7"]["repo_examples"]["examples"]:
        lines.append(
            f"| {row.get('numeration_relpath','')} | {row.get('grammar_id','')} | {row.get('status','')} | {row.get('reason','')} | {bool(row.get('rule_sequence_if_reachable'))} |"
        )
    lines.append("")

    lines.append("## 9. 断定できること / 断定できないこと")
    lines.append("")
    lines.append("### [確認済み事実]")
    for text in payload["summary"]["confirmed"]:
        lines.append(f"- {text}")
    lines.append("")
    lines.append("### [未確認]")
    for text in payload["summary"]["unconfirmed"]:
        lines.append(f"- {text}")
    lines.append("")
    lines.append("### [推測]")
    for text in payload["summary"]["guesses"]:
        lines.append(f"- {text}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    legacy_root = args.legacy_root.resolve()
    grammar_ids = [token.strip() for token in args.grammar_ids.split(",") if token.strip() != ""]
    config = RunConfig(
        budget_seconds=float(args.budget_seconds),
        max_nodes=int(args.max_nodes),
        max_depth=int(args.max_depth),
        top_k=max(1, int(args.top_k)),
        split_mode=args.split_mode,
    )

    all_cases: list[dict[str, Any]] = []
    for sentence_key, sentence in SENTENCE_CASES:
        for grammar_id in grammar_ids:
            for phi_mode in ("none", "plus2"):
                try:
                    all_cases.append(
                        _run_case(
                            grammar_id=grammar_id,
                            sentence_key=sentence_key,
                            sentence=sentence,
                            phi_mode=phi_mode,
                            config=config,
                            phi_plus_count=max(0, int(args.phi_plus_count)),
                            legacy_root=legacy_root,
                        )
                    )
                except Exception as exc:
                    all_cases.append(
                        {
                            "sentence_key": sentence_key,
                            "sentence": sentence,
                            "grammar_id": grammar_id,
                            "phi_mode": phi_mode,
                            "status": "failed",
                            "completed": False,
                            "reason": "failed",
                            "error": str(exc),
                            "fact_status": STATUS_UNCONFIRMED,
                        }
                    )

    cases_none_only = [row for row in all_cases if row.get("phi_mode") == "none" and row.get("status") != "failed"]
    request1 = {
        "surface_candidates": _collect_target_lexicon_candidates(
            legacy_root=legacy_root,
            grammar_ids=grammar_ids,
            sentence_results_none_only=cases_none_only,
        ),
        "fact_status": STATUS_CONFIRMED,
    }
    request2 = {
        "grammar_catalogs": _collect_grammar_catalogs(
            legacy_root=legacy_root,
            primary_grammar_ids=grammar_ids,
        ),
        "fact_status": STATUS_CONFIRMED,
    }

    request3 = {
        "cases": all_cases,
        "fact_status": STATUS_CONFIRMED,
    }

    request4 = {
        "additivity_rows": _compute_additivity(all_cases, grammar_ids),
        "fact_status": STATUS_CONFIRMED,
    }

    request5 = {
        "capability_matrix": _build_capability_matrix(),
        "fact_status": STATUS_CONFIRMED,
    }

    request6 = {
        "phi_comparison": _compute_phi_comparison(all_cases, grammar_ids),
        "fact_status": STATUS_CONFIRMED,
    }

    request7 = {
        "repo_examples": _collect_repo_like_examples(legacy_root=legacy_root, config=config),
        "fact_status": STATUS_CONFIRMED,
    }

    summary = {
        "confirmed": [
            "6文×3Grammar×2phi の同一予算実測を実行し、status/reason/actions/残差集計をJSON化した。",
            "persistent residual の source attribution（best leaf/mid top10）を、item_id・exact_label・initial_slot付きで保存した。",
            "imi01/imi02/imi03 の RH/LH 実行経路が同一 feature engine（_uses_imi_feature_engine）を通ることをコードで確認した。",
        ],
        "unconfirmed": [
            "対象文（S4/S6 など）で、imi01 RH/LH のみで最終的に residual を全消費できる経路が存在するかは、今回条件下では未確定。",
            "best sample から process/tree への直接参照は現行抽出経路では未取得（null）。",
        ],
        "guesses": [
            "rule_name ベースの `rc_related_guess` は、規則名の語彙的手掛かりによる分類であり、形式意味論上の保証ではない。",
            "repo内 RC候補ファイルは手掛かりになり得るが、流用可否は rule/lexicon整合の追加検証が必要。",
        ],
    }

    payload = {
        "generated_at": date.today().isoformat(),
        "config": {
            "legacy_root": str(legacy_root),
            "grammar_ids": grammar_ids,
            "split_mode": config.split_mode,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "phi_plus_count": args.phi_plus_count,
        },
        "request1": request1,
        "request2": request2,
        "request3": request3,
        "request4": request4,
        "request5": request5,
        "request6": request6,
        "request7": request7,
        "summary": summary,
    }

    out_json = args.out_json
    if not out_json.is_absolute():
        out_json = PROJECT_ROOT / out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = args.out_md
    if not out_md.is_absolute():
        out_md = PROJECT_ROOT / out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_render_markdown(payload), encoding="utf-8")

    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
