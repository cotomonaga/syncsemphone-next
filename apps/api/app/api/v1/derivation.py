from __future__ import annotations

import json
import heapq
import itertools
import multiprocessing as mp
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

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


class DerivationReachabilityRequest(BaseModel):
    state: DerivationState
    max_evidences: int = 50
    offset: int = 0
    limit: int = 10
    parallel_cores: Optional[int] = None
    search_signature_mode: Optional[str] = None
    budget_seconds: float = 10.0
    max_nodes: int = 220000
    max_depth: int = 28
    return_process_text: bool = True
    legacy_root: Optional[str] = None
    rh_merge_version: Optional[str] = None
    lh_merge_version: Optional[str] = None


class ReachabilityRuleStepResponse(BaseModel):
    step: int
    rule_name: str
    rule_number: int
    rule_kind: str
    left: Optional[int] = None
    right: Optional[int] = None
    check: Optional[int] = None
    left_id: Optional[str] = None
    right_id: Optional[str] = None


class ReachabilityEvidenceResponse(BaseModel):
    rank: int
    steps_to_goal: int
    rule_sequence: list[ReachabilityRuleStepResponse]
    tree_root: dict[str, Any]
    process_text: Optional[str] = None


class ReachabilityMetricsResponse(BaseModel):
    expanded_nodes: int
    generated_nodes: int
    packed_nodes: int
    max_frontier: int
    elapsed_ms: int
    max_depth_reached: int
    actions_attempted: int


class ReachabilityCountsResponse(BaseModel):
    count_unit: str
    count_basis: str
    tree_signature_basis: str
    count_status: str
    goal_count_exact: Optional[str] = None
    total_exact: Optional[str] = None
    total_upper_bound_a_pair_only: str
    total_upper_bound_b_pair_rulemax: str
    rule_max_per_pair_bound: int
    rule_max_per_pair_observed: int
    shown_count: int
    offset: int
    limit: int
    shown_ratio_exact_percent: Optional[float] = None
    coverage_upper_bound_a_percent: float
    coverage_upper_bound_b_percent: float
    has_next: bool = False


class DerivationReachabilityResponse(BaseModel):
    status: str
    completed: bool
    reason: str
    metrics: ReachabilityMetricsResponse
    counts: ReachabilityCountsResponse
    evidences: list[ReachabilityEvidenceResponse]


class DerivationReachabilityJobStartResponse(BaseModel):
    job_id: str
    status: str
    created_at: float


class ReachabilityProgressResponse(BaseModel):
    percent: float
    phase: str
    message: str


class DerivationReachabilityJobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: float
    updated_at: float
    progress: ReachabilityProgressResponse
    metrics: Optional[ReachabilityMetricsResponse] = None
    counts: Optional[ReachabilityCountsResponse] = None
    reason: Optional[str] = None
    completed: Optional[bool] = None
    error: Optional[str] = None


class DerivationReachabilityEvidencePageResponse(BaseModel):
    job_id: str
    status: str
    counts: ReachabilityCountsResponse
    evidences: list[ReachabilityEvidenceResponse]


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
_HEAD_ASSIST_MAX_EVIDENCES_CAP = 200
_HEAD_ASSIST_PAGE_LIMIT_CAP = 100
_HEAD_ASSIST_JOBS_TTL_SECONDS = 1800.0
_BASELINE_SEARCH_MAX_DEPTH_CAP = 32
_BASELINE_SEARCH_MAX_NODES_CAP = 2_000_000
_BASELINE_SEARCH_BUDGET_SECONDS_CAP = 300.0
_DOUBLE_LEFT_HEADED_RULES = {
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
}
_CASE_PARTICLE_SURFACES = {
    "が",
    "を",
    "の",
    "で",
    "に",
    "へ",
    "と",
    "から",
    "まで",
    "ga",
    "wo",
    "no",
    "de",
    "ni",
    "he",
    "to",
    "kara",
    "made",
}


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


@dataclass
class _ReachabilityPathStep:
    rule_name: str
    rule_number: int
    rule_kind: str
    left: Optional[int]
    right: Optional[int]
    check: Optional[int]
    left_id: Optional[str]
    right_id: Optional[str]


@dataclass
class _ReachabilityEvidenceInternal:
    steps: list[_ReachabilityPathStep]
    final_state: DerivationState
    tree_signature: str


@dataclass
class _ReachabilityResultInternal:
    status: str
    completed: bool
    reason: str
    expanded_nodes: int
    generated_nodes: int
    max_frontier: int
    max_depth_reached: int
    actions_attempted: int
    rule_max_per_pair_observed: int
    elapsed_ms: int
    count_status: str
    goal_count_exact: Optional[int]
    total_exact: Optional[int]
    total_upper_bound_a_pair_only: int
    total_upper_bound_b_pair_rulemax: int
    rule_max_per_pair_bound: int
    count_basis: str
    tree_signature_basis: str
    evidences: list[_ReachabilityEvidenceInternal]


_REACHABILITY_JOBS: dict[str, dict[str, Any]] = {}
_REACHABILITY_JOBS_LOCK = threading.Lock()


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
    unresolved_before = _count_uninterpretable_like_perl(state)

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
                if candidate.rule_kind == "double" and not _passes_nohead_constraint(
                    state=state,
                    rule_name=candidate.rule_name,
                    left=actual_left,
                    right=actual_right,
                ):
                    continue
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
                unresolved_after = _count_uninterpretable_like_perl(next_state)
                # 探索縮約: 未解釈素性を減らさない遷移は展開しない。
                if unresolved_after >= unresolved_before:
                    continue
                if state_signature_fn(next_state) == state_key:
                    continue
                transitions.append((candidate, actual_left, actual_right, next_state))

    case_local_transitions = [
        row
        for row in transitions
        if _is_case_particle_local_transition(
            state=state,
            candidate=row[0],
            left=row[1],
            right=row[2],
        )
    ]
    if case_local_transitions:
        transitions = case_local_transitions
    else:
        vt_local_transitions = [
            row
            for row in transitions
            if _is_local_vt_transition(
                state=state,
                candidate=row[0],
                left=row[1],
                right=row[2],
            )
        ]
        if vt_local_transitions:
            transitions = vt_local_transitions

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


def _resolve_reachability_max_evidences(value: int) -> int:
    if value <= 0:
        return 1
    return min(_HEAD_ASSIST_MAX_EVIDENCES_CAP, value)


def _resolve_reachability_page(offset: int, limit: int, *, max_evidences: int) -> tuple[int, int]:
    resolved_offset = max(0, offset)
    resolved_limit = max(1, min(limit, _HEAD_ASSIST_PAGE_LIMIT_CAP))
    if resolved_offset > max_evidences:
        resolved_offset = max_evidences
    return resolved_offset, resolved_limit


def _resolve_reachability_max_depth(requested_depth: int, *, state: DerivationState) -> int:
    cap = _resolve_head_assist_max_total_depth(state)
    if requested_depth <= 0:
        return 1
    return max(1, min(requested_depth, cap))


def _resolve_reachability_budget_seconds(requested_budget: float) -> float:
    if requested_budget <= 0:
        return 0.1
    return min(_BASELINE_SEARCH_BUDGET_SECONDS_CAP, requested_budget)


def _resolve_reachability_max_nodes(requested_nodes: int) -> int:
    if requested_nodes <= 0:
        return 10
    return min(_BASELINE_SEARCH_MAX_NODES_CAP, requested_nodes)


def _item_id_for_index(state: DerivationState, index: Optional[int]) -> Optional[str]:
    if index is None:
        return None
    if index < 1 or index > state.basenum:
        return None
    item = state.base[index]
    if isinstance(item, list) and len(item) > 0:
        return str(item[0])
    return None


def _generate_numeration_with_unknown_token_fallback(
    *,
    grammar_id: str,
    sentence: str,
    legacy_root: Path,
    tokens: Optional[list[str]],
    split_mode: str,
):
    # 手動トークン指定時は利用者入力を優先し、分割モードフォールバックは行わない。
    if tokens:
        return generate_numeration_from_sentence(
            grammar_id=grammar_id,
            sentence=sentence,
            legacy_root=legacy_root,
            tokens=tokens,
            split_mode=split_mode,
        )

    tried: set[str] = set()
    ordered_modes: list[str] = [split_mode, "B", "C", "A"]
    last_error: Optional[ValueError] = None
    for mode in ordered_modes:
        if mode in tried:
            continue
        tried.add(mode)
        try:
            return generate_numeration_from_sentence(
                grammar_id=grammar_id,
                sentence=sentence,
                legacy_root=legacy_root,
                tokens=tokens,
                split_mode=mode,
            )
        except ValueError as exc:
            last_error = exc
            if not str(exc).startswith("Unknown token for lexicon lookup:"):
                raise
            continue
    if last_error is not None:
        raise last_error
    raise ValueError("numeration generation failed")


def _item_for_index(state: DerivationState, index: int) -> Optional[list[Any]]:
    if index < 1 or index > state.basenum:
        return None
    row = state.base[index]
    if not isinstance(row, list):
        return None
    return row


def _item_category_for_index(state: DerivationState, index: int) -> str:
    row = _item_for_index(state, index)
    if row is None or len(row) < 2:
        return ""
    return str(row[1])


def _item_surface_for_index(state: DerivationState, index: int) -> str:
    row = _item_for_index(state, index)
    if row is None or len(row) < 7:
        return ""
    return str(row[6]).strip()


def _item_sy_features_for_index(state: DerivationState, index: int) -> list[str]:
    row = _item_for_index(state, index)
    if row is None or len(row) < 4 or not isinstance(row[3], list):
        return []
    return [str(value) for value in row[3] if value is not None and str(value) != ""]


def _feature_role_tags(features: list[str]) -> set[str]:
    tags: set[str] = set()
    for raw in features:
        parts = [part.strip() for part in raw.split(",")]
        for part in parts:
            if part in {"head", "nonhead"}:
                tags.add(part)
    return tags


def _head_nonhead_indices(rule_name: str, left: int, right: int) -> tuple[Optional[int], Optional[int]]:
    if rule_name == "RH-Merge":
        return right, left
    if rule_name in _DOUBLE_LEFT_HEADED_RULES:
        return left, right
    return None, None


def _passes_nohead_constraint(
    *,
    state: DerivationState,
    rule_name: str,
    left: int,
    right: int,
) -> bool:
    head_idx, nonhead_idx = _head_nonhead_indices(rule_name, left, right)
    if head_idx is None or nonhead_idx is None:
        return True
    head_roles = _feature_role_tags(_item_sy_features_for_index(state, head_idx))
    if head_roles == {"nonhead"}:
        return False
    nonhead_roles = _feature_role_tags(_item_sy_features_for_index(state, nonhead_idx))
    if nonhead_roles == {"head"}:
        return False
    return True


def _is_nominal_category(category: str) -> bool:
    return category in {"N", "NP"}


def _is_case_particle_item(state: DerivationState, index: int) -> bool:
    if _item_category_for_index(state, index) != "J":
        return False
    surface = _item_surface_for_index(state, index)
    return surface == "" or surface in _CASE_PARTICLE_SURFACES


def _nearest_preceding_nominal_index(state: DerivationState, index: int) -> Optional[int]:
    for candidate in range(index - 1, 0, -1):
        if _is_nominal_category(_item_category_for_index(state, candidate)):
            return candidate
    return None


def _is_case_particle_local_transition(
    *,
    state: DerivationState,
    candidate: RuleCandidate,
    left: int,
    right: int,
) -> bool:
    if candidate.rule_kind != "double":
        return False
    if _is_case_particle_item(state, right) and _is_nominal_category(_item_category_for_index(state, left)):
        j_index = right
        noun_index = left
    elif _is_case_particle_item(state, left) and _is_nominal_category(_item_category_for_index(state, right)):
        j_index = left
        noun_index = right
    else:
        return False
    nearest_nominal = _nearest_preceding_nominal_index(state, j_index)
    if nearest_nominal is not None and noun_index != nearest_nominal:
        return False
    return candidate.rule_name in {"LH-Merge", "J-Merge", "RH-Merge"}


def _is_local_vt_transition(
    *,
    state: DerivationState,
    candidate: RuleCandidate,
    left: int,
    right: int,
) -> bool:
    if candidate.rule_kind != "double":
        return False
    left_category = _item_category_for_index(state, left)
    right_category = _item_category_for_index(state, right)
    if {left_category, right_category} != {"V", "T"}:
        return False
    return abs(left - right) == 1


def _build_tree_node(item: object) -> dict[str, Any]:
    if not isinstance(item, list):
        return {
            "item_id": str(item),
            "category": "",
            "sy": [],
            "sl": "",
            "se": [],
            "phono": "",
            "children": [],
        }
    children: list[dict[str, Any]] = []
    if len(item) > 7 and isinstance(item[7], list):
        for child in item[7]:
            if child == "zero":
                continue
            if isinstance(child, list):
                children.append(_build_tree_node(child))
    sy_values = item[3] if len(item) > 3 and isinstance(item[3], list) else []
    se_values = item[5] if len(item) > 5 and isinstance(item[5], list) else []
    return {
        "item_id": str(item[0]) if len(item) > 0 else "",
        "category": str(item[1]) if len(item) > 1 else "",
        "sy": [str(v) for v in sy_values if v is not None and str(v) != ""],
        "sl": str(item[4]) if len(item) > 4 and item[4] is not None else "",
        "se": [str(v) for v in se_values if v is not None and str(v) != ""],
        "phono": str(item[6]) if len(item) > 6 and item[6] is not None else "",
        "children": children,
    }


def _select_tree_root(state: DerivationState) -> dict[str, Any]:
    for index in range(1, state.basenum + 1):
        item = state.base[index]
        if item == "zero":
            continue
        return _build_tree_node(item)
    return {
        "item_id": "(empty)",
        "category": "",
        "sy": [],
        "sl": "",
        "se": [],
        "phono": "",
        "children": [],
    }


def _canonical_tree_signature(tree_root: dict[str, Any]) -> str:
    return json.dumps(tree_root, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_rule_max_per_pair_bound(*, grammar_id: str, legacy_root: Path) -> int:
    try:
        catalog = load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root)
    except ValueError:
        return 1
    return max(1, len(catalog))


def _upper_bound_pair_only_prefix_count(*, basenum: int, depth: int) -> int:
    max_depth = min(max(0, depth), max(0, basenum - 1))
    total = 0
    term = 1
    for step in range(0, max_depth):
        current = basenum - step
        term *= current * (current - 1)
        total += term
    return max(1, total)


def _upper_bound_pair_rule_prefix_count(*, basenum: int, depth: int, rule_bound: int) -> int:
    max_depth = min(max(0, depth), max(0, basenum - 1))
    total = 0
    term = 1
    safe_rule_bound = max(1, rule_bound)
    for step in range(0, max_depth):
        current = basenum - step
        term *= current * (current - 1) * safe_rule_bound
        total += term
    return max(1, total)


def _coverage_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    ratio = (float(numerator) / float(denominator)) * 100.0
    return min(100.0, round(ratio, 4))


def _search_reachability(
    *,
    request: DerivationReachabilityRequest,
    legacy_root: Path,
    rh_version: str,
    lh_version: str,
    search_signature_mode: str,
    progress_hook: Optional[Callable[[float, str, str], None]] = None,
) -> _ReachabilityResultInternal:
    max_evidences = _resolve_reachability_max_evidences(request.max_evidences)
    max_depth = _resolve_reachability_max_depth(request.max_depth, state=request.state)
    max_nodes = _resolve_reachability_max_nodes(request.max_nodes)
    budget_seconds = _resolve_reachability_budget_seconds(request.budget_seconds)
    deadline = time.perf_counter() + budget_seconds
    started = time.perf_counter()

    rule_max_bound = _resolve_rule_max_per_pair_bound(
        grammar_id=request.state.grammar_id,
        legacy_root=legacy_root,
    )
    upper_bound_a = _upper_bound_pair_only_prefix_count(
        basenum=request.state.basenum,
        depth=max_depth,
    )
    upper_bound_b = _upper_bound_pair_rule_prefix_count(
        basenum=request.state.basenum,
        depth=max_depth,
        rule_bound=rule_max_bound,
    )

    transition_cache: dict[str, list[tuple[RuleCandidate, int, int, DerivationState]]] = {}
    evidence_by_tree_sig: dict[str, _ReachabilityEvidenceInternal] = {}
    goal_tree_sigs: set[str] = set()

    expanded_nodes = 0
    generated_nodes = 0
    max_frontier = 0
    max_depth_reached = 0
    actions_attempted = 0
    rule_max_observed = 0

    aborted_reason: Optional[str] = None
    progress_tick_interval = 200

    def report_progress(phase: str, message: str) -> None:
        if progress_hook is None:
            return
        percent = _coverage_percent(actions_attempted, upper_bound_a)
        if phase != "finalizing":
            percent = min(percent, 99.0)
        progress_hook(percent, phase, message)

    def dfs(
        current: DerivationState,
        remaining_depth: int,
        path: list[_ReachabilityPathStep],
    ) -> bool:
        nonlocal expanded_nodes, generated_nodes, max_frontier, max_depth_reached
        nonlocal actions_attempted, rule_max_observed, aborted_reason

        max_depth_reached = max(max_depth_reached, len(path))
        if time.perf_counter() >= deadline:
            aborted_reason = "timeout"
            return False
        if actions_attempted >= max_nodes:
            aborted_reason = "node_limit"
            return False

        if _is_grammatical_like_perl(current):
            tree_root = _select_tree_root(current)
            tree_sig = _canonical_tree_signature(tree_root)
            goal_tree_sigs.add(tree_sig)
            if tree_sig not in evidence_by_tree_sig and len(evidence_by_tree_sig) < max_evidences:
                evidence_by_tree_sig[tree_sig] = _ReachabilityEvidenceInternal(
                    steps=list(path),
                    final_state=current.model_copy(deep=True),
                    tree_signature=tree_sig,
                )
            return True

        if remaining_depth <= 0:
            return True

        transitions = _enumerate_candidate_transitions(
            state=current,
            legacy_root=legacy_root,
            rh_merge_version=rh_version,
            lh_merge_version=lh_version,
            state_signature_fn=_state_structural_signature,
            cache=transition_cache,
        )
        ordered = sorted(transitions, key=_head_assist_transition_rank_key)
        generated_nodes += len(ordered)
        max_frontier = max(max_frontier, len(ordered))
        # observed は「1 pair あたりで実際に使われた rule 種別数」の観測値として保持する。
        # 遷移本数(全pair合計)を使うと上界(bound)比較の意味が崩れるため、rule番号のユニーク件数にする。
        rule_max_observed = max(
            rule_max_observed,
            len({candidate.rule_number for candidate, _, _, _ in ordered}),
        )
        expanded_nodes += 1

        for candidate, actual_left, actual_right, next_state in ordered:
            if time.perf_counter() >= deadline:
                aborted_reason = "timeout"
                return False
            if actions_attempted >= max_nodes:
                aborted_reason = "node_limit"
                return False
            actions_attempted += 1
            left_id = _item_id_for_index(current, actual_left)
            right_id = _item_id_for_index(current, actual_right)
            path.append(
                _ReachabilityPathStep(
                    rule_name=candidate.rule_name,
                    rule_number=candidate.rule_number,
                    rule_kind=candidate.rule_kind,
                    left=actual_left,
                    right=actual_right,
                    check=candidate.check,
                    left_id=left_id,
                    right_id=right_id,
                )
            )
            ok = dfs(next_state, remaining_depth - 1, path)
            path.pop()
            if not ok:
                return False
            if actions_attempted % progress_tick_interval == 0:
                report_progress("enumerating", "到達候補を探索中")
        return True

    report_progress("enumerating", "探索を開始しました")
    completed = dfs(request.state.model_copy(deep=True), max_depth, [])

    if not completed:
        status = "unknown"
        reason = aborted_reason or "unknown"
        count_status = "upper_bound_only"
        goal_count_exact: Optional[int] = None
        total_exact: Optional[int] = None
    else:
        if len(goal_tree_sigs) > 0:
            status = "reachable"
        else:
            status = "unreachable"
        reason = "completed"
        count_status = "exact"
        goal_count_exact = len(goal_tree_sigs)
        total_exact = len(goal_tree_sigs)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    report_progress("finalizing", "結果を整形中")

    count_basis = "packed_signature_v1" if search_signature_mode == "packed" else "structural_signature_v1"
    evidences = sorted(
        evidence_by_tree_sig.values(),
        key=lambda row: (len(row.steps), row.tree_signature),
    )
    return _ReachabilityResultInternal(
        status=status,
        completed=completed,
        reason=reason,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        max_frontier=max_frontier,
        max_depth_reached=max_depth_reached,
        actions_attempted=actions_attempted,
        rule_max_per_pair_observed=rule_max_observed,
        elapsed_ms=elapsed_ms,
        count_status=count_status,
        goal_count_exact=goal_count_exact,
        total_exact=total_exact,
        total_upper_bound_a_pair_only=upper_bound_a,
        total_upper_bound_b_pair_rulemax=upper_bound_b,
        rule_max_per_pair_bound=rule_max_bound,
        count_basis=count_basis,
        tree_signature_basis="canonical_tree_v1",
        evidences=evidences,
    )


def _build_reachability_response(
    *,
    request: DerivationReachabilityRequest,
    internal: _ReachabilityResultInternal,
) -> DerivationReachabilityResponse:
    max_evidences = _resolve_reachability_max_evidences(request.max_evidences)
    offset, limit = _resolve_reachability_page(
        request.offset,
        request.limit,
        max_evidences=max_evidences,
    )
    evidences_capped = internal.evidences[:max_evidences]
    page_rows = evidences_capped[offset : offset + limit]
    shown_count = len(page_rows)

    evidence_rows: list[ReachabilityEvidenceResponse] = []
    for idx, row in enumerate(page_rows, start=offset + 1):
        rule_sequence = [
            ReachabilityRuleStepResponse(
                step=step_no,
                rule_name=step.rule_name,
                rule_number=step.rule_number,
                rule_kind=step.rule_kind,
                left=step.left,
                right=step.right,
                check=step.check,
                left_id=step.left_id,
                right_id=step.right_id,
            )
            for step_no, step in enumerate(row.steps, start=1)
        ]
        evidence_rows.append(
            ReachabilityEvidenceResponse(
                rank=idx,
                steps_to_goal=len(row.steps),
                rule_sequence=rule_sequence,
                tree_root=_select_tree_root(row.final_state),
                process_text=(
                    export_process_text_like_perl(row.final_state)
                    if request.return_process_text
                    else None
                ),
            )
        )

    shown_ratio_exact_percent: Optional[float] = None
    if internal.total_exact is not None and internal.total_exact > 0:
        shown_ratio_exact_percent = round((float(shown_count) / float(internal.total_exact)) * 100.0, 4)

    metrics = ReachabilityMetricsResponse(
        expanded_nodes=internal.expanded_nodes,
        generated_nodes=internal.generated_nodes,
        packed_nodes=0,
        max_frontier=internal.max_frontier,
        elapsed_ms=internal.elapsed_ms,
        max_depth_reached=internal.max_depth_reached,
        actions_attempted=internal.actions_attempted,
    )
    counts = ReachabilityCountsResponse(
        count_unit="derivation_tree",
        count_basis=internal.count_basis,
        tree_signature_basis=internal.tree_signature_basis,
        count_status=internal.count_status,
        goal_count_exact=str(internal.goal_count_exact) if internal.goal_count_exact is not None else None,
        total_exact=str(internal.total_exact) if internal.total_exact is not None else None,
        total_upper_bound_a_pair_only=str(internal.total_upper_bound_a_pair_only),
        total_upper_bound_b_pair_rulemax=str(internal.total_upper_bound_b_pair_rulemax),
        rule_max_per_pair_bound=internal.rule_max_per_pair_bound,
        rule_max_per_pair_observed=internal.rule_max_per_pair_observed,
        shown_count=shown_count,
        offset=offset,
        limit=limit,
        shown_ratio_exact_percent=shown_ratio_exact_percent,
        coverage_upper_bound_a_percent=_coverage_percent(
            internal.actions_attempted,
            internal.total_upper_bound_a_pair_only,
        ),
        coverage_upper_bound_b_percent=_coverage_percent(
            internal.actions_attempted,
            internal.total_upper_bound_b_pair_rulemax,
        ),
        has_next=(offset + shown_count) < len(evidences_capped),
    )
    return DerivationReachabilityResponse(
        status=internal.status,
        completed=internal.completed,
        reason=internal.reason,
        metrics=metrics,
        counts=counts,
        evidences=evidence_rows,
    )


def _cleanup_reachability_jobs() -> None:
    now = time.time()
    with _REACHABILITY_JOBS_LOCK:
        expired_ids = [
            job_id
            for job_id, row in _REACHABILITY_JOBS.items()
            if (now - float(row.get("updated_at", row.get("created_at", now)))) > _HEAD_ASSIST_JOBS_TTL_SECONDS
        ]
        for job_id in expired_ids:
            _REACHABILITY_JOBS.pop(job_id, None)


def _set_reachability_job_progress(
    *,
    job_id: str,
    percent: float,
    phase: str,
    message: str,
) -> None:
    with _REACHABILITY_JOBS_LOCK:
        row = _REACHABILITY_JOBS.get(job_id)
        if row is None:
            return
        row["progress"] = {
            "percent": max(0.0, min(100.0, percent)),
            "phase": phase,
            "message": message,
        }
        row["updated_at"] = time.time()


def _run_reachability_job(
    *,
    job_id: str,
    request: DerivationReachabilityRequest,
    legacy_root: Path,
    rh_version: str,
    lh_version: str,
    search_signature_mode: str,
) -> None:
    try:
        with _REACHABILITY_JOBS_LOCK:
            row = _REACHABILITY_JOBS.get(job_id)
            if row is None:
                return
            row["status"] = "running"
            row["updated_at"] = time.time()

        internal = _search_reachability(
            request=request,
            legacy_root=legacy_root,
            rh_version=rh_version,
            lh_version=lh_version,
            search_signature_mode=search_signature_mode,
            progress_hook=lambda percent, phase, message: _set_reachability_job_progress(
                job_id=job_id,
                percent=percent,
                phase=phase,
                message=message,
            ),
        )
        full_result_request = request.model_copy(
            update={
                "offset": 0,
                "limit": _resolve_reachability_max_evidences(request.max_evidences),
            }
        )
        response = _build_reachability_response(
            request=full_result_request,
            internal=internal,
        )
        with _REACHABILITY_JOBS_LOCK:
            row = _REACHABILITY_JOBS.get(job_id)
            if row is None:
                return
            row["status"] = response.status
            row["completed"] = response.completed
            row["reason"] = response.reason
            row["result"] = response
            row["updated_at"] = time.time()
            row["progress"] = {
                "percent": 100.0,
                "phase": "finalizing",
                "message": "完了",
            }
    except Exception as exc:
        with _REACHABILITY_JOBS_LOCK:
            row = _REACHABILITY_JOBS.get(job_id)
            if row is None:
                return
            row["status"] = "failed"
            row["completed"] = False
            row["reason"] = "failed"
            row["error"] = str(exc)
            row["updated_at"] = time.time()
            row["progress"] = {
                "percent": 100.0,
                "phase": "finalizing",
                "message": "失敗",
            }


def _get_reachability_job(job_id: str) -> dict[str, Any]:
    _cleanup_reachability_jobs()
    with _REACHABILITY_JOBS_LOCK:
        row = _REACHABILITY_JOBS.get(job_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Reachability job not found: {job_id}")
        return dict(row)


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
        generated = _generate_numeration_with_unknown_token_fallback(
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
        generated = _generate_numeration_with_unknown_token_fallback(
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


@router.post("/reachability", response_model=DerivationReachabilityResponse)
def derivation_reachability(request: DerivationReachabilityRequest) -> DerivationReachabilityResponse:
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
        search_signature_mode = _resolve_head_assist_signature_mode(request.search_signature_mode)
        _resolve_head_assist_parallel_cores(request.parallel_cores)
        rh_version = request.rh_merge_version or profile.rh_merge_version
        lh_version = request.lh_merge_version or profile.lh_merge_version
        internal = _search_reachability(
            request=request,
            legacy_root=legacy_root,
            rh_version=rh_version,
            lh_version=lh_version,
            search_signature_mode=search_signature_mode,
        )
        return _build_reachability_response(
            request=request,
            internal=internal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reachability/jobs", response_model=DerivationReachabilityJobStartResponse)
def derivation_reachability_jobs_start(
    request: DerivationReachabilityRequest,
) -> DerivationReachabilityJobStartResponse:
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
        search_signature_mode = _resolve_head_assist_signature_mode(request.search_signature_mode)
        _resolve_head_assist_parallel_cores(request.parallel_cores)
        rh_version = request.rh_merge_version or profile.rh_merge_version
        lh_version = request.lh_merge_version or profile.lh_merge_version
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _cleanup_reachability_jobs()
    created_at = time.time()
    job_id = uuid.uuid4().hex
    with _REACHABILITY_JOBS_LOCK:
        _REACHABILITY_JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": created_at,
            "updated_at": created_at,
            "progress": {
                "percent": 0.0,
                "phase": "queued",
                "message": "キューに登録しました",
            },
            "request": request,
            "legacy_root": legacy_root,
            "rh_version": rh_version,
            "lh_version": lh_version,
            "search_signature_mode": search_signature_mode,
            "result": None,
            "reason": None,
            "completed": None,
            "error": None,
        }

    worker = threading.Thread(
        target=_run_reachability_job,
        kwargs={
            "job_id": job_id,
            "request": request,
            "legacy_root": legacy_root,
            "rh_version": rh_version,
            "lh_version": lh_version,
            "search_signature_mode": search_signature_mode,
        },
        daemon=True,
    )
    worker.start()
    return DerivationReachabilityJobStartResponse(
        job_id=job_id,
        status="queued",
        created_at=created_at,
    )


@router.get("/reachability/jobs/{job_id}", response_model=DerivationReachabilityJobStatusResponse)
def derivation_reachability_job_status(job_id: str) -> DerivationReachabilityJobStatusResponse:
    row = _get_reachability_job(job_id)
    result = row.get("result")
    metrics: Optional[ReachabilityMetricsResponse] = None
    counts: Optional[ReachabilityCountsResponse] = None
    if isinstance(result, DerivationReachabilityResponse):
        metrics = result.metrics
        counts = result.counts

    progress = row.get("progress") or {"percent": 0.0, "phase": "queued", "message": "待機中"}
    return DerivationReachabilityJobStatusResponse(
        job_id=job_id,
        status=str(row.get("status", "queued")),
        created_at=float(row.get("created_at", time.time())),
        updated_at=float(row.get("updated_at", time.time())),
        progress=ReachabilityProgressResponse(
            percent=float(progress.get("percent", 0.0)),
            phase=str(progress.get("phase", "queued")),
            message=str(progress.get("message", "待機中")),
        ),
        metrics=metrics,
        counts=counts,
        reason=(str(row["reason"]) if row.get("reason") is not None else None),
        completed=(bool(row["completed"]) if row.get("completed") is not None else None),
        error=(str(row["error"]) if row.get("error") is not None else None),
    )


@router.get("/reachability/jobs/{job_id}/evidences", response_model=DerivationReachabilityEvidencePageResponse)
def derivation_reachability_job_evidences(
    job_id: str,
    offset: int = 0,
    limit: int = 10,
) -> DerivationReachabilityEvidencePageResponse:
    row = _get_reachability_job(job_id)
    result = row.get("result")
    status = str(row.get("status", "queued"))
    if not isinstance(result, DerivationReachabilityResponse):
        raise HTTPException(status_code=409, detail="Reachability job has not finished yet.")

    request_obj = row.get("request")
    max_evidences = (
        _resolve_reachability_max_evidences(request_obj.max_evidences)
        if isinstance(request_obj, DerivationReachabilityRequest)
        else _HEAD_ASSIST_MAX_EVIDENCES_CAP
    )
    resolved_offset, resolved_limit = _resolve_reachability_page(
        offset,
        limit,
        max_evidences=max_evidences,
    )
    capped_rows = result.evidences[:max_evidences]
    page_rows = capped_rows[resolved_offset : resolved_offset + resolved_limit]
    shown_count = len(page_rows)

    counts = result.counts.model_copy(deep=True)
    counts.offset = resolved_offset
    counts.limit = resolved_limit
    counts.shown_count = shown_count
    counts.has_next = (resolved_offset + shown_count) < len(capped_rows)
    if counts.total_exact is not None:
        try:
            total_exact_int = int(counts.total_exact)
        except ValueError:
            total_exact_int = 0
        counts.shown_ratio_exact_percent = (
            round((float(shown_count) / float(total_exact_int)) * 100.0, 4)
            if total_exact_int > 0
            else None
        )
    else:
        counts.shown_ratio_exact_percent = None

    return DerivationReachabilityEvidencePageResponse(
        job_id=job_id,
        status=status,
        counts=counts,
        evidences=page_rows,
    )


@router.post("/reachability/diagnose", response_model=DerivationReachabilityDiagnoseResponse)
def derivation_reachability_diagnose(
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
