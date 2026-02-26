from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

from domain.grammar.legacy_catalog import load_legacy_grammar_entries


@dataclass(frozen=True)
class GrammarProfile:
    grammar_id: str
    folder: str
    uses_lexicon_all: bool
    has_zero_merge: bool = False
    rh_merge_version: str = "03"
    lh_merge_version: str = "03"


_GRAMMAR_MAP: dict[str, GrammarProfile] = {
    "imi01": GrammarProfile(
        grammar_id="imi01",
        folder="imi01",
        uses_lexicon_all=True,
    ),
    "imi02": GrammarProfile(
        grammar_id="imi02",
        folder="imi02",
        uses_lexicon_all=True,
        has_zero_merge=True,
    ),
    "imi03": GrammarProfile(
        grammar_id="imi03",
        folder="imi03",
        uses_lexicon_all=True,
        has_zero_merge=True,
        rh_merge_version="03",
        lh_merge_version="03",
    ),
    "japanese2": GrammarProfile(
        grammar_id="japanese2",
        folder="japanese2",
        uses_lexicon_all=False,
        has_zero_merge=True,
        rh_merge_version="01",
        lh_merge_version="01",
    ),
}

_RULENAME_RE = re.compile(
    r"\['(?P<name>RH-Merge|LH-Merge)'\s*,\s*'(?P<file>(RH-Merge|LH-Merge)_(?P<version>\d+))'"
)

_DYNAMIC_GRAMMAR_MAP: dict[str, GrammarProfile] | None = None


def _load_dynamic_grammar_map() -> dict[str, GrammarProfile]:
    global _DYNAMIC_GRAMMAR_MAP
    if _DYNAMIC_GRAMMAR_MAP is not None:
        return _DYNAMIC_GRAMMAR_MAP

    dynamic: dict[str, GrammarProfile] = {}
    for entry in load_legacy_grammar_entries():
        dynamic[entry.grammar_id] = GrammarProfile(
            grammar_id=entry.grammar_id,
            folder=entry.folder,
            uses_lexicon_all=entry.uses_lexicon_all,
        )
    _DYNAMIC_GRAMMAR_MAP = dynamic
    return dynamic


def get_grammar_profile(grammar_id: str) -> GrammarProfile:
    profile = _GRAMMAR_MAP.get(grammar_id)
    if profile is None:
        profile = _load_dynamic_grammar_map().get(grammar_id)
    if profile is None:
        supported = ", ".join(sorted(set(_GRAMMAR_MAP) | set(_load_dynamic_grammar_map())))
        raise ValueError(f"Unsupported grammar_id: {grammar_id}. Supported: {supported}")
    return profile


def get_grammar_id_from_folder(folder: str) -> str:
    combined = {**_load_dynamic_grammar_map(), **_GRAMMAR_MAP}
    for grammar_id, profile in combined.items():
        if profile.folder == folder:
            return grammar_id
    raise ValueError(f"Unsupported grammar folder in resume: {folder}")


def resolve_rule_versions(profile: GrammarProfile, legacy_root: Path) -> GrammarProfile:
    if profile.grammar_id != "imi03":
        return profile

    rule_file = legacy_root / "imi03" / "imi03R.pl"
    if not rule_file.exists():
        return profile

    text = rule_file.read_text(encoding="utf-8")
    rh_version = profile.rh_merge_version
    lh_version = profile.lh_merge_version
    for match in _RULENAME_RE.finditer(text):
        name = match.group("name")
        version = match.group("version")
        if name == "RH-Merge":
            rh_version = version
        if name == "LH-Merge":
            lh_version = version
    return replace(profile, rh_merge_version=rh_version, lh_merge_version=lh_version)
