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


def main() -> None:
    args = _parse_args()
    legacy_root = args.legacy_root.resolve()
    numeration_text = (legacy_root / args.numeration_relpath).read_text(encoding="utf-8")

    state = build_initial_derivation_state(
        grammar_id=args.grammar_id,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
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
        "best_leaf_samples": best_leaf_samples,
        "best_mid_state_samples": best_mid_samples,
        "aggregates": {
            "best_leaf_residual_family_totals": _aggregate_residual_families(best_leaf_samples),
            "best_mid_residual_family_totals": _aggregate_residual_families(best_mid_samples),
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
