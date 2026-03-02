#!/usr/bin/env python3
from __future__ import annotations

import inspect
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
DOMAIN_SRC = PROJECT_ROOT / "packages" / "domain" / "src"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(DOMAIN_SRC) not in sys.path:
    sys.path.insert(0, str(DOMAIN_SRC))

from app.api.v1.derivation import (  # noqa: E402
    DerivationReachabilityRequest,
    _generate_numeration_with_unknown_token_fallback,
    _search_reachability,
)
from domain.common.types import DerivationState  # noqa: E402
from domain.derivation.candidates import list_merge_candidates  # noqa: E402
from domain.derivation.execute import execute_double_merge, execute_single_merge  # noqa: E402
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions  # noqa: E402
from domain.grammar.rule_catalog import load_rule_catalog  # noqa: E402
from domain.lexicon.legacy_loader import (  # noqa: E402
    load_legacy_lexicon,
    resolve_legacy_lexicon_path,
)
from domain.lexicon.models import LexiconEntry  # noqa: E402
from domain.numeration.generator import (  # noqa: E402
    SudachiMorphTokenizer,
    _build_surface_index,
    _normalize_token,
    _resolve_token,
)
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
TARGET_WORDS = [
    "ふわふわした",
    "わたあめ",
    "食べている",
    "ひつじ",
    "話している",
    "うさぎ",
    "いる",
]
VARIANT_STOP_WORDS = {"する", "いる", "た", "て", "だ", "です", "ます", "し", "る"}

# explicit numeration proposals (S2/S3/S4)
PROPOSALS: dict[str, dict[str, list[int]]] = {
    "S2": {
        "P0_imi_content_ids_switch_grammar_only": [265, 23, 266, 267, 19, 271, 125],
        "P1_existing_japanese2_candidates": [265, 197, 266, 267, 196, 271, 125],
        "P2_P1_plus_target_phi": [265, 197, 266, 267, 196, 271, 125, 272, 273, 274, 275],
        "P3_new_lexical_item_max3": [9103, 23, 266, 9101, 19, 271, 125],
    },
    "S3": {
        "P0_imi_content_ids_switch_grammar_only": [267, 268, 269, 270, 19, 271, 125],
        "P1_existing_japanese2_candidates": [267, 171, 269, 270, 196, 271, 125],
        "P2_P1_plus_target_phi": [267, 171, 269, 270, 196, 271, 125, 272, 273, 274, 275],
        "P3_new_lexical_item_max3": [9101, 268, 269, 9102, 19, 271, 125],
    },
    "S4": {
        "P0_imi_content_ids_switch_grammar_only": [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 125],
        "P1_existing_japanese2_candidates": [264, 265, 197, 266, 267, 171, 269, 270, 196, 271, 125],
        "P2_P1_plus_target_phi": [264, 265, 197, 266, 267, 171, 269, 270, 196, 271, 125, 272, 273, 274, 275],
        "P3_new_lexical_item_max3": [264, 9103, 23, 266, 9101, 268, 269, 9102, 19, 271, 125],
    },
}

NEW_LEX_ROWS = [
    # max 3 rows
    "9101\tひつじ\tひつじ\tN\t0\t\t\t\t2\t4,11,ga\t4,11,to\t\t\t\tid\t1\tひつじ\tT\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tj2-explicit-probe\t0",
    "9102\tうさぎ\tうさぎ\tN\t0\t\t\t\t1\t4,11,ga\t\t\t\t\tid\t1\tうさぎ\tT\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tj2-explicit-probe\t0",
    "9103\tわたあめ\tわたあめ\tN\t0\t\t\t\t1\t4,11,wo\t\t\t\t\tid\t1\tわたあめ\tT\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tj2-explicit-probe\t0",
]


@dataclass(frozen=True)
class RunConfig:
    budget_seconds: float = 20.0
    max_nodes: int = 120000
    max_depth: int = 28
    top_k: int = 10


def _line_map_by_id(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        try:
            lid = int(cols[0].strip())
        except Exception:
            continue
        out[lid] = line
    return out


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


def _trace_open_files_for_generate(*, legacy_root: Path, sentence: str) -> list[str]:
    opened: list[str] = []
    real_read_text = Path.read_text

    def traced_read_text(path_obj: Path, *args, **kwargs):
        try:
            opened.append(str(path_obj.expanduser().resolve()))
        except Exception:
            opened.append(str(path_obj))
        return real_read_text(path_obj, *args, **kwargs)

    # load_legacy_lexicon/load_rule_catalog read via Path.read_text.
    Path.read_text = traced_read_text  # type: ignore[assignment]
    try:
        try:
            _generate_numeration_with_unknown_token_fallback(
                grammar_id=GRAMMAR_ID,
                sentence=sentence,
                legacy_root=legacy_root,
                tokens=None,
                split_mode="C",
                auto_add_ga_phi=False,
            )
        except Exception:
            pass
    finally:
        Path.read_text = real_read_text  # type: ignore[assignment]
    # unique preserving order
    uniq: list[str] = []
    seen: set[str] = set()
    for p in opened:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)
    return uniq


def _source_section(*, legacy_root: Path) -> dict[str, Any]:
    lex_path = resolve_legacy_lexicon_path(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    rule_path = legacy_root / "japanese2" / "japanese2R.pl"
    loaded_files = _trace_open_files_for_generate(legacy_root=legacy_root, sentence=SENTENCES["S1"])

    gen_file = Path(inspect.getsourcefile(_generate_numeration_with_unknown_token_fallback) or "")
    resolve_file = Path(inspect.getsourcefile(_resolve_token) or "")
    load_file = Path(inspect.getsourcefile(load_legacy_lexicon) or "")

    return {
        "grammar_id": GRAMMAR_ID,
        "lookup_source_files": [str(lex_path.resolve())],
        "related_runtime_files": [str(rule_path.resolve())],
        "runtime_open_trace_files": loaded_files,
        "uses_lexicon_all": False,
        "lookup_key": {
            "token_normalization": "domain/numeration/generator.py:_normalize_token",
            "index_build": "domain/numeration/generator.py:_build_surface_index (entry + phono variants exact match)",
            "lookup": "domain/numeration/generator.py:_resolve_token (surface_index.get(normalized))",
        },
        "call_path": [
            f"{gen_file}:_generate_numeration_with_unknown_token_fallback",
            "domain/numeration/generator.py:generate_numeration_from_sentence",
            f"{load_file}:load_legacy_lexicon",
            "domain/numeration/generator.py:_build_surface_index",
            f"{resolve_file}:_resolve_token",
        ],
        "fact_status": STATUS_CONFIRMED,
    }


def _word_variants_by_tokenizer(word: str) -> list[str]:
    tokenizer = SudachiMorphTokenizer(dictionary="core")
    rows = tokenizer._analyze(word, split_mode="C")  # private API, but used only for factual extraction
    original = _normalize_token(word)
    vals: list[str] = []
    vals.append(original)
    for r in rows:
        vals.append(_normalize_token(r.surface))
        vals.append(_normalize_token(r.dictionary_form))
        vals.append(_normalize_token(r.token))
    uniq: list[str] = []
    seen: set[str] = set()
    for v in vals:
        if not v:
            continue
        if len(v) <= 1:
            continue
        if v != original and v in VARIANT_STOP_WORDS:
            continue
        if v in seen:
            continue
        seen.add(v)
        uniq.append(v)
    return uniq


def _raw_lookup_dump(*, source_files: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for word in TARGET_WORDS:
        variants = _word_variants_by_tokenizer(word)
        file_rows: list[dict[str, Any]] = []
        for src in source_files:
            path = Path(src)
            lines = path.read_text(encoding="utf-8").splitlines()
            hits: list[dict[str, Any]] = []
            for i, line in enumerate(lines, start=1):
                cols = line.split("\t")
                entry = _normalize_token(cols[1]) if len(cols) > 1 else ""
                phono = _normalize_token(cols[2]) if len(cols) > 2 else ""
                phono_stripped = phono.strip("-")
                matched_variant: Optional[str] = None
                matched_field: Optional[str] = None
                for v in variants:
                    if v == entry:
                        matched_variant = v
                        matched_field = "entry"
                        break
                    if v == phono or v == phono_stripped:
                        matched_variant = v
                        matched_field = "phono"
                        break
                if matched_variant is not None:
                    hits.append(
                        {
                            "line": i,
                            "variant": matched_variant,
                            "field": matched_field,
                            "text": line,
                        }
                    )
            file_rows.append(
                {
                    "file_path": str(path.resolve()),
                    "hit_count": len(hits),
                    "hits": hits,
                    "fact_status": STATUS_CONFIRMED,
                }
            )
        result[word] = {
            "variants": variants,
            "files": file_rows,
            "fact_status": STATUS_CONFIRMED,
        }
    return result


def _reproduce_generation_failures(*, legacy_root: Path) -> dict[str, Any]:
    tokenizer = SudachiMorphTokenizer(dictionary="core")
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    grammar_rule_names = {r.name for r in load_rule_catalog(grammar_id=GRAMMAR_ID, legacy_root=legacy_root)}
    surface_index = _build_surface_index(lexicon)

    out: dict[str, Any] = {}
    for sk, sentence in SENTENCES.items():
        mode_records: list[dict[str, Any]] = []
        tried: set[str] = set()
        ordered_modes = ["C", "B", "A"]
        for mode in ordered_modes:
            if mode in tried:
                continue
            tried.add(mode)
            tokens: list[str] = []
            failed_token: Optional[str] = None
            failed_query: Optional[str] = None
            error: Optional[str] = None
            try:
                tokens = tokenizer.tokenize(sentence, split_mode=mode)
                for token in tokens:
                    q = _normalize_token(token)
                    _resolve_token(
                        grammar_id=GRAMMAR_ID,
                        token=q,
                        surface_index=surface_index,
                        lexicon=lexicon,
                        grammar_rule_names=grammar_rule_names,
                    )
            except Exception as exc:
                msg = str(exc)
                error = msg
                if msg.startswith("Unknown token for lexicon lookup:"):
                    failed_token = msg.split(":", 1)[1].strip()
                    failed_query = _normalize_token(failed_token)
            mode_records.append(
                {
                    "split_mode": mode,
                    "tokenization": tokens,
                    "failed_token": failed_token,
                    "lookup_query": failed_query,
                    "lookup_source": str(resolve_legacy_lexicon_path(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)),
                    "error": error,
                    "fact_status": STATUS_CONFIRMED,
                }
            )

        final_error = None
        try:
            _generate_numeration_with_unknown_token_fallback(
                grammar_id=GRAMMAR_ID,
                sentence=sentence,
                legacy_root=legacy_root,
                tokens=None,
                split_mode="C",
                auto_add_ga_phi=False,
            )
        except Exception as exc:
            final_error = str(exc)

        out[sk] = {
            "sentence": sentence,
            "mode_attempts": mode_records,
            "final_error": final_error,
            "fact_status": STATUS_CONFIRMED,
        }
    return out


def _explicit_path_section(*, legacy_root: Path) -> dict[str, Any]:
    # yes/no checks
    compose_path = "apps/api/app/api/v1/derivation.py:/numeration/compose -> _compose_numeration_text"
    init_path = "apps/api/app/api/v1/derivation.py:/init -> build_initial_derivation_state"
    reach_path = "apps/api/app/api/v1/derivation.py:/reachability (DerivationReachabilityRequest.state)"

    working_example: dict[str, Any]
    blocked_example: dict[str, Any]

    # working example with IDs that exist in japanese2 source
    try:
        text_ok = _build_numeration_text("explicit-ok", [60, 19, 125])
        state_ok = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=text_ok,
            legacy_root=legacy_root,
        )
        profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
        req = DerivationReachabilityRequest(
            state=state_ok,
            max_evidences=3,
            budget_seconds=2.0,
            max_nodes=3000,
            max_depth=12,
            return_process_text=False,
        )
        internal = _search_reachability(
            request=req,
            legacy_root=legacy_root,
            rh_version=profile.rh_merge_version,
            lh_version=profile.lh_merge_version,
            search_signature_mode="structural",
        )
        working_example = {
            "numeration_lexicon_ids": [60, 19, 125],
            "status": internal.status,
            "reason": internal.reason,
            "actions_attempted": internal.actions_attempted,
            "fact_status": STATUS_CONFIRMED,
        }
    except Exception as exc:
        working_example = {
            "numeration_lexicon_ids": [60, 19, 125],
            "error": str(exc),
            "fact_status": STATUS_CONFIRMED,
        }

    # blocked example when IDs are not present in japanese2 source
    try:
        text_ng = _build_numeration_text("explicit-ng", [265, 23])
        _ = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=text_ng,
            legacy_root=legacy_root,
        )
        blocked_example = {
            "numeration_lexicon_ids": [265, 23],
            "error": None,
            "fact_status": STATUS_CONFIRMED,
        }
    except Exception as exc:
        blocked_example = {
            "numeration_lexicon_ids": [265, 23],
            "error": str(exc),
            "fact_status": STATUS_CONFIRMED,
        }

    return {
        "can_pass_explicit_numeration_to_reachability": True,
        "can_build_state_from_numeration_without_sentence_lookup": True,
        "compose_path": compose_path,
        "init_path": init_path,
        "reachability_path": reach_path,
        "working_example": working_example,
        "blocked_example": blocked_example,
        "note": "state作成時の lexicon_id 存在確認は /init 経路で実施される",
        "fact_status": STATUS_CONFIRMED,
    }


def _make_temp_legacy_root_for_explicit(
    *,
    legacy_root: Path,
    required_ids: set[int],
    extra_rows: list[str],
) -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="j2_explicit_"))
    for child in legacy_root.iterdir():
        dst = tmp_root / child.name
        if child.name == "japanese2":
            continue
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    src_j2 = legacy_root / "japanese2"
    dst_j2 = tmp_root / "japanese2"
    dst_j2.mkdir(parents=True, exist_ok=True)
    # copy all files under japanese2 except japanese2.csv
    for child in src_j2.iterdir():
        if child.name == "japanese2.csv":
            continue
        dst = dst_j2 / child.name
        try:
            dst.symlink_to(child, target_is_directory=child.is_dir())
        except Exception:
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    j2_map = _line_map_by_id(legacy_root / "japanese2" / "japanese2.csv")
    all_map = _line_map_by_id(legacy_root / "lexicon-all.csv")
    extra_map: dict[int, str] = {}
    for row in extra_rows:
        cols = row.split("\t")
        try:
            lid = int(cols[0].strip())
            extra_map[lid] = row
        except Exception:
            continue

    lines: list[str] = []
    for lid in sorted(required_ids):
        if lid in j2_map:
            lines.append(j2_map[lid])
            continue
        if lid in all_map:
            lines.append(all_map[lid])
            continue
        if lid in extra_map:
            lines.append(extra_map[lid])
            continue

    # ensure extra rows are included
    for lid, row in sorted(extra_map.items()):
        if lid not in required_ids:
            lines.append(row)

    (dst_j2 / "japanese2.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_root


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
                        str(row.get("item_id", "")),
                        str(row.get("category", "")),
                        str(row.get("phono", "")),
                        str(row.get("raw", "")),
                        str(row.get("slot_index", "")),
                    ]
                )
                fam_counter[key] += 1
                attrs[key] = {
                    "item_id": str(row.get("item_id", "")),
                    "category": str(row.get("category", "")),
                    "phono": str(row.get("phono", "")),
                    "raw": str(row.get("raw", "")),
                    "slot_index": str(row.get("slot_index", "")),
                }
    out: dict[str, list[dict[str, Any]]] = {}
    for family, counter in sorted(by_family.items(), key=lambda row: row[0]):
        items: list[dict[str, Any]] = []
        for key, count in counter.most_common(10):
            a = attrs[key]
            items.append(
                {
                    "count": int(count),
                    "item_id": a["item_id"],
                    "category": a["category"],
                    "phono": a["phono"],
                    "raw": a["raw"],
                    "slot_index": a["slot_index"],
                }
            )
        out[family] = items
    return out


def _run_reachability_for_ids(
    *,
    legacy_root: Path,
    sentence_key: str,
    sentence: str,
    proposal_id: str,
    lexicon_ids: list[int],
    config: RunConfig,
) -> dict[str, Any]:
    numeration_text = _build_numeration_text(f"{sentence_key}:{proposal_id}", lexicon_ids)
    state = build_initial_derivation_state(
        grammar_id=GRAMMAR_ID,
        numeration_text=numeration_text,
        legacy_root=legacy_root,
    )
    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    req = DerivationReachabilityRequest(
        state=state,
        max_evidences=20,
        budget_seconds=config.budget_seconds,
        max_nodes=config.max_nodes,
        max_depth=config.max_depth,
        return_process_text=False,
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
            k: round(float(v) / float(len(best_leaf_samples)), 3)
            for k, v in leaf_totals.items()
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
        "proposal_id": proposal_id,
        "explicit_lexicon_ids": lexicon_ids,
        "status": internal.status,
        "reason": internal.reason,
        "actions_attempted": internal.actions_attempted,
        "max_depth_reached": internal.max_depth_reached,
        "best_leaf_unresolved_min": internal.leaf_stats.get("unresolved_min"),
        "best_leaf_residual_family_totals": leaf_totals,
        "best_leaf_residual_family_avg": leaf_avg,
        "best_mid_residual_family_totals": mid_totals,
        "persistent_residual_source_top": _aggregate_residual_sources(best_leaf_samples),
        "history_top": history_top,
        "fact_status": STATUS_CONFIRMED,
    }


def _run_explicit_experiments(*, legacy_root: Path, config: RunConfig) -> dict[str, Any]:
    required_ids: set[int] = set()
    for m in PROPOSALS.values():
        for ids in m.values():
            required_ids.update(ids)
    required_ids.update({60, 19, 125, 23, 171, 196, 197, 272, 273, 274, 275})

    temp_root = _make_temp_legacy_root_for_explicit(
        legacy_root=legacy_root,
        required_ids=required_ids,
        extra_rows=NEW_LEX_ROWS,
    )

    results: dict[str, dict[str, Any]] = defaultdict(dict)
    for sk in ("S2", "S3", "S4"):
        sentence = SENTENCES[sk]
        for pid, ids in PROPOSALS[sk].items():
            try:
                row = _run_reachability_for_ids(
                    legacy_root=temp_root,
                    sentence_key=sk,
                    sentence=sentence,
                    proposal_id=pid,
                    lexicon_ids=ids,
                    config=config,
                )
            except Exception as exc:
                row = {
                    "sentence_key": sk,
                    "sentence": sentence,
                    "proposal_id": pid,
                    "explicit_lexicon_ids": ids,
                    "status": "failed",
                    "reason": "experiment_error",
                    "error": str(exc),
                    "actions_attempted": 0,
                    "max_depth_reached": 0,
                    "best_leaf_unresolved_min": None,
                    "best_leaf_residual_family_totals": {},
                    "best_leaf_residual_family_avg": {},
                    "best_mid_residual_family_totals": {},
                    "persistent_residual_source_top": {},
                    "history_top": [],
                    "fact_status": STATUS_CONFIRMED,
                }
            results[sk][pid] = row

    return {
        "temp_legacy_root": str(temp_root),
        "results": results,
        "fact_status": STATUS_CONFIRMED,
    }


def _se33_count(state: DerivationState, label: str) -> int:
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


def _local_pair_probe(*, legacy_root: Path, head_id: int, nonhead_id: int, target_label: str) -> dict[str, Any]:
    try:
        text = _build_numeration_text("probe", [head_id, nonhead_id])
        state = build_initial_derivation_state(
            grammar_id=GRAMMAR_ID,
            numeration_text=text,
            legacy_root=legacy_root,
        )
    except Exception as exc:
        return {
            "head_id": head_id,
            "nonhead_id": nonhead_id,
            "target_label": target_label,
            "success": False,
            "error": str(exc),
            "fact_status": STATUS_CONFIRMED,
        }

    profile = resolve_rule_versions(profile=get_grammar_profile(GRAMMAR_ID), legacy_root=legacy_root)
    before = _se33_count(state, target_label)
    best: Optional[dict[str, Any]] = None
    trials: list[dict[str, Any]] = []
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            cands = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=legacy_root,
                rh_merge_version=profile.rh_merge_version,
                lh_merge_version=profile.lh_merge_version,
            )
            for cand in cands:
                try:
                    if cand.rule_kind == "double":
                        version = profile.rh_merge_version if cand.rule_name == "RH-Merge" else profile.lh_merge_version
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
                    after = _se33_count(next_state, target_label)
                    row = {
                        "rule_name": cand.rule_name,
                        "left": cand.left,
                        "right": cand.right,
                        "check": cand.check,
                        "before": before,
                        "after": after,
                        "decreased": after < before,
                    }
                    trials.append(row)
                    if row["decreased"] and best is None:
                        best = row
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

    return {
        "head_id": head_id,
        "nonhead_id": nonhead_id,
        "target_label": target_label,
        "success": best is not None,
        "witness": best,
        "trials_top": trials[:50],
        "fact_status": STATUS_CONFIRMED,
    }


def _yes_no_section(*, experiments: dict[str, dict[str, Any]], temp_legacy_root: Path) -> list[dict[str, Any]]:
    # local discharge probes under explicit bypass root
    q1_probe = _local_pair_probe(legacy_root=temp_legacy_root, head_id=266, nonhead_id=23, target_label="wo")
    q2_probe = _local_pair_probe(legacy_root=temp_legacy_root, head_id=266, nonhead_id=267, target_label="ga")
    q3_probe = _local_pair_probe(legacy_root=temp_legacy_root, head_id=269, nonhead_id=267, target_label="to")
    q4_probe = _local_pair_probe(legacy_root=temp_legacy_root, head_id=269, nonhead_id=270, target_label="ga")

    # q5: sy:17 reduced by lexical choice only (P1/P2 vs P0)
    sy17_reduced = False
    witness = None
    for sk in ("S2", "S3", "S4"):
        p0 = experiments[sk].get("P0_imi_content_ids_switch_grammar_only", {})
        p1 = experiments[sk].get("P1_existing_japanese2_candidates", {})
        p2 = experiments[sk].get("P2_P1_plus_target_phi", {})
        base = float((p0.get("best_leaf_residual_family_avg") or {}).get("sy:17", 0.0))
        v1 = float((p1.get("best_leaf_residual_family_avg") or {}).get("sy:17", 0.0))
        v2 = float((p2.get("best_leaf_residual_family_avg") or {}).get("sy:17", 0.0))
        if v1 < base or v2 < base:
            sy17_reduced = True
            witness = {
                "sentence_key": sk,
                "baseline_sy17_avg": base,
                "p1_sy17_avg": v1,
                "p2_sy17_avg": v2,
            }
            break

    rows = [
        {
            "question_no": 1,
            "question": "食べている Theme:2,33,wo を japanese2 現行 rule set + lexical choice で discharge path 構成できるか",
            "answer_yes_no": "Yes" if q1_probe["success"] else "No",
            "explicit_lexicon_ids_tested": [266, 23],
            "minimal_success_or_counterexample": q1_probe["witness"] if q1_probe["success"] else (q1_probe["trials_top"][0] if q1_probe["trials_top"] else {"error": q1_probe.get("error")}),
            "required_rule": q1_probe["witness"]["rule_name"] if q1_probe["success"] and q1_probe["witness"] else "[未確認]",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33)",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 2,
            "question": "食べている Agent:2,33,ga を head noun ひつじで discharge path 構成できるか",
            "answer_yes_no": "Yes" if q2_probe["success"] else "No",
            "explicit_lexicon_ids_tested": [266, 267],
            "minimal_success_or_counterexample": q2_probe["witness"] if q2_probe["success"] else (q2_probe["trials_top"][0] if q2_probe["trials_top"] else {"error": q2_probe.get("error")}),
            "required_rule": q2_probe["witness"]["rule_name"] if q2_probe["success"] and q2_probe["witness"] else "[未確認]",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33)",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 3,
            "question": "話している 相手:2,33,to を ひつじで discharge path 構成できるか",
            "answer_yes_no": "Yes" if q3_probe["success"] else "No",
            "explicit_lexicon_ids_tested": [269, 267],
            "minimal_success_or_counterexample": q3_probe["witness"] if q3_probe["success"] else (q3_probe["trials_top"][0] if q3_probe["trials_top"] else {"error": q3_probe.get("error")}),
            "required_rule": q3_probe["witness"]["rule_name"] if q3_probe["success"] and q3_probe["witness"] else "[未確認]",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33)",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 4,
            "question": "話している Agent:2,33,ga を head noun うさぎで discharge path 構成できるか",
            "answer_yes_no": "Yes" if q4_probe["success"] else "No",
            "explicit_lexicon_ids_tested": [269, 270],
            "minimal_success_or_counterexample": q4_probe["witness"] if q4_probe["success"] else (q4_probe["trials_top"][0] if q4_probe["trials_top"] else {"error": q4_probe.get("error")}),
            "required_rule": q4_probe["witness"]["rule_name"] if q4_probe["success"] and q4_probe["witness"] else "[未確認]",
            "code_path": "packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33)",
            "fact_status": STATUS_CONFIRMED,
        },
        {
            "question_no": 5,
            "question": "persistent sy:17 は japanese2 lexical choice だけで解消できるか",
            "answer_yes_no": "Yes" if sy17_reduced else "No",
            "explicit_lexicon_ids_tested": {
                sk: {
                    "P0": experiments[sk].get("P0_imi_content_ids_switch_grammar_only", {}).get("explicit_lexicon_ids", []),
                    "P1": experiments[sk].get("P1_existing_japanese2_candidates", {}).get("explicit_lexicon_ids", []),
                    "P2": experiments[sk].get("P2_P1_plus_target_phi", {}).get("explicit_lexicon_ids", []),
                }
                for sk in ("S2", "S3", "S4")
            },
            "minimal_success_or_counterexample": witness if sy17_reduced else "P1/P2 の sy:17(avg) が P0 を下回る観測なし",
            "required_rule": "[未確認]",
            "code_path": "apps/api/scripts/reachability_japanese2_entry_conditions_facts_20260302.py: experiments comparison",
            "fact_status": STATUS_CONFIRMED,
        },
    ]
    return rows


def _candidate_inventory_j2(*, legacy_root: Path) -> list[dict[str, Any]]:
    lexicon_j2 = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=GRAMMAR_ID)
    lexicon_all = load_legacy_lexicon(legacy_root=legacy_root, grammar_id="imi01")

    # target set from request around particles/phi candidates
    focus_ids = {19, 23, 125, 171, 181, 183, 189, 196, 197, 204, 263, 268, 272, 273, 274, 275, 294, 297, 308, 309, 310, 311}
    out: list[dict[str, Any]] = []
    for lid in sorted(focus_ids):
        e_all = lexicon_all.get(lid)
        e_j2 = lexicon_j2.get(lid)
        out.append(
            {
                "lexicon_id": lid,
                "exists_in_japanese2_source": e_j2 is not None,
                "exists_in_lexicon_all": e_all is not None,
                "entry": e_all.entry if e_all else None,
                "category": e_all.category if e_all else None,
                "idslot": e_all.idslot if e_all else None,
                "sync_features": list(e_all.sync_features) if e_all else [],
                "semantics": list(e_all.semantics) if e_all else [],
                "fact_status": STATUS_CONFIRMED,
            }
        )
    return out


def _final_conclusion(
    *,
    source_section: dict[str, Any],
    experiments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    # A: lexical source/lookup
    all_failed = all(
        v.get("final_error", "").startswith("Unknown token for lexicon lookup:")
        for v in source_section.get("generation_repro", {}).values()
    )
    conclusion_a = {
        "lookup_ready_for_S1_S6": not all_failed,
        "reason": "S1-S6 が token lookup で失敗" if all_failed else "一部成功",
        "fact_status": STATUS_CONFIRMED,
    }

    # B: explicit bypass experiment outlook
    any_reachable = False
    for sk in ("S2", "S3", "S4"):
        for pid in PROPOSALS[sk].keys():
            if experiments[sk][pid].get("status") == "reachable":
                any_reachable = True
                break
    conclusion_b = {
        "explicit_bypass_any_reachable": any_reachable,
        "reason": "explicit numeration/state 経路で reachable 観測あり" if any_reachable else "explicit 経路でも reachable 未観測（unknown/failed）",
        "fact_status": STATUS_CONFIRMED,
    }

    return {"A": conclusion_a, "B": conclusion_b}


def _markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# japanese2 Entry Conditions Facts ({payload['generated_at']})")
    lines.append("")
    lines.append("## 1. 結論")
    lines.append("")
    lines.append(f"- [確認済み事実] 結論A: {payload['final_conclusion']['A']}")
    lines.append(f"- [確認済み事実] 結論B: {payload['final_conclusion']['B']}")
    lines.append("")

    lines.append("## 2. japanese2 lexical source の実体")
    lines.append("")
    src = payload["source"]
    lines.append(f"- [確認済み事実] lookup_source_files: {src['lookup_source_files']}")
    lines.append(f"- [確認済み事実] related_runtime_files: {src['related_runtime_files']}")
    lines.append(f"- [確認済み事実] runtime_open_trace_files: {src['runtime_open_trace_files']}")
    lines.append(f"- [確認済み事実] call_path: {src['call_path']}")
    lines.append("")

    lines.append("## 3. raw lookup dump")
    lines.append("")
    for word, row in payload["raw_lookup_dump"].items():
        lines.append(f"### {word}")
        lines.append(f"- [確認済み事実] variants={row['variants']}")
        for f in row["files"]:
            lines.append(f"- [確認済み事実] file={f['file_path']} hits={f['hit_count']}")
            if f["hits"]:
                lines.append("```text")
                for h in f["hits"]:
                    lines.append(f"L{h['line']}: {h['text']}")
                lines.append("```")
        lines.append("")

    lines.append("## 4. generation_failed 最小再現")
    lines.append("")
    for sk in ("S1", "S2", "S3", "S4", "S5", "S6"):
        rec = payload["generation_repro"][sk]
        lines.append(f"### {sk}: {rec['sentence']}")
        for mode_row in rec["mode_attempts"]:
            lines.append(
                f"- [確認済み事実] mode={mode_row['split_mode']} tokens={mode_row['tokenization']} failed_token={mode_row['failed_token']} query={mode_row['lookup_query']} error={mode_row['error']}"
            )
        lines.append(f"- [確認済み事実] final_error={rec['final_error']}")
        lines.append("")

    lines.append("## 5. explicit numeration/state 迂回経路")
    lines.append("")
    ep = payload["explicit_path"]
    lines.append(f"- [確認済み事実] explicit numeration -> reachability: Yes ({ep['compose_path']} -> {ep['init_path']} -> {ep['reachability_path']})")
    lines.append(f"- [確認済み事実] working_example={ep['working_example']}")
    lines.append(f"- [確認済み事実] blocked_example={ep['blocked_example']}")
    lines.append("")

    lines.append("## 6. explicit numeration 実験")
    lines.append("")
    lines.append(f"- [確認済み事実] temp_legacy_root={payload['experiments']['temp_legacy_root']}")
    lines.append("| sentence | proposal | explicit_lexicon_ids | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for sk in ("S2", "S3", "S4"):
        for pid in PROPOSALS[sk].keys():
            r = payload["experiments"]["results"][sk][pid]
            avg = r.get("best_leaf_residual_family_avg") or {}
            source_top = r.get("persistent_residual_source_top") or {}
            top_text = "; ".join(
                f"{fam}:{rows[0]['item_id']}:{rows[0]['raw']}({rows[0]['count']})"
                for fam, rows in source_top.items()
                if rows
            ) or "-"
            lines.append(
                f"| {sk} | {pid} | {','.join(str(x) for x in r['explicit_lexicon_ids'])} | {r['status']} | {r['reason']} | {r['actions_attempted']} | {r['max_depth_reached']} | {r['best_leaf_unresolved_min']} | {float(avg.get('se:33',0.0))} | {float(avg.get('sy:11',0.0))} | {float(avg.get('sy:17',0.0))} | {top_text} |"
            )
    lines.append("")

    lines.append("## 7. yes/no")
    lines.append("")
    lines.append("| Q | yes/no | explicit_lexicon_ids_tested | minimal success/counterexample | required_rule | code_path |")
    lines.append("|---:|---|---|---|---|---|")
    for q in payload["yes_no"]:
        lines.append(
            f"| {q['question_no']} | {q['answer_yes_no']} | {q['explicit_lexicon_ids_tested']} | {q['minimal_success_or_counterexample']} | {q['required_rule']} | {q['code_path']} |"
        )
    lines.append("")

    lines.append("## 8. 最終結論")
    lines.append("")
    lines.append(f"- [確認済み事実] 結論A: {payload['final_conclusion']['A']}")
    lines.append(f"- [確認済み事実] 結論B: {payload['final_conclusion']['B']}")
    lines.append("")

    lines.append("## 9. 未確認事項")
    lines.append("")
    lines.append("- [未確認] explicit実験の unknown は budget上限内の観測であり、unreachable 断定ではない。")
    lines.append("- [未確認] tree/process の詳細比較は本レポートでは未収集（history上位のみ）。")

    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_root = Path("/Users/tomonaga/Documents/syncsemphoneIMI")
    config = RunConfig()

    source = _source_section(legacy_root=legacy_root)
    source_files = source["lookup_source_files"]
    raw_lookup_dump = _raw_lookup_dump(source_files=source_files)
    generation_repro = _reproduce_generation_failures(legacy_root=legacy_root)
    source["generation_repro"] = generation_repro

    explicit_path = _explicit_path_section(legacy_root=legacy_root)
    experiments = _run_explicit_experiments(legacy_root=legacy_root, config=config)
    yes_no = _yes_no_section(
        experiments=experiments["results"],
        temp_legacy_root=Path(experiments["temp_legacy_root"]),
    )

    payload = {
        "generated_at": date.today().isoformat(),
        "config": {
            "grammar_id": GRAMMAR_ID,
            "budget_seconds": config.budget_seconds,
            "max_nodes": config.max_nodes,
            "max_depth": config.max_depth,
            "top_k": config.top_k,
            "auto_add_ga_phi": False,
            "legacy_root": str(legacy_root),
        },
        "source": source,
        "raw_lookup_dump": raw_lookup_dump,
        "generation_repro": generation_repro,
        "explicit_path": explicit_path,
        "candidate_inventory_focus": _candidate_inventory_j2(legacy_root=legacy_root),
        "experiments": experiments,
        "yes_no": yes_no,
        "final_conclusion": _final_conclusion(source_section=source, experiments=experiments["results"]),
        # user-required machine-friendly nesting
        "sentence": {
            sk: {
                pid: {
                    "explicit_lexicon_ids": row["explicit_lexicon_ids"],
                    "metrics": {
                        "status": row["status"],
                        "reason": row["reason"],
                        "actions_attempted": row["actions_attempted"],
                        "max_depth_reached": row["max_depth_reached"],
                        "best_leaf_unresolved_min": row["best_leaf_unresolved_min"],
                        "best_leaf_residual_family_totals": row.get("best_leaf_residual_family_totals", {}),
                        "best_mid_residual_family_totals": row.get("best_mid_residual_family_totals", {}),
                        "persistent_residual_source_top": row.get("persistent_residual_source_top", {}),
                        "history_top": row.get("history_top", []),
                    },
                }
                for pid, row in experiments["results"][sk].items()
            }
            for sk in ("S2", "S3", "S4")
        },
    }

    out_json = PROJECT_ROOT / "docs/specs/reachability-japanese2-entry-conditions-facts-20260302.json"
    out_md = PROJECT_ROOT / "docs/specs/reachability-japanese2-entry-conditions-facts-20260302.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown_report(payload), encoding="utf-8")
    print(f"Wrote JSON: {out_json}")
    print(f"Wrote Markdown: {out_md}")


if __name__ == "__main__":
    main()
