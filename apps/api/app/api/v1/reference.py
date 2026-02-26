from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.grammar.rule_catalog import load_rule_catalog

router = APIRouter(prefix="/reference", tags=["reference"])

_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class FeatureDocEntry(BaseModel):
    file_name: str


class RuleDocEntry(BaseModel):
    rule_number: int
    rule_name: str
    file_name: str


class HtmlDocResponse(BaseModel):
    file_name: str
    html_text: str


class GrammarRuleSourceEntry(BaseModel):
    rule_number: int
    rule_name: str
    file_name: str
    exists: bool


class GrammarRuleSourceResponse(BaseModel):
    grammar_id: str
    rule_number: int
    rule_name: str
    file_name: str
    source_text: str


class GrammarRuleSourceSaveRequest(BaseModel):
    source_text: str
    legacy_root: Optional[str] = None


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path(__file__).resolve().parents[6]


def _safe_filename(file_name: str) -> str:
    if not _SAFE_FILE_RE.fullmatch(file_name):
        raise HTTPException(status_code=400, detail=f"Unsafe filename: {file_name}")
    return file_name


def _resolve_legacy_root(raw: Optional[str]) -> Path:
    return Path(raw).expanduser().resolve() if raw else _default_legacy_root()


def _resolve_rule_source(
    grammar_id: str,
    rule_number: int,
    legacy_root: Path,
) -> tuple[int, str, str, Path]:
    try:
        rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    target = next((rule for rule in rules if rule.number == rule_number), None)
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"Rule not found: grammar_id={grammar_id}, rule_number={rule_number}",
        )
    file_name = _safe_filename(f"{target.file_name}.pl")
    path = (legacy_root / "MergeRule" / file_name).resolve()
    if not str(path).startswith(str((legacy_root / "MergeRule").resolve())):
        raise HTTPException(status_code=400, detail=f"Unsafe rule path: {file_name}")
    return target.number, target.name, file_name, path


@router.get("/features", response_model=list[FeatureDocEntry])
def list_feature_docs(legacy_root: Optional[str] = None) -> list[FeatureDocEntry]:
    root = _resolve_legacy_root(legacy_root)
    feature_dir = root / "features"
    if not feature_dir.exists():
        return []
    return [FeatureDocEntry(file_name=path.name) for path in sorted(feature_dir.glob("*.html"))]


@router.get("/features/{file_name}", response_model=HtmlDocResponse)
def get_feature_doc(file_name: str, legacy_root: Optional[str] = None) -> HtmlDocResponse:
    safe_name = _safe_filename(file_name)
    root = _resolve_legacy_root(legacy_root)
    path = (root / "features" / safe_name).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Feature doc not found: {safe_name}")
    return HtmlDocResponse(file_name=safe_name, html_text=path.read_text(encoding="utf-8"))


@router.get("/rules/{grammar_id}", response_model=list[RuleDocEntry])
def list_rule_docs(grammar_id: str, legacy_root: Optional[str] = None) -> list[RuleDocEntry]:
    root = _resolve_legacy_root(legacy_root)
    try:
        rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [
        RuleDocEntry(
            rule_number=rule.number,
            rule_name=rule.name,
            file_name=f"{rule.file_name}.html",
        )
        for rule in rules
    ]


@router.get("/rules/doc/{file_name}", response_model=HtmlDocResponse)
def get_rule_doc(file_name: str, legacy_root: Optional[str] = None) -> HtmlDocResponse:
    safe_name = _safe_filename(file_name)
    root = _resolve_legacy_root(legacy_root)
    path = (root / "MergeRule" / safe_name).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Rule doc not found: {safe_name}")
    return HtmlDocResponse(file_name=safe_name, html_text=path.read_text(encoding="utf-8"))


@router.get(
    "/grammars/{grammar_id}/rule-sources",
    response_model=list[GrammarRuleSourceEntry],
)
def list_grammar_rule_sources(
    grammar_id: str,
    legacy_root: Optional[str] = None,
) -> list[GrammarRuleSourceEntry]:
    root = _resolve_legacy_root(legacy_root)
    try:
        rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    merge_rule_dir = root / "MergeRule"
    return [
        GrammarRuleSourceEntry(
            rule_number=rule.number,
            rule_name=rule.name,
            file_name=f"{rule.file_name}.pl",
            exists=(merge_rule_dir / f"{rule.file_name}.pl").exists(),
        )
        for rule in rules
    ]


@router.get(
    "/grammars/{grammar_id}/rule-sources/{rule_number}",
    response_model=GrammarRuleSourceResponse,
)
def get_grammar_rule_source(
    grammar_id: str,
    rule_number: int,
    legacy_root: Optional[str] = None,
) -> GrammarRuleSourceResponse:
    root = _resolve_legacy_root(legacy_root)
    number, name, file_name, path = _resolve_rule_source(
        grammar_id=grammar_id,
        rule_number=rule_number,
        legacy_root=root,
    )
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Rule source not found: {file_name}")
    return GrammarRuleSourceResponse(
        grammar_id=grammar_id,
        rule_number=number,
        rule_name=name,
        file_name=file_name,
        source_text=path.read_text(encoding="utf-8"),
    )


@router.post(
    "/grammars/{grammar_id}/rule-sources/{rule_number}",
    response_model=GrammarRuleSourceResponse,
)
def save_grammar_rule_source(
    grammar_id: str,
    rule_number: int,
    request: GrammarRuleSourceSaveRequest,
) -> GrammarRuleSourceResponse:
    root = _resolve_legacy_root(request.legacy_root)
    number, name, file_name, path = _resolve_rule_source(
        grammar_id=grammar_id,
        rule_number=rule_number,
        legacy_root=root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_text = request.source_text.replace("\r\n", "\n")
    path.write_text(normalized_text, encoding="utf-8")
    return GrammarRuleSourceResponse(
        grammar_id=grammar_id,
        rule_number=number,
        rule_name=name,
        file_name=file_name,
        source_text=normalized_text,
    )
