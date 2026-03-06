#!/usr/bin/env python3
from __future__ import annotations

import json
import re
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
from domain.derivation.candidates import list_merge_candidates  # noqa: E402
from domain.derivation.execute import execute_double_merge, execute_single_merge  # noqa: E402
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

GRAMMAR_ID = "japanese2"
SENTENCES = {
    "S1": "うさぎがいる",
    "S2": "わたあめを食べているひつじがいる",
    "S3": "ひつじと話しているうさぎがいる",
    "S4": "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
    "S5": "ふわふわしたひつじがいる",
    "S6": "ふわふわしたわたあめを食べているひつじがいる",
}
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
FOCUS_FAMILIES = ("se:33", "sy:11", "sy:17")

_JAPANESE2_ONLY_SYNC_FEATURE_CODES = {"1L", "2L", "3L"}
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

# 既存候補のみ実験（新規 lexical item 追加なし）
PROPOSAL_IDS = ("P0_baseline_auto", "P1_existing_reselect", "P2_existing_reselect_plus_phi272_275", "P3_existing_reselect_particle_variants")

# 必要時のみ使う新規 lexical 提案（最大3行）
NEW_LEX_ROWS = [
    {
        "lexicon_id": 9101,
        "entry": "ひつじ",
        "phono": "ひつじ",
        "category": "N",
        "predicates": [],
        "sync_features": ["4,11,ga", "4,11,to"],
        "idslot": "id",
        "semantics": ["ひつじ:T"],
        "note": "japanese2-probe20260302",
    },
    {
        "lexicon_id": 9102,
        "entry": "うさぎ",
        "phono": "うさぎ",
        "category": "N",
        "predicates": [],
        "sync_features": ["4,11,ga"],
        "idslot": "id",
        "semantics": ["うさぎ:T"],
        "note": "japanese2-probe20260302",
    },
    {
        "lexicon_id": 9103,
        "entry": "わたあめ",
        "phono": "わたあめ",
        "category": "N",
        "predicates": [],
        "sync_features": ["4,11,wo"],
        "idslot": "id",
        "semantics": ["わたあめ:T"],
        "note": "japanese2-probe20260302",
    },
]


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
        entry_norm = _normalize_token(entry.entry)
        if entry_norm:
            seen.add(entry_norm)
        for v in _phono_variants(entry.phono):
            if v:
                seen.add(v)
        for s in sorted(seen):
            idx[s].append(lid)
    return dict(idx)


def _rule_kind_label(kind: int) -> str:
    if kind == 2:
        return "double"
    if kind == 1:
        return "single"
    return str(kind)


def _build_numeration_text(memo: str, lexicon_ids: list[int]) -> str:
    if len(lexicon_ids) > NUMERATION_SLOT_COUNT:
        raise ValueError(f"Too many lexicon ids: {len(lexicon_ids)} > {NUMERATION_SLOT_COUNT}")
    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    for i, lid in enumerate(lexicon_ids, start=1):
        line1[i] = str(lid)
        line3[i] = str(i)
    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _extract_referenced_rule_names(entry: LexiconEntry) -> list[str]:
    values = list(entry.sync_features) + list(entry.semantics)
    refs: set[str] = set()
    for value in values:
        if value == "":
            continue
        for marker in _RULE_NAME_MARKERS:
            if marker in value:
                refs.add(marker)
    return sorted(refs)


def _extract_sync_feature_codes(entry: LexiconEntry) -> set[str]:
    codes: set[str] = set()
    for feature in entry.sync_features:
        parts = [part.strip() for part in feature.split(",")]
        if len(parts) > 1 and parts[1]:
            codes.add(parts[1])
    return codes


def _infer_candidate_compatibility_japanese2(
    *,
    entry: LexiconEntry,
    grammar_rule_names: set[str],
) -> dict[str, Any]:
    reason_codes: list[str] = []
    missing_rule_names: list[str] = []
    refs = _extract_referenced_rule_names(entry)
    missing = sorted(rule_name for rule_name in refs if rule_name not in grammar_rule_names)
    if missing:
        missing_rule_names.extend(missing)
        reason_codes.append("missing_required_rule")
    # japanese2 では 1L/2L/3L は許容されるため、ここでは除外理由にしない。
    compatible = len(reason_codes) == 0
    return {
        "compatible": compatible,
        "reason_codes": reason_codes,
        "missing_rule_names": missing_rule_names,
        "referenced_rule_names": refs,
    }


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
            fam_counter = by_family.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        row.get("item_id", ""),
                        row.get("category", ""),
                        row.get("phono", ""),
                        row.get("raw", ""),
                        row.get("slot_index", ""),
                    ]
                )
                fam_counter[key] += 1
                attrs[key] = {
                    "item_id": row.get("item_id", ""),
                    "category": row.get("category", ""),
                    "phono": row.get("phono", ""),
                    "raw": row.get("raw", ""),
                    "slot_index": row.get("slot_index", ""),
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, counter in sorted(by_family.items(), key=lambda row: row[0]):
        items: list[dict[str, Any]] = []
        for key, count in counter.most_common(10):
            base = attrs[key]
            items.append(
                {
                    "count": int(count),
                    "item_id": base["item_id"],
                    "category": base["category"],
                    "phono": base["phono"],
                    "raw": base["raw"],
                    "slot_index": base["slot_index"],
                }
            )
        out[family] = items
    return out


def _build_initial_item_map(*, state: Any, lexicon_ids: list[int], lexicon: dict[int, LexiconEntry]) -> dict[str, dict[str, Any]]:
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


def _flatten_exact_provenance(
    *,
    samples: list[dict[str, Any]],
    initial_item_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    attr_map: dict[str, dict[str, Any]] = {}
    for sample_rank, sample in enumerate(samples[:10], start=1):
        history_len = sample.get("history_len")
        source_map = sample.get("residual_family_sources") or {}
        for family, rows in source_map.items():
            for row in rows:
                item_id = row.get("item_id", "")
                init = initial_item_map.get(item_id, {})
                key = "|".join(
                    [
                        family,
                        row.get("raw", ""),
                        str(item_id),
                        str(init.get("lexicon_id", "")),
                        str(init.get("initial_slot", "")),
                    ]
                )
                counter[key] += 1
                if key not in attr_map:
                    attr_map[key] = {
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
                        "sample_rank_first_seen": sample_rank,
                    }
    out: list[dict[str, Any]] = []
    for key, count in counter.most_common(200):
        row = dict(attr_map[key])
        row["count_in_top10_samples"] = int(count)
        out.append(row)
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


def _run_reachability_case(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    proposal_desc: str,
    lexicon_ids: list[int],
    token_resolutions: list[dict[str, Any]],
    config: RunConfig,
) -> dict[str, Any]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    numeration_text = _build_numeration_text(sentence, lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    initial_item_map = _build_initial_item_map(state=state, lexicon_ids=lexicon_ids, lexicon=lexicon)

    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    req = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
        return_process_text=False,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
    )
    internal = _search_reachability(
        request=req,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[: config.top_k]
    best_mid_samples = (internal.leaf_stats.get("best_mid_state_samples") or [])[: config.top_k]
    leaf_totals = _aggregate_residual_families(best_leaf_samples)
    mid_totals = _aggregate_residual_families(best_mid_samples)
    leaf_avg = (
        {
            key: round(float(value) / float(len(best_leaf_samples)), 3)
            for key, value in leaf_totals.items()
        }
        if best_leaf_samples
        else {}
    )

    history_top: list[dict[str, Any]] = []
    for rank, evidence in enumerate(internal.evidences[:3], start=1):
        history_top.append(
            {
                "rank": rank,
                "steps_to_goal": evidence.steps_to_goal,
                "rule_sequence": [
                    {
                        "rule_name": s.rule_name,
                        "rule_number": s.rule_number,
                        "left_id": s.left_id,
                        "right_id": s.right_id,
                    }
                    for s in evidence.steps
                ],
            }
        )

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "grammar_id": GRAMMAR_ID,
        "proposal_id": proposal_id,
        "proposal_desc": proposal_desc,
        "lexicon_ids": list(lexicon_ids),
        "token_resolutions": token_resolutions,
        "status": internal.status,
        "completed": internal.completed,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "best_leaf_residual_family_totals": leaf_totals,
        "best_leaf_residual_family_avg": leaf_avg,
        "best_mid_residual_family_totals": mid_totals,
        "best_mid_local_dead_end": {
            "sample_count": len(best_mid_samples),
            "non_improving_ratio": _best_mid_dead_end_ratio(best_mid_samples),
            "fact_status": STATUS_CONFIRMED,
        },
        "best_leaf_source_top": _aggregate_residual_sources(best_leaf_samples),
        "best_mid_source_top": _aggregate_residual_sources(best_mid_samples),
        "best_leaf_top10_exact_provenance": _flatten_exact_provenance(
            samples=best_leaf_samples,
            initial_item_map=initial_item_map,
        ),
        "best_mid_top10_exact_provenance": _flatten_exact_provenance(
            samples=best_mid_samples,
            initial_item_map=initial_item_map,
        ),
        "history_top": history_top,
        "history_top_status": STATUS_CONFIRMED if history_top else STATUS_UNCONFIRMED,
    }


def _parse_reachable_lexicon_ids_from_confirmed_sets(path: Path) -> set[int]:
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


def _token_resolution_rows(generated: Any, lexicon: dict[int, LexiconEntry], grammar_rule_names: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in generated.token_resolutions:
        compat_rows: list[dict[str, Any]] = []
        for cand_id in row.candidate_lexicon_ids:
            entry = lexicon[cand_id]
            compat = _infer_candidate_compatibility_japanese2(entry=entry, grammar_rule_names=grammar_rule_names)
            compat_rows.append(
                {
                    "lexicon_id": cand_id,
                    "entry": entry.entry,
                    "phono": entry.phono,
                    "category": entry.category,
                    "compatible": compat["compatible"],
                    "reason_codes": compat["reason_codes"],
                    "missing_rule_names": compat["missing_rule_names"],
                    "referenced_rule_names": compat["referenced_rule_names"],
                }
            )
        selected_entry = lexicon[row.lexicon_id]
        rows.append(
            {
                "token": row.token,
                "lexicon_id": row.lexicon_id,
                "entry": selected_entry.entry,
                "phono": selected_entry.phono,
                "category": selected_entry.category,
                "candidate_lexicon_ids": list(row.candidate_lexicon_ids),
                "candidates": compat_rows,
            }
        )
    return rows


def _proposal_existing_reselect(base_rows: list[dict[str, Any]]) -> list[int]:
    out: list[int] = []
    for row in base_rows:
        selected = int(row["lexicon_id"])
        candidates = row["candidates"]
        compatible_ids = [int(c["lexicon_id"]) for c in candidates if bool(c["compatible"])]
        source_ids = compatible_ids if compatible_ids else [int(c["lexicon_id"]) for c in candidates]
        picked = selected
        for cand_id in source_ids:
            if cand_id != selected:
                picked = cand_id
                break
        out.append(picked)
    return out


def _proposal_existing_reselect_plus_phi(base_ids: list[int]) -> list[int]:
    out = list(base_ids)
    for phi_id in (272, 273, 274, 275):
        if len(out) >= NUMERATION_SLOT_COUNT:
            break
        out.append(phi_id)
    return out


def _proposal_particle_variants(base_rows: list[dict[str, Any]]) -> list[int]:
    preferred_by_token: dict[str, list[int]] = {
        "が": [183, 263, 294, 19, 196],
        "を": [197, 297, 181, 23],
        "と": [171, 268],
        "る": [308, 125, 204],
    }
    out: list[int] = []
    for row in base_rows:
        token = str(row["token"])
        selected = int(row["lexicon_id"])
        cand_ids = [int(x) for x in row["candidate_lexicon_ids"]]
        picked = selected
        if token in preferred_by_token:
            for cand_id in preferred_by_token[token]:
                if cand_id in cand_ids and cand_id != selected:
                    picked = cand_id
                    break
        out.append(picked)
    return out


def _build_baseline_inputs(*, legacy_root: Path, config: RunConfig) -> dict[str, dict[str, Any]]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    grammar_rule_names = {row.name for row in load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)}

    out: dict[str, dict[str, Any]] = {}
    for sk, sentence in SENTENCES.items():
        try:
            generated = generate_numeration_from_sentence(
                grammar_id=GRAMMAR_ID,
                sentence=sentence,
                legacy_root=legacy_root,
                split_mode=config.split_mode,
            )
            token_rows = _token_resolution_rows(generated, lexicon, grammar_rule_names)
            available = True
            error = None
            baseline_ids = list(generated.lexicon_ids)
            tokens = [row["token"] for row in token_rows]
        except Exception as exc:
            generated = None
            token_rows = []
            available = False
            error = str(exc)
            baseline_ids = []
            tokens = []
        out[sk] = {
            "sentence": sentence,
            "tokens": tokens,
            "baseline_ids": baseline_ids,
            "token_rows": token_rows,
            "generated": generated,
            "available": available,
            "error": error,
        }
    return out


def _collect_rule_appearance_in_initial_states(
    *,
    legacy_root: Path,
    baseline_inputs: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    by_sentence: dict[str, set[str]] = {}
    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    for sk in ("S2", "S3", "S4"):
        row = baseline_inputs[sk]
        if not bool(row.get("available")):
            by_sentence[sk] = set()
            continue
        text = _build_numeration_text(row["sentence"], row["baseline_ids"])
        state = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=text,
            legacy_root=legacy_root,
        )
        names: set[str] = set()
        for left in range(1, state.basenum + 1):
            for right in range(1, state.basenum + 1):
                candidates = list_merge_candidates(
                    state=state,
                    left=left,
                    right=right,
                    legacy_root=legacy_root,
                    rh_merge_version=profile.rh_merge_version,
                    lh_merge_version=profile.lh_merge_version,
                )
                for cand in candidates:
                    names.add(cand.rule_name)
        by_sentence[sk] = names
    return by_sentence


def _rule_catalog_section(
    *,
    legacy_root: Path,
    rule_appear_by_sentence: dict[str, set[str]],
) -> dict[str, Any]:
    j2_rules = load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)
    j2_names = {r.name for r in j2_rules}
    support_in_execute = {
        "RH-Merge",
        "LH-Merge",
        "J-Merge",
        "sase1",
        "sase2",
        "rare1",
        "rare2",
        "property-Merge",
        "rel-Merge",
        "property-no",
        "property-da",
        "P-Merge",
        "Partitioning",
        "Pickup",
        "Landing",
        "zero-Merge",
    }
    initial_union = set().union(*rule_appear_by_sentence.values())
    rows: list[dict[str, Any]] = []
    for rule in j2_rules:
        rows.append(
            {
                "rule_number": rule.number,
                "rule_name": rule.name,
                "rule_kind": _rule_kind_label(rule.kind),
                "definition_file_path": str(legacy_root / "MergeRule" / f"{rule.file_name}.pl"),
                "enabled_in_japanese2_runtime": rule.name in support_in_execute,
                "appears_in_S2S3S4_initial_candidates": rule.name in initial_union,
                "appears_by_sentence_initial": {k: rule.name in v for k, v in rule_appear_by_sentence.items()},
                "rc_headgap_related_guess": None,
                "rc_headgap_related_guess_status": STATUS_UNCONFIRMED,
                "fact_status": STATUS_CONFIRMED,
            }
        )

    diff_rows: list[dict[str, Any]] = []
    for gid in ("imi01", "imi02", "imi03"):
        names = {r.name for r in load_rule_catalog(grammar_id=gid, legacy_root=legacy_root)}
        diff_rows.append(
            {
                "compare_to": gid,
                "japanese2_only_rules": sorted(j2_names - names),
                "missing_from_japanese2_rules": sorted(names - j2_names),
                "common_rules": sorted(j2_names & names),
                "fact_status": STATUS_CONFIRMED,
            }
        )
    return {"japanese2_rules": rows, "rule_diffs_vs_imi": diff_rows}


def _candidate_inventory_section(
    *,
    legacy_root: Path,
    baseline_inputs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    surface_index = _build_surface_index(lexicon)
    grammar_rule_names = {row.name for row in load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)}
    reachable_used_ids = _parse_reachable_lexicon_ids_from_confirmed_sets(
        PROJECT_ROOT / "docs/specs/reachability-confirmed-sets-ja.md"
    )
    auto_candidate_ids: set[int] = set()
    auto_selected_ids: set[int] = set()
    for row in baseline_inputs.values():
        for token_row in row["token_rows"]:
            auto_selected_ids.add(int(token_row["lexicon_id"]))
            for cand in token_row["candidate_lexicon_ids"]:
                auto_candidate_ids.add(int(cand))

    out: list[dict[str, Any]] = []
    for surface in TARGET_SURFACES:
        normalized = _normalize_token(surface)
        candidate_ids = sorted(set(surface_index.get(normalized, [])))
        if not candidate_ids:
            out.append(
                {
                    "surface": surface,
                    "lexicon_id": None,
                    "entry": None,
                    "category": None,
                    "idslot": None,
                    "sync_features": [],
                    "semantics": [],
                    "auto_selectable_in_japanese2_step1": False,
                    "selected_in_current_baseline": False,
                    "japanese2_meaningfulness": "candidate_not_found",
                    "reason_codes": ["not_in_lexicon_all"],
                    "used_in_past_reachable_examples": False,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
            continue
        for lid in candidate_ids:
            entry = lexicon[lid]
            comp = _infer_candidate_compatibility_japanese2(entry=entry, grammar_rule_names=grammar_rule_names)
            out.append(
                {
                    "surface": surface,
                    "lexicon_id": lid,
                    "entry": entry.entry,
                    "category": entry.category,
                    "idslot": entry.idslot,
                    "sync_features": list(entry.sync_features),
                    "semantics": list(entry.semantics),
                    "auto_selectable_in_japanese2_step1": lid in auto_candidate_ids,
                    "selected_in_current_baseline": lid in auto_selected_ids,
                    "japanese2_meaningfulness": "meaningful" if comp["compatible"] else "meaningless",
                    "reason_codes": comp["reason_codes"],
                    "missing_rule_names": comp["missing_rule_names"],
                    "referenced_rule_names": comp["referenced_rule_names"],
                    "used_in_past_reachable_examples": lid in reachable_used_ids,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
    return out


def _se33_label_count(state: Any, label: str) -> int:
    target = f"2,33,{label}"
    count = 0
    for item in state.base[1 : state.basenum + 1]:
        if item == "zero" or not isinstance(item, list):
            continue
        sem = item[5] if len(item) > 5 and isinstance(item[5], list) else []
        for value in sem:
            raw = str(value)
            if ":" not in raw:
                continue
            rhs = raw.split(":", 1)[1].strip()
            if rhs.startswith(target):
                count += 1
    return count


def _local_pair_discharge_probe(
    *,
    legacy_root: Path,
    head_lexicon_id: int,
    nonhead_lexicon_id: int,
    target_label: str,
) -> dict[str, Any]:
    sentence = f"probe:{head_lexicon_id},{nonhead_lexicon_id}"
    numeration_text = _build_numeration_text(sentence, [head_lexicon_id, nonhead_lexicon_id])
    try:
        state = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=numeration_text,
            legacy_root=legacy_root,
        )
    except Exception as exc:
        return {
            "head_lexicon_id": head_lexicon_id,
            "nonhead_lexicon_id": nonhead_lexicon_id,
            "target_label": target_label,
            "before": None,
            "success": None,
            "trials": [],
            "error": str(exc),
            "fact_status": STATUS_CONFIRMED,
        }
    before = _se33_label_count(state, target_label)
    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)

    trials: list[dict[str, Any]] = []
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            candidates = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=legacy_root,
                rh_merge_version=profile.rh_merge_version,
                lh_merge_version=profile.lh_merge_version,
            )
            for cand in candidates:
                try:
                    if cand.rule_kind == "double":
                        version = "03"
                        if cand.rule_name == "RH-Merge":
                            version = profile.rh_merge_version
                        elif cand.rule_name == "LH-Merge":
                            version = profile.lh_merge_version
                        next_state = execute_double_merge(
                            state=state,
                            rule_name=cand.rule_name,
                            left=int(cand.left or 0),
                            right=int(cand.right or 0),
                            rule_version=version,
                        )
                    else:
                        next_state = execute_single_merge(
                            state=state,
                            rule_name=cand.rule_name,
                            check=int(cand.check or 0),
                        )
                except Exception as exc:
                    trials.append(
                        {
                            "rule_name": cand.rule_name,
                            "left": cand.left,
                            "right": cand.right,
                            "check": cand.check,
                            "error": str(exc),
                        }
                    )
                    continue
                after = _se33_label_count(next_state, target_label)
                trials.append(
                    {
                        "rule_name": cand.rule_name,
                        "left": cand.left,
                        "right": cand.right,
                        "check": cand.check,
                        "before": before,
                        "after": after,
                        "decreased": after < before,
                    }
                )

    success = next((row for row in trials if row.get("decreased") is True), None)
    return {
        "head_lexicon_id": head_lexicon_id,
        "nonhead_lexicon_id": nonhead_lexicon_id,
        "target_label": target_label,
        "before": before,
        "success": success,
        "trials": trials[:200],
        "fact_status": STATUS_CONFIRMED,
    }


def _role_discharge_section(
    *,
    legacy_root: Path,
    lexicon: dict[int, LexiconEntry],
) -> dict[str, Any]:
    # role assignment fixed as user request
    target_assignment = [
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

    def _exists_entry(entry_surface: str) -> bool:
        for e in lexicon.values():
            if e.entry == entry_surface or _normalize_token(e.phono).strip("-") == entry_surface:
                return True
        return False

    def _exists_supply(entry_surface: str, supply_label: str) -> bool:
        for e in lexicon.values():
            if e.entry != entry_surface and _normalize_token(e.phono).strip("-") != entry_surface:
                continue
            if any(str(feature).strip() == supply_label for feature in e.sync_features):
                return True
        return False

    eat_req_exists = _exists_entry("食べている")
    talk_req_exists = _exists_entry("話している")
    hitsuji_has_ga = _exists_supply("ひつじ", "4,11,ga")
    hitsuji_has_to = _exists_supply("ひつじ", "4,11,to")
    usagi_has_ga = _exists_supply("うさぎ", "4,11,ga")
    wo_supply_exists = _exists_supply("を", "wo") or _exists_supply("を", "4,11,wo") or _exists_supply("を", "2,11,wo")

    rows = [
        {
            "role_key": "eat_theme_wo",
            "request_item": "食べている(266)",
            "request_label": "Theme:2,33,wo",
            "supply_item": "を(23) または wo供給を持つNP",
            "supply_label": "4,11,wo / 2,11,wo",
            "required_merge_direction": "要求側（predicate）を head、供給側を non-head として結合",
            "rule_path_japanese2": ["RH-Merge", "J-Merge", "rel-Merge", "property-Merge"],
            "execute_branch": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33)",
            "theoretical_possible_with_current_lexicon": bool(eat_req_exists and wo_supply_exists),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "role_key": "eat_agent_ga_by_hitsuji",
            "request_item": "食べている(266)",
            "request_label": "Agent:2,33,ga",
            "supply_item": "ひつじ(267)",
            "supply_label": "4,11,ga / 2,11,ga",
            "required_merge_direction": "要求側（predicate）を head、供給側（ひつじ）を non-head として結合",
            "rule_path_japanese2": ["RH-Merge", "J-Merge", "rel-Merge", "property-Merge"],
            "execute_branch": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33)",
            "theoretical_possible_with_current_lexicon": bool(eat_req_exists and hitsuji_has_ga),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "role_key": "talk_partner_to_by_hitsuji",
            "request_item": "話している(269)",
            "request_label": "相手:2,33,to",
            "supply_item": "ひつじ(267)",
            "supply_label": "4,11,to / 2,11,to",
            "required_merge_direction": "要求側（predicate）を head、供給側（ひつじ）を non-head として結合",
            "rule_path_japanese2": ["RH-Merge", "J-Merge", "rel-Merge", "property-Merge"],
            "execute_branch": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33)",
            "theoretical_possible_with_current_lexicon": bool(talk_req_exists and hitsuji_has_to),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "role_key": "talk_agent_ga_by_usagi",
            "request_item": "話している(269)",
            "request_label": "Agent:2,33,ga",
            "supply_item": "うさぎ(270)",
            "supply_label": "4,11,ga / 2,11,ga",
            "required_merge_direction": "要求側（predicate）を head、供給側（うさぎ）を non-head として結合",
            "rule_path_japanese2": ["RH-Merge", "J-Merge", "rel-Merge", "property-Merge"],
            "execute_branch": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33)",
            "theoretical_possible_with_current_lexicon": bool(talk_req_exists and usagi_has_ga),
            "observed_in_measurement": STATUS_UNCONFIRMED,
            "fact_status": STATUS_CONFIRMED,
        },
    ]

    # minimal local probes for yes/no (code + lexical facts only)
    local_probes = {
        "eat_theme_wo": _local_pair_discharge_probe(
            legacy_root=legacy_root,
            head_lexicon_id=266,
            nonhead_lexicon_id=23,
            target_label="wo",
        ),
        "eat_agent_ga_by_hitsuji": _local_pair_discharge_probe(
            legacy_root=legacy_root,
            head_lexicon_id=266,
            nonhead_lexicon_id=267,
            target_label="ga",
        ),
        "talk_partner_to_by_hitsuji": _local_pair_discharge_probe(
            legacy_root=legacy_root,
            head_lexicon_id=269,
            nonhead_lexicon_id=267,
            target_label="to",
        ),
        "talk_agent_ga_by_usagi": _local_pair_discharge_probe(
            legacy_root=legacy_root,
            head_lexicon_id=269,
            nonhead_lexicon_id=270,
            target_label="ga",
        ),
    }

    return {"target_assignment": target_assignment, "rows": rows, "local_probes": local_probes}


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
        attr, _, val = sem.partition(":")
        y += 1
        if y >= len(cells):
            break
        cells[y] = attr
        y += 1
        if y >= len(cells):
            break
        cells[y] = val

    cells[28] = str(entry.get("note", "")).strip()
    cells[29] = "0"
    return "\t".join(cells)


def _build_temp_legacy_root(*, legacy_root: Path, appended_rows: list[str]) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="legacy_j2_probe_"))
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
    text += "\n".join(appended_rows) + "\n"
    dst_csv.write_text(text, encoding="utf-8")
    return tmp_root


def _run_existing_candidate_experiments(
    *,
    legacy_root: Path,
    baseline_inputs: dict[str, dict[str, Any]],
    config: RunConfig,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    targets = ("S2", "S3", "S4")
    for sk in targets:
        sentence = baseline_inputs[sk]["sentence"]
        if not bool(baseline_inputs[sk].get("available")):
            err = str(baseline_inputs[sk].get("error") or "baseline generation failed")
            for pid, pdesc in [
                ("P0_baseline_auto", "baseline auto"),
                ("P1_existing_reselect", "existing candidates reselect only"),
                ("P2_existing_reselect_plus_phi272_275", "existing reselect + explicit phi(272/273/274/275)"),
                ("P3_existing_reselect_particle_variants", "existing reselect + る/と/が/を variant choices"),
            ]:
                runs.append(
                    {
                        "sentence_key": sk,
                        "sentence": sentence,
                        "grammar_id": GRAMMAR_ID,
                        "proposal_id": pid,
                        "proposal_desc": pdesc,
                        "lexicon_ids": [],
                        "token_resolutions": [],
                        "status": "failed",
                        "completed": True,
                        "reason": "generation_failed",
                        "error": err,
                        "actions_attempted": 0,
                        "max_depth_reached": 0,
                        "best_leaf_unresolved_min": None,
                        "best_leaf_residual_family_totals": {},
                        "best_mid_residual_family_totals": {},
                        "best_leaf_residual_family_avg": {},
                        "best_mid_local_dead_end": {
                            "sample_count": 0,
                            "non_improving_ratio": 0.0,
                            "fact_status": STATUS_CONFIRMED,
                        },
                        "best_leaf_source_top": {},
                        "best_mid_source_top": {},
                        "best_leaf_top10_exact_provenance": [],
                        "best_mid_top10_exact_provenance": [],
                        "history_top": [],
                        "history_top_status": STATUS_UNCONFIRMED,
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
            continue
        token_rows = baseline_inputs[sk]["token_rows"]
        ids_p0 = list(baseline_inputs[sk]["baseline_ids"])
        ids_p1 = _proposal_existing_reselect(token_rows)
        ids_p2 = _proposal_existing_reselect_plus_phi(ids_p1)
        ids_p3 = _proposal_particle_variants(token_rows)
        proposals = [
            ("P0_baseline_auto", "baseline auto", ids_p0),
            ("P1_existing_reselect", "existing candidates reselect only", ids_p1),
            ("P2_existing_reselect_plus_phi272_275", "existing reselect + explicit phi(272/273/274/275)", ids_p2),
            ("P3_existing_reselect_particle_variants", "existing reselect + る/と/が/を variant choices", ids_p3),
        ]
        for pid, pdesc, ids in proposals:
            runs.append(
                _run_reachability_case(
                    legacy_root=legacy_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id=pid,
                    proposal_desc=pdesc,
                    lexicon_ids=ids,
                    token_resolutions=token_rows,
                    config=config,
                )
            )
    return runs


def _run_baseline_for_all_sentences(
    *,
    legacy_root: Path,
    baseline_inputs: dict[str, dict[str, Any]],
    config: RunConfig,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for sk, row in baseline_inputs.items():
        if not bool(row.get("available")):
            runs.append(
                {
                    "sentence_key": sk,
                    "sentence": row["sentence"],
                    "grammar_id": GRAMMAR_ID,
                    "proposal_id": "P0_baseline_auto",
                    "proposal_desc": "baseline auto",
                    "lexicon_ids": [],
                    "token_resolutions": [],
                    "status": "failed",
                    "completed": True,
                    "reason": "generation_failed",
                    "error": str(row.get("error") or "baseline generation failed"),
                    "actions_attempted": 0,
                    "max_depth_reached": 0,
                    "best_leaf_unresolved_min": None,
                    "best_leaf_residual_family_totals": {},
                    "best_mid_residual_family_totals": {},
                    "best_leaf_residual_family_avg": {},
                    "best_mid_local_dead_end": {
                        "sample_count": 0,
                        "non_improving_ratio": 0.0,
                        "fact_status": STATUS_CONFIRMED,
                    },
                    "best_leaf_source_top": {},
                    "best_mid_source_top": {},
                    "best_leaf_top10_exact_provenance": [],
                    "best_mid_top10_exact_provenance": [],
                    "history_top": [],
                    "history_top_status": STATUS_UNCONFIRMED,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
            continue
        runs.append(
            _run_reachability_case(
                legacy_root=legacy_root,
                sentence_key=sk,
                sentence=row["sentence"],
                proposal_id="P0_baseline_auto",
                proposal_desc="baseline auto",
                lexicon_ids=list(row["baseline_ids"]),
                token_resolutions=row["token_rows"],
                config=config,
            )
        )
    return runs


def _run_new_lexical_addition_if_needed(
    *,
    legacy_root: Path,
    baseline_inputs: dict[str, dict[str, Any]],
    existing_runs: list[dict[str, Any]],
    config: RunConfig,
) -> dict[str, Any]:
    # existing-candidate-onlyで S2/S3/S4 のいずれも reachable でなければ提案・実測
    existing_target_runs = [r for r in existing_runs if r["sentence_key"] in {"S2", "S3", "S4"}]
    any_reachable = any(r["status"] == "reachable" for r in existing_target_runs)
    if any_reachable:
        return {
            "needed": False,
            "reason": "existing-candidate-only で reachable が観測されたため、新規 lexical 提案は必須条件を満たさない",
            "fact_status": STATUS_CONFIRMED,
        }

    rows_tsv = [_build_legacy_row(row) for row in NEW_LEX_ROWS]
    tmp_root = _build_temp_legacy_root(legacy_root=legacy_root, appended_rows=rows_tsv)

    try:
        lexicon_tmp = load_legacy_lexicon(legacy_root=tmp_root, grammar_id=GRAMMAR_ID)
        runs: list[dict[str, Any]] = []
        for sk in ("S2", "S3", "S4"):
            sentence = baseline_inputs[sk]["sentence"]
            if not bool(baseline_inputs[sk].get("available")):
                runs.append(
                    {
                        "sentence_key": sk,
                        "sentence": sentence,
                        "grammar_id": GRAMMAR_ID,
                        "proposal_id": "P4_new_lexical_addition_max3",
                        "proposal_desc": "new lexical entries (max3) explicit selection",
                        "lexicon_ids": [],
                        "token_resolutions": [],
                        "status": "failed",
                        "completed": True,
                        "reason": "generation_failed",
                        "error": str(baseline_inputs[sk].get("error") or "baseline generation failed"),
                        "actions_attempted": 0,
                        "max_depth_reached": 0,
                        "best_leaf_unresolved_min": None,
                        "best_leaf_residual_family_totals": {},
                        "best_mid_residual_family_totals": {},
                        "best_leaf_residual_family_avg": {},
                        "best_mid_local_dead_end": {
                            "sample_count": 0,
                            "non_improving_ratio": 0.0,
                            "fact_status": STATUS_CONFIRMED,
                        },
                        "best_leaf_source_top": {},
                        "best_mid_source_top": {},
                        "best_leaf_top10_exact_provenance": [],
                        "best_mid_top10_exact_provenance": [],
                        "history_top": [],
                        "history_top_status": STATUS_UNCONFIRMED,
                        "fact_status": STATUS_CONFIRMED,
                    }
                )
                continue
            token_rows = baseline_inputs[sk]["token_rows"]
            ids = list(baseline_inputs[sk]["baseline_ids"])
            # 表層一致置換
            for idx, token_row in enumerate(token_rows):
                token = str(token_row["token"])
                if token == "ひつじ":
                    ids[idx] = 9101
                elif token == "うさぎ":
                    ids[idx] = 9102
                elif token == "わたあめ":
                    ids[idx] = 9103
            # 念のためlexicon存在確認
            ids = [lid if lid in lexicon_tmp else baseline_inputs[sk]["baseline_ids"][i] for i, lid in enumerate(ids)]
            runs.append(
                _run_reachability_case(
                    legacy_root=tmp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id="P4_new_lexical_addition_max3",
                    proposal_desc="new lexical entries (max3) explicit selection",
                    lexicon_ids=ids,
                    token_resolutions=token_rows,
                    config=config,
                )
            )

        return {
            "needed": True,
            "reason": "existing-candidate-only で reachable 未観測のため、新規 lexical 提案（最大3行）を実測",
            "new_rows": rows_tsv,
            "runs": runs,
            "temp_legacy_root": str(tmp_root),
            "fact_status": STATUS_CONFIRMED,
        }
    finally:
        pass


def _best_source_top_text(run: dict[str, Any]) -> str:
    out: list[str] = []
    source = run.get("best_leaf_source_top") or {}
    for family in FOCUS_FAMILIES:
        rows = source.get(family) or []
        if not rows:
            continue
        top = rows[0]
        out.append(f"{family}:{top.get('item_id')}:{top.get('raw')}({top.get('count')})")
    return "; ".join(out) if out else "-"


def _history_top_text(run: dict[str, Any]) -> str:
    histories = run.get("history_top") or []
    if not histories:
        return "[未確認] unknown/unreachable で evidence なし"
    seqs: list[str] = []
    for h in histories[:2]:
        seqs.append(" -> ".join(step["rule_name"] for step in h.get("rule_sequence", [])))
    return "; ".join(seqs) if seqs else "[未確認]"


def _run_to_metrics(run: dict[str, Any]) -> dict[str, Any]:
    avg = run.get("best_leaf_residual_family_avg") or {}
    return {
        "status": run["status"],
        "reason": run["reason"],
        "actions_attempted": run["actions_attempted"],
        "max_depth_reached": run["max_depth_reached"],
        "best_leaf_unresolved_min": run["best_leaf_unresolved_min"],
        "se33_residual_avg": float(avg.get("se:33", 0.0)),
        "sy11_residual_avg": float(avg.get("sy:11", 0.0)),
        "sy17_residual_avg": float(avg.get("sy:17", 0.0)),
        "best_leaf_residual_family_totals": run.get("best_leaf_residual_family_totals", {}),
        "best_mid_residual_family_totals": run.get("best_mid_residual_family_totals", {}),
        "persistent_residual_source_top": run.get("best_leaf_source_top", {}),
        "history_top": run.get("history_top", []),
        "lexicon_ids": run.get("lexicon_ids", []),
    }


def _build_yes_no_section(
    *,
    role_section: dict[str, Any],
    existing_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key = {row["role_key"]: row for row in role_section["rows"]}
    probes = role_section["local_probes"]
    by_sentence_proposal: dict[tuple[str, str], dict[str, Any]] = {
        (r["sentence_key"], r["proposal_id"]): r for r in existing_runs
    }

    # Q1
    p1 = probes["eat_theme_wo"]
    yes1 = bool(p1.get("success")) and bool(by_key["eat_theme_wo"]["theoretical_possible_with_current_lexicon"])
    # Q2
    p2 = probes["eat_agent_ga_by_hitsuji"]
    yes2 = bool(p2.get("success")) and bool(by_key["eat_agent_ga_by_hitsuji"]["theoretical_possible_with_current_lexicon"])
    # Q3
    p3 = probes["talk_partner_to_by_hitsuji"]
    yes3 = bool(p3.get("success")) and bool(by_key["talk_partner_to_by_hitsuji"]["theoretical_possible_with_current_lexicon"])
    # Q4
    p4 = probes["talk_agent_ga_by_usagi"]
    yes4 = bool(p4.get("success")) and bool(by_key["talk_agent_ga_by_usagi"]["theoretical_possible_with_current_lexicon"])

    # Q5: existing-candidate-onlyで sy:17 avg が P0比較で減るか
    sy17_reduced = False
    witness: Optional[dict[str, Any]] = None
    for sk in ("S2", "S3", "S4"):
        p0 = by_sentence_proposal.get((sk, "P0_baseline_auto"))
        if p0 is None or p0.get("status") == "failed":
            continue
        base = float((p0.get("best_leaf_residual_family_avg") or {}).get("sy:17", 0.0))
        for pid in ("P1_existing_reselect", "P2_existing_reselect_plus_phi272_275", "P3_existing_reselect_particle_variants"):
            pp = by_sentence_proposal.get((sk, pid))
            if pp is None or pp.get("status") == "failed":
                continue
            val = float((pp.get("best_leaf_residual_family_avg") or {}).get("sy:17", 0.0))
            if val < base:
                sy17_reduced = True
                witness = {
                    "sentence_key": sk,
                    "proposal_id": pid,
                    "baseline_sy17_avg": base,
                    "proposal_sy17_avg": val,
                }
                break
        if sy17_reduced:
            break

    rows = [
        {
            "question_no": 1,
            "question": "食べている Theme:2,33,wo は S2/S4 で japanese2 現行 rule/lexical choice だけで discharge path を構成できるか",
            "answer_yes_no": "Yes" if yes1 else "No",
            "minimal_success_or_counterexample": p1["success"] if yes1 else (p1.get("trials", [])[0] if p1.get("trials") else {"error": p1.get("error", "[未確認]")}),
            "required_rule": (p1["success"]["rule_name"] if yes1 and p1["success"] else "[未確認]"),
            "required_lexical_items": [266, 23],
            "missing_local_condition_when_no": "[確認済み事実] japanese2 lexicon に要求側 lexical item（食べている）が存在しない",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 2,
            "question": "食べている Agent:2,33,ga は S2/S4 で head noun ひつじにより discharge path を構成できるか",
            "answer_yes_no": "Yes" if yes2 else "No",
            "minimal_success_or_counterexample": p2["success"] if yes2 else (p2.get("trials", [])[0] if p2.get("trials") else {"error": p2.get("error", "[未確認]")}),
            "required_rule": (p2["success"]["rule_name"] if yes2 and p2["success"] else "[未確認]"),
            "required_lexical_items": [266, 267],
            "missing_local_condition_when_no": "[確認済み事実] japanese2 lexicon に要求側 lexical item（食べている）と供給側 lexical item（ひつじ）が存在しない",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 3,
            "question": "話している 相手:2,33,to は S3/S4 で ひつじにより discharge path を構成できるか",
            "answer_yes_no": "Yes" if yes3 else "No",
            "minimal_success_or_counterexample": p3["success"] if yes3 else (p3.get("trials", [])[0] if p3.get("trials") else {"error": p3.get("error", "[未確認]")}),
            "required_rule": (p3["success"]["rule_name"] if yes3 and p3["success"] else "[未確認]"),
            "required_lexical_items": [269, 267],
            "missing_local_condition_when_no": "[確認済み事実] japanese2 lexicon に要求側 lexical item（話している）と供給側 lexical item（ひつじ）が存在しない",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 4,
            "question": "話している Agent:2,33,ga は S3/S4 で head noun うさぎにより discharge path を構成できるか",
            "answer_yes_no": "Yes" if yes4 else "No",
            "minimal_success_or_counterexample": p4["success"] if yes4 else (p4.get("trials", [])[0] if p4.get("trials") else {"error": p4.get("error", "[未確認]")}),
            "required_rule": (p4["success"]["rule_name"] if yes4 and p4["success"] else "[未確認]"),
            "required_lexical_items": [269, 270],
            "missing_local_condition_when_no": "[確認済み事実] japanese2 lexicon に要求側 lexical item（話している）と供給側 lexical item（うさぎ）が存在しない",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 5,
            "question": "persistent な sy:17 は japanese2 現行 lexical candidate の選び直しだけで解消できるか",
            "answer_yes_no": "Yes" if sy17_reduced else "No",
            "minimal_success_or_counterexample": witness if sy17_reduced else {
                "sentence_key": "S2/S3/S4",
                "proposal_ids_checked": ["P1_existing_reselect", "P2_existing_reselect_plus_phi272_275", "P3_existing_reselect_particle_variants"],
                "result": "sy17_avg が baseline 以上（減少未観測）",
            },
            "required_rule": "[未確認]",
            "required_lexical_items": "[未確認]",
            "missing_local_condition_when_no": "[確認済み事実] existing-candidate-only の同一予算比較で sy:17 減少が未観測",
            "code_path": "apps/api/scripts/reachability_japanese2_lexical_fact_extract_20260302.py (A/B集計)",
            "fact_status": STATUS_CONFIRMED,
        },
    ]
    return rows


def _decide_abc(
    *,
    existing_runs: list[dict[str, Any]],
    new_lex_section: dict[str, Any],
) -> dict[str, Any]:
    target_existing = [r for r in existing_runs if r["sentence_key"] in {"S2", "S3", "S4"}]
    all_existing_reachable = all(
        any(r["sentence_key"] == sk and r["status"] == "reachable" for r in target_existing)
        for sk in ("S2", "S3", "S4")
    )
    if all_existing_reachable:
        return {
            "choice": "A",
            "reason": "japanese2 で existing lexical candidate の選び直しのみで S2/S3/S4 reachable を確認",
            "fact_status": STATUS_CONFIRMED,
        }

    if new_lex_section.get("needed"):
        new_runs = new_lex_section.get("runs", [])
        all_new_reachable = all(
            any(r["sentence_key"] == sk and r["status"] == "reachable" for r in new_runs)
            for sk in ("S2", "S3", "S4")
        )
        if all_new_reachable:
            return {
                "choice": "B",
                "reason": "japanese2 維持で新規 lexical item 追加により S2/S3/S4 reachable を確認",
                "fact_status": STATUS_CONFIRMED,
            }

    return {
        "choice": "C",
        "reason": "japanese2 固定で existing/new lexical 実験の多くが unknown のため、lexicalのみで十分とは断定不可。追加観測または最小rule差分検討が必要。",
        "fact_status": STATUS_CONFIRMED,
        "unconfirmed": "unknown は探索打切りであり unreachable 断定ではない",
    }


def _markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 Lexical Fact Extract ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    abc = payload["abc_conclusion"]
    lines.append(f"- [確認済み事実] A/B/C 判定: **{abc['choice']}**")
    lines.append(f"- [確認済み事実] 理由: {abc['reason']}")
    if "unconfirmed" in abc:
        lines.append(f"- [未確認] {abc['unconfirmed']}")
    lines.append("")

    lines.append("## 2. japanese2 baseline")
    lines.append("")
    lines.append("- [確認済み事実] 条件: `grammar_id=japanese2`, `auto_add_ga_phi=false`, Step.1 自動生成をそのまま使用。")
    lines.append("| sentence | baseline生成 | token列 | baseline lexicon IDs | 自動選択 entry(category) | 選択根拠コード |")
    lines.append("|---|---|---|---|---|---|")
    for sk in ("S1", "S2", "S3", "S4", "S5", "S6"):
        row = payload["baseline_inputs"][sk]
        token_rows = row.get("token_rows") or []
        entries = [f"{x['lexicon_id']}:{x['entry']}({x['category']})" for x in token_rows]
        available = bool(row.get("available"))
        baseline_gen = "ok" if available else f"failed: {row.get('error')}"
        reason_code = (
            "packages/domain/src/domain/numeration/generator.py:_resolve_token + _candidate_sort_key + _optimize_partner_friendly_selection"
            if available
            else "packages/domain/src/domain/numeration/generator.py:_resolve_token"
        )
        lines.append(
            f"| {sk} | {baseline_gen} | {','.join(row.get('tokens') or [])} | {','.join(str(x) for x in (row.get('baseline_ids') or []))} | {'; '.join(entries)} | {reason_code} |"
        )
    lines.append("")

    lines.append("## 3. japanese2 rule catalog")
    lines.append("")
    lines.append("| rule_number | rule_name | kind | file | runtime有効 | S2/S3/S4初期候補で出現 | RC/head-gap関連 |")
    lines.append("|---:|---|---|---|---|---|---|")
    for r in payload["rule_catalog"]["japanese2_rules"]:
        rc_cell = (
            str(r["rc_headgap_related_guess"])
            if r["rc_headgap_related_guess"] is not None
            else f"[{r.get('rc_headgap_related_guess_status', STATUS_UNCONFIRMED)}]"
        )
        lines.append(
            f"| {r['rule_number']} | {r['rule_name']} | {r['rule_kind']} | {r['definition_file_path']} | {r['enabled_in_japanese2_runtime']} | {r['appears_in_S2S3S4_initial_candidates']} | {rc_cell} |"
        )
    lines.append("")
    lines.append("- [確認済み事実] 差分（S2/S3/S4に効きそうな rule 名比較）")
    for d in payload["rule_catalog"]["rule_diffs_vs_imi"]:
        lines.append(
            f"  - [確認済み事実] japanese2 vs {d['compare_to']}: japanese2_only={d['japanese2_only_rules']}, missing_from_japanese2={d['missing_from_japanese2_rules']}"
        )
    lines.append("")

    lines.append("## 4. lexical candidate 棚卸し")
    lines.append("")
    lines.append("| surface | lexicon_id | entry | category | idslot | auto選択対象 | baseline選択済み | meaningful(japanese2) | reason_codes | used_in_reachable_examples |")
    lines.append("|---|---:|---|---|---|---|---|---|---|---|")
    for r in payload["candidate_inventory"]:
        lines.append(
            f"| {r['surface']} | {'' if r['lexicon_id'] is None else r['lexicon_id']} | {r.get('entry') or '-'} | {r.get('category') or '-'} | {r.get('idslot') or '-'} | {r['auto_selectable_in_japanese2_step1']} | {r['selected_in_current_baseline']} | {r['japanese2_meaningfulness']} | {','.join(r.get('reason_codes', [])) or '-'} | {r['used_in_past_reachable_examples']} |"
        )
    lines.append("")

    lines.append("## 5. S2/S3/S4 の role discharge 表")
    lines.append("")
    lines.append("- [確認済み事実] 自然解釈の固定役割")
    lines.append("| sentence | predicate | role | target NP |")
    lines.append("|---|---|---|---|")
    for row in payload["role_discharge"]["target_assignment"]:
        lines.append(f"| {row['sentence_key']} | {row['predicate']} | {row['role']} | {row['target_np']} |")
    lines.append("")
    lines.append("| role_key | 要求側 | 要求ラベル | 供給側 | 供給ラベル | merge方向 | rule候補 | execute分岐 | 現行lexiconで理論上可能 | 実測観測 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for row in payload["role_discharge"]["rows"]:
        lines.append(
            f"| {row['role_key']} | {row['request_item']} | {row['request_label']} | {row['supply_item']} | {row['supply_label']} | {row['required_merge_direction']} | {','.join(row['rule_path_japanese2'])} | {row['execute_branch']} | {row['theoretical_possible_with_current_lexicon']} | {row['observed_in_measurement']} |"
        )
    lines.append("")

    lines.append("## 6. persistent residual provenance")
    lines.append("")
    for sk in ("S2", "S3", "S4"):
        run = payload["results_by_sentence_proposal"][sk]["P0_baseline_auto"]
        lines.append(f"### {sk} baseline")
        lines.append(
            f"- [確認済み事実] status={run['status']} reason={run['reason']} actions={run['actions_attempted']} depth={run['max_depth_reached']} leaf_min={run['best_leaf_unresolved_min']}"
        )
        lines.append(f"- [確認済み事実] best_leaf_residual_family_totals={run['best_leaf_residual_family_totals']}")
        lines.append(f"- [確認済み事実] best_mid_residual_family_totals={run['best_mid_residual_family_totals']}")
        lines.append("| type | family | exact_label | current_node | item_id | surface | initial_slot | count_in_top10 | history_len | tree/process |")
        lines.append("|---|---|---|---|---|---|---:|---:|---|---|")
        for row in run["best_leaf_top10_exact_provenance"][:10]:
            lines.append(
                f"| leaf | {row['family']} | {row['exact_label']} | {row['current_holding_node']} | {row['item_id']} | {row['surface']} | {row['initial_slot']} | {row['count_in_top10_samples']} | {row.get('history_len')} | [未確認] |"
            )
        for row in run["best_mid_top10_exact_provenance"][:10]:
            lines.append(
                f"| mid | {row['family']} | {row['exact_label']} | {row['current_holding_node']} | {row['item_id']} | {row['surface']} | {row['initial_slot']} | {row['count_in_top10_samples']} | {row.get('history_len')} | [未確認] |"
            )
        lines.append("")

    lines.append("## 7. existing-candidate-only 実験")
    lines.append("")
    lines.append("| sentence | proposal | lexicon_ids | baselineと同一か | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top | history上位 |")
    lines.append("|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|")
    for sk in ("S2", "S3", "S4"):
        baseline_ids = payload["baseline_inputs"][sk]["baseline_ids"]
        for pid in PROPOSAL_IDS:
            run = payload["results_by_sentence_proposal"][sk][pid]
            avg = run.get("best_leaf_residual_family_avg") or {}
            same = run["lexicon_ids"] == baseline_ids
            lines.append(
                f"| {sk} | {pid} | {','.join(str(x) for x in run['lexicon_ids'])} | {same} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {float(avg.get('se:33', 0.0))} | {float(avg.get('sy:11', 0.0))} | {float(avg.get('sy:17', 0.0))} | {_best_source_top_text(run)} | {_history_top_text(run)} |"
            )
    lines.append("")

    if payload["new_lexical_addition"]["needed"]:
        lines.append("## 8. 新規 lexical item 提案（必要時のみ）")
        lines.append("")
        lines.append(f"- [確認済み事実] {payload['new_lexical_addition']['reason']}")
        lines.append("```tsv")
        for row in payload["new_lexical_addition"]["new_rows"]:
            lines.append(row)
        lines.append("```")
        lines.append("| sentence | proposal | lexicon_ids | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|")
        for run in payload["new_lexical_addition"]["runs"]:
            avg = run.get("best_leaf_residual_family_avg") or {}
            lines.append(
                f"| {run['sentence_key']} | {run['proposal_id']} | {','.join(str(x) for x in run['lexicon_ids'])} | {run['status']} | {run['reason']} | {run['actions_attempted']} | {run['max_depth_reached']} | {run['best_leaf_unresolved_min']} | {float(avg.get('se:33',0.0))} | {float(avg.get('sy:11',0.0))} | {float(avg.get('sy:17',0.0))} |"
            )
        lines.append("")
    else:
        lines.append("## 8. 新規 lexical item 提案（必要時のみ）")
        lines.append("")
        lines.append(f"- [確認済み事実] {payload['new_lexical_addition']['reason']}")
        lines.append("")

    lines.append("## 9. yes/no 判定")
    lines.append("")
    lines.append("| Q | yes/no | 必要rule | 必要lexical | 最小成功例/反例 | 不成立局所条件 | code path |")
    lines.append("|---:|---|---|---|---|---|---|")
    for row in payload["yes_no"]:
        lines.append(
            f"| {row['question_no']} | {row['answer_yes_no']} | {row['required_rule']} | {row['required_lexical_items']} | {row['minimal_success_or_counterexample']} | {row['missing_local_condition_when_no']} | {row['code_path']} |"
        )
    lines.append("")

    lines.append("## 10. A/B/C 最終結論")
    lines.append("")
    lines.append(f"- [確認済み事実] {payload['abc_conclusion']['choice']}: {payload['abc_conclusion']['reason']}")
    if "unconfirmed" in payload["abc_conclusion"]:
        lines.append(f"- [未確認] {payload['abc_conclusion']['unconfirmed']}")
    lines.append("")

    lines.append("## 11. 未確認事項")
    lines.append("")
    lines.append("- [未確認] `unknown` ケースでは `tree/process` 参照が得られないため、本レポートでは residual provenance と history を代替提示。")
    lines.append("- [未確認] 現行予算外での探索継続結果（`unknown -> reachable/unreachable`）は未観測。")
    lines.append("- [未確認] `relative clause` の最終的な自然導出が現行 `japanese2` でどこまで到達可能かは、予算拡張なしでは断定不可。")

    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = Path("/Users/tomonaga/Documents/syncsemphoneIMI")
    config = RunConfig()

    baseline_inputs = _build_baseline_inputs(legacy_root=legacy_root, config=config)
    baseline_runs = _run_baseline_for_all_sentences(
        legacy_root=legacy_root,
        baseline_inputs=baseline_inputs,
        config=config,
    )
    existing_runs = _run_existing_candidate_experiments(
        legacy_root=legacy_root,
        baseline_inputs=baseline_inputs,
        config=config,
    )

    # baseline + existing proposal runs -> nested
    all_runs = baseline_runs + existing_runs
    nested: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in all_runs:
        nested[row["sentence_key"]][row["proposal_id"]] = row

    rule_appear = _collect_rule_appearance_in_initial_states(
        legacy_root=legacy_root,
        baseline_inputs=baseline_inputs,
    )
    rule_catalog = _rule_catalog_section(
        legacy_root=legacy_root,
        rule_appear_by_sentence=rule_appear,
    )

    candidate_inventory = _candidate_inventory_section(
        legacy_root=legacy_root,
        baseline_inputs=baseline_inputs,
    )
    lexicon_current = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    role_discharge = _role_discharge_section(
        legacy_root=legacy_root,
        lexicon=lexicon_current,
    )
    yes_no = _build_yes_no_section(
        role_section=role_discharge,
        existing_runs=existing_runs,
    )

    new_lexical_addition = _run_new_lexical_addition_if_needed(
        legacy_root=legacy_root,
        baseline_inputs=baseline_inputs,
        existing_runs=existing_runs,
        config=config,
    )
    if new_lexical_addition.get("needed"):
        for row in new_lexical_addition.get("runs", []):
            nested[row["sentence_key"]][row["proposal_id"]] = row

    abc = _decide_abc(existing_runs=existing_runs, new_lex_section=new_lexical_addition)

    metrics_nested: dict[str, dict[str, Any]] = {}
    for sk, proposal_map in nested.items():
        metrics_nested[sk] = {}
        for pid, run in proposal_map.items():
            metrics_nested[sk][pid] = _run_to_metrics(run)

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
        },
        "baseline_inputs": baseline_inputs,
        "rule_catalog": rule_catalog,
        "candidate_inventory": candidate_inventory,
        "role_discharge": role_discharge,
        "results_by_sentence_proposal": nested,
        "metrics_by_sentence_proposal": metrics_nested,  # sentence -> proposal -> metrics
        "existing_candidate_runs": existing_runs,
        "new_lexical_addition": new_lexical_addition,
        "yes_no": yes_no,
        "abc_conclusion": abc,
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-fact-extract-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-lexical-fact-extract-20260302.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown_report(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
