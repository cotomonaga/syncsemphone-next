from pathlib import Path

from domain.derivation.candidates import list_merge_candidates
from domain.numeration.init_builder import build_initial_derivation_state


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_japanese2_candidates_use_catalog_rule_number_and_skip_missing_lh() -> None:
    numeration_text = (_legacy_root() / "japanese2/set-numeration/00-00-01.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    rows = list_merge_candidates(
        state=state,
        left=5,
        right=6,
        legacy_root=_legacy_root(),
    )

    rh = [row for row in rows if row.rule_name == "RH-Merge"]
    lh = [row for row in rows if row.rule_name == "LH-Merge"]
    assert len(rh) == 1
    assert rh[0].rule_number == 11
    assert len(lh) == 0


def test_japanese2_candidates_include_jmerge_on_n_plus_j() -> None:
    numeration_text = (_legacy_root() / "japanese2/set-numeration/00-00-01.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    rows = list_merge_candidates(
        state=state,
        left=1,
        right=2,
        legacy_root=_legacy_root(),
    )

    names = [row.rule_name for row in rows]
    assert "J-Merge" in names
    assert "RH-Merge" not in names
    jmerge = [row for row in rows if row.rule_name == "J-Merge"][0]
    assert jmerge.rule_number == 7
