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
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _collect_residual_family_counts,
    _search_reachability,
)
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.numeration.generator import generate_numeration_from_sentence  # noqa: E402
from domain.numeration.init_builder import build_initial_derivation_state  # noqa: E402
from domain.numeration.parser import NUMERATION_SLOT_COUNT  # noqa: E402


SENTENCE_CASES: list[tuple[str, str]] = [
    ("S1", "うさぎがいる"),
    ("S2", "わたあめを食べているひつじがいる"),
    ("S3", "ひつじと話しているうさぎがいる"),
    ("S4", "ふわふわしたわたあめを食べているひつじと話しているうさぎがいる"),
]

FOCUS_FAMILIES = ("se:33", "sy:11", "sy:17")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reachability discharge matrix audit")
    parser.add_argument("--legacy-root", type=Path, default=Path("/Users/tomonaga/Documents/syncsemphoneIMI"))
    parser.add_argument("--grammar-ids", default="imi01,imi02,imi03")
    parser.add_argument("--split-mode", default="A")
    parser.add_argument("--budget-seconds", type=float, default=120.0)
    parser.add_argument("--max-nodes", type=int, default=40000)
    parser.add_argument("--max-depth", type=int, default=28)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--phi-plus-count", type=int, default=2)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("docs/specs/reachability-discharge-matrix-20260302.json"),
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("docs/specs/reachability-discharge-matrix-20260302.md"),
    )
    return parser.parse_args()


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


def _focus_text(mapping: dict[str, int | float]) -> str:
    return ", ".join(f"{name}={mapping.get(name, 0)}" for name in FOCUS_FAMILIES)


def _run_case(
    *,
    grammar_id: str,
    sentence_key: str,
    sentence: str,
    phi_mode: str,
    phi_plus_count: int,
    split_mode: str,
    budget_seconds: float,
    max_nodes: int,
    max_depth: int,
    top_k: int,
    legacy_root: Path,
) -> dict[str, Any]:
    generated = generate_numeration_from_sentence(
        grammar_id=grammar_id,
        sentence=sentence,
        legacy_root=legacy_root,
        split_mode=split_mode,
        auto_add_ga_phi=False,
    )
    lexicon_ids = list(generated.lexicon_ids)
    if phi_mode == "plus2" and phi_plus_count > 0:
        space = max(0, NUMERATION_SLOT_COUNT - len(lexicon_ids))
        for _ in range(min(phi_plus_count, space)):
            lexicon_ids.append(309)
    numeration_text = _build_numeration_text(memo=sentence, lexicon_ids=lexicon_ids)

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
        return_process_text=False,
        budget_seconds=budget_seconds,
        max_nodes=max_nodes,
        max_depth=max_depth,
    )
    internal = _search_reachability(
        request=request,
        legacy_root=legacy_root,
        rh_version=profile.rh_merge_version,
        lh_version=profile.lh_merge_version,
        search_signature_mode="structural",
    )

    initial_family_counts = _collect_residual_family_counts(state)
    best_leaf_samples = (internal.leaf_stats.get("best_samples") or [])[:top_k]
    residual_totals = _aggregate_residual_families(best_leaf_samples)
    residual_avg = {
        key: round(float(value) / float(len(best_leaf_samples)), 3)
        for key, value in residual_totals.items()
    } if best_leaf_samples else {}
    source_totals = _aggregate_residual_sources(best_leaf_samples)

    discharge_table: list[dict[str, Any]] = []
    for family in FOCUS_FAMILIES:
        initial_count = int(initial_family_counts.get(family, 0))
        residual_average = float(residual_avg.get(family, 0.0))
        discharge_table.append(
            {
                "family": family,
                "initial_count": initial_count,
                "residual_avg_per_best_leaf": residual_average,
                "estimated_discharged_per_path": round(max(float(initial_count) - residual_average, 0.0), 3),
            }
        )

    return {
        "sentence_key": sentence_key,
        "sentence": sentence,
        "grammar_id": grammar_id,
        "phi_mode": phi_mode,
        "lexicon_ids": lexicon_ids,
        "status": internal.status,
        "completed": internal.completed,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "leaf_unresolved_max": internal.leaf_stats.get("unresolved_max"),
        "initial_family_counts": initial_family_counts,
        "best_leaf_residual_family_totals": residual_totals,
        "best_leaf_residual_family_avg": residual_avg,
        "best_leaf_residual_source_totals": source_totals,
        "discharge_table": discharge_table,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Reachability discharge matrix（{payload['generated_at']}）")
    lines.append("")
    lines.append("条件:")
    lines.append(f"- grammars: `{', '.join(payload['grammar_ids'])}`")
    lines.append(f"- split_mode: `{payload['split_mode']}`")
    lines.append(f"- budget_seconds: `{payload['budget_seconds']}`")
    lines.append(f"- max_nodes: `{payload['max_nodes']}`")
    lines.append(f"- max_depth: `{payload['max_depth']}`")
    lines.append(f"- top_k(best_leaf): `{payload['top_k']}`")
    lines.append(f"- phi_mode: `none`, `plus2`（`309` を +2）")
    lines.append("")
    lines.append("注記:")
    lines.append("- `discharge_table` の `estimated_discharged_per_path` は、`initial_count - best_leaf平均残差` の観測値です（証明値ではありません）。")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("| sentence | grammar | phi | status | reason | actions | depth | leaf_min | residual(avg) |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---|")
    for row in payload["results"]:
        lines.append(
            "| {sentence_key} | {grammar_id} | {phi_mode} | {status} | {reason} | {actions} | {depth} | {leaf_min} | {residual} |".format(
                sentence_key=row["sentence_key"],
                grammar_id=row["grammar_id"],
                phi_mode=row["phi_mode"],
                status=row["status"],
                reason=row["reason"],
                actions=row["actions_attempted"],
                depth=row["max_depth_reached"],
                leaf_min=row["leaf_unresolved_min"],
                residual=_focus_text(row.get("best_leaf_residual_family_avg") or {}),
            )
        )

    lines.append("")
    lines.append("## 詳細（family discharge + source）")
    for row in payload["results"]:
        lines.append("")
        lines.append(
            f"### {row['sentence_key']} / {row['grammar_id']} / {row['phi_mode']} ({row['status']}, {row['reason']})"
        )
        lines.append(f"- sentence: `{row['sentence']}`")
        lines.append(f"- lexicon_ids: `{row['lexicon_ids']}`")
        lines.append(f"- initial families: `{_focus_text(row.get('initial_family_counts') or {})}`")
        lines.append(f"- residual(avg): `{_focus_text(row.get('best_leaf_residual_family_avg') or {})}`")
        lines.append("")
        lines.append("| family | initial | residual(avg) | estimated discharged |")
        lines.append("|---|---:|---:|---:|")
        for discharge in row["discharge_table"]:
            lines.append(
                f"| {discharge['family']} | {discharge['initial_count']} | {discharge['residual_avg_per_best_leaf']} | {discharge['estimated_discharged_per_path']} |"
            )
        lines.append("")
        source_totals = row.get("best_leaf_residual_source_totals") or {}
        if not source_totals:
            lines.append("- residual source totals: (none)")
        else:
            for family in FOCUS_FAMILIES:
                family_rows = source_totals.get(family) or []
                if not family_rows:
                    continue
                lines.append(f"- {family} source top:")
                for source in family_rows[:5]:
                    lines.append(
                        "  - `{item}` {raw} ({count})".format(
                            item=source.get("item_id", ""),
                            raw=source.get("raw", ""),
                            count=source.get("count", 0),
                        )
                    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    legacy_root = args.legacy_root.resolve()
    grammar_ids = [token.strip() for token in args.grammar_ids.split(",") if token.strip() != ""]
    phi_modes = ["none", "plus2"]

    results: list[dict[str, Any]] = []
    for sentence_key, sentence in SENTENCE_CASES:
        for grammar_id in grammar_ids:
            for phi_mode in phi_modes:
                try:
                    row = _run_case(
                        grammar_id=grammar_id,
                        sentence_key=sentence_key,
                        sentence=sentence,
                        phi_mode=phi_mode,
                        phi_plus_count=max(0, int(args.phi_plus_count)),
                        split_mode=args.split_mode,
                        budget_seconds=float(args.budget_seconds),
                        max_nodes=int(args.max_nodes),
                        max_depth=int(args.max_depth),
                        top_k=max(1, int(args.top_k)),
                        legacy_root=legacy_root,
                    )
                except Exception as exc:
                    row = {
                        "sentence_key": sentence_key,
                        "sentence": sentence,
                        "grammar_id": grammar_id,
                        "phi_mode": phi_mode,
                        "status": "failed",
                        "completed": False,
                        "reason": "failed",
                        "error": str(exc),
                    }
                results.append(row)

    payload = {
        "generated_at": date.today().isoformat(),
        "legacy_root": str(legacy_root),
        "grammar_ids": grammar_ids,
        "split_mode": args.split_mode,
        "budget_seconds": args.budget_seconds,
        "max_nodes": args.max_nodes,
        "max_depth": args.max_depth,
        "top_k": args.top_k,
        "phi_plus_count": args.phi_plus_count,
        "results": results,
    }

    out_json = args.out_json
    if not out_json.is_absolute():
        out_json = API_ROOT.parents[1] / out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = args.out_md
    if not out_md.is_absolute():
        out_md = API_ROOT.parents[1] / out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_render_markdown(payload), encoding="utf-8")

    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
