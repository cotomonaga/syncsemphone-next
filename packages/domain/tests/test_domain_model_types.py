import json
from pathlib import Path

import pytest

from domain.common.domain_types import (
    DerivationIndex,
    DoubleMergeTarget,
    RuleRef,
    SingleMergeTarget,
)


def _specs_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "docs/specs"


def test_derivation_index_requires_positive() -> None:
    assert DerivationIndex(value=1).value == 1
    with pytest.raises(Exception):
        DerivationIndex(value=0)


def test_double_merge_target_requires_distinct_indices() -> None:
    target = DoubleMergeTarget(left=DerivationIndex(value=1), right=DerivationIndex(value=2))
    assert target.left.value == 1
    assert target.right.value == 2
    with pytest.raises(Exception):
        DoubleMergeTarget(left=DerivationIndex(value=3), right=DerivationIndex(value=3))


def test_single_merge_target_holds_check_index() -> None:
    target = SingleMergeTarget(check=DerivationIndex(value=5))
    assert target.check.value == 5


def test_rule_ref_requires_name_or_number() -> None:
    assert RuleRef(rule_name="RH-Merge").rule_name == "RH-Merge"
    assert RuleRef(rule_number=11).rule_number == 11
    assert RuleRef(rule_name="RH-Merge", rule_number=11).rule_number == 11
    with pytest.raises(Exception):
        RuleRef()


def test_domain_model_types_doc_contract() -> None:
    specs = _specs_dir()
    text = (specs / "domain-model-types-ja.md").read_text(encoding="utf-8")
    contract = json.loads((specs / "domain-model-types-contract.json").read_text(encoding="utf-8"))
    assert contract["version"] == "v1"
    missing = [term for term in contract["required_terms"] if term not in text]
    assert missing == [], f"Missing domain model terms: {missing}"


def test_behavior_priority_doc_contract() -> None:
    specs = _specs_dir()
    text = (specs / "behavior-priority-ja.md").read_text(encoding="utf-8")
    contract = json.loads((specs / "behavior-priority-contract-ja.json").read_text(encoding="utf-8"))
    assert contract["version"] == "v1"
    missing_ids = [rid for rid in contract["required_rule_ids"] if rid not in text]
    missing_phrases = [phrase for phrase in contract["required_phrases"] if phrase not in text]
    assert missing_ids == [], f"Missing behavior rule ids: {missing_ids}"
    assert missing_phrases == [], f"Missing behavior rule phrases: {missing_phrases}"
