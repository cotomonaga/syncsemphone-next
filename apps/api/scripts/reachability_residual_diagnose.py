#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
import sys
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _search_reachability,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Residual diagnostics for reachability search")
    parser.add_argument("--legacy-root", type=Path, default=Path("/Users/tomonaga/Documents/syncsemphoneIMI"))
    parser.add_argument("--numeration-relpath", default="imi01/set-numeration/1608131500.num")
    parser.add_argument("--grammar-id", default="imi01")
    parser.add_argument("--budget-seconds", type=float, default=600.0)
    parser.add_argument("--max-nodes", type=int, default=100000)
    parser.add_argument("--max-depth", type=int, default=28)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("docs/specs/reachability-residual-diagnose-20260301.json"),
    )
    return parser.parse_args()


def _aggregate_residual_families(samples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for sample in samples:
        for key, value in (sample.get("residual_family_counts") or {}).items():
            counter[key] += int(value)
    return dict(sorted(counter.items(), key=lambda row: (-row[1], row[0])))


def _local_dead_end_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        return {
            "sample_count": 0,
            "non_improving_count": 0,
            "non_improving_ratio": 0.0,
        }
    non_improving = 0
    for sample in samples:
        min_delta = sample.get("min_delta_unresolved")
        if min_delta is None:
            continue
        if int(min_delta) >= 0:
            non_improving += 1
    return {
        "sample_count": len(samples),
        "non_improving_count": non_improving,
        "non_improving_ratio": round(float(non_improving) / float(len(samples)), 6),
    }


def _parse_initial_numeration_ids(numeration_text: str) -> list[int]:
    lines = numeration_text.splitlines()
    if not lines:
        return []
    cols = lines[0].split("\t")
    ids: list[int] = []
    for token in cols[1:]:
        raw = token.strip()
        if raw == "":
            continue
        try:
            ids.append(int(raw))
        except ValueError:
            continue
    return ids


def _load_lexicon_lookup(legacy_root: Path) -> dict[int, dict[str, str]]:
    lexicon_csv = legacy_root / "lexicon-all.csv"
    lookup: dict[int, dict[str, str]] = {}
    for line in lexicon_csv.read_text(encoding="utf-8").splitlines():
        if line.strip() == "":
            continue
        cols = line.split("\t")
        try:
            lid = int(cols[0].strip())
        except Exception:
            continue
        lookup[lid] = {
            "entry": cols[1].strip() if len(cols) > 1 else "",
            "surface": cols[2].strip() if len(cols) > 2 else "",
            "category": cols[3].strip() if len(cols) > 3 else "",
        }
    return lookup


def _feature_families_for_item(item: object) -> list[str]:
    families: list[str] = []
    if item == "zero" or not isinstance(item, list):
        return families
    sy_values = item[3] if len(item) > 3 and isinstance(item[3], list) else []
    se_values = item[5] if len(item) > 5 and isinstance(item[5], list) else []
    for feature in sy_values:
        raw = str(feature).strip()
        if raw == "":
            continue
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) >= 2 and parts[1].isdigit():
            families.append(f"sy:{parts[1]}")
    for semantic in se_values:
        raw = str(semantic)
        if ":" not in raw:
            continue
        rhs = raw.split(":", 1)[1].strip()
        parts = [part.strip() for part in rhs.split(",")]
        if len(parts) >= 2 and parts[1].isdigit():
            families.append(f"se:{parts[1]}")
    return sorted(set(families))


def _build_initial_slot_map(
    *,
    state: Any,
    numeration_ids: list[int],
    lexicon_lookup: dict[int, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot_index in range(1, state.basenum + 1):
        item = state.base[slot_index]
        if item == "zero" or not isinstance(item, list):
            continue
        lexicon_id = numeration_ids[slot_index - 1] if slot_index - 1 < len(numeration_ids) else None
        lex = lexicon_lookup.get(lexicon_id or -1, {})
        rows.append(
            {
                "slot_index": slot_index,
                "lexicon_id": lexicon_id,
                "entry": lex.get("entry", ""),
                "surface": lex.get("surface", ""),
                "lexicon_category": lex.get("category", ""),
                "item_id": str(item[0]) if len(item) > 0 else "",
                "state_category": str(item[1]) if len(item) > 1 else "",
                "phono": "" if len(item) <= 6 or item[6] is None else str(item[6]),
                "families": _feature_families_for_item(item),
            }
        )
    return rows


def _aggregate_residual_sources(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_family: dict[str, Counter[str]] = {}
    attr_by_key: dict[str, dict[str, str]] = {}
    for sample in samples:
        src = sample.get("residual_family_sources") or {}
        for family, rows in src.items():
            counter = by_family.setdefault(family, Counter())
            for row in rows:
                key = "|".join(
                    [
                        row.get("item_id", ""),
                        row.get("phono", ""),
                        row.get("category", ""),
                        row.get("raw", ""),
                    ]
                )
                counter[key] += 1
                attr_by_key[key] = {
                    "item_id": row.get("item_id", ""),
                    "phono": row.get("phono", ""),
                    "category": row.get("category", ""),
                    "raw": row.get("raw", ""),
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, counter in sorted(by_family.items(), key=lambda row: row[0]):
        rows: list[dict[str, Any]] = []
        for key, count in counter.most_common():
            attrs = attr_by_key.get(key, {})
            rows.append(
                {
                    "count": int(count),
                    "item_id": attrs.get("item_id", ""),
                    "phono": attrs.get("phono", ""),
                    "category": attrs.get("category", ""),
                    "raw": attrs.get("raw", ""),
                }
            )
        out[family] = rows
    return out


def main() -> None:
    args = _parse_args()
    legacy_root = args.legacy_root.resolve()
    numeration_text = (legacy_root / args.numeration_relpath).read_text(encoding="utf-8")

    state = build_initial_derivation_state(
        grammar_id=args.grammar_id,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    numeration_ids = _parse_initial_numeration_ids(numeration_text)
    lexicon_lookup = _load_lexicon_lookup(legacy_root)
    profile = resolve_rule_versions(
        profile=get_grammar_profile(args.grammar_id),
        legacy_root=legacy_root,
    )

    request = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
        offset=0,
        limit=10,
        search_signature_mode="structural",
        budget_seconds=args.budget_seconds,
        max_nodes=args.max_nodes,
        max_depth=args.max_depth,
        return_process_text=False,
    )

    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
        imi_fast_path_enabled=True,
        global_deficit_ordering_enabled=True,
    )

    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[: args.top_k]
    best_mid_samples = (internal.leaf_stats.get("best_mid_state_samples") or [])[: args.top_k]

    payload = {
        "generated_at": str(date.today()),
        "grammar_id": args.grammar_id,
        "numeration_relpath": args.numeration_relpath,
        "budget_seconds": args.budget_seconds,
        "max_nodes": args.max_nodes,
        "max_depth": args.max_depth,
        "top_k": args.top_k,
        "status": internal.status,
        "completed": internal.completed,
        "reason": internal.reason,
        "metrics": {
            "actions_attempted": internal.actions_attempted,
            "expanded_nodes": internal.expanded_nodes,
            "generated_nodes": internal.generated_nodes,
            "max_depth_reached": internal.max_depth_reached,
            "cache_stats": internal.cache_stats,
            "timing_ms": internal.timing_ms,
        },
        "leaf_stats": {
            "count": internal.leaf_stats.get("count"),
            "unresolved_min": internal.leaf_stats.get("unresolved_min"),
            "unresolved_max": internal.leaf_stats.get("unresolved_max"),
            "unresolved_histogram": internal.leaf_stats.get("unresolved_histogram"),
        },
        "initial_slots": _build_initial_slot_map(
            state=state,
            numeration_ids=numeration_ids,
            lexicon_lookup=lexicon_lookup,
        ),
        "best_leaf_samples": best_leaf_samples,
        "best_mid_state_samples": best_mid_samples,
        "aggregates": {
            "best_leaf_residual_family_totals": _aggregate_residual_families(best_leaf_samples),
            "best_mid_residual_family_totals": _aggregate_residual_families(best_mid_samples),
            "best_leaf_residual_source_totals": _aggregate_residual_sources(best_leaf_samples),
            "best_mid_residual_source_totals": _aggregate_residual_sources(best_mid_samples),
            "best_mid_local_dead_end": _local_dead_end_summary(best_mid_samples),
        },
    }

    out_json = args.out_json
    if not out_json.is_absolute():
        out_json = (PROJECT_ROOT / out_json).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_json)


if __name__ == "__main__":
    main()
