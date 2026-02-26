from pathlib import Path

from domain.derivation.candidates import list_merge_candidates
from domain.numeration.init_builder import build_initial_derivation_state


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _baseline_state():
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    return build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )


def test_hypothesis_loop_experiment_a_baseline_03() -> None:
    state = _baseline_state()

    vt = list_merge_candidates(
        state=state,
        left=5,
        right=6,
        legacy_root=_legacy_root(),
        rh_merge_version="03",
        lh_merge_version="03",
    )
    assert [rule.rule_name for rule in vt] == ["RH-Merge", "LH-Merge", "zero-Merge"]

    nj = list_merge_candidates(
        state=state,
        left=1,
        right=2,
        legacy_root=_legacy_root(),
        rh_merge_version="03",
        lh_merge_version="03",
    )
    assert [rule.rule_name for rule in nj] == ["RH-Merge", "LH-Merge"]


def test_hypothesis_loop_experiment_b_swap_04() -> None:
    state = _baseline_state()

    vt = list_merge_candidates(
        state=state,
        left=5,
        right=6,
        legacy_root=_legacy_root(),
        rh_merge_version="04",
        lh_merge_version="04",
    )
    assert [rule.rule_name for rule in vt] == ["LH-Merge", "zero-Merge"]

    nj = list_merge_candidates(
        state=state,
        left=1,
        right=2,
        legacy_root=_legacy_root(),
        rh_merge_version="04",
        lh_merge_version="04",
    )
    assert [rule.rule_name for rule in nj] == ["RH-Merge"]
