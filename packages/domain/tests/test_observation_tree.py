from pathlib import Path

from domain.derivation.execute import execute_double_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.observation.tree import build_treedrawer_csv_lines


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _state_after_one_step():
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(state=state, rule_name="LH-Merge", left=5, right=6)


def test_tree_lines_include_leaf_phonology() -> None:
    state = _state_after_one_step()
    lines = build_treedrawer_csv_lines(state=state, mode="tree")
    assert len(lines) > 0
    assert any("&lt;br&gt;-ta" in line for line in lines)


def test_tree_cat_lines_include_leaf_category_phonology() -> None:
    state = _state_after_one_step()
    lines = build_treedrawer_csv_lines(state=state, mode="tree_cat")
    assert len(lines) > 0
    assert any("T&lt;br&gt;-ta" in line for line in lines)
