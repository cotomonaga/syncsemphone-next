from domain.common.types import DerivationState


def test_derivation_state_defaults() -> None:
    state = DerivationState(grammar_id="imi03")
    assert state.grammar_id == "imi03"
    assert state.newnum == 0
    assert state.base == [None]
