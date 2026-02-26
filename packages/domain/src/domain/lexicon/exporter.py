from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from domain.lexicon.legacy_loader import load_legacy_lexicon, resolve_legacy_lexicon_path
from domain.lexicon.models import LexiconEntry


@dataclass(frozen=True)
class LexiconExportBundle:
    grammar_id: str
    lexicon_path: Path
    entry_count: int
    csv_text: str
    yaml_text: str


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _split_semantic(value: str) -> tuple[str, str]:
    parts = value.split(":", 1)
    if len(parts) == 1:
        return value, ""
    return parts[0], parts[1]


def _normalize_note(note: str) -> str:
    if note.startswith("[") and note.endswith("]"):
        return note[1:-1]
    return note


def build_lexicon_yaml_text(
    *,
    grammar_id: str,
    source_csv: str,
    entries: dict[int, LexiconEntry],
    generated_at: str | None = None,
) -> str:
    timestamp = generated_at
    if timestamp is None:
        timestamp = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        )

    lines: list[str] = []
    lines.append("meta:")
    lines.append(f"  grammar_id: {_yaml_quote(grammar_id)}")
    lines.append(f"  source_csv: {_yaml_quote(source_csv)}")
    lines.append(f"  generated_at: {_yaml_quote(timestamp)}")
    lines.append("  schema_version: 1")
    lines.append("")
    lines.append("entries:")

    for lexicon_id in sorted(entries):
        entry = entries[lexicon_id]
        lines.append(f"  - no: {entry.lexicon_id}")
        lines.append(f"    entry: {_yaml_quote(entry.entry)}")
        lines.append(f"    phono: {_yaml_quote(entry.phono)}")
        lines.append(f"    category: {_yaml_quote(entry.category)}")

        if entry.predicates:
            lines.append("    predication:")
            for pred_i, pred_s, pred_p in entry.predicates:
                lines.append(
                    "      - "
                    + f"[{_yaml_quote(pred_i)}, {_yaml_quote(pred_s)}, {_yaml_quote(pred_p)}]"
                )
        else:
            lines.append("    predication: []")

        if entry.sync_features:
            lines.append("    sync:")
            for feature in entry.sync_features:
                lines.append(f"      - {_yaml_quote(feature)}")
        else:
            lines.append("    sync: []")

        lines.append(f"    idslot: {_yaml_quote(entry.idslot)}")

        if entry.semantics:
            lines.append("    semantics:")
            for semantic in entry.semantics:
                attr, value = _split_semantic(semantic)
                lines.append("      -")
                lines.append(f"        attr: {_yaml_quote(attr)}")
                lines.append(f"        value: {_yaml_quote(value)}")
        else:
            lines.append("    semantics: []")

        lines.append(f"    note: {_yaml_quote(_normalize_note(entry.note))}")

    return "\n".join(lines) + "\n"


def export_legacy_lexicon_bundle(legacy_root: Path, grammar_id: str) -> LexiconExportBundle:
    lexicon_path = resolve_legacy_lexicon_path(legacy_root=legacy_root, grammar_id=grammar_id)
    if not lexicon_path.exists():
        raise ValueError(f"Lexicon file not found: {lexicon_path}")

    entries = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
    csv_text = lexicon_path.read_text(encoding="utf-8")
    yaml_text = build_lexicon_yaml_text(
        grammar_id=grammar_id,
        source_csv=lexicon_path.name,
        entries=entries,
    )
    return LexiconExportBundle(
        grammar_id=grammar_id,
        lexicon_path=lexicon_path,
        entry_count=len(entries),
        csv_text=csv_text,
        yaml_text=yaml_text,
    )
