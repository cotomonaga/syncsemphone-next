from pathlib import Path

from domain.derivation.execute import execute_double_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.resume.codec import export_resume_text, import_resume_text


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _initial_state():
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    return build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )


def test_execute_lh_merge_changes_basenum_and_history() -> None:
    state = _initial_state()
    next_state = execute_double_merge(
        state=state,
        rule_name="LH-Merge",
        left=5,
        right=6,
    )
    assert next_state.basenum == 5
    assert next_state.history.endswith("LH-Merge) ")
    assert next_state.base[5][0] == "x5-1"
    assert isinstance(next_state.base[5][7], list)
    assert next_state.base[5][7][0][1] == "V"
    assert next_state.base[5][7][1][1] == "T"
    # imi03 の feature 17 条件で V 側の未解釈素性が消える
    assert "2,17,T,,,left,head" not in next_state.base[5][3]


def test_resume_roundtrip_for_t0_t1_t2() -> None:
    t0 = _initial_state()
    t1 = execute_double_merge(state=t0, rule_name="LH-Merge", left=5, right=6)
    t2 = execute_double_merge(state=t1, rule_name="RH-Merge", left=1, right=2)

    for state in (t0, t1, t2):
        resume_text = export_resume_text(state)
        restored = import_resume_text(resume_text)
        assert restored.grammar_id == state.grammar_id
        assert restored.memo == state.memo
        assert restored.newnum == state.newnum
        assert restored.basenum == state.basenum
        assert restored.history == state.history
        assert restored.base == state.base


def test_execute_lh_merge_resolves_case_linked_semantics_feature_33() -> None:
    state = _initial_state()
    # V(head) + を(J, non-head): Theme:2,33,wo -> Theme:x4-1
    next_state = execute_double_merge(
        state=state,
        rule_name="LH-Merge",
        left=5,
        right=4,
    )
    mother = None
    for idx in range(1, next_state.basenum + 1):
        if next_state.base[idx][0] == "x5-1":
            mother = next_state.base[idx]
            break
    assert mother is not None
    assert "Theme:x4-1" in mother[5]
    # se処理で参照された wo-marking を nonhead sy から消してから sy 処理へ渡す
    nonhead_sy_after = mother[7][1][3]
    assert all(",11,wo" not in value for value in nonhead_sy_after)


def test_execute_pr_feature_24_replaced_by_merge_partner_id() -> None:
    # head側のPredication項 feature 24 が merge相手id に解決されること
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text="synthetic\t60\t103\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state.base[1][2] = [["x1-2", "2,24", "Pred"]]
    next_state = execute_double_merge(
        state=state,
        rule_name="LH-Merge",
        left=1,
        right=2,
    )
    mother = next_state.base[1]
    assert mother[2][0][1] == "x2-1"
