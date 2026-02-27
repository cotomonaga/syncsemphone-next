from __future__ import annotations

import json
import heapq
import itertools
import multiprocessing as mp
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.common.types import DerivationState, RuleCandidate
from domain.derivation.candidates import list_merge_candidates
from domain.derivation.execute import execute_double_merge, execute_single_merge
from domain.grammar.legacy_catalog import load_legacy_grammar_entries
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions
from domain.grammar.rule_catalog import (
    get_rule_name_by_number,
    get_rule_number_by_name,
    load_rule_catalog,
)
from domain.numeration.generator import SudachiMorphTokenizer, generate_numeration_from_sentence
from domain.numeration.init_builder import build_initial_derivation_state
from domain.numeration.parser import NUMERATION_SLOT_COUNT
from domain.resume.codec import (
    export_process_text_like_perl,
    export_resume_text,
    import_resume_text,
)

router = APIRouter(prefix="/derivation", tags=["derivation"])


class DerivationInitRequest(BaseModel):
    grammar_id: str
    numeration_text: str
    legacy_root: Optional[str] = None


class DerivationCandidatesRequest(BaseModel):
    state: DerivationState
    left: int
    right: int
    legacy_root: Optional[str] = None
    rh_merge_version: Optional[str] = None
    lh_merge_version: Optional[str] = None


class DerivationHeadAssistRequest(BaseModel):
    state: DerivationState
    top_k: int = 5
    parallel_cores: Optional[int] = None
    search_signature_mode: Optional[str] = None
    legacy_root: Optional[str] = None
    rh_merge_version: Optional[str] = None
    lh_merge_version: Optional[str] = None


class HeadAssistSuggestionResponse(BaseModel):
    rank: int
    rule_number: int
    rule_name: str
    rule_kind: str
    left: int
    right: int
    check: Optional[int] = None
    unresolved_before: int
    unresolved_after: int
    unresolved_delta: int
    grammatical_after: bool
    basenum_before: int
    basenum_after: int
    reachable_grammatical: bool = False
    steps_to_grammatical: Optional[int] = None


class DerivationReachabilityDiagnoseRequest(BaseModel):
    state: DerivationState
    baseline_max_depth: int = 7
    baseline_budget_seconds: float = 10.0
    baseline_max_nodes: int = 250000
    legacy_root: Optional[str] = None
    rh_merge_version: Optional[str] = None
    lh_merge_version: Optional[str] = None


class ReplayStepTraceResponse(BaseModel):
    step: int
    rule_name: str
    left_id: str
    right_id: str
    left_index: Optional[int] = None
    right_index: Optional[int] = None
    candidate_rule_names: list[str]
    rule_available: bool
    unresolved_before: int
    unresolved_after: Optional[int] = None
    basenum_before: int
    basenum_after: Optional[int] = None


class StrictReplayDiagnosticResponse(BaseModel):
    available: bool
    reached_grammatical: bool
    final_unresolved: int
    trace: list[ReplayStepTraceResponse]


class BaselineReachabilityDiagnosticResponse(BaseModel):
    status: str
    max_depth: int
    budget_seconds: float
    max_nodes: int
    expanded_nodes: int
    steps_to_grammatical: Optional[int] = None


class DerivationReachabilityDiagnoseResponse(BaseModel):
    strict_replay: StrictReplayDiagnosticResponse
    baseline_complete: BaselineReachabilityDiagnosticResponse


class DerivationExecuteRequest(BaseModel):
    state: DerivationState
    rule_name: Optional[str] = None
    rule_number: Optional[int] = None
    left: Optional[int] = None
    right: Optional[int] = None
    check: Optional[int] = None
    legacy_root: Optional[str] = None
    rh_merge_version: Optional[str] = None
    lh_merge_version: Optional[str] = None


class ResumeExportRequest(BaseModel):
    state: DerivationState


class ResumeExportResponse(BaseModel):
    resume_text: str


class ProcessExportRequest(BaseModel):
    state: DerivationState


class ProcessExportResponse(BaseModel):
    process_text: str


class ResumeImportRequest(BaseModel):
    resume_text: str


class SentenceNumerationGenerateRequest(BaseModel):
    grammar_id: str
    sentence: str
    tokens: Optional[list[str]] = None
    split_mode: str = "C"
    legacy_root: Optional[str] = None


class TokenResolutionResponse(BaseModel):
    token: str
    lexicon_id: int
    candidate_lexicon_ids: list[int]


class SentenceNumerationGenerateResponse(BaseModel):
    memo: str
    lexicon_ids: list[int]
    token_resolutions: list[TokenResolutionResponse]
    numeration_text: str


class SentenceTokenizeResponse(BaseModel):
    tokens: list[str]


class DerivationInitFromSentenceResponse(BaseModel):
    numeration: SentenceNumerationGenerateResponse
    state: DerivationState


class GrammarOptionResponse(BaseModel):
    grammar_id: str
    folder: str
    uses_lexicon_all: bool
    display_name: str


class NumerationFileEntry(BaseModel):
    path: str
    file_name: str
    memo: str
    source: str


class NumerationLoadRequest(BaseModel):
    grammar_id: str
    path: str
    legacy_root: Optional[str] = None


class NumerationLoadResponse(BaseModel):
    path: str
    numeration_text: str
    memo: str


class NumerationSaveRequest(BaseModel):
    grammar_id: str
    numeration_text: str
    memo: Optional[str] = None
    legacy_root: Optional[str] = None


class NumerationSaveResponse(BaseModel):
    path: str
    numeration_text: str
    memo: str


class NumerationComposeRequest(BaseModel):
    memo: str
    lexicon_ids: list[int]
    plus_values: Optional[list[str]] = None
    idx_values: Optional[list[str]] = None


class NumerationComposeResponse(BaseModel):
    numeration_text: str


_UNINTERPRETABLE_PATTERN = re.compile(r",[0-9]+")
_HEAD_ASSIST_SEARCH_BUDGET_SECONDS = 10.0
_HEAD_ASSIST_SEARCH_MAX_DEPTH_CAP = 28
_HEAD_ASSIST_SEARCH_SINGLE_STEP_ALLOWANCE = 12
_HEAD_ASSIST_SEARCH_ROOT_LIMIT = 16
_HEAD_ASSIST_SEARCH_FRONTIER_LIMIT = 40000
_HEAD_ASSIST_SEARCH_MAX_NODES = 220000
_HEAD_ASSIST_SEARCH_WEIGHT = 0.5
_HEAD_ASSIST_DEFAULT_PARALLEL_CORES = 2
_HEAD_ASSIST_MAX_PARALLEL_CORES = 8
_BASELINE_SEARCH_MAX_DEPTH_CAP = 32
_BASELINE_SEARCH_MAX_NODES_CAP = 2_000_000
_BASELINE_SEARCH_BUDGET_SECONDS_CAP = 300.0


@dataclass
class _HeadAssistWorkerPayload:
    root_transitions: list[tuple[int, dict, int]]
    legacy_root: str
    rh_merge_version: str
    lh_merge_version: str
    search_signature_mode: str
    max_total_depth: int
    budget_seconds: float


@dataclass
class _BaselineSearchOutcome:
    status: str
    expanded_nodes: int
    steps_to_grammatical: Optional[int] = None


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    # .../syncsemphone-next/apps/api/app/api/v1/derivation.py -> project root
    return Path(__file__).resolve().parents[6]


def _extract_memo(numeration_text: str) -> str:
    first_line = numeration_text.splitlines()[0] if numeration_text.strip() != "" else ""
    cells = first_line.split("\t")
    return cells[0] if cells else ""


def _compose_numeration_text(
    memo: str,
    lexicon_ids: list[int],
    plus_values: list[str] | None = None,
    idx_values: list[str] | None = None,
) -> str:
    if len(lexicon_ids) > NUMERATION_SLOT_COUNT:
        raise ValueError(
            f"Too many lexicon ids: {len(lexicon_ids)} > {NUMERATION_SLOT_COUNT}"
        )

    line1 = [memo] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line2 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]
    line3 = [" "] + ["" for _ in range(NUMERATION_SLOT_COUNT)]

    for slot, lexicon_id in enumerate(lexicon_ids, start=1):
        line1[slot] = str(lexicon_id)
        if plus_values and slot - 1 < len(plus_values):
            line2[slot] = plus_values[slot - 1]
        if idx_values and slot - 1 < len(idx_values):
            idx_value = str(idx_values[slot - 1]).strip()
            line3[slot] = idx_value if idx_value != "" else str(slot)
        else:
            line3[slot] = str(slot)

    return "\n".join(["\t".join(line1), "\t".join(line2), "\t".join(line3)])


def _resolve_legacy_root(raw: Optional[str]) -> Path:
    return Path(raw).expanduser().resolve() if raw else _default_legacy_root()


def _count_uninterpretable_like_perl(state: DerivationState) -> int:
    raw = json.dumps(state.base, ensure_ascii=False, separators=(",", ":"))
    return len(_UNINTERPRETABLE_PATTERN.findall(raw))


def _is_grammatical_like_perl(state: DerivationState) -> bool:
    return _count_uninterpretable_like_perl(state) == 0


def _state_structural_signature(state: DerivationState) -> str:
    return json.dumps(
        {
            "grammar_id": state.grammar_id,
            "newnum": state.newnum,
            "basenum": state.basenum,
            "base": state.base,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _feature_core_for_packing(value: object) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "" or raw == "zero":
        return None
    rhs = raw.split(":", 1)[1] if ":" in raw else raw
    parts = [part.strip() for part in rhs.split(",")]
    if len(parts) <= 1 or not parts[1].isdigit():
        return None

    out = [parts[1]]
    if len(parts) > 2 and parts[2] != "":
        out.append(parts[2])
    if len(parts) > 4 and parts[4] in {"left", "right"}:
        out.append(parts[4])
    if len(parts) > 5 and parts[5] in {"head", "nonhead"}:
        out.append(parts[5])
    return "|".join(out)


def _pack_item_for_signature(item: object) -> object:
    if item == "zero":
        return "zero"
    if not isinstance(item, list):
        return str(item)

    category = str(item[1]) if len(item) > 1 else ""

    sy_core: list[str] = []
    if len(item) > 3 and isinstance(item[3], list):
        for value in item[3]:
            core = _feature_core_for_packing(value)
            if core:
                sy_core.append(core)

    sl_core = _feature_core_for_packing(item[4]) if len(item) > 4 else None

    se_core: list[str] = []
    if len(item) > 5 and isinstance(item[5], list):
        for value in item[5]:
            core = _feature_core_for_packing(value)
            if core:
                se_core.append(core)

    pr_core: list[str] = []
    if len(item) > 2 and isinstance(item[2], list):
        for triple in item[2]:
            if not isinstance(triple, list):
                continue
            for value in triple:
                core = _feature_core_for_packing(value)
                if core:
                    pr_core.append(core)

    wo_core: list[object] = []
    if len(item) > 7 and isinstance(item[7], list):
        for daughter in item[7]:
            if daughter == "zero":
                wo_core.append("zero")
            elif isinstance(daughter, list):
                wo_core.append(_pack_item_for_signature(daughter))
            else:
                wo_core.append(str(daughter))

    return (
        category,
        tuple(sorted(sy_core)),
        tuple(sorted(se_core)),
        tuple(sorted(pr_core)),
        sl_core,
        tuple(wo_core),
    )


def _state_packed_signature(state: DerivationState) -> str:
    rows = [_pack_item_for_signature(state.base[idx]) for idx in range(1, state.basenum + 1)]
    return json.dumps(
        {
            "grammar_id": state.grammar_id,
            "newnum": state.newnum,
            "basenum": state.basenum,
            "rows": rows,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _resolve_head_assist_signature_mode(mode: Optional[str]) -> str:
    if mode is None:
        return "structural"
    normalized = mode.strip().lower()
    if normalized in {"packed", "structural"}:
        return normalized
    raise ValueError(
        f"Unsupported search_signature_mode: {mode}. Use packed/structural."
    )


def _execute_candidate_for_assist(
    *,
    state: DerivationState,
    candidate: RuleCandidate,
    fallback_left: int,
    fallback_right: int,
    rh_merge_version: str,
    lh_merge_version: str,
) -> tuple[int, int, DerivationState]:
    actual_left = candidate.left if candidate.left is not None else fallback_left
    actual_right = candidate.right if candidate.right is not None else fallback_right

    if candidate.rule_kind == "single":
        check_value = candidate.check
        if check_value is None:
            raise ValueError("single candidate requires check value")
        next_state = execute_single_merge(
            state=state,
            rule_name=candidate.rule_name,
            check=check_value,
        )
        return actual_left, actual_right, next_state

    if candidate.rule_name == "RH-Merge":
        rule_version = rh_merge_version
    elif candidate.rule_name == "LH-Merge":
        rule_version = lh_merge_version
    else:
        rule_version = "03"
    next_state = execute_double_merge(
        state=state,
        rule_name=candidate.rule_name,
        left=actual_left,
        right=actual_right,
        rule_version=rule_version,
    )
    return actual_left, actual_right, next_state


def _enumerate_candidate_transitions(
    *,
    state: DerivationState,
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
    state_signature_fn: Callable[[DerivationState], str],
    cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]],
) -> list[tuple[RuleCandidate, int, int, DerivationState]]:
    state_key = state_signature_fn(state)
    cached = cache.get(state_key)
    if cached is not None:
        return cached

    transitions: list[tuple[RuleCandidate, int, int, DerivationState]] = []
    seen_actions: set[tuple[int, str, str, int, int, int]] = set()

    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            candidates = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=legacy_root,
                rh_merge_version=rh_merge_version,
                lh_merge_version=lh_merge_version,
            )
            for candidate in candidates:
                actual_left = candidate.left if candidate.left is not None else left
                actual_right = candidate.right if candidate.right is not None else right
                action_key = (
                    candidate.rule_number,
                    candidate.rule_name,
                    candidate.rule_kind,
                    actual_left,
                    actual_right,
                    candidate.check if candidate.check is not None else -1,
                )
                if action_key in seen_actions:
                    continue
                seen_actions.add(action_key)

                try:
                    _, _, next_state = _execute_candidate_for_assist(
                        state=state,
                        candidate=candidate,
                        fallback_left=left,
                        fallback_right=right,
                        rh_merge_version=rh_merge_version,
                        lh_merge_version=lh_merge_version,
                    )
                except ValueError:
                    continue
                if state_signature_fn(next_state) == state_key:
                    continue
                transitions.append((candidate, actual_left, actual_right, next_state))

    cache[state_key] = transitions
    return transitions


def _head_assist_transition_rank_key(
    row: tuple[RuleCandidate, int, int, DerivationState]
) -> tuple[int, int, int, int, int, int]:
    candidate, left, right, next_state = row
    return (
        _count_uninterpretable_like_perl(next_state),
        next_state.basenum,
        candidate.rule_number,
        left,
        right,
        candidate.check if candidate.check is not None else 0,
    )


def _reduce_transitions_with_conservative_dpor(
    transitions: list[tuple[RuleCandidate, int, int, DerivationState]],
    *,
    successor_signature_fn: Callable[[DerivationState], str],
) -> list[tuple[RuleCandidate, int, int, DerivationState]]:
    # 保守運用: 同一状態に収束する遷移だけを1本に畳む（到達集合は維持）。
    selected: dict[str, tuple[RuleCandidate, int, int, DerivationState]] = {}
    for row in sorted(transitions, key=_head_assist_transition_rank_key):
        sig = successor_signature_fn(row[3])
        if sig in selected:
            continue
        selected[sig] = row
    return list(selected.values())


def _resolve_head_assist_max_total_depth(state: DerivationState) -> int:
    merge_only_bound = max(1, state.basenum - 1)
    bound_with_single_rules = merge_only_bound + _HEAD_ASSIST_SEARCH_SINGLE_STEP_ALLOWANCE
    return max(merge_only_bound, min(_HEAD_ASSIST_SEARCH_MAX_DEPTH_CAP, bound_with_single_rules))


def _find_item_index_by_id(state: DerivationState, item_id: str) -> Optional[int]:
    for index in range(1, state.basenum + 1):
        item = state.base[index]
        if isinstance(item, list) and len(item) > 0 and str(item[0]) == item_id:
            return index
    return None


def _known_replay_sequence_for_state(state: DerivationState) -> Optional[list[tuple[str, str, str]]]:
    memo = state.memo.strip()
    if state.grammar_id == "imi01" and memo == "ジョンがメアリをスケートボードで追いかけた":
        return [
            ("LH-Merge", "x7-1", "x8-1"),
            ("RH-Merge", "x5-1", "x6-1"),
            ("LH-Merge", "x1-1", "x2-1"),
            ("LH-Merge", "x3-1", "x4-1"),
            ("RH-Merge", "x3-1", "x7-1"),
            ("RH-Merge", "x6-1", "x7-1"),
            ("RH-Merge", "x1-1", "x7-1"),
        ]
    return None


def _replay_known_sequence_diagnostics(
    *,
    state: DerivationState,
    known_sequence: list[tuple[str, str, str]],
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
) -> tuple[bool, DerivationState, list[ReplayStepTraceResponse]]:
    working = state.model_copy(deep=True)
    trace: list[ReplayStepTraceResponse] = []
    for step_no, (rule_name, left_id, right_id) in enumerate(known_sequence, start=1):
        left_index = _find_item_index_by_id(working, left_id)
        right_index = _find_item_index_by_id(working, right_id)
        unresolved_before = _count_uninterpretable_like_perl(working)
        basenum_before = working.basenum
        candidate_rule_names: list[str] = []
        rule_available = False

        if left_index is not None and right_index is not None:
            candidates = list_merge_candidates(
                state=working,
                left=left_index,
                right=right_index,
                legacy_root=legacy_root,
                rh_merge_version=rh_merge_version,
                lh_merge_version=lh_merge_version,
            )
            candidate_rule_names = [candidate.rule_name for candidate in candidates]
            rule_available = rule_name in candidate_rule_names

        if left_index is None or right_index is None or not rule_available:
            trace.append(
                ReplayStepTraceResponse(
                    step=step_no,
                    rule_name=rule_name,
                    left_id=left_id,
                    right_id=right_id,
                    left_index=left_index,
                    right_index=right_index,
                    candidate_rule_names=candidate_rule_names,
                    rule_available=rule_available,
                    unresolved_before=unresolved_before,
                    unresolved_after=None,
                    basenum_before=basenum_before,
                    basenum_after=None,
                )
            )
            return False, working, trace

        rule_version = (
            rh_merge_version
            if rule_name == "RH-Merge"
            else lh_merge_version if rule_name == "LH-Merge" else "03"
        )
        try:
            working = execute_double_merge(
                state=working,
                rule_name=rule_name,
                left=left_index,
                right=right_index,
                rule_version=rule_version,
            )
        except ValueError:
            trace.append(
                ReplayStepTraceResponse(
                    step=step_no,
                    rule_name=rule_name,
                    left_id=left_id,
                    right_id=right_id,
                    left_index=left_index,
                    right_index=right_index,
                    candidate_rule_names=candidate_rule_names,
                    rule_available=rule_available,
                    unresolved_before=unresolved_before,
                    unresolved_after=None,
                    basenum_before=basenum_before,
                    basenum_after=None,
                )
            )
            return False, working, trace

        trace.append(
            ReplayStepTraceResponse(
                step=step_no,
                rule_name=rule_name,
                left_id=left_id,
                right_id=right_id,
                left_index=left_index,
                right_index=right_index,
                candidate_rule_names=candidate_rule_names,
                rule_available=True,
                unresolved_before=unresolved_before,
                unresolved_after=_count_uninterpretable_like_perl(working),
                basenum_before=basenum_before,
                basenum_after=working.basenum,
            )
        )

    return _is_grammatical_like_perl(working), working, trace


def _resolve_baseline_max_depth(
    requested_depth: int,
    *,
    state: DerivationState,
) -> int:
    computed = _resolve_head_assist_max_total_depth(state)
    if requested_depth <= 0:
        return 1
    clamped = min(_BASELINE_SEARCH_MAX_DEPTH_CAP, requested_depth)
    return max(1, min(clamped, computed))


def _resolve_baseline_budget_seconds(requested_budget: float) -> float:
    if requested_budget <= 0:
        return 0.1
    return min(_BASELINE_SEARCH_BUDGET_SECONDS_CAP, requested_budget)


def _resolve_baseline_max_nodes(requested_max_nodes: int) -> int:
    if requested_max_nodes <= 0:
        return 10
    return min(_BASELINE_SEARCH_MAX_NODES_CAP, requested_max_nodes)


def _baseline_find_grammatical_within_depth(
    *,
    state: DerivationState,
    max_total_depth: int,
    deadline: float,
    max_nodes: int,
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
) -> _BaselineSearchOutcome:
    if _is_grammatical_like_perl(state):
        return _BaselineSearchOutcome(status="reachable", expanded_nodes=0, steps_to_grammatical=0)

    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]] = {}
    expanded_nodes = 0

    def dfs(current: DerivationState, remaining_depth: int) -> list[tuple[str, int, int, Optional[int]]] | None | bool:
        nonlocal expanded_nodes
        if time.perf_counter() >= deadline:
            return False
        if expanded_nodes >= max_nodes:
            return False
        if _is_grammatical_like_perl(current):
            return []
        if remaining_depth <= 0:
            return None

        transitions = _enumerate_candidate_transitions(
            state=current,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            state_signature_fn=_state_structural_signature,
            cache=transition_cache,
        )
        ordered_transitions = sorted(transitions, key=_head_assist_transition_rank_key)
        for candidate, actual_left, actual_right, next_state in ordered_transitions:
            if time.perf_counter() >= deadline:
                return False
            if expanded_nodes >= max_nodes:
                return False
            expanded_nodes += 1
            child_result = dfs(next_state, remaining_depth - 1)
            if child_result is False:
                return False
            if child_result is None:
                continue
            return [
                (
                    candidate.rule_name,
                    actual_left,
                    actual_right,
                    candidate.check,
                )
            ] + child_result
        return None

    for depth in range(1, max_total_depth + 1):
        result = dfs(state, depth)
        if result is False:
            return _BaselineSearchOutcome(
                status="unknown",
                expanded_nodes=expanded_nodes,
                steps_to_grammatical=None,
            )
        if result is None:
            continue
        return _BaselineSearchOutcome(
            status="reachable",
            expanded_nodes=expanded_nodes,
            steps_to_grammatical=len(result),
        )

    return _BaselineSearchOutcome(
        status="unreachable",
        expanded_nodes=expanded_nodes,
        steps_to_grammatical=None,
    )


def _dls_reaches_grammatical(
    *,
    state: DerivationState,
    remaining_depth: int,
    deadline: float,
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
    search_signature_fn: Callable[[DerivationState], str],
    transition_signature_fn: Callable[[DerivationState], str],
    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]],
    transposition_remaining_depth: dict[str, int],
) -> Optional[bool]:
    if time.perf_counter() >= deadline:
        return None

    unresolved = _count_uninterpretable_like_perl(state)
    if unresolved == 0:
        return True
    if remaining_depth <= 0:
        return False

    state_sig = search_signature_fn(state)
    best_remaining = transposition_remaining_depth.get(state_sig)
    if best_remaining is not None and best_remaining >= remaining_depth:
        return False
    transposition_remaining_depth[state_sig] = remaining_depth

    transitions = _enumerate_candidate_transitions(
        state=state,
        legacy_root=legacy_root,
        rh_merge_version=rh_merge_version,
        lh_merge_version=lh_merge_version,
        state_signature_fn=transition_signature_fn,
        cache=transition_cache,
    )
    if not transitions:
        return False

    reduced_transitions = _reduce_transitions_with_conservative_dpor(
        transitions,
        successor_signature_fn=search_signature_fn,
    )
    for _, _, _, next_state in reduced_transitions:
        result = _dls_reaches_grammatical(
            state=next_state,
            remaining_depth=remaining_depth - 1,
            deadline=deadline,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            search_signature_fn=search_signature_fn,
            transition_signature_fn=transition_signature_fn,
            transition_cache=transition_cache,
            transposition_remaining_depth=transposition_remaining_depth,
        )
        if result is None:
            return None
        if result:
            return True
    return False


def _estimate_steps_for_root_transition(
    *,
    root_state: DerivationState,
    max_total_depth: int,
    deadline: float,
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
    search_signature_fn: Callable[[DerivationState], str],
    transition_signature_fn: Callable[[DerivationState], str],
    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]],
) -> Optional[int]:
    transposition_remaining_depth: dict[str, int] = {}
    max_additional_depth = max_total_depth - 1
    for additional_depth in range(0, max_additional_depth + 1):
        result = _dls_reaches_grammatical(
            state=root_state,
            remaining_depth=additional_depth,
            deadline=deadline,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            search_signature_fn=search_signature_fn,
            transition_signature_fn=transition_signature_fn,
            transition_cache=transition_cache,
            transposition_remaining_depth=transposition_remaining_depth,
        )
        if result is None:
            return None
        if result:
            return additional_depth + 1
    return None


def _estimate_steps_by_first_action(
    *,
    root_transitions: list[tuple[int, DerivationState, int]],
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
    max_total_depth: int,
    budget_seconds: float,
    search_signature_fn: Callable[[DerivationState], str],
    transition_signature_fn: Callable[[DerivationState], str],
    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]],
) -> dict[int, int]:
    if not root_transitions:
        return {}

    deadline = time.perf_counter() + max(0.1, budget_seconds)
    best_steps: dict[int, int] = {}
    counter = itertools.count()
    frontier: list[tuple[float, int, int, int, int, int, DerivationState]] = []
    visited_depth: dict[tuple[int, str], int] = {}

    ordered_roots = sorted(root_transitions, key=lambda row: (row[2], row[1].basenum, row[0]))
    for action_index, next_state, after_unresolved in ordered_roots:
        if after_unresolved == 0:
            best_steps[action_index] = 1
            continue
        if max_total_depth <= 1:
            continue
        sig = search_signature_fn(next_state)
        visited_depth[(action_index, sig)] = 1
        score = 1 + (_HEAD_ASSIST_SEARCH_WEIGHT * after_unresolved)
        heapq.heappush(
            frontier,
            (
                score,
                1,
                after_unresolved,
                next_state.basenum,
                next(counter),
                action_index,
                next_state,
            ),
        )

    expanded_nodes = 0
    while frontier and time.perf_counter() < deadline:
        if expanded_nodes >= _HEAD_ASSIST_SEARCH_MAX_NODES:
            break
        _, depth, unresolved, _, _, action_index, state = heapq.heappop(frontier)
        if action_index in best_steps and best_steps[action_index] <= depth:
            continue
        if depth >= max_total_depth:
            continue
        if unresolved == 0:
            best_steps[action_index] = min(best_steps.get(action_index, 10_000_000), depth)
            continue

        expanded_nodes += 1
        transitions = _enumerate_candidate_transitions(
            state=state,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            state_signature_fn=transition_signature_fn,
            cache=transition_cache,
        )
        reduced_transitions = _reduce_transitions_with_conservative_dpor(
            transitions,
            successor_signature_fn=search_signature_fn,
        )
        for _, _, _, next_state in reduced_transitions:
            if time.perf_counter() >= deadline:
                break
            next_depth = depth + 1
            if next_depth > max_total_depth:
                continue
            if action_index in best_steps and best_steps[action_index] <= next_depth:
                continue
            next_sig = search_signature_fn(next_state)
            key = (action_index, next_sig)
            known_depth = visited_depth.get(key)
            if known_depth is not None and known_depth <= next_depth:
                continue
            visited_depth[key] = next_depth
            unresolved_after = _count_uninterpretable_like_perl(next_state)
            if unresolved_after == 0:
                best_steps[action_index] = next_depth
                continue
            score = next_depth + (_HEAD_ASSIST_SEARCH_WEIGHT * unresolved_after)
            heapq.heappush(
                frontier,
                (
                    score,
                    next_depth,
                    unresolved_after,
                    next_state.basenum,
                    next(counter),
                    action_index,
                    next_state,
                ),
            )
        if len(frontier) > _HEAD_ASSIST_SEARCH_FRONTIER_LIMIT:
            frontier = heapq.nsmallest(_HEAD_ASSIST_SEARCH_FRONTIER_LIMIT, frontier)
            heapq.heapify(frontier)

    return best_steps


def _resolve_head_assist_parallel_cores(
    requested_cores: Optional[int],
    *,
    cpu_count_override: Optional[int] = None,
) -> int:
    cpu_count_raw = cpu_count_override if cpu_count_override is not None else os.cpu_count()
    cpu_count = cpu_count_raw if isinstance(cpu_count_raw, int) and cpu_count_raw > 0 else 1
    max_allowed = max(1, min(cpu_count, _HEAD_ASSIST_MAX_PARALLEL_CORES))
    if requested_cores is None:
        return min(_HEAD_ASSIST_DEFAULT_PARALLEL_CORES, max_allowed)
    return max(1, min(requested_cores, max_allowed))


def _estimate_steps_by_first_action_worker(payload: _HeadAssistWorkerPayload) -> dict[int, int]:
    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]] = {}
    reconstructed_transitions = [
        (action_index, DerivationState.model_validate(state_payload), after_unresolved)
        for action_index, state_payload, after_unresolved in payload.root_transitions
    ]
    search_signature_fn = (
        _state_packed_signature
        if payload.search_signature_mode == "packed"
        else _state_structural_signature
    )
    return _estimate_steps_by_first_action(
        root_transitions=reconstructed_transitions,
        legacy_root=Path(payload.legacy_root),
        rh_merge_version=payload.rh_merge_version,
        lh_merge_version=payload.lh_merge_version,
        max_total_depth=payload.max_total_depth,
        budget_seconds=payload.budget_seconds,
        search_signature_fn=search_signature_fn,
        transition_signature_fn=_state_structural_signature,
        transition_cache=transition_cache,
    )


def _estimate_steps_by_first_action_parallel(
    *,
    root_transitions: list[tuple[int, DerivationState, int]],
    legacy_root: Path,
    rh_merge_version: str,
    lh_merge_version: str,
    search_signature_mode: str,
    parallel_cores: int,
    max_total_depth: int,
    budget_seconds: float,
    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]],
) -> dict[int, int]:
    if len(root_transitions) == 0:
        return {}
    if parallel_cores <= 1 or len(root_transitions) <= 1:
        search_signature_fn = (
            _state_packed_signature
            if search_signature_mode == "packed"
            else _state_structural_signature
        )
        return _estimate_steps_by_first_action(
            root_transitions=root_transitions,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            max_total_depth=max_total_depth,
            budget_seconds=budget_seconds,
            search_signature_fn=search_signature_fn,
            transition_signature_fn=_state_structural_signature,
            transition_cache=transition_cache,
        )

    chunk_count = min(parallel_cores, len(root_transitions))
    chunks: list[list[tuple[int, DerivationState, int]]] = [[] for _ in range(chunk_count)]
    for index, row in enumerate(root_transitions):
        chunks[index % chunk_count].append(row)
    chunks = [rows for rows in chunks if rows]
    if len(chunks) <= 1:
        search_signature_fn = (
            _state_packed_signature
            if search_signature_mode == "packed"
            else _state_structural_signature
        )
        return _estimate_steps_by_first_action(
            root_transitions=root_transitions,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            max_total_depth=max_total_depth,
            budget_seconds=budget_seconds,
            search_signature_fn=search_signature_fn,
            transition_signature_fn=_state_structural_signature,
            transition_cache=transition_cache,
        )

    payloads = [
        _HeadAssistWorkerPayload(
            root_transitions=[
                (
                    action_index,
                    state.model_dump(mode="python"),
                    after_unresolved,
                )
                for action_index, state, after_unresolved in chunk
            ],
            legacy_root=str(legacy_root),
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            search_signature_mode=search_signature_mode,
            max_total_depth=max_total_depth,
            budget_seconds=budget_seconds,
        )
        for chunk in chunks
    ]

    try:
        context = mp.get_context("spawn")
        with context.Pool(processes=len(payloads)) as pool:
            results = pool.map(_estimate_steps_by_first_action_worker, payloads)
    except Exception:
        search_signature_fn = (
            _state_packed_signature
            if search_signature_mode == "packed"
            else _state_structural_signature
        )
        return _estimate_steps_by_first_action(
            root_transitions=root_transitions,
            legacy_root=legacy_root,
            rh_merge_version=rh_merge_version,
            lh_merge_version=lh_merge_version,
            max_total_depth=max_total_depth,
            budget_seconds=budget_seconds,
            search_signature_fn=search_signature_fn,
            transition_signature_fn=_state_structural_signature,
            transition_cache=transition_cache,
        )

    merged: dict[int, int] = {}
    for partial in results:
        for action_index, steps in partial.items():
            if action_index not in merged or steps < merged[action_index]:
                merged[action_index] = steps
    return merged


def _numeration_dirs(legacy_root: Path, grammar_id: str) -> dict[str, Path]:
    profile = get_grammar_profile(grammar_id)
    base = legacy_root / profile.folder
    return {
        "set": base / "set-numeration",
        "saved": base / "numeration",
    }


def _ensure_under(base_dir: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


@router.get("/grammars", response_model=list[GrammarOptionResponse])
def derivation_grammars() -> list[GrammarOptionResponse]:
    entries = load_legacy_grammar_entries(_default_legacy_root())
    if not entries:
        fallback = [
            ("imi01", "imi01", True),
            ("imi02", "imi02", True),
            ("imi03", "imi03", True),
            ("japanese2", "japanese2", False),
        ]
        return [
            GrammarOptionResponse(
                grammar_id=grammar_id,
                folder=folder,
                uses_lexicon_all=uses_lexicon_all,
                display_name=grammar_id,
            )
            for grammar_id, folder, uses_lexicon_all in fallback
        ]
    return [
        GrammarOptionResponse(
            grammar_id=entry.grammar_id,
            folder=entry.folder,
            uses_lexicon_all=entry.uses_lexicon_all,
            display_name=entry.display_name,
        )
        for entry in entries
    ]


@router.get("/rules/{grammar_id}", response_model=list[RuleCandidate])
def derivation_rules(grammar_id: str, legacy_root: Optional[str] = None) -> list[RuleCandidate]:
    root = _resolve_legacy_root(legacy_root)
    try:
        rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [
        RuleCandidate(
            rule_number=rule.number,
            rule_name=rule.name,
            rule_kind="single" if rule.kind == 1 else "double",
        )
        for rule in rules
    ]


@router.get("/numeration/files", response_model=list[NumerationFileEntry])
def derivation_numeration_files(
    grammar_id: str,
    source: str = "set",
    legacy_root: Optional[str] = None,
) -> list[NumerationFileEntry]:
    root = _resolve_legacy_root(legacy_root)
    try:
        dirs = _numeration_dirs(root, grammar_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if source not in dirs:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}. Use set/saved.")

    target_dir = dirs[source]
    if not target_dir.exists():
        return []

    rows: list[NumerationFileEntry] = []
    for path in sorted(target_dir.glob("*.num")):
        text = path.read_text(encoding="utf-8")
        rows.append(
            NumerationFileEntry(
                path=str(path.resolve()),
                file_name=path.name,
                memo=_extract_memo(text),
                source=source,
            )
        )
    return rows


@router.post("/numeration/load", response_model=NumerationLoadResponse)
def derivation_numeration_load(request: NumerationLoadRequest) -> NumerationLoadResponse:
    root = _resolve_legacy_root(request.legacy_root)
    dirs = _numeration_dirs(root, request.grammar_id)
    path = Path(request.path).expanduser().resolve()
    allowed = _ensure_under(dirs["set"], path) or _ensure_under(dirs["saved"], path)
    if not allowed:
        raise HTTPException(status_code=400, detail="Path is outside allowed numeration directories.")
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Numeration file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return NumerationLoadResponse(path=str(path), numeration_text=text, memo=_extract_memo(text))


@router.post("/numeration/save", response_model=NumerationSaveResponse)
def derivation_numeration_save(request: NumerationSaveRequest) -> NumerationSaveResponse:
    root = _resolve_legacy_root(request.legacy_root)
    dirs = _numeration_dirs(root, request.grammar_id)
    target_dir = dirs["saved"]
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    path = target_dir / f"{timestamp}.num"

    text = request.numeration_text.strip("\n")
    memo = request.memo if request.memo is not None else _extract_memo(text)
    if memo.strip() != "":
        lines = text.splitlines()
        if lines:
            cells = lines[0].split("\t")
            if cells:
                cells[0] = memo
                lines[0] = "\t".join(cells)
                text = "\n".join(lines)

    path.write_text(text + "\n", encoding="utf-8")
    return NumerationSaveResponse(path=str(path.resolve()), numeration_text=text, memo=_extract_memo(text))


@router.post("/numeration/compose", response_model=NumerationComposeResponse)
def derivation_numeration_compose(request: NumerationComposeRequest) -> NumerationComposeResponse:
    try:
        numeration_text = _compose_numeration_text(
            memo=request.memo,
            lexicon_ids=request.lexicon_ids,
            plus_values=request.plus_values,
            idx_values=request.idx_values,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NumerationComposeResponse(numeration_text=numeration_text)


@router.post("/init", response_model=DerivationState)
def init_derivation(request: DerivationInitRequest) -> DerivationState:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        return build_initial_derivation_state(
            grammar_id=request.grammar_id,
            numeration_text=request.numeration_text,
            legacy_root=legacy_root,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/numeration/generate",
    response_model=SentenceNumerationGenerateResponse,
)
def generate_numeration(request: SentenceNumerationGenerateRequest) -> SentenceNumerationGenerateResponse:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        generated = generate_numeration_from_sentence(
            grammar_id=request.grammar_id,
            sentence=request.sentence,
            legacy_root=legacy_root,
            tokens=request.tokens,
            split_mode=request.split_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SentenceNumerationGenerateResponse(
        memo=generated.memo,
        lexicon_ids=generated.lexicon_ids,
        token_resolutions=[
            TokenResolutionResponse(
                token=row.token,
                lexicon_id=row.lexicon_id,
                candidate_lexicon_ids=row.candidate_lexicon_ids,
            )
            for row in generated.token_resolutions
        ],
        numeration_text=generated.numeration_text,
    )


@router.post(
    "/numeration/tokenize",
    response_model=SentenceTokenizeResponse,
)
def tokenize_sentence(request: SentenceNumerationGenerateRequest) -> SentenceTokenizeResponse:
    if request.sentence.strip() == "":
        raise HTTPException(status_code=400, detail="sentence must not be empty")
    try:
        tokenizer = SudachiMorphTokenizer(dictionary="core")
        tokens = tokenizer.tokenize(request.sentence, split_mode=request.split_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SentenceTokenizeResponse(tokens=tokens)


@router.post(
    "/init/from-sentence",
    response_model=DerivationInitFromSentenceResponse,
)
def init_derivation_from_sentence(
    request: SentenceNumerationGenerateRequest,
) -> DerivationInitFromSentenceResponse:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        generated = generate_numeration_from_sentence(
            grammar_id=request.grammar_id,
            sentence=request.sentence,
            legacy_root=legacy_root,
            tokens=request.tokens,
            split_mode=request.split_mode,
        )
        state = build_initial_derivation_state(
            grammar_id=request.grammar_id,
            numeration_text=generated.numeration_text,
            legacy_root=legacy_root,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DerivationInitFromSentenceResponse(
        numeration=SentenceNumerationGenerateResponse(
            memo=generated.memo,
            lexicon_ids=generated.lexicon_ids,
            token_resolutions=[
                TokenResolutionResponse(
                    token=row.token,
                    lexicon_id=row.lexicon_id,
                    candidate_lexicon_ids=row.candidate_lexicon_ids,
                )
                for row in generated.token_resolutions
            ],
            numeration_text=generated.numeration_text,
        ),
        state=state,
    )


@router.post("/candidates", response_model=list[RuleCandidate])
def derivation_candidates(request: DerivationCandidatesRequest) -> list[RuleCandidate]:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        return list_merge_candidates(
            state=request.state,
            left=request.left,
            right=request.right,
            legacy_root=legacy_root,
            rh_merge_version=request.rh_merge_version,
            lh_merge_version=request.lh_merge_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/head-assist", response_model=list[HeadAssistSuggestionResponse])
def derivation_head_assist(request: DerivationHeadAssistRequest) -> list[HeadAssistSuggestionResponse]:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        top_k = max(1, min(request.top_k, 5))
        before_unresolved = _count_uninterpretable_like_perl(request.state)
        profile = resolve_rule_versions(
            profile=get_grammar_profile(request.state.grammar_id),
            legacy_root=legacy_root,
        )
        search_signature_mode = _resolve_head_assist_signature_mode(
            request.search_signature_mode
        )
        rh_version = request.rh_merge_version or profile.rh_merge_version
        lh_version = request.lh_merge_version or profile.lh_merge_version

        transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]] = {}
        transitions = _enumerate_candidate_transitions(
            state=request.state,
            legacy_root=legacy_root,
            rh_merge_version=rh_version,
            lh_merge_version=lh_version,
            state_signature_fn=_state_structural_signature,
            cache=transition_cache,
        )

        transition_rows: list[tuple[int, RuleCandidate, int, int, DerivationState, int, int, bool]] = []
        for action_index, (candidate, actual_left, actual_right, next_state) in enumerate(transitions):
            after_unresolved = _count_uninterpretable_like_perl(next_state)
            unresolved_delta = before_unresolved - after_unresolved
            transition_rows.append(
                (
                    action_index,
                    candidate,
                    actual_left,
                    actual_right,
                    next_state,
                    after_unresolved,
                    unresolved_delta,
                    after_unresolved == 0,
                )
            )
        transition_rows.sort(
            key=lambda row: (
                row[5],
                row[4].basenum,
                row[1].rule_number,
                row[2],
                row[3],
                row[1].check if row[1].check is not None else 0,
            )
        )
        root_search_limit = max(_HEAD_ASSIST_SEARCH_ROOT_LIMIT, top_k * 3)
        root_transitions_for_search = [
            (action_index, next_state, after_unresolved)
            for (
                action_index,
                _candidate,
                _actual_left,
                _actual_right,
                next_state,
                after_unresolved,
                _unresolved_delta,
                _grammatical_after,
            ) in transition_rows[:root_search_limit]
        ]
        parallel_cores = _resolve_head_assist_parallel_cores(request.parallel_cores)
        max_total_depth = _resolve_head_assist_max_total_depth(request.state)
        steps_by_first_action = _estimate_steps_by_first_action_parallel(
            root_transitions=root_transitions_for_search,
            legacy_root=legacy_root,
            rh_merge_version=rh_version,
            lh_merge_version=lh_version,
            search_signature_mode=search_signature_mode,
            parallel_cores=parallel_cores,
            max_total_depth=max_total_depth,
            budget_seconds=_HEAD_ASSIST_SEARCH_BUDGET_SECONDS,
            transition_cache=transition_cache,
        )
        suggestions: list[HeadAssistSuggestionResponse] = []
        for (
            action_index,
            candidate,
            actual_left,
            actual_right,
            next_state,
            after_unresolved,
            unresolved_delta,
            grammatical_after,
        ) in transition_rows:
            steps_to_goal = steps_by_first_action.get(action_index)
            if steps_to_goal is None and grammatical_after:
                steps_to_goal = 1
            reachable = steps_to_goal is not None

            suggestions.append(
                HeadAssistSuggestionResponse(
                    rank=0,
                    rule_number=candidate.rule_number,
                    rule_name=candidate.rule_name,
                    rule_kind=candidate.rule_kind,
                    left=actual_left,
                    right=actual_right,
                    check=candidate.check,
                    unresolved_before=before_unresolved,
                    unresolved_after=after_unresolved,
                    unresolved_delta=unresolved_delta,
                    grammatical_after=grammatical_after,
                    basenum_before=request.state.basenum,
                    basenum_after=next_state.basenum,
                    reachable_grammatical=reachable,
                    steps_to_grammatical=steps_to_goal,
                )
            )

        suggestions.sort(
            key=lambda row: (
                0 if row.reachable_grammatical else 1,
                row.steps_to_grammatical if row.steps_to_grammatical is not None else 10_000,
                row.unresolved_after,
                row.basenum_after,
                -row.unresolved_delta,
                row.rule_number,
                row.left,
                row.right,
                row.check if row.check is not None else 0,
            )
        )
        for idx, suggestion in enumerate(suggestions[:top_k], start=1):
            suggestion.rank = idx
        return suggestions[:top_k]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/head-assist/diagnose", response_model=DerivationReachabilityDiagnoseResponse)
def derivation_head_assist_diagnose(
    request: DerivationReachabilityDiagnoseRequest,
) -> DerivationReachabilityDiagnoseResponse:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        profile = resolve_rule_versions(
            profile=get_grammar_profile(request.state.grammar_id),
            legacy_root=legacy_root,
        )
        rh_version = request.rh_merge_version or profile.rh_merge_version
        lh_version = request.lh_merge_version or profile.lh_merge_version

        known_sequence = _known_replay_sequence_for_state(request.state)
        if known_sequence is None:
            strict_replay = StrictReplayDiagnosticResponse(
                available=False,
                reached_grammatical=False,
                final_unresolved=_count_uninterpretable_like_perl(request.state),
                trace=[],
            )
        else:
            reached, replay_final_state, trace = _replay_known_sequence_diagnostics(
                state=request.state,
                known_sequence=known_sequence,
                legacy_root=legacy_root,
                rh_merge_version=rh_version,
                lh_merge_version=lh_version,
            )
            strict_replay = StrictReplayDiagnosticResponse(
                available=True,
                reached_grammatical=reached,
                final_unresolved=_count_uninterpretable_like_perl(replay_final_state),
                trace=trace,
            )

        baseline_max_depth = _resolve_baseline_max_depth(
            request.baseline_max_depth,
            state=request.state,
        )
        baseline_budget_seconds = _resolve_baseline_budget_seconds(
            request.baseline_budget_seconds
        )
        baseline_max_nodes = _resolve_baseline_max_nodes(request.baseline_max_nodes)

        baseline_deadline = time.perf_counter() + baseline_budget_seconds
        baseline_result = _baseline_find_grammatical_within_depth(
            state=request.state,
            max_total_depth=baseline_max_depth,
            deadline=baseline_deadline,
            max_nodes=baseline_max_nodes,
            legacy_root=legacy_root,
            rh_merge_version=rh_version,
            lh_merge_version=lh_version,
        )
        baseline_complete = BaselineReachabilityDiagnosticResponse(
            status=baseline_result.status,
            max_depth=baseline_max_depth,
            budget_seconds=baseline_budget_seconds,
            max_nodes=baseline_max_nodes,
            expanded_nodes=baseline_result.expanded_nodes,
            steps_to_grammatical=baseline_result.steps_to_grammatical,
        )

        return DerivationReachabilityDiagnoseResponse(
            strict_replay=strict_replay,
            baseline_complete=baseline_complete,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/execute", response_model=DerivationState)
def derivation_execute(request: DerivationExecuteRequest) -> DerivationState:
    legacy_root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    try:
        if request.rule_name is None and request.rule_number is None:
            raise ValueError("Either rule_name or rule_number is required")

        resolved_rule_name = request.rule_name
        if resolved_rule_name is None and request.rule_number is not None:
            resolved_rule_name = get_rule_name_by_number(
                grammar_id=request.state.grammar_id,
                rule_number=request.rule_number,
                legacy_root=legacy_root,
            )
            if resolved_rule_name is None:
                raise ValueError(f"Unknown rule_number: {request.rule_number}")

        if resolved_rule_name is not None and request.rule_number is not None:
            expected_number = get_rule_number_by_name(
                grammar_id=request.state.grammar_id,
                rule_name=resolved_rule_name,
                legacy_root=legacy_root,
            )
            if expected_number is not None and expected_number != request.rule_number:
                raise ValueError(
                    f"rule_name/rule_number mismatch: {resolved_rule_name} != {request.rule_number}"
                )

        single_rules = {"zero-Merge", "Pickup", "Landing", "Partitioning"}
        if resolved_rule_name in single_rules:
            check_value = request.check
            if check_value is None:
                if request.left is None:
                    raise ValueError("check (or left as alias) is required for single merge rules")
                check_value = request.left
            return execute_single_merge(
                state=request.state,
                rule_name=resolved_rule_name,
                check=check_value,
            )

        if request.left is None or request.right is None:
            raise ValueError("left/right are required for double merge rules")

        profile = resolve_rule_versions(
            profile=get_grammar_profile(request.state.grammar_id),
            legacy_root=legacy_root,
        )
        if resolved_rule_name == "RH-Merge":
            rule_version = request.rh_merge_version or profile.rh_merge_version
        elif resolved_rule_name == "LH-Merge":
            rule_version = request.lh_merge_version or profile.lh_merge_version
        else:
            rule_version = "03"
        return execute_double_merge(
            state=request.state,
            rule_name=resolved_rule_name,
            left=request.left,
            right=request.right,
            rule_version=rule_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/resume/export", response_model=ResumeExportResponse)
def resume_export(request: ResumeExportRequest) -> ResumeExportResponse:
    try:
        return ResumeExportResponse(resume_text=export_resume_text(request.state))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/process/export", response_model=ProcessExportResponse)
def process_export(request: ProcessExportRequest) -> ProcessExportResponse:
    try:
        return ProcessExportResponse(process_text=export_process_text_like_perl(request.state))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/resume/import", response_model=DerivationState)
def resume_import(request: ResumeImportRequest) -> DerivationState:
    try:
        return import_resume_text(request.resume_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
