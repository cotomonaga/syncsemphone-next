from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from domain.grammar.profiles import get_grammar_profile

_RULE_ENTRY_RE = re.compile(
    r"\[\s*'(?P<name>[^']*)'\s*,\s*'(?P<file>[^']*)'\s*,\s*(?P<kind>\d+)\s*\]"
)


@dataclass(frozen=True)
class GrammarRule:
    number: int
    name: str
    file_name: str
    kind: int


def _rule_file_path(grammar_id: str, legacy_root: Path) -> Path:
    profile = get_grammar_profile(grammar_id)
    return legacy_root / profile.folder / f"{profile.folder}R.pl"


def load_rule_catalog(grammar_id: str, legacy_root: Path) -> list[GrammarRule]:
    rule_file = _rule_file_path(grammar_id=grammar_id, legacy_root=legacy_root)
    if not rule_file.exists():
        raise ValueError(f"Rule file not found: {rule_file}")

    text = rule_file.read_text(encoding="utf-8")
    rules: list[GrammarRule] = []
    for matched in _RULE_ENTRY_RE.finditer(text):
        kind = int(matched.group("kind"))
        if kind not in (1, 2):
            continue
        rules.append(
            GrammarRule(
                number=len(rules) + 1,
                name=matched.group("name"),
                file_name=matched.group("file"),
                kind=kind,
            )
        )
    if not rules:
        raise ValueError(f"No rules found in: {rule_file}")
    return rules


def get_rule_number_by_name(
    grammar_id: str, rule_name: str, legacy_root: Path
) -> int | None:
    for rule in load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root):
        if rule.name == rule_name:
            return rule.number
    return None


def get_rule_name_by_number(
    grammar_id: str, rule_number: int, legacy_root: Path
) -> str | None:
    for rule in load_rule_catalog(grammar_id=grammar_id, legacy_root=legacy_root):
        if rule.number == rule_number:
            return rule.name
    return None
