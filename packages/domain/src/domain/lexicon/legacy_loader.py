from __future__ import annotations

from pathlib import Path

from domain.grammar.profiles import get_grammar_profile
from domain.lexicon.models import LexiconEntry


def _to_int(value: str, default: int = 0) -> int:
    raw = value.strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _cell(cells: list[str], index: int) -> str:
    if index < len(cells):
        return cells[index].strip()
    return ""


def _resolve_lexicon_path(legacy_root: Path, grammar_id: str) -> Path:
    profile = get_grammar_profile(grammar_id)
    if profile.uses_lexicon_all:
        return legacy_root / "lexicon-all.csv"
    return legacy_root / profile.folder / f"{profile.folder}.csv"


def resolve_legacy_lexicon_path(legacy_root: Path, grammar_id: str) -> Path:
    return _resolve_lexicon_path(legacy_root=legacy_root, grammar_id=grammar_id)


def load_legacy_lexicon(legacy_root: Path, grammar_id: str) -> dict[int, LexiconEntry]:
    lexicon_path = _resolve_lexicon_path(legacy_root, grammar_id)
    if not lexicon_path.exists():
        raise ValueError(f"Lexicon file not found: {lexicon_path}")

    lines = lexicon_path.read_text(encoding="utf-8").splitlines()
    entries: dict[int, LexiconEntry] = {}
    for line in lines:
        if line.strip() == "":
            continue
        cells = line.split("\t")
        cells += [""] * max(0, 30 - len(cells))

        lexicon_id = _to_int(_cell(cells, 0), default=-1)
        if lexicon_id < 0:
            continue

        entry = _cell(cells, 1)
        phono = _cell(cells, 2) or entry
        category = _cell(cells, 3)

        prednum = _to_int(_cell(cells, 4), default=0)
        y = 4
        predicates: list[tuple[str, str, str]] = []
        for _ in range(prednum):
            triple: list[str] = []
            for _ in range(3):
                y += 1
                triple.append(_cell(cells, y))
            predicates.append((triple[0], triple[1], triple[2]))

        syncnum = _to_int(_cell(cells, 8), default=0)
        y = 8
        sync_features: list[str] = []
        for _ in range(syncnum):
            y += 1
            sync_features.append(_cell(cells, y))

        idslot = _cell(cells, 14)

        semnum = _to_int(_cell(cells, 15), default=0)
        y = 15
        semantics: list[str] = []
        for _ in range(semnum):
            y += 1
            attribute = _cell(cells, y)
            y += 1
            value = _cell(cells, y)
            if value == "":
                value = "＿"
            semantics.append(f"{attribute}:{value}")

        note = _cell(cells, 28)
        if note != "":
            note = f"[{note}]"

        entries[lexicon_id] = LexiconEntry(
            lexicon_id=lexicon_id,
            entry=entry,
            phono=phono,
            category=category,
            predicates=predicates,
            sync_features=sync_features,
            idslot=idslot,
            semantics=semantics,
            note=note,
        )

    return entries
