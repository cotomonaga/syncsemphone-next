from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LexiconEntry:
    lexicon_id: int
    entry: str
    phono: str
    category: str
    predicates: list[tuple[str, str, str]]
    sync_features: list[str]
    idslot: str
    semantics: list[str]
    note: str
