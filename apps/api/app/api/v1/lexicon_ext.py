from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

DOMAIN_SRC = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src"
if str(DOMAIN_SRC) not in sys.path:
    sys.path.append(str(DOMAIN_SRC))

from domain.grammar.legacy_catalog import load_legacy_grammar_entries
from domain.lexicon.commit import commit_lexicon_yaml
from domain.lexicon.exporter import build_lexicon_yaml_text
from domain.lexicon.legacy_loader import load_legacy_lexicon, resolve_legacy_lexicon_path
from domain.lexicon.models import LexiconEntry

router = APIRouter(prefix="/lexicon", tags=["lexicon"])

ValueKind = Literal["category", "predicate", "sync_feature", "idslot", "semantic"]


class LexiconItemPayload(BaseModel):
    lexicon_id: Optional[int] = None
    entry: str
    phono: str
    category: str
    predicates: list[list[str]] = Field(default_factory=list)
    sync_features: list[str] = Field(default_factory=list)
    idslot: str = ""
    semantics: list[str] = Field(default_factory=list)
    note: str = ""


class LexiconItemResponse(BaseModel):
    grammar_id: str
    item: LexiconItemPayload


class LexiconItemsResponse(BaseModel):
    grammar_id: str
    total_count: int
    page: int
    page_size: int
    items: list[LexiconItemPayload]


class ValueDictionaryItem(BaseModel):
    id: int
    kind: ValueKind
    normalized_value: str
    display_value: str
    metadata_json: dict[str, Any]
    created_at: str
    updated_at: str


class ValueDictionaryListResponse(BaseModel):
    source: Literal["db", "lexicon_fallback"] = "db"
    items: list[ValueDictionaryItem]


class ValueDictionaryCreateRequest(BaseModel):
    kind: ValueKind
    display_value: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ValueDictionaryUpdateRequest(BaseModel):
    display_value: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ValueDictionaryUsageResponse(BaseModel):
    source: Literal["db", "lexicon_fallback"] = "db"
    id: int
    kind: ValueKind
    display_value: str
    total_usages: int
    usages_by_grammar: dict[str, int]
    usage_lexicon_items: list[dict[str, Any]] = Field(default_factory=list)


class ValueDictionaryReplaceRequest(BaseModel):
    replacement_value_id: int


class NumLinkItem(BaseModel):
    id: int
    grammar_id: str
    lexicon_id: int
    num_path: str
    memo: str
    slot_no: Optional[int]
    idx_value: str
    comment: str
    created_at: str
    updated_at: str


class NumLinkCreateRequest(BaseModel):
    num_path: str
    memo: str = ""
    slot_no: Optional[int] = None
    idx_value: str = ""
    comment: str = ""


class NumLinkUpdateRequest(BaseModel):
    memo: str = ""
    slot_no: Optional[int] = None
    idx_value: str = ""
    comment: str = ""


class NumLinksResponse(BaseModel):
    items: list[NumLinkItem]


class NoteCurrentResponse(BaseModel):
    grammar_id: str
    lexicon_id: int
    markdown: str
    updated_at: Optional[str]


class NoteUpdateRequest(BaseModel):
    markdown: str
    author: str = "unknown"
    change_summary: str = ""


class NoteRevisionItem(BaseModel):
    id: int
    revision_no: int
    author: str
    created_at: str
    change_summary: str


class NoteRevisionsResponse(BaseModel):
    items: list[NoteRevisionItem]


class NoteRevisionResponse(BaseModel):
    id: int
    revision_no: int
    markdown: str
    author: str
    created_at: str
    change_summary: str


class LexiconVersionItem(BaseModel):
    revision_id: str
    author: str
    date: str
    message: str


class LexiconVersionsResponse(BaseModel):
    grammar_id: str
    lexicon_path: str
    items: list[LexiconVersionItem]


class LexiconVersionDiffResponse(BaseModel):
    grammar_id: str
    revision_id: str
    diff_text: str


def _default_legacy_root() -> Path:
    env_value = os.getenv("SYNCSEMPHONE_LEGACY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path(__file__).resolve().parents[6]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _meta_db_url_optional() -> Optional[str]:
    for key in ("SYNCSEMPHONE_META_DB_URL", "SYNCSEMPHONE_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return None


def _meta_db_url() -> str:
    url = _meta_db_url_optional()
    if url:
        return url
    raise HTTPException(
        status_code=500,
        detail="Metadata DB URL is missing. Set SYNCSEMPHONE_META_DB_URL or DATABASE_URL.",
    )


def _normalize_value(raw: str) -> str:
    return " ".join(raw.strip().split()).casefold()


def _normalize_idslot(raw: str) -> str:
    return raw.strip().rstrip(",")


def _fallback_grammar_ids() -> list[str]:
    static_ids = ["imi01", "imi02", "imi03"]
    dynamic_ids: list[str] = []
    try:
        dynamic_ids = [entry.grammar_id for entry in load_legacy_grammar_entries() if entry.grammar_id.startswith("imi")]
    except Exception:
        dynamic_ids = []
    return sorted(set(static_ids + dynamic_ids))


def _dictionary_values_from_entry(entry: LexiconEntry, kind: ValueKind) -> list[str]:
    if kind == "category":
        return [entry.category] if entry.category.strip() else []
    if kind == "predicate":
        return ["|".join(part.strip() for part in row) for row in entry.predicates if any(part.strip() for part in row)]
    if kind == "sync_feature":
        return [row.strip() for row in entry.sync_features if row.strip()]
    if kind == "idslot":
        normalized = _normalize_idslot(entry.idslot)
        return [normalized] if normalized else []
    if kind == "semantic":
        return [row.strip() for row in entry.semantics if row.strip()]
    return []


def _build_fallback_value_dictionary(kind: Optional[ValueKind], legacy_root: Path) -> list[ValueDictionaryItem]:
    target_kinds: list[ValueKind] = [kind] if kind else ["category", "predicate", "sync_feature", "idslot", "semantic"]
    values_by_kind: dict[ValueKind, set[str]] = {target_kind: set() for target_kind in target_kinds}

    for grammar_id in _fallback_grammar_ids():
        try:
            entries = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
        except Exception:
            continue
        for entry in entries.values():
            for target_kind in target_kinds:
                values_by_kind[target_kind].update(_dictionary_values_from_entry(entry, target_kind))

    items: list[ValueDictionaryItem] = []
    next_id = 1
    for target_kind in target_kinds:
        for display_value in sorted(values_by_kind[target_kind], key=lambda row: row.casefold()):
            items.append(
                ValueDictionaryItem(
                    id=next_id,
                    kind=target_kind,
                    normalized_value=_normalize_value(display_value),
                    display_value=display_value,
                    metadata_json={},
                    created_at="",
                    updated_at="",
                )
            )
            next_id += 1
    return items


def _resolve_fallback_value_item(*, value_id: int, legacy_root: Path) -> Optional[ValueDictionaryItem]:
    items = _build_fallback_value_dictionary(kind=None, legacy_root=legacy_root)
    for item in items:
        if item.id == value_id:
            return item
    return None


def _collect_value_usage_lexicon_items(kind: ValueKind, display_value: str, legacy_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for grammar_id in _iter_grammar_ids():
        try:
            entries = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
        except Exception:
            continue
        for entry in entries.values():
            match_count = 0
            if kind == "category":
                match_count = 1 if entry.category == display_value else 0
            elif kind == "idslot":
                match_count = 1 if _normalize_idslot(entry.idslot) == _normalize_idslot(display_value) else 0
            elif kind == "sync_feature":
                match_count = sum(1 for row in entry.sync_features if row == display_value)
            elif kind == "semantic":
                match_count = sum(1 for row in entry.semantics if row == display_value)
            elif kind == "predicate":
                needle = display_value
                match_count = sum(
                    1 for pred in entry.predicates if "|".join([pred[0], pred[1], pred[2]]) == needle
                )
            if match_count > 0:
                rows.append(
                    {
                        "grammar_id": grammar_id,
                        "lexicon_id": int(entry.lexicon_id),
                        "entry": str(entry.entry),
                        "category": str(entry.category),
                        "match_count": int(match_count),
                    }
                )
    rows.sort(key=lambda row: (row["grammar_id"], row["lexicon_id"]))
    return rows


def _parse_utc(ts: Any) -> str:
    if ts is None:
        return ""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc).isoformat()
        return ts.astimezone(timezone.utc).isoformat()
    return str(ts)


@contextmanager
def _meta_conn():
    try:
        import psycopg  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail="psycopg is required for lexicon metadata endpoints.",
        ) from exc

    conn = psycopg.connect(_meta_db_url())
    try:
        _ensure_meta_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_meta_schema(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lexicon_value_dictionary (
              id BIGSERIAL PRIMARY KEY,
              kind TEXT NOT NULL,
              normalized_value TEXT NOT NULL,
              display_value TEXT NOT NULL,
              metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE(kind, normalized_value)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lexicon_item_num_links (
              id BIGSERIAL PRIMARY KEY,
              grammar_id TEXT NOT NULL,
              lexicon_id INTEGER NOT NULL,
              num_path TEXT NOT NULL,
              memo TEXT NOT NULL DEFAULT '',
              slot_no INTEGER NULL,
              idx_value TEXT NOT NULL DEFAULT '',
              comment TEXT NOT NULL DEFAULT '',
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE(grammar_id, lexicon_id, num_path, slot_no, idx_value)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lexicon_item_notes (
              grammar_id TEXT NOT NULL,
              lexicon_id INTEGER NOT NULL,
              current_markdown TEXT NOT NULL DEFAULT '',
              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              PRIMARY KEY(grammar_id, lexicon_id)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lexicon_item_note_revisions (
              id BIGSERIAL PRIMARY KEY,
              grammar_id TEXT NOT NULL,
              lexicon_id INTEGER NOT NULL,
              revision_no INTEGER NOT NULL,
              markdown TEXT NOT NULL,
              author TEXT NOT NULL DEFAULT 'unknown',
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              change_summary TEXT NOT NULL DEFAULT '',
              UNIQUE(grammar_id, lexicon_id, revision_no)
            );
            """
        )


def _to_payload(entry: LexiconEntry) -> LexiconItemPayload:
    return LexiconItemPayload(
        lexicon_id=entry.lexicon_id,
        entry=entry.entry,
        phono=entry.phono,
        category=entry.category,
        predicates=[list(pred) for pred in entry.predicates],
        sync_features=entry.sync_features,
        idslot=entry.idslot,
        semantics=entry.semantics,
        note=entry.note,
    )


def _to_entry(payload: LexiconItemPayload, lexicon_id: int) -> LexiconEntry:
    predicates: list[tuple[str, str, str]] = []
    for row in payload.predicates:
        if len(row) != 3:
            raise HTTPException(status_code=400, detail="predicates must contain 3-item arrays.")
        predicates.append((str(row[0]), str(row[1]), str(row[2])))
    return LexiconEntry(
        lexicon_id=lexicon_id,
        entry=payload.entry,
        phono=payload.phono,
        category=payload.category,
        predicates=predicates,
        sync_features=[str(value) for value in payload.sync_features],
        idslot=payload.idslot,
        semantics=[str(value) for value in payload.semantics],
        note=payload.note,
    )


def _save_entries(grammar_id: str, legacy_root: Path, entries: dict[int, LexiconEntry]) -> None:
    lexicon_path = resolve_legacy_lexicon_path(legacy_root=legacy_root, grammar_id=grammar_id)
    yaml_text = build_lexicon_yaml_text(
        grammar_id=grammar_id,
        source_csv=lexicon_path.name,
        entries=entries,
    )
    result = commit_lexicon_yaml(
        grammar_id=grammar_id,
        yaml_text=yaml_text,
        source_csv=lexicon_path.name,
        legacy_root=legacy_root,
        project_root=_project_root(),
        run_compatibility_tests=False,
    )
    if not result.committed:
        message = result.message or "Failed to save lexicon entries."
        if result.errors:
            message += f" ({'; '.join(result.errors[:2])})"
        raise HTTPException(status_code=400, detail=message)


def _iter_grammar_ids() -> list[str]:
    ids = [entry.grammar_id for entry in load_legacy_grammar_entries()]
    if not ids:
        return ["imi01", "imi02", "imi03", "japanese2"]
    seen: set[str] = set()
    ordered: list[str] = []
    for grammar_id in ids:
        if grammar_id in seen:
            continue
        seen.add(grammar_id)
        ordered.append(grammar_id)
    return ordered


def _count_value_usages(kind: ValueKind, display_value: str, legacy_root: Path) -> dict[str, int]:
    usages: dict[str, int] = {}
    for grammar_id in _iter_grammar_ids():
        try:
            entries = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
        except Exception:
            continue
        count = 0
        for entry in entries.values():
            if kind == "category":
                count += 1 if entry.category == display_value else 0
            elif kind == "idslot":
                count += 1 if _normalize_idslot(entry.idslot) == _normalize_idslot(display_value) else 0
            elif kind == "sync_feature":
                count += sum(1 for row in entry.sync_features if row == display_value)
            elif kind == "semantic":
                count += sum(1 for row in entry.semantics if row == display_value)
            elif kind == "predicate":
                needle = display_value
                count += sum(
                    1 for pred in entry.predicates if "|".join([pred[0], pred[1], pred[2]]) == needle
                )
        if count > 0:
            usages[grammar_id] = count
    return usages


def _replace_value_in_entries(
    *,
    kind: ValueKind,
    old_value: str,
    new_value: str,
    legacy_root: Path,
) -> int:
    total_changed = 0
    for grammar_id in _iter_grammar_ids():
        try:
            entries = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
        except Exception:
            continue
        changed = False
        for lexicon_id, entry in list(entries.items()):
            category = entry.category
            idslot = entry.idslot
            sync_features = list(entry.sync_features)
            semantics = list(entry.semantics)
            predicates = list(entry.predicates)
            if kind == "category" and category == old_value:
                category = new_value
                changed = True
                total_changed += 1
            elif kind == "idslot" and idslot == old_value:
                idslot = new_value
                changed = True
                total_changed += 1
            elif kind == "sync_feature":
                next_rows = [new_value if row == old_value else row for row in sync_features]
                if next_rows != sync_features:
                    sync_features = next_rows
                    changed = True
                    total_changed += sum(1 for row in entry.sync_features if row == old_value)
            elif kind == "semantic":
                next_rows = [new_value if row == old_value else row for row in semantics]
                if next_rows != semantics:
                    semantics = next_rows
                    changed = True
                    total_changed += sum(1 for row in entry.semantics if row == old_value)
            elif kind == "predicate":
                old_triplet = tuple(old_value.split("|", 2))
                new_triplet = tuple(new_value.split("|", 2))
                if len(old_triplet) == 3 and len(new_triplet) == 3:
                    next_preds = [new_triplet if pred == old_triplet else pred for pred in predicates]
                    if next_preds != predicates:
                        predicates = next_preds
                        changed = True
                        total_changed += sum(1 for pred in entry.predicates if pred == old_triplet)
            if changed:
                entries[lexicon_id] = LexiconEntry(
                    lexicon_id=entry.lexicon_id,
                    entry=entry.entry,
                    phono=entry.phono,
                    category=category,
                    predicates=predicates,
                    sync_features=sync_features,
                    idslot=idslot,
                    semantics=semantics,
                    note=entry.note,
                )
        if changed:
            _save_entries(grammar_id=grammar_id, legacy_root=legacy_root, entries=entries)
    return total_changed


def _to_value_item(row: Iterable[Any]) -> ValueDictionaryItem:
    values = list(row)
    return ValueDictionaryItem(
        id=int(values[0]),
        kind=str(values[1]),  # type: ignore[arg-type]
        normalized_value=str(values[2]),
        display_value=str(values[3]),
        metadata_json=values[4] or {},
        created_at=_parse_utc(values[5]),
        updated_at=_parse_utc(values[6]),
    )


@router.get("/{grammar_id}/items", response_model=LexiconItemsResponse)
def list_lexicon_items(
    grammar_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=300),
    q: str = Query(default=""),
    sort: Literal["lexicon_id", "entry", "category"] = Query(default="lexicon_id"),
    order: Literal["asc", "desc"] = Query(default="asc"),
) -> LexiconItemsResponse:
    root = _default_legacy_root()
    entries = list(load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id).values())
    if q.strip():
        category_filter: Optional[str] = None
        text_tokens: list[str] = []
        for token in q.strip().split():
            lowered = token.casefold()
            if lowered.startswith("category:"):
                category_filter = token.split(":", 1)[1].strip()
            else:
                text_tokens.append(token)

        if category_filter:
            category_needle = category_filter.casefold()
            entries = [row for row in entries if category_needle in row.category.casefold()]

        if text_tokens:
            text_needles = [token.casefold() for token in text_tokens if token.strip()]

            def _match_row(row: LexiconEntry) -> bool:
                haystack = f"{row.entry}\n{row.phono}\n{row.category}\n{row.lexicon_id}".casefold()
                return all(needle in haystack for needle in text_needles)

            entries = [row for row in entries if _match_row(row)]

    reverse = order == "desc"
    if sort == "entry":
        entries.sort(key=lambda row: (row.entry.casefold(), row.lexicon_id), reverse=reverse)
    elif sort == "category":
        entries.sort(key=lambda row: (row.category.casefold(), row.lexicon_id), reverse=reverse)
    else:
        entries.sort(key=lambda row: row.lexicon_id, reverse=reverse)
    total = len(entries)
    start = (page - 1) * page_size
    items = entries[start:start + page_size]
    return LexiconItemsResponse(
        grammar_id=grammar_id,
        total_count=total,
        page=page,
        page_size=page_size,
        items=[_to_payload(row) for row in items],
    )


@router.get("/{grammar_id}/items/{lexicon_id}", response_model=LexiconItemResponse)
def get_lexicon_item(grammar_id: str, lexicon_id: int) -> LexiconItemResponse:
    root = _default_legacy_root()
    entry = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id).get(lexicon_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Lexicon item not found: {lexicon_id}")
    return LexiconItemResponse(grammar_id=grammar_id, item=_to_payload(entry))


@router.post("/{grammar_id}/items", response_model=LexiconItemResponse)
def create_lexicon_item(grammar_id: str, request: LexiconItemPayload) -> LexiconItemResponse:
    root = _default_legacy_root()
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
    if request.lexicon_id is None:
        next_id = (max(entries.keys()) + 1) if entries else 1
    else:
        next_id = request.lexicon_id
    if next_id in entries:
        raise HTTPException(status_code=409, detail=f"Lexicon item already exists: {next_id}")
    entries[next_id] = _to_entry(request, next_id)
    _save_entries(grammar_id=grammar_id, legacy_root=root, entries=entries)
    return LexiconItemResponse(grammar_id=grammar_id, item=_to_payload(entries[next_id]))


@router.put("/{grammar_id}/items/{lexicon_id}", response_model=LexiconItemResponse)
def update_lexicon_item(
    grammar_id: str,
    lexicon_id: int,
    request: LexiconItemPayload,
) -> LexiconItemResponse:
    root = _default_legacy_root()
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
    if lexicon_id not in entries:
        raise HTTPException(status_code=404, detail=f"Lexicon item not found: {lexicon_id}")
    entries[lexicon_id] = _to_entry(request, lexicon_id)
    _save_entries(grammar_id=grammar_id, legacy_root=root, entries=entries)
    return LexiconItemResponse(grammar_id=grammar_id, item=_to_payload(entries[lexicon_id]))


@router.delete("/{grammar_id}/items/{lexicon_id}")
def delete_lexicon_item(grammar_id: str, lexicon_id: int) -> dict[str, Any]:
    root = _default_legacy_root()
    entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
    if lexicon_id not in entries:
        raise HTTPException(status_code=404, detail=f"Lexicon item not found: {lexicon_id}")
    del entries[lexicon_id]
    _save_entries(grammar_id=grammar_id, legacy_root=root, entries=entries)
    return {"deleted": True, "grammar_id": grammar_id, "lexicon_id": lexicon_id}


@router.get("/value-dictionary", response_model=ValueDictionaryListResponse)
def list_value_dictionary(
    kind: Optional[ValueKind] = Query(default=None),
) -> ValueDictionaryListResponse:
    if _meta_db_url_optional() is None:
        return ValueDictionaryListResponse(
            source="lexicon_fallback",
            items=_build_fallback_value_dictionary(kind=kind, legacy_root=_default_legacy_root()),
        )
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            if kind:
                cur.execute(
                    """
                    SELECT id, kind, normalized_value, display_value, metadata_json, created_at, updated_at
                    FROM lexicon_value_dictionary
                    WHERE kind = %s
                    ORDER BY display_value
                    """,
                    (kind,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, kind, normalized_value, display_value, metadata_json, created_at, updated_at
                    FROM lexicon_value_dictionary
                    ORDER BY kind, display_value
                    """
                )
            rows = [_to_value_item(row) for row in cur.fetchall()]
    return ValueDictionaryListResponse(source="db", items=rows)


@router.post("/value-dictionary", response_model=ValueDictionaryItem)
def create_value_dictionary(request: ValueDictionaryCreateRequest) -> ValueDictionaryItem:
    normalized = _normalize_value(request.display_value)
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lexicon_value_dictionary(kind, normalized_value, display_value, metadata_json)
                VALUES (%s, %s, %s, %s::jsonb)
                RETURNING id, kind, normalized_value, display_value, metadata_json, created_at, updated_at
                """,
                (request.kind, normalized, request.display_value, json.dumps(request.metadata_json, ensure_ascii=False)),
            )
            row = cur.fetchone()
    return _to_value_item(row)


@router.put("/value-dictionary/{value_id}", response_model=ValueDictionaryItem)
def update_value_dictionary(value_id: int, request: ValueDictionaryUpdateRequest) -> ValueDictionaryItem:
    if _meta_db_url_optional() is None:
        legacy_root = _default_legacy_root()
        fallback_item = _resolve_fallback_value_item(value_id=value_id, legacy_root=legacy_root)
        if not fallback_item:
            raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
        old_value = fallback_item.display_value
        new_value = request.display_value
        if fallback_item.kind == "idslot":
            new_value = _normalize_idslot(new_value)
            old_value = _normalize_idslot(old_value)
        _replace_value_in_entries(
            kind=fallback_item.kind,
            old_value=old_value,
            new_value=new_value,
            legacy_root=legacy_root,
        )
        return ValueDictionaryItem(
            id=fallback_item.id,
            kind=fallback_item.kind,
            normalized_value=_normalize_value(new_value),
            display_value=new_value,
            metadata_json={},
            created_at="",
            updated_at="",
        )

    normalized = _normalize_value(request.display_value)
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE lexicon_value_dictionary
                SET normalized_value = %s,
                    display_value = %s,
                    metadata_json = %s::jsonb,
                    updated_at = now()
                WHERE id = %s
                RETURNING id, kind, normalized_value, display_value, metadata_json, created_at, updated_at
                """,
                (
                    normalized,
                    request.display_value,
                    json.dumps(request.metadata_json, ensure_ascii=False),
                    value_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
    return _to_value_item(row)


@router.get("/value-dictionary/{value_id}/usages", response_model=ValueDictionaryUsageResponse)
def get_value_dictionary_usages(value_id: int) -> ValueDictionaryUsageResponse:
    if _meta_db_url_optional() is None:
        legacy_root = _default_legacy_root()
        fallback_item = _resolve_fallback_value_item(value_id=value_id, legacy_root=legacy_root)
        if not fallback_item:
            raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
        usages = _count_value_usages(kind=fallback_item.kind, display_value=fallback_item.display_value, legacy_root=legacy_root)
        usage_rows = _collect_value_usage_lexicon_items(
            kind=fallback_item.kind,
            display_value=fallback_item.display_value,
            legacy_root=legacy_root,
        )
        return ValueDictionaryUsageResponse(
            source="lexicon_fallback",
            id=fallback_item.id,
            kind=fallback_item.kind,
            display_value=fallback_item.display_value,
            total_usages=sum(usages.values()),
            usages_by_grammar=usages,
            usage_lexicon_items=usage_rows,
        )

    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, kind, display_value
                FROM lexicon_value_dictionary
                WHERE id = %s
                """,
                (value_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
    kind = row[1]
    display_value = row[2]
    usages = _count_value_usages(kind=kind, display_value=display_value, legacy_root=_default_legacy_root())
    usage_rows = _collect_value_usage_lexicon_items(kind=kind, display_value=display_value, legacy_root=_default_legacy_root())
    return ValueDictionaryUsageResponse(
        source="db",
        id=int(row[0]),
        kind=kind,
        display_value=display_value,
        total_usages=sum(usages.values()),
        usages_by_grammar=usages,
        usage_lexicon_items=usage_rows,
    )


@router.post("/value-dictionary/{value_id}/replace")
def replace_value_dictionary(value_id: int, request: ValueDictionaryReplaceRequest) -> dict[str, Any]:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, kind, display_value
                FROM lexicon_value_dictionary
                WHERE id = %s
                """,
                (value_id,),
            )
            source = cur.fetchone()
            if not source:
                raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
            cur.execute(
                """
                SELECT id, kind, display_value
                FROM lexicon_value_dictionary
                WHERE id = %s
                """,
                (request.replacement_value_id,),
            )
            target = cur.fetchone()
            if not target:
                raise HTTPException(
                    status_code=404,
                    detail=f"Replacement value dictionary item not found: {request.replacement_value_id}",
                )
    if source[1] != target[1]:
        raise HTTPException(status_code=400, detail="Replacement kind mismatch.")
    changed = _replace_value_in_entries(
        kind=source[1],
        old_value=source[2],
        new_value=target[2],
        legacy_root=_default_legacy_root(),
    )
    return {"replaced": True, "changed_count": changed}


@router.delete("/value-dictionary/{value_id}")
def delete_value_dictionary(value_id: int) -> dict[str, Any]:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, kind, display_value
                FROM lexicon_value_dictionary
                WHERE id = %s
                """,
                (value_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Value dictionary item not found: {value_id}")
    usages = _count_value_usages(kind=row[1], display_value=row[2], legacy_root=_default_legacy_root())
    total = sum(usages.values())
    if total > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Value is used by {total} lexicon fields. Replace usages before deletion.",
        )
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM lexicon_value_dictionary WHERE id = %s", (value_id,))
    return {"deleted": True, "id": value_id}


@router.get("/{grammar_id}/items/{lexicon_id}/num-links", response_model=NumLinksResponse)
def list_num_links(grammar_id: str, lexicon_id: int) -> NumLinksResponse:
    if _meta_db_url_optional() is None:
        return NumLinksResponse(items=[])
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, grammar_id, lexicon_id, num_path, memo, slot_no, idx_value, comment, created_at, updated_at
                FROM lexicon_item_num_links
                WHERE grammar_id = %s AND lexicon_id = %s
                ORDER BY id
                """,
                (grammar_id, lexicon_id),
            )
            rows = [
                NumLinkItem(
                    id=int(row[0]),
                    grammar_id=str(row[1]),
                    lexicon_id=int(row[2]),
                    num_path=str(row[3]),
                    memo=str(row[4]),
                    slot_no=row[5],
                    idx_value=str(row[6]),
                    comment=str(row[7]),
                    created_at=_parse_utc(row[8]),
                    updated_at=_parse_utc(row[9]),
                )
                for row in cur.fetchall()
            ]
    return NumLinksResponse(items=rows)


@router.post("/{grammar_id}/items/{lexicon_id}/num-links", response_model=NumLinkItem)
def create_num_link(grammar_id: str, lexicon_id: int, request: NumLinkCreateRequest) -> NumLinkItem:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lexicon_item_num_links(grammar_id, lexicon_id, num_path, memo, slot_no, idx_value, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, grammar_id, lexicon_id, num_path, memo, slot_no, idx_value, comment, created_at, updated_at
                """,
                (
                    grammar_id,
                    lexicon_id,
                    request.num_path,
                    request.memo,
                    request.slot_no,
                    request.idx_value,
                    request.comment,
                ),
            )
            row = cur.fetchone()
    return NumLinkItem(
        id=int(row[0]),
        grammar_id=str(row[1]),
        lexicon_id=int(row[2]),
        num_path=str(row[3]),
        memo=str(row[4]),
        slot_no=row[5],
        idx_value=str(row[6]),
        comment=str(row[7]),
        created_at=_parse_utc(row[8]),
        updated_at=_parse_utc(row[9]),
    )


@router.put("/{grammar_id}/items/{lexicon_id}/num-links/{link_id}", response_model=NumLinkItem)
def update_num_link(
    grammar_id: str,
    lexicon_id: int,
    link_id: int,
    request: NumLinkUpdateRequest,
) -> NumLinkItem:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE lexicon_item_num_links
                SET memo = %s,
                    slot_no = %s,
                    idx_value = %s,
                    comment = %s,
                    updated_at = now()
                WHERE id = %s AND grammar_id = %s AND lexicon_id = %s
                RETURNING id, grammar_id, lexicon_id, num_path, memo, slot_no, idx_value, comment, created_at, updated_at
                """,
                (
                    request.memo,
                    request.slot_no,
                    request.idx_value,
                    request.comment,
                    link_id,
                    grammar_id,
                    lexicon_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Num link not found: {link_id}")
    return NumLinkItem(
        id=int(row[0]),
        grammar_id=str(row[1]),
        lexicon_id=int(row[2]),
        num_path=str(row[3]),
        memo=str(row[4]),
        slot_no=row[5],
        idx_value=str(row[6]),
        comment=str(row[7]),
        created_at=_parse_utc(row[8]),
        updated_at=_parse_utc(row[9]),
    )


@router.delete("/{grammar_id}/items/{lexicon_id}/num-links/{link_id}")
def delete_num_link(grammar_id: str, lexicon_id: int, link_id: int) -> dict[str, Any]:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM lexicon_item_num_links
                WHERE id = %s AND grammar_id = %s AND lexicon_id = %s
                """,
                (link_id, grammar_id, lexicon_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Num link not found: {link_id}")
    return {"deleted": True, "id": link_id}


@router.get("/{grammar_id}/items/{lexicon_id}/notes", response_model=NoteCurrentResponse)
def get_note(grammar_id: str, lexicon_id: int) -> NoteCurrentResponse:
    if _meta_db_url_optional() is None:
        return NoteCurrentResponse(grammar_id=grammar_id, lexicon_id=lexicon_id, markdown="", updated_at=None)
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT current_markdown, updated_at
                FROM lexicon_item_notes
                WHERE grammar_id = %s AND lexicon_id = %s
                """,
                (grammar_id, lexicon_id),
            )
            row = cur.fetchone()
    if not row:
        return NoteCurrentResponse(grammar_id=grammar_id, lexicon_id=lexicon_id, markdown="", updated_at=None)
    return NoteCurrentResponse(
        grammar_id=grammar_id,
        lexicon_id=lexicon_id,
        markdown=str(row[0]),
        updated_at=_parse_utc(row[1]),
    )


@router.put("/{grammar_id}/items/{lexicon_id}/notes", response_model=NoteCurrentResponse)
def put_note(grammar_id: str, lexicon_id: int, request: NoteUpdateRequest) -> NoteCurrentResponse:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(revision_no), 0)
                FROM lexicon_item_note_revisions
                WHERE grammar_id = %s AND lexicon_id = %s
                """,
                (grammar_id, lexicon_id),
            )
            revision_no = int(cur.fetchone()[0]) + 1
            cur.execute(
                """
                INSERT INTO lexicon_item_note_revisions(grammar_id, lexicon_id, revision_no, markdown, author, change_summary)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    grammar_id,
                    lexicon_id,
                    revision_no,
                    request.markdown,
                    request.author,
                    request.change_summary,
                ),
            )
            cur.execute(
                """
                INSERT INTO lexicon_item_notes(grammar_id, lexicon_id, current_markdown, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (grammar_id, lexicon_id)
                DO UPDATE SET current_markdown = EXCLUDED.current_markdown, updated_at = now()
                RETURNING updated_at
                """,
                (grammar_id, lexicon_id, request.markdown),
            )
            updated = cur.fetchone()[0]
    return NoteCurrentResponse(
        grammar_id=grammar_id,
        lexicon_id=lexicon_id,
        markdown=request.markdown,
        updated_at=_parse_utc(updated),
    )


@router.get("/{grammar_id}/items/{lexicon_id}/notes/revisions", response_model=NoteRevisionsResponse)
def list_note_revisions(grammar_id: str, lexicon_id: int) -> NoteRevisionsResponse:
    if _meta_db_url_optional() is None:
        return NoteRevisionsResponse(items=[])
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, revision_no, author, created_at, change_summary
                FROM lexicon_item_note_revisions
                WHERE grammar_id = %s AND lexicon_id = %s
                ORDER BY revision_no DESC
                """,
                (grammar_id, lexicon_id),
            )
            rows = [
                NoteRevisionItem(
                    id=int(row[0]),
                    revision_no=int(row[1]),
                    author=str(row[2]),
                    created_at=_parse_utc(row[3]),
                    change_summary=str(row[4]),
                )
                for row in cur.fetchall()
            ]
    return NoteRevisionsResponse(items=rows)


@router.get("/{grammar_id}/items/{lexicon_id}/notes/revisions/{revision_id}", response_model=NoteRevisionResponse)
def get_note_revision(grammar_id: str, lexicon_id: int, revision_id: int) -> NoteRevisionResponse:
    with _meta_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, revision_no, markdown, author, created_at, change_summary
                FROM lexicon_item_note_revisions
                WHERE id = %s AND grammar_id = %s AND lexicon_id = %s
                """,
                (revision_id, grammar_id, lexicon_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Note revision not found: {revision_id}")
    return NoteRevisionResponse(
        id=int(row[0]),
        revision_no=int(row[1]),
        markdown=str(row[2]),
        author=str(row[3]),
        created_at=_parse_utc(row[4]),
        change_summary=str(row[5]),
    )


@router.post("/{grammar_id}/items/{lexicon_id}/notes/revisions/{revision_id}/restore", response_model=NoteCurrentResponse)
def restore_note_revision(grammar_id: str, lexicon_id: int, revision_id: int) -> NoteCurrentResponse:
    revision = get_note_revision(grammar_id=grammar_id, lexicon_id=lexicon_id, revision_id=revision_id)
    return put_note(
        grammar_id=grammar_id,
        lexicon_id=lexicon_id,
        request=NoteUpdateRequest(
            markdown=revision.markdown,
            author="restore",
            change_summary=f"restore revision {revision.revision_no}",
        ),
    )


@router.get("/{grammar_id}/versions", response_model=LexiconVersionsResponse)
def list_lexicon_versions(
    grammar_id: str,
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> LexiconVersionsResponse:
    root = _default_legacy_root()
    lexicon_path = resolve_legacy_lexicon_path(legacy_root=root, grammar_id=grammar_id)
    project_root = _project_root()
    items: list[LexiconVersionItem] = []
    try:
        rel = lexicon_path.relative_to(project_root)
        cmd = [
            "git",
            "-C",
            str(project_root),
            "log",
            f"--max-count={limit}",
            f"--skip={offset}",
            "--date=iso",
            "--pretty=format:%H%x1f%an%x1f%ad%x1f%s",
            "--",
            str(rel),
        ]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split("\x1f")
            if len(parts) < 4:
                continue
            items.append(
                LexiconVersionItem(
                    revision_id=parts[0],
                    author=parts[1],
                    date=parts[2],
                    message=parts[3],
                )
            )
    except Exception:
        backup_files = sorted(
            lexicon_path.parent.glob(f"{lexicon_path.name}.bak.*"),
            reverse=True,
        )
        for file_path in backup_files[offset:offset + limit]:
            items.append(
                LexiconVersionItem(
                    revision_id=file_path.name,
                    author="local-backup",
                    date=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat(),
                    message="backup snapshot",
                )
            )
    return LexiconVersionsResponse(
        grammar_id=grammar_id,
        lexicon_path=str(lexicon_path),
        items=items,
    )


@router.get("/{grammar_id}/versions/{revision_id}/diff", response_model=LexiconVersionDiffResponse)
def get_lexicon_version_diff(
    grammar_id: str,
    revision_id: str,
    format: Literal["csv", "yaml"] = Query(default="csv"),
) -> LexiconVersionDiffResponse:
    root = _default_legacy_root()
    lexicon_path = resolve_legacy_lexicon_path(legacy_root=root, grammar_id=grammar_id)
    project_root = _project_root()
    diff_text = ""
    try:
        rel = lexicon_path.relative_to(project_root)
        cmd = [
            "git",
            "-C",
            str(project_root),
            "show",
            f"{revision_id}:{rel}",
        ]
        body = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        if format == "yaml":
            entries = load_legacy_lexicon(legacy_root=root, grammar_id=grammar_id)
            diff_text = build_lexicon_yaml_text(
                grammar_id=grammar_id,
                source_csv=lexicon_path.name,
                entries=entries,
            )
            diff_text = f"# requested revision: {revision_id}\n{diff_text}"
        else:
            diff_text = body
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Revision diff not found: {revision_id}") from exc
    return LexiconVersionDiffResponse(grammar_id=grammar_id, revision_id=revision_id, diff_text=diff_text)
