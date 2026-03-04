from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyGrammarEntry:
    grammar_id: str
    folder: str
    uses_lexicon_all: bool
    display_name: str


_FOLDER_RE = re.compile(r"\$folder\[\$(?P<var>\w+)\]\s*=\s*'(?P<folder>[^']+)';")
_LEXICON_ALL_RE = re.compile(r"\$lexicon\[\$(?P<var>\w+)\]\s*=\s*'all';")
_GRAMMAR_NAME_RE = re.compile(r"\$grammar\[\$(?P<var>\w+)\]\s*=\s*'(?P<name>[^']*)';")


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


def _load_grammar_list_text(legacy_root: Path) -> str:
    grammar_file = legacy_root / "grammar-list.pl"
    if not grammar_file.exists():
        return ""
    return grammar_file.read_text(encoding="utf-8")


def load_legacy_grammar_entries(legacy_root: Path | None = None) -> list[LegacyGrammarEntry]:
    root = legacy_root or _default_legacy_root()
    text = _load_grammar_list_text(root)
    if text == "":
        return []

    folder_by_var: dict[str, str] = {
        match.group("var"): match.group("folder") for match in _FOLDER_RE.finditer(text)
    }
    uses_lexicon_all_vars = {match.group("var") for match in _LEXICON_ALL_RE.finditer(text)}
    name_by_var: dict[str, str] = {
        match.group("var"): match.group("name") for match in _GRAMMAR_NAME_RE.finditer(text)
    }

    entries: list[LegacyGrammarEntry] = []
    for var_name, folder in folder_by_var.items():
        entries.append(
            LegacyGrammarEntry(
                grammar_id=folder,
                folder=folder,
                uses_lexicon_all=var_name in uses_lexicon_all_vars,
                display_name=name_by_var.get(var_name, folder),
            )
        )

    entries.sort(key=lambda entry: entry.grammar_id)
    return entries
