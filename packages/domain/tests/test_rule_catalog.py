from pathlib import Path

from domain.grammar.rule_catalog import (
    get_rule_name_by_number,
    get_rule_number_by_name,
    load_rule_catalog,
)


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_load_rule_catalog_imi03_basic_rules() -> None:
    rules = load_rule_catalog(grammar_id="imi03", legacy_root=_legacy_root())
    assert [rule.name for rule in rules] == ["RH-Merge", "LH-Merge", "zero-Merge"]
    assert [rule.number for rule in rules] == [1, 2, 3]


def test_load_rule_catalog_japanese2_contains_expected_entries() -> None:
    rules = load_rule_catalog(grammar_id="japanese2", legacy_root=_legacy_root())
    assert rules[0].name == "sase1"
    assert get_rule_number_by_name("japanese2", "RH-Merge", _legacy_root()) == 11
    assert get_rule_number_by_name("japanese2", "zero-Merge", _legacy_root()) == 14


def test_rule_name_number_lookup_roundtrip_imi02() -> None:
    assert get_rule_number_by_name("imi02", "RH-Merge", _legacy_root()) == 1
    assert get_rule_name_by_number("imi02", 2, _legacy_root()) == "LH-Merge"
