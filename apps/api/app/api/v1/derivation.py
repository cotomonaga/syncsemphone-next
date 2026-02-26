from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

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
from domain.resume.codec import export_resume_text, import_resume_text

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


@router.post("/resume/import", response_model=DerivationState)
def resume_import(request: ResumeImportRequest) -> DerivationState:
    try:
        return import_resume_text(request.resume_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
