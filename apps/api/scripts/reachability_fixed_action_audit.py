#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (
    DerivationReachabilityRequest,
    _resolve_reachability_budget_seconds,
    _resolve_reachability_max_depth,
    _resolve_reachability_max_nodes,
    _search_reachability,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions
from domain.numeration.init_builder import build_initial_derivation_state


@dataclass(frozen=True)
class RunConfig:
    label: str
    global_deficit_ordering_enabled: bool
    max_nodes: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed-action reachability A/B audit.")
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=Path("/Users/tomonaga/Documents/syncsemphoneIMI"),
        help="Legacy root directory",
    )
    parser.add_argument(
        "--numeration-relpath",
        default="imi01/set-numeration/1608131500.num",
        help="Relative path to .num file under legacy root",
    )
    parser.add_argument(
        "--grammar-id",
        default="imi01",
        help="Grammar id",
    )
    parser.add_argument(
        "--search-signature-mode",
        default="structural",
        choices=["structural", "packed"],
        help="Search signature mode",
    )
    parser.add_argument(
        "--budgets",
        default="25000,50000,100000",
        help="Comma-separated max_nodes budgets",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=28,
        help="Search max depth",
    )
    parser.add_argument(
        "--budget-seconds",
        type=float,
        default=600.0,
        help="Time budget per run (seconds)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("docs/specs/reachability-fixed-action-audit-20260301.json"),
        help="Output JSON path",
    )
    return parser.parse_args()


def _normalize_partner_residuals(sample: dict[str, Any]) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for label, count in (sample.get("deficit_33") or {}).items():
        normalized[f"33:{label}"] = int(count)
    for label, count in (sample.get("deficit_25") or {}).items():
        normalized[f"25:{label}"] = int(count)
    return dict(sorted(normalized.items(), key=lambda row: row[0]))


def _run_case(
    *,
    config: RunConfig,
    grammar_id: str,
    numeration_text: str,
    legacy_root: Path,
    search_signature_mode: str,
    max_depth: int,
    budget_seconds: float,
) -> dict[str, Any]:
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
        max_evidences=20,
        offset=0,
        limit=10,
        search_signature_mode=search_signature_mode,
        budget_seconds=budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=max_depth,
        return_process_text=False,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode=search_signature_mode,
        imi_fast_path_enabled=True,
        global_deficit_ordering_enabled=config.global_deficit_ordering_enabled,
    )

    best_sample = (internal.leaf_stats.get("best_samples") or [{}])[0]
    layer_rows = internal.layer_stats.values()
    descriptors_emitted_total = sum(int(row.get("descriptors_emitted", 0)) for row in layer_rows)
    children_materialized_total = sum(int(row.get("children_materialized", 0)) for row in layer_rows)
    children_finalized_total = sum(int(row.get("children_finalized", 0)) for row in layer_rows)

    def _ratio(value_ms: float, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(float(value_ms) / float(denominator), 6)

    return {
        "label": config.label,
        "global_deficit_ordering_enabled": config.global_deficit_ordering_enabled,
        "max_nodes": _resolve_reachability_max_nodes(config.max_nodes),
        "budget_seconds": _resolve_reachability_budget_seconds(budget_seconds),
        "max_depth": _resolve_reachability_max_depth(max_depth, state=state),
        "status": internal.status,
        "completed": internal.completed,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "expanded_nodes": internal.expanded_nodes,
        "generated_nodes": internal.generated_nodes,
        "max_depth_reached": internal.max_depth_reached,
        "max_frontier": internal.max_frontier,
        "timing_ms": internal.timing_ms,
        "cache_stats": internal.cache_stats,
        "leaf_stats": internal.leaf_stats,
        "best_sample_normalized_partner_residuals": _normalize_partner_residuals(best_sample),
        "aggregates": {
            "descriptors_emitted_total": descriptors_emitted_total,
            "children_materialized_total": children_materialized_total,
            "children_finalized_total": children_finalized_total,
            "rule_expand_per_descriptor_ms": _ratio(
                float(internal.timing_ms.get("rule_expand", 0.0)),
                descriptors_emitted_total,
            ),
            "execute_per_materialized_ms": _ratio(
                float(internal.timing_ms.get("execute_double_merge", 0.0)),
                children_materialized_total,
            ),
            "post_filter_per_finalized_ms": _ratio(
                float(internal.timing_ms.get("post_filter", 0.0)),
                children_finalized_total,
            ),
        },
    }


def main() -> None:
    args = _parse_args()
    legacy_root = args.legacy_root.resolve()
    numeration_text = (legacy_root / args.numeration_relpath).read_text(encoding="utf-8")
    budgets = [int(raw.strip()) for raw in args.budgets.split(",") if raw.strip() != ""]
    runs: list[dict[str, Any]] = []
    for budget in budgets:
        runs.append(
            _run_case(
                config=RunConfig(
                    label=f"fixed_action_ordering_off_{budget}",
                    global_deficit_ordering_enabled=False,
                    max_nodes=budget,
                ),
                grammar_id=args.grammar_id,
                numeration_text=numeration_text,
                legacy_root=legacy_root,
                search_signature_mode=args.search_signature_mode,
                max_depth=args.max_depth,
                budget_seconds=args.budget_seconds,
            )
        )
        runs.append(
            _run_case(
                config=RunConfig(
                    label=f"fixed_action_ordering_on_{budget}",
                    global_deficit_ordering_enabled=True,
                    max_nodes=budget,
                ),
                grammar_id=args.grammar_id,
                numeration_text=numeration_text,
                legacy_root=legacy_root,
                search_signature_mode=args.search_signature_mode,
                max_depth=args.max_depth,
                budget_seconds=args.budget_seconds,
            )
        )

    out_json = args.out_json
    if not out_json.is_absolute():
        out_json = (PROJECT_ROOT / out_json).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": str(date.today()),
        "legacy_root": str(legacy_root),
        "grammar_id": args.grammar_id,
        "numeration_relpath": args.numeration_relpath,
        "search_signature_mode": args.search_signature_mode,
        "runs": runs,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_json)


if __name__ == "__main__":
    main()
