from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Optional

from domain.lexicon.exporter import build_lexicon_yaml_text
from domain.lexicon.models import LexiconEntry


@dataclass(frozen=True)
class LexiconYamlValidationResult:
    grammar_id: str
    valid: bool
    entry_count: int
    errors: list[str]
    normalized_yaml_text: str
    preview_csv_text: str


def _yaml_load(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency environment specific
        raise ValueError("PyYAML is required. Install PyYAML to import lexicon YAML.") from exc

    try:
        # BaseLoader keeps scalars as strings and avoids YAML 1.1 boolean coercion
        # (e.g. key "no" -> False), which would break lexicon field parsing.
        return yaml.load(text, Loader=yaml.BaseLoader)
    except Exception as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc


def _json_str(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _split_semantic(value: str) -> tuple[str, str]:
    parts = value.split(":", 1)
    if len(parts) == 1:
        return value, "＿"
    return parts[0], parts[1] if parts[1] != "" else "＿"


def _normalize_note(note: str) -> str:
    if note.startswith("[") and note.endswith("]"):
        return note[1:-1]
    return note


def _validate_and_parse_entries(
    *,
    grammar_id: str,
    payload: Any,
) -> tuple[dict[int, LexiconEntry], list[str]]:
    errors: list[str] = []
    entries: dict[int, LexiconEntry] = {}

    if not isinstance(payload, dict):
        return {}, ["YAML root must be a mapping"]

    meta = payload.get("meta", {})
    if meta is not None and not isinstance(meta, dict):
        errors.append("meta must be a mapping")
    if isinstance(meta, dict):
        meta_grammar = meta.get("grammar_id")
        if meta_grammar is not None and str(meta_grammar) != grammar_id:
            errors.append(
                f"meta.grammar_id mismatch: expected={grammar_id}, got={meta_grammar}"
            )

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        return {}, errors + ["entries must be a list"]

    seen_ids: set[int] = set()
    for idx, raw in enumerate(raw_entries, start=1):
        prefix = f"entries[{idx}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be a mapping")
            continue

        raw_id = raw.get("no")
        try:
            lexicon_id = int(raw_id)
        except Exception:
            errors.append(f"{prefix}.no must be integer")
            continue
        if lexicon_id <= 0:
            errors.append(f"{prefix}.no must be > 0")
            continue
        if lexicon_id in seen_ids:
            errors.append(f"{prefix}.no duplicated: {lexicon_id}")
            continue
        seen_ids.add(lexicon_id)

        entry = str(raw.get("entry", "")).strip()
        if entry == "":
            errors.append(f"{prefix}.entry is required")
            continue

        phono = str(raw.get("phono", "")).strip() or entry
        category = str(raw.get("category", "")).strip()
        if category == "":
            errors.append(f"{prefix}.category is required")
            continue

        raw_pred = raw.get("predication", [])
        predicates: list[tuple[str, str, str]] = []
        if not isinstance(raw_pred, list):
            errors.append(f"{prefix}.predication must be a list")
            continue
        if len(raw_pred) > 1:
            errors.append(f"{prefix}.predication supports at most 1 triple for Perl CSV compatibility")
            continue
        for pred_idx, triple in enumerate(raw_pred, start=1):
            pred_prefix = f"{prefix}.predication[{pred_idx}]"
            if not isinstance(triple, list) or len(triple) != 3:
                errors.append(f"{pred_prefix} must be a 3-item list")
                continue
            predicates.append((str(triple[0]), str(triple[1]), str(triple[2])))

        raw_sync = raw.get("sync", [])
        if not isinstance(raw_sync, list):
            errors.append(f"{prefix}.sync must be a list")
            continue
        sync_features = [str(value) for value in raw_sync]
        if len(sync_features) > 5:
            errors.append(f"{prefix}.sync supports at most 5 items for Perl CSV compatibility")
            continue

        idslot = str(raw.get("idslot", "")).strip()

        raw_semantics = raw.get("semantics", [])
        semantics: list[str] = []
        if not isinstance(raw_semantics, list):
            errors.append(f"{prefix}.semantics must be a list")
            continue
        if len(raw_semantics) > 6:
            errors.append(f"{prefix}.semantics supports at most 6 items for Perl CSV compatibility")
            continue
        for sem_idx, sem_row in enumerate(raw_semantics, start=1):
            sem_prefix = f"{prefix}.semantics[{sem_idx}]"
            if not isinstance(sem_row, dict):
                errors.append(f"{sem_prefix} must be an object with attr/value")
                continue
            attr = str(sem_row.get("attr", "")).strip()
            value = str(sem_row.get("value", "＿"))
            if attr == "":
                errors.append(f"{sem_prefix}.attr is required")
                continue
            semantics.append(f"{attr}:{value if value != '' else '＿'}")

        note = _normalize_note(str(raw.get("note", "")).strip())

        entries[lexicon_id] = LexiconEntry(
            lexicon_id=lexicon_id,
            entry=entry,
            phono=phono,
            category=category,
            predicates=predicates,
            sync_features=sync_features,
            idslot=idslot,
            semantics=semantics,
            note=f"[{note}]" if note else "",
        )

    return entries, errors


def build_lexicon_csv_text(entries: dict[int, LexiconEntry]) -> str:
    lines: list[str] = []
    for lexicon_id in sorted(entries):
        entry = entries[lexicon_id]
        row = ["" for _ in range(30)]
        row[0] = str(entry.lexicon_id)
        row[1] = entry.entry
        row[2] = entry.phono
        row[3] = entry.category

        row[4] = str(len(entry.predicates))
        if entry.predicates:
            pred = entry.predicates[0]
            row[5], row[6], row[7] = pred

        row[8] = str(len(entry.sync_features))
        for idx, feature in enumerate(entry.sync_features):
            row[9 + idx] = feature

        row[14] = entry.idslot

        row[15] = str(len(entry.semantics))
        for idx, semantic in enumerate(entry.semantics):
            attr, value = _split_semantic(semantic)
            row[16 + idx * 2] = attr
            row[17 + idx * 2] = value

        row[28] = _normalize_note(entry.note)
        row[29] = "0"
        lines.append("\t".join(row))

    return "\n".join(lines) + ("\n" if lines else "")


def validate_lexicon_yaml_text(
    *,
    grammar_id: str,
    yaml_text: str,
    source_csv: Optional[str] = None,
) -> LexiconYamlValidationResult:
    try:
        payload = _yaml_load(yaml_text)
    except ValueError as exc:
        return LexiconYamlValidationResult(
            grammar_id=grammar_id,
            valid=False,
            entry_count=0,
            errors=[str(exc)],
            normalized_yaml_text="",
            preview_csv_text="",
        )

    entries, errors = _validate_and_parse_entries(grammar_id=grammar_id, payload=payload)
    if errors:
        return LexiconYamlValidationResult(
            grammar_id=grammar_id,
            valid=False,
            entry_count=len(entries),
            errors=errors,
            normalized_yaml_text="",
            preview_csv_text="",
        )

    csv_text = build_lexicon_csv_text(entries)
    normalized_yaml_text = build_lexicon_yaml_text(
        grammar_id=grammar_id,
        source_csv=source_csv or "lexicon-all.csv",
        entries=entries,
    )
    return LexiconYamlValidationResult(
        grammar_id=grammar_id,
        valid=True,
        entry_count=len(entries),
        errors=[],
        normalized_yaml_text=normalized_yaml_text,
        preview_csv_text=csv_text,
    )
