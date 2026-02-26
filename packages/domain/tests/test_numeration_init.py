from pathlib import Path

from domain.numeration.init_builder import build_initial_derivation_state


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_init_from_imi03_04_num() -> None:
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.memo == "ジョンがメアリを追いかけた"
    assert state.basenum == 6
    assert state.newnum == 7
    assert state.base[1][0] == "x1-1"
    assert state.base[6][1] == "T"
    assert state.base[6][6] == "-ta"


def test_target_plus_feature_in_imi03() -> None:
    numeration_text = "\n".join(
        [
            "plus-target\t24\t60",
            "\ttarget\t",
            "\t1\t2",
        ]
    )
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.basenum == 2
    assert state.base[1][3] == ["3,53,target,id"]


def test_beta_generation_from_sync_3_103() -> None:
    numeration_text = "\n".join(
        [
            "beta-case\t57",
            "\t",
            "\t",
        ]
    )
    state = build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.base[1][0] == "β1"
    assert state.base[1][3][0] == "3,103,1"


def test_init_from_legacy_one_line_num_japanese2() -> None:
    numeration_text = (
        _legacy_root() / "japanese2/set-numeration/03-05-832.num"
    ).read_text(encoding="utf-8")
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.memo.startswith("ビルがジョンにメアリを追いかけさせられた")
    assert state.basenum == 10
    assert state.newnum == 11


def test_init_from_legacy_two_line_num_japanese2() -> None:
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-01-29.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    assert state.memo.startswith("ビルがジョンにメアリを追いかけさせた")
    assert state.basenum == 9
    assert state.newnum == 10
