from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.lexicon.exporter import export_legacy_lexicon_bundle
from domain.lexicon.importer import validate_lexicon_yaml_text
from domain.lexicon.commit import commit_lexicon_yaml

router = APIRouter(prefix="/lexicon", tags=["lexicon"])


class LexiconExportResponse(BaseModel):
    grammar_id: str
    format: Literal["yaml", "csv"]
    lexicon_path: str
    entry_count: int
    content_text: str


class LexiconYamlRequest(BaseModel):
    yaml_text: str
    source_csv: Optional[str] = None
    legacy_root: Optional[str] = None


class LexiconYamlValidateResponse(BaseModel):
    grammar_id: str
    valid: bool
    entry_count: int
    errors: list[str]
    normalized_yaml_text: str
    preview_csv_text: str


class LexiconYamlImportResponse(BaseModel):
    grammar_id: str
    entry_count: int
    normalized_yaml_text: str
    csv_text: str


class LexiconCommitRequest(BaseModel):
    yaml_text: str
    source_csv: Optional[str] = None
    legacy_root: Optional[str] = None
    run_compatibility_tests: bool = True


class LexiconCommitResponse(BaseModel):
    grammar_id: str
    committed: bool
    rolled_back: bool
    compatibility_passed: bool
    run_compatibility_tests: bool
    entry_count: int
    lexicon_path: str
    backup_path: str
    message: str
    errors: list[str]
    normalized_yaml_text: str
    committed_csv_text: str
    command: str
    stdout: str
    stderr: str


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path(__file__).resolve().parents[6]


@router.get("/{grammar_id}", response_model=LexiconExportResponse)
def get_lexicon(
    grammar_id: str,
    format: Literal["yaml", "csv"] = Query(default="yaml"),
    legacy_root: Optional[str] = Query(default=None),
) -> LexiconExportResponse:
    root = Path(legacy_root).expanduser().resolve() if legacy_root else _default_legacy_root()
    try:
        exported = export_legacy_lexicon_bundle(legacy_root=root, grammar_id=grammar_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content_text = exported.yaml_text if format == "yaml" else exported.csv_text
    return LexiconExportResponse(
        grammar_id=grammar_id,
        format=format,
        lexicon_path=str(exported.lexicon_path),
        entry_count=exported.entry_count,
        content_text=content_text,
    )


@router.post("/{grammar_id}/validate", response_model=LexiconYamlValidateResponse)
def validate_lexicon_yaml(
    grammar_id: str,
    request: LexiconYamlRequest,
) -> LexiconYamlValidateResponse:
    result = validate_lexicon_yaml_text(
        grammar_id=grammar_id,
        yaml_text=request.yaml_text,
        source_csv=request.source_csv,
    )
    return LexiconYamlValidateResponse(
        grammar_id=result.grammar_id,
        valid=result.valid,
        entry_count=result.entry_count,
        errors=result.errors,
        normalized_yaml_text=result.normalized_yaml_text,
        preview_csv_text=result.preview_csv_text,
    )


@router.post("/{grammar_id}/import", response_model=LexiconYamlImportResponse)
def import_lexicon_yaml(
    grammar_id: str,
    request: LexiconYamlRequest,
) -> LexiconYamlImportResponse:
    result = validate_lexicon_yaml_text(
        grammar_id=grammar_id,
        yaml_text=request.yaml_text,
        source_csv=request.source_csv,
    )
    if not result.valid:
        message = "; ".join(result.errors[:3]) if result.errors else "Invalid YAML"
        raise HTTPException(status_code=400, detail=message)
    return LexiconYamlImportResponse(
        grammar_id=result.grammar_id,
        entry_count=result.entry_count,
        normalized_yaml_text=result.normalized_yaml_text,
        csv_text=result.preview_csv_text,
    )


@router.post("/{grammar_id}/commit", response_model=LexiconCommitResponse)
def commit_lexicon(
    grammar_id: str,
    request: LexiconCommitRequest,
) -> LexiconCommitResponse:
    root = (
        Path(request.legacy_root).expanduser().resolve()
        if request.legacy_root
        else _default_legacy_root()
    )
    project_root = Path(__file__).resolve().parents[5]

    result = commit_lexicon_yaml(
        grammar_id=grammar_id,
        yaml_text=request.yaml_text,
        source_csv=request.source_csv,
        legacy_root=root,
        project_root=project_root,
        run_compatibility_tests=request.run_compatibility_tests,
    )
    return LexiconCommitResponse(
        grammar_id=result.grammar_id,
        committed=result.committed,
        rolled_back=result.rolled_back,
        compatibility_passed=result.compatibility_passed,
        run_compatibility_tests=result.run_compatibility_tests,
        entry_count=result.entry_count,
        lexicon_path=result.lexicon_path,
        backup_path=result.backup_path,
        message=result.message,
        errors=result.errors,
        normalized_yaml_text=result.normalized_yaml_text,
        committed_csv_text=result.committed_csv_text,
        command=result.command,
        stdout=result.stdout,
        stderr=result.stderr,
    )
