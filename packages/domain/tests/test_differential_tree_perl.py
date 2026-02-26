import json
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path

import pytest

from domain.derivation.execute import execute_double_merge, execute_single_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.observation.tree import build_treedrawer_csv_lines


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _state_t0():
    numeration_text = (_legacy_root() / "imi03/set-numeration/04.num").read_text(
        encoding="utf-8"
    )
    return build_initial_derivation_state(
        grammar_id="imi03",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )


def _state_t1():
    return execute_double_merge(state=_state_t0(), rule_name="LH-Merge", left=5, right=6)


def _state_t2():
    t1 = _state_t1()
    return execute_double_merge(state=t1, rule_name="RH-Merge", left=1, right=2)


def _state_japanese2_080115_rh():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/08-01-15.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=7,
        right=3,
        rule_version="01",
    )


def _state_japanese2_property_da():
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


def _state_japanese2_p_merge():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/08-05-45.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="P-Merge",
        left=1,
        right=5,
        rule_version="01",
    )


def _state_japanese2_zero_merge():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/05-03-09.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    from domain.derivation.execute import execute_single_merge

    return execute_single_merge(
        state=state,
        rule_name="zero-Merge",
        check=4,
    )


def _state_japanese2_rel_merge():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-05-831.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="rel-Merge",
        left=10,
        right=1,
        rule_version="01",
    )


def _state_japanese2_partitioning():
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


def _state_japanese2_j_merge():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/00-00-01.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="J-Merge",
        left=1,
        right=2,
        rule_version="01",
    )


def _state_japanese2_sase1():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-01-29.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="sase1",
        left=7,
        right=8,
        rule_version="01",
    )


def _state_japanese2_sase2():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-05-831.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="sase2",
        left=9,
        right=8,
        rule_version="01",
    )


def _state_japanese2_rare1():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-05-831.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="rare1",
        left=7,
        right=9,
        rule_version="01",
    )


def _state_japanese2_rare2():
    numeration_text = (_legacy_root() / "japanese2/set-numeration/03-05-832.num").read_text(
        encoding="utf-8"
    )
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )
    return execute_double_merge(
        state=state,
        rule_name="rare2",
        left=7,
        right=9,
        rule_version="01",
    )


def _state_japanese2_property_no_synthetic():
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state = state.model_copy(deep=True)
    state.base[1][4] = "x1-1"
    state.base[2][3] = ["1,1,N", "2,3,N"]
    return execute_double_merge(
        state=state,
        rule_name="property-no",
        left=1,
        right=2,
        rule_version="01",
    )


def _synthetic_pickup_state():
    mover = ["x200-1", "N", [], ["1,11,ga"], "x200-1", [], "", ["zero", "zero"]]
    head = ["x201-1", "V", [], ["v"], "x201-1", [], "", ["zero", "zero"]]
    target = ["x1-1", "V", [], [], "x1-1", [], "", [mover, head]]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    return build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1",
        legacy_root=_legacy_root(),
    ).model_copy(
        update={
            "memo": "synthetic-pickup",
            "newnum": 300,
            "basenum": 2,
            "history": "",
            "base": [None, target, filler],
        }
    )


def _synthetic_landing_state():
    mover = [
        "x300-1",
        "N",
        [],
        ["3,107,move", "1,11,ga"],
        "x300-1",
        [],
        "",
        ["zero", "zero"],
    ]
    payload = json.dumps(mover, ensure_ascii=False, separators=(",", ":"))
    target = [
        "x1-1",
        "V",
        [],
        [f"3,106,{payload}"],
        "x1-1",
        [],
        "",
        ["zero", "zero"],
    ]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    return build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1",
        legacy_root=_legacy_root(),
    ).model_copy(
        update={
            "memo": "synthetic-landing",
            "newnum": 400,
            "basenum": 2,
            "history": "",
            "base": [None, target, filler],
        }
    )


def _state_japanese2_pickup():
    return execute_single_merge(
        state=_synthetic_pickup_state(),
        rule_name="Pickup",
        check=1,
    )


def _state_japanese2_landing():
    return execute_single_merge(
        state=_synthetic_landing_state(),
        rule_name="Landing",
        check=1,
    )


def _perl_tree_csv_lines(mode: str, state) -> list[str]:
    grammar_no = 5 if state.grammar_id == "imi03" else 1
    params = {
        "grammar": str(grammar_no),
        "mode": mode,
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(state.base, ensure_ascii=False),
    }
    payload = urllib.parse.urlencode(params)
    env = os.environ.copy()
    env["REQUEST_METHOD"] = "POST"
    env["CONTENT_LENGTH"] = str(len(payload.encode("utf-8")))
    proc = subprocess.run(
        ["perl", "-I.", "syncsemphone.cgi"],
        input=payload.encode("utf-8"),
        cwd=str(_legacy_root()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr.decode("utf-8", errors="ignore"))
    html = proc.stdout.decode("utf-8", errors="ignore")
    match = re.search(r'id="source_csv"[^>]*>(.*?)</textarea>', html, re.S)
    if not match:
        raise AssertionError("source_csv textarea not found in perl output")
    return [line.strip() for line in match.group(1).strip().splitlines() if line.strip()]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("mode", ["tree", "tree_cat"])
def test_differential_tree_t0_matches_perl(mode: str) -> None:
    state = _state_t0()
    py_lines = build_treedrawer_csv_lines(state=state, mode=mode)
    perl_lines = _perl_tree_csv_lines(mode=mode, state=state)
    assert py_lines == perl_lines


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("mode", ["tree", "tree_cat"])
def test_differential_tree_t1_matches_perl(mode: str) -> None:
    state = _state_t1()
    py_lines = build_treedrawer_csv_lines(state=state, mode=mode)
    perl_lines = _perl_tree_csv_lines(mode=mode, state=state)
    assert py_lines == perl_lines


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("mode", ["tree", "tree_cat"])
def test_differential_tree_t2_matches_perl(mode: str) -> None:
    state = _state_t2()
    py_lines = build_treedrawer_csv_lines(state=state, mode=mode)
    perl_lines = _perl_tree_csv_lines(mode=mode, state=state)
    assert py_lines == perl_lines


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("mode", ["tree", "tree_cat"])
def test_differential_tree_japanese2_080115_rh_matches_perl(mode: str) -> None:
    state = _state_japanese2_080115_rh()
    py_lines = build_treedrawer_csv_lines(state=state, mode=mode)
    perl_lines = _perl_tree_csv_lines(mode=mode, state=state)
    assert py_lines == perl_lines


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("mode", ["tree", "tree_cat"])
@pytest.mark.parametrize(
    "state_factory",
    [
        _state_japanese2_property_da,
        _state_japanese2_p_merge,
        _state_japanese2_zero_merge,
        _state_japanese2_rel_merge,
        _state_japanese2_partitioning,
        _state_japanese2_j_merge,
        _state_japanese2_sase1,
        _state_japanese2_sase2,
        _state_japanese2_rare1,
        _state_japanese2_rare2,
        _state_japanese2_property_no_synthetic,
        _state_japanese2_pickup,
        _state_japanese2_landing,
    ],
)
def test_differential_tree_japanese2_multi_rule_states_match_perl(
    mode: str, state_factory
) -> None:
    state = state_factory()
    py_lines = build_treedrawer_csv_lines(state=state, mode=mode)
    perl_lines = _perl_tree_csv_lines(mode=mode, state=state)
    assert py_lines == perl_lines
