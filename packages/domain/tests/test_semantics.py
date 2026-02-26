from pathlib import Path

from domain.common.types import DerivationState
from domain.derivation.execute import execute_double_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.semantics.lf_sr import build_lf_items, build_sr_layers


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


def test_lf_items_include_name_semantics() -> None:
    state = _state_after_one_step()
    items = build_lf_items(state)
    semantic_values = [value for item in items for value in item.semantics]
    assert "Name:ジョン" in semantic_values
    assert "Name:メアリ" in semantic_values


def test_sr_layers_group_by_object_layer() -> None:
    state = _state_after_one_step()
    layers = build_sr_layers(state)
    assert any(row.object_id == 1 and row.layer == 1 for row in layers)
    assert any(
        row.object_id == 1
        and row.layer == 1
        and any(value.startswith("Name:") for value in row.properties)
        for row in layers
    )


def test_sr_layers_resolve_beta_binding_synthetic() -> None:
    state = DerivationState(
        grammar_id="japanese2",
        memo="beta-synth",
        newnum=6,
        basenum=3,
        history="",
        base=[
            None,
            ["x2-1", "V", [], [], "x2-1", ["Agent:x4-1"], "", ""],
            [
                "x5-1",
                "N",
                [],
                ["beta#5#Agent(x2-1)"],
                "β5",
                ["Kind:betaThing"],
                "",
                "",
            ],
            ["x4-1", "N", [], [], "x4-1", ["Name:target"], "", ""],
        ],
    )

    layers = build_sr_layers(state)
    assert any(
        row.object_id == 4
        and row.layer == 1
        and "Kind:betaThing" in row.properties
        for row in layers
    )
    assert not any(row.object_id == 5 for row in layers)


def test_sr_layers_resolve_multiple_beta_bindings_synthetic() -> None:
    state = DerivationState(
        grammar_id="japanese2",
        memo="beta-multi-synth",
        newnum=9,
        basenum=5,
        history="",
        base=[
            None,
            ["x2-1", "V", [], [], "x2-1", ["Agent:x4-1", "Theme:x8-1"], "", ""],
            ["x5-1", "N", [], ["beta#5#Agent(x2-1)"], "β5", ["Kind:betaA"], "", ""],
            ["x6-1", "N", [], ["beta#6#Theme(x2-1)"], "β6", ["Kind:betaB"], "", ""],
            ["x4-1", "N", [], [], "x4-1", ["Name:targetA"], "", ""],
            ["x8-1", "N", [], [], "x8-1", ["Name:targetB"], "", ""],
        ],
    )

    layers = build_sr_layers(state)
    assert any(
        row.object_id == 4
        and row.layer == 1
        and "Kind:betaA" in row.properties
        for row in layers
    )
    assert any(
        row.object_id == 8
        and row.layer == 1
        and "Kind:betaB" in row.properties
        for row in layers
    )
    assert not any(row.object_id in {5, 6} for row in layers)
