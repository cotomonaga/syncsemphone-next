import json
from pathlib import Path

import pytest

from domain.common.types import DerivationState
from domain.derivation.execute import execute_double_merge, execute_single_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.observation.tree import build_treedrawer_csv_lines
from domain.resume.codec import export_resume_text, import_resume_text


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _state_imi03_t0() -> DerivationState:
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    return build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )


def _state_imi03_t1() -> DerivationState:
    return execute_double_merge(
        state=_state_imi03_t0(),
        rule_name="LH-Merge",
        left=5,
        right=6,
    )


def _state_imi03_t2() -> DerivationState:
    return execute_double_merge(
        state=_state_imi03_t1(),
        rule_name="RH-Merge",
        left=1,
        right=2,
    )


def _state_japanese2_property_da() -> DerivationState:
    numeration_text = (_legacy_root() / "japanese2/set-numeration/05-03-09.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="property-da",
        left=1,
        right=4,
        rule_version="01",
    )


def _state_japanese2_partitioning() -> DerivationState:
    numeration_text = (_legacy_root() / "japanese2/set-numeration/08-05-45.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_single_merge(
        state=state,
        rule_name="Partitioning",
        check=5,
    )


def _state_japanese2_pickup() -> DerivationState:
    mover = ["x200-1", "N", [], ["1,11,ga"], "x200-1", [], "", ["zero", "zero"]]
    head = ["x201-1", "V", [], ["v"], "x201-1", [], "", ["zero", "zero"]]
    target = ["x1-1", "V", [], [], "x1-1", [], "", [mover, head]]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    state = DerivationState(
        grammar_id="japanese2",
        memo="synthetic-pickup",
        newnum=300,
        basenum=2,
        history="",
        base=[None, target, filler],
    )
    return execute_single_merge(
        state=state,
        rule_name="Pickup",
        check=1,
    )


@pytest.mark.parametrize(
    "state_factory",
    [
        _state_imi03_t0,
        _state_imi03_t1,
        _state_imi03_t2,
        _state_japanese2_property_da,
        _state_japanese2_partitioning,
        _state_japanese2_pickup,
    ],
)
def test_resume_roundtrip_keeps_tree_csvs(state_factory) -> None:
    original = state_factory()
    resume_text = export_resume_text(original)
    restored = import_resume_text(resume_text)

    for mode in ("tree", "tree_cat"):
        before = build_treedrawer_csv_lines(state=original, mode=mode)
        after = build_treedrawer_csv_lines(state=restored, mode=mode)
        assert after == before


@pytest.mark.parametrize(
    "state_factory",
    [
        _state_imi03_t2,
        _state_japanese2_property_da,
        _state_japanese2_partitioning,
        _state_japanese2_pickup,
    ],
)
def test_resume_export_import_export_is_stable(state_factory) -> None:
    state = state_factory()
    first = export_resume_text(state)
    restored = import_resume_text(first)
    second = export_resume_text(restored)
    assert second == first


def test_resume_text_is_six_line_format_with_single_line_base_json() -> None:
    state = _state_imi03_t2()
    resume_text = export_resume_text(state)
    lines = resume_text.splitlines()
    assert len(lines) == 6
    assert lines[0] == "imi03"
    base = json.loads(lines[5])
    assert base == state.base
