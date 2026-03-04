from __future__ import annotations

import os
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.grammar.rule_catalog import load_rule_catalog
from domain.lexicon.legacy_loader import load_legacy_lexicon, resolve_legacy_lexicon_path

router = APIRouter(prefix="/reference", tags=["reference"])

_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_LEGACY_GRAMMAR_LIST_RE = re.compile(
    r"\((?P<body>.*?)\)\s*=\s*\(0\.\.\$lgnum-1\);", flags=re.DOTALL
)
_LEGACY_GRAMMAR_VAR_RE = re.compile(r"\$(?P<var>[A-Za-z0-9_]+)")
_LEGACY_FOLDER_RE = re.compile(r"\$folder\[\$(?P<var>\w+)\]\s*=\s*'(?P<folder>[^']+)';")


class FeatureDocEntry(BaseModel):
    file_name: str
    title: str


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


class LexiconSummaryItem(BaseModel):
    category: str
    count: int


class LexiconSummaryResponse(BaseModel):
    grammar_id: str
    display_name: str
    source_csv: str
    entry_count: int
    legacy_grammar_no: Optional[int]
    legacy_lexicon_cgi_url: Optional[str]
    category_counts: list[LexiconSummaryItem]


class LexiconInspectItem(BaseModel):
    lexicon_id: int
    entry: str
    phono: str
    category: str
    sync_features: list[str]
    idslot: str
    semantics: list[str]
    note: str


class LexiconItemsPageResponse(BaseModel):
    grammar_id: str
    category_filter: Optional[str]
    page: int
    page_size: int
    total_count: int
    total_pages: int
    items: list[LexiconInspectItem]


class LexiconItemLookupItem(BaseModel):
    lexicon_id: int
    found: bool
    entry: str = ""
    phono: str = ""
    category: str = ""
    sync_features: list[str] = []
    idslot: str = ""
    semantics: list[str] = []
    note: str = ""


class LexiconItemsLookupRequest(BaseModel):
    ids: list[int]


class LexiconItemsLookupResponse(BaseModel):
    grammar_id: str
    requested_count: int
    found_count: int
    missing_ids: list[int]
    items: list[LexiconItemLookupItem]


class MergeRuleEntryResponse(BaseModel):
    rule_number: int
    rule_name: str
    rule_kind: str
    file_name: str
    is_core_merge: bool


class RuleCompareResponse(BaseModel):
    grammar_id: str
    rule_number: int
    rule_name: str
    perl_file_name: str
    perl_source_text: str
    python_file_name: str
    python_source_text: str


@router.post(
    "/grammars/{grammar_id}/lexicon-items/by-ids",
    response_model=LexiconItemsLookupResponse,
)
def get_lexicon_items_by_ids(
    grammar_id: str,
    request: LexiconItemsLookupRequest,
    legacy_root: Optional[str] = None,
) -> LexiconItemsLookupResponse:
    root = _resolve_legacy_root(legacy_root)
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)

    unique_ids: list[int] = []
    seen: set[int] = set()
    for lexicon_id in request.ids:
        if lexicon_id in seen:
            continue
        if isinstance(lexicon_id, int):
            seen.add(lexicon_id)
            unique_ids.append(lexicon_id)

    found_items: list[LexiconItemLookupItem] = []
    missing: list[int] = []
    for lexicon_id in unique_ids:
        entry = entries.get(lexicon_id)
        if entry is None:
            missing.append(lexicon_id)
            found_items.append(
                LexiconItemLookupItem(
                    lexicon_id=lexicon_id,
                    found=False,
                )
            )
            continue

        found_items.append(
            LexiconItemLookupItem(
                lexicon_id=entry.lexicon_id,
                found=True,
                entry=entry.entry,
                phono=entry.phono,
                category=entry.category,
                sync_features=entry.sync_features,
                idslot=entry.idslot,
                semantics=entry.semantics,
                note=entry.note,
            )
        )

    return LexiconItemsLookupResponse(
        grammar_id=grammar_id,
        requested_count=len(unique_ids),
        found_count=len(found_items) - len(missing),
        missing_ids=missing,
        items=found_items,
    )


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[5]
    bundled_root = repo_root / "legacy"
    if bundled_root.exists():
        return bundled_root
    legacy_parent = Path(__file__).resolve().parents[6]
    if (legacy_parent / "grammar-list.pl").exists():
        return legacy_parent
    return bundled_root


def _safe_filename(file_name: str) -> str:
    if not _SAFE_FILE_RE.fullmatch(file_name):
        raise HTTPException(status_code=400, detail=f"Unsafe filename: {file_name}")
    return file_name


def _resolve_legacy_root(raw: Optional[str]) -> Path:
    return Path(raw).expanduser().resolve() if raw else _default_legacy_root()


def _extract_html_title(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    raw_title = match.group(1).strip()
    return unescape(raw_title)


def _grammar_display_name_map(legacy_root: Path) -> dict[str, str]:
    grammar_file = legacy_root / "grammar-list.pl"
    if not grammar_file.exists():
        return {}
    text = grammar_file.read_text(encoding="utf-8")
    grammar_by_var = {
        matched.group("var"): matched.group("name")
        for matched in re.finditer(r"\$grammar\[\$(?P<var>\w+)\]\s*=\s*'(?P<name>[^']*)';", text)
    }
    folder_by_var = {
        matched.group("var"): matched.group("folder")
        for matched in _LEGACY_FOLDER_RE.finditer(text)
    }
    return {
        folder: grammar_by_var.get(var, folder)
        for var, folder in folder_by_var.items()
    }


def _grammar_number_map(legacy_root: Path) -> dict[str, int]:
    grammar_file = legacy_root / "grammar-list.pl"
    if not grammar_file.exists():
        return {"imi01": 3, "imi02": 4, "imi03": 5}
    text = grammar_file.read_text(encoding="utf-8")
    var_order_match = _LEGACY_GRAMMAR_LIST_RE.search(text)
    if not var_order_match:
        return {"imi01": 3, "imi02": 4, "imi03": 5}
    ordered_vars = [
        matched.group("var")
        for matched in _LEGACY_GRAMMAR_VAR_RE.finditer(var_order_match.group("body"))
    ]
    folder_by_var = {
        matched.group("var"): matched.group("folder")
        for matched in _LEGACY_FOLDER_RE.finditer(text)
    }
    result: dict[str, int] = {}
    for idx, var_name in enumerate(ordered_vars):
        folder = folder_by_var.get(var_name)
        if not folder:
            continue
        result[folder] = idx
    if not result:
        return {"imi01": 3, "imi02": 4, "imi03": 5}
    return result


def _execute_python_file_path() -> Path:
    return DOMAIN_SRC / "domain" / "derivation" / "execute.py"


def _extract_rule_branch(lines: list[str], function_name: str, rule_name: str) -> str:
    function_header = f"def {function_name}("
    function_start = next((idx for idx, line in enumerate(lines) if line.startswith(function_header)), -1)
    if function_start < 0:
        return ""
    function_end = next(
        (idx for idx in range(function_start + 1, len(lines)) if lines[idx].startswith("def ")),
        len(lines),
    )

    match_idx = -1
    for idx in range(function_start + 1, function_end):
        line = lines[idx]
        if not line.startswith("    "):
            continue
        if f'rule_name == "{rule_name}"' in line:
            match_idx = idx
            break
        if "rule_name in {" in line and f'"{rule_name}"' in line:
            match_idx = idx
            break
    if match_idx < 0:
        return ""

    branch_end = function_end
    for idx in range(match_idx + 1, function_end):
        line = lines[idx]
        if line.startswith("    elif rule_name") or line.startswith("    else:"):
            branch_end = idx
            break
    snippet = "".join(lines[match_idx:branch_end]).strip("\n")
    return snippet


def _extract_python_rule_source(rule_name: str) -> str:
    path = _execute_python_file_path()
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_single = _extract_rule_branch(lines, "execute_single_merge", rule_name)
    in_double = _extract_rule_branch(lines, "execute_double_merge", rule_name)
    if in_single and in_double:
        return f"# execute_single_merge\n{in_single}\n\n# execute_double_merge\n{in_double}\n"
    if in_single:
        return f"# execute_single_merge\n{in_single}\n"
    if in_double:
        return f"# execute_double_merge\n{in_double}\n"
    return ""


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


def _resolve_rule_by_number(
    grammar_id: str,
    rule_number: int,
    legacy_root: Path,
):
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
    return target


@router.get("/features", response_model=list[FeatureDocEntry])
def list_feature_docs(legacy_root: Optional[str] = None) -> list[FeatureDocEntry]:
    root = _resolve_legacy_root(legacy_root)
    feature_dir = root / "features"
    if not feature_dir.exists():
        return []
    entries: list[FeatureDocEntry] = []
    for path in sorted(feature_dir.glob("*.html")):
        html_text = path.read_text(encoding="utf-8")
        title = _extract_html_title(html_text) or path.stem
        entries.append(FeatureDocEntry(file_name=path.name, title=title))
    return entries


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


@router.get("/grammars/{grammar_id}/lexicon-summary", response_model=LexiconSummaryResponse)
def get_lexicon_summary(grammar_id: str, legacy_root: Optional[str] = None) -> LexiconSummaryResponse:
    root = _resolve_legacy_root(legacy_root)
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
    lexicon_path = resolve_legacy_lexicon_path(legacy_root=root, grammar_id=grammar_id)
    category_counter = Counter(entry.category for entry in entries.values())
    sorted_categories = sorted(category_counter.items(), key=lambda row: (-row[1], row[0]))
    grammar_numbers = _grammar_number_map(root)
    grammar_display_names = _grammar_display_name_map(root)
    grammar_no = grammar_numbers.get(grammar_id)
    return LexiconSummaryResponse(
        grammar_id=grammar_id,
        display_name=grammar_display_names.get(grammar_id, grammar_id),
        source_csv=lexicon_path.name,
        entry_count=len(entries),
        legacy_grammar_no=grammar_no,
        legacy_lexicon_cgi_url=(
            f"/v1/legacy/perl/lexicon.cgi?grammar={grammar_no}" if grammar_no is not None else None
        ),
        category_counts=[
            LexiconSummaryItem(category=category, count=count)
            for category, count in sorted_categories
        ],
    )


@router.get("/grammars/{grammar_id}/lexicon-items", response_model=LexiconItemsPageResponse)
def get_lexicon_items(
    grammar_id: str,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    legacy_root: Optional[str] = None,
) -> LexiconItemsPageResponse:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 200:
        raise HTTPException(status_code=400, detail="page_size must be in 1..200")
    root = _resolve_legacy_root(legacy_root)
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
    ordered = [entries[key] for key in sorted(entries)]
    normalized_category = category if category and category.strip() != "" else None
    filtered = (
        [entry for entry in ordered if entry.category == normalized_category]
        if normalized_category is not None
        else ordered
    )
    total_count = len(filtered)
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    chunk = filtered[start:end]
    return LexiconItemsPageResponse(
        grammar_id=grammar_id,
        category_filter=normalized_category,
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        items=[
            LexiconInspectItem(
                lexicon_id=row.lexicon_id,
                entry=row.entry,
                phono=row.phono,
                category=row.category,
                sync_features=row.sync_features,
                idslot=row.idslot,
                semantics=row.semantics,
                note=row.note,
            )
            for row in chunk
        ],
    )


@router.get("/grammars/{grammar_id}/merge-rules", response_model=list[MergeRuleEntryResponse])
def get_merge_rules(grammar_id: str, legacy_root: Optional[str] = None) -> list[MergeRuleEntryResponse]:
    root = _resolve_legacy_root(legacy_root)
    try:
        rules = load_rule_catalog(grammar_id=grammar_id, legacy_root=root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [
        MergeRuleEntryResponse(
            rule_number=rule.number,
            rule_name=rule.name,
            rule_kind="single" if rule.kind == 1 else "double",
            file_name=f"{rule.file_name}.pl",
            is_core_merge=rule.name in {"RH-Merge", "LH-Merge"},
        )
        for rule in rules
    ]


@router.get("/grammars/{grammar_id}/rule-compare/{rule_number}", response_model=RuleCompareResponse)
def get_rule_compare(
    grammar_id: str,
    rule_number: int,
    legacy_root: Optional[str] = None,
) -> RuleCompareResponse:
    root = _resolve_legacy_root(legacy_root)
    target = _resolve_rule_by_number(grammar_id=grammar_id, rule_number=rule_number, legacy_root=root)
    perl_file_name = _safe_filename(f"{target.file_name}.pl")
    perl_path = (root / "MergeRule" / perl_file_name).resolve()
    if not perl_path.exists():
        raise HTTPException(status_code=404, detail=f"Perl rule source not found: {perl_file_name}")
    perl_source = perl_path.read_text(encoding="utf-8")
    python_source = _extract_python_rule_source(target.name)
    if python_source.strip() == "":
        python_source = "# 該当する rule_name 分岐が execute.py から見つかりませんでした。\n"
    return RuleCompareResponse(
        grammar_id=grammar_id,
        rule_number=target.number,
        rule_name=target.name,
        perl_file_name=perl_file_name,
        perl_source_text=perl_source,
        python_file_name="execute.py",
        python_source_text=python_source,
    )
