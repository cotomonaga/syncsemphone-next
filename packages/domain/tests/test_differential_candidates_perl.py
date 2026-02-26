import copy
from collections import deque
import json
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional

import pytest

from domain.common.types import DerivationState
from domain.derivation.candidates import list_merge_candidates
from domain.derivation.execute import execute_double_merge, execute_single_merge
from domain.grammar.rule_catalog import get_rule_name_by_number, load_rule_catalog
from domain.numeration.init_builder import build_initial_derivation_state


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


def _state(grammar_id: str, numeration_relpath: str):
    numeration_text = (_legacy_root() / numeration_relpath).read_text(encoding="utf-8")
    return build_initial_derivation_state(
        grammar_id=grammar_id,
        numeration_text=numeration_text,
        legacy_root=_legacy_root(),
    )


def _synthetic_pickup_state() -> DerivationState:
    mover = ["x200-1", "N", [], ["1,11,ga"], "x200-1", [], "", ["zero", "zero"]]
    head = ["x201-1", "V", [], ["v"], "x201-1", [], "", ["zero", "zero"]]
    target = ["x1-1", "V", [], [], "x1-1", [], "", [mover, head]]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    return DerivationState(
        grammar_id="japanese2",
        memo="synthetic-pickup",
        newnum=300,
        basenum=2,
        history="",
        base=[None, target, filler],
    )


def _synthetic_landing_state() -> DerivationState:
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
    return DerivationState(
        grammar_id="japanese2",
        memo="synthetic-landing",
        newnum=400,
        basenum=2,
        history="",
        base=[None, target, filler],
    )


def _state_japanese2_080115_rh() -> DerivationState:
    state = _state("japanese2", "japanese2/set-numeration/08-01-15.num")
    return execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=7,
        right=3,
        rule_version="01",
    )


def _state_japanese2_property_da() -> DerivationState:
    state = _state("japanese2", "japanese2/set-numeration/05-03-09.num")
    return execute_double_merge(
        state=state,
        rule_name="property-da",
        left=1,
        right=4,
        rule_version="01",
    )


def _state_japanese2_zero_merge() -> DerivationState:
    state = _state("japanese2", "japanese2/set-numeration/05-03-09.num")
    return execute_single_merge(
        state=state,
        rule_name="zero-Merge",
        check=4,
    )


def _state_japanese2_partitioning() -> DerivationState:
    state = _state("japanese2", "japanese2/set-numeration/08-05-45.num")
    return execute_single_merge(
        state=state,
        rule_name="Partitioning",
        check=5,
    )


def _state_japanese2_pickup() -> DerivationState:
    state = _synthetic_pickup_state()
    return execute_single_merge(
        state=state,
        rule_name="Pickup",
        check=1,
    )


def _state_japanese2_landing() -> DerivationState:
    state = _synthetic_landing_state()
    return execute_single_merge(
        state=state,
        rule_name="Landing",
        check=1,
    )


def _to_perl_item(item):
    if not isinstance(item, list) or len(item) < 8:
        return item
    out = copy.deepcopy(item)
    if isinstance(out[2], list):
        out[2] = [None] + out[2]
    if isinstance(out[3], list):
        out[3] = [None] + out[3]
    if isinstance(out[5], list):
        out[5] = [None] + out[5]
    if isinstance(out[7], list):
        converted = []
        for child in out[7]:
            if child == "zero":
                converted.append(child)
            else:
                converted.append(_to_perl_item(child))
        out[7] = converted
    return out


def _to_perl_base(base):
    return [None] + [_to_perl_item(item) for item in base[1:]]


def _perl_candidates(
    state,
    left: int,
    right: int,
    grammar_no: int,
    allowed_rule_names: Optional[set[str]] = None,
) -> list[tuple[str, Optional[int], Optional[int], Optional[int]]]:
    params = {
        "grammar": str(grammar_no),
        "mode": "rule_select",
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(_to_perl_base(state.base), ensure_ascii=False),
        "left": str(left),
        "right": str(right),
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
    out = proc.stdout.decode("utf-8", errors="ignore")

    pattern = re.compile(r'name="rule(?P<choice>\d+)" value=(?P<rule>\d+)')
    rows: list[tuple[str, int | None, int | None, int | None]] = []
    allowed = allowed_rule_names or {"RH-Merge", "LH-Merge", "zero-Merge", "J-Merge"}
    for match in pattern.finditer(out):
        choice = match.group("choice")
        rule_number = int(match.group("rule"))
        rule_name = get_rule_name_by_number(
            grammar_id=state.grammar_id,
            rule_number=rule_number,
            legacy_root=_legacy_root(),
        )
        if rule_name is None:
            continue
        if rule_name not in allowed:
            continue
        left_match = re.search(rf'name="left{choice}" value="(\d+)"', out)
        right_match = re.search(rf'name="right{choice}" value="(\d+)"', out)
        check_match = re.search(rf'name="check{choice}" value="(\d+)"', out)
        left_value = int(left_match.group(1)) if left_match else None
        right_value = int(right_match.group(1)) if right_match else None
        check_value = int(check_match.group(1)) if check_match else None
        rows.append((rule_name, left_value, right_value, check_value))
    return rows


def _py_candidates(
    state,
    left: int,
    right: int,
    allowed_rule_names: Optional[set[str]] = None,
):
    allowed = allowed_rule_names or {"RH-Merge", "LH-Merge", "zero-Merge", "J-Merge"}
    rows = []
    for candidate in list_merge_candidates(
        state=state,
        left=left,
        right=right,
        legacy_root=_legacy_root(),
    ):
        if candidate.rule_name not in allowed:
            continue
        rows.append((candidate.rule_name, candidate.left, candidate.right, candidate.check))
    return rows


def _state_key(state: DerivationState) -> str:
    payload = {
        "memo": state.memo,
        "newnum": state.newnum,
        "basenum": state.basenum,
        "history": state.history,
        "base": state.base,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("left,right", [(5, 6), (1, 2), (5, 4), (3, 4)])
def test_differential_candidates_match_perl(left: int, right: int) -> None:
    state = _state_t0()
    assert _py_candidates(state, left, right) == _perl_candidates(
        state, left, right, grammar_no=5
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("grammar_id", "numeration_relpath", "grammar_no"),
    [
        ("imi01", "imi01/set-numeration/04.num", 3),
        ("imi02", "imi02/set-numeration/04.num", 4),
    ],
)
def test_differential_candidates_t0_all_pairs_match_perl_for_imi01_imi02(
    grammar_id: str, numeration_relpath: str, grammar_no: int
) -> None:
    state = _state(grammar_id=grammar_id, numeration_relpath=numeration_relpath)
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            assert _py_candidates(state, left, right) == _perl_candidates(
                state, left, right, grammar_no=grammar_no
            )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("left,right", [(1, 2), (2, 1), (5, 6), (6, 5), (3, 4)])
def test_differential_candidates_japanese2_match_perl(left: int, right: int) -> None:
    state = _state(grammar_id="japanese2", numeration_relpath="japanese2/set-numeration/00-00-01.num")
    assert _py_candidates(state, left, right) == _perl_candidates(
        state, left, right, grammar_no=1
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "left", "right"),
    [
        ("japanese2/set-numeration/03-01-29.num", 7, 8),
        ("japanese2/set-numeration/03-05-831.num", 7, 8),
        ("japanese2/set-numeration/03-05-831.num", 7, 9),
        ("japanese2/set-numeration/03-05-832.num", 7, 8),
        ("japanese2/set-numeration/03-05-832.num", 7, 9),
        ("japanese2/set-numeration/03-05-831.num", 9, 8),
    ],
)
def test_differential_candidates_japanese2_special_rules_match_perl(
    numeration_relpath: str, left: int, right: int
) -> None:
    state = _state(grammar_id="japanese2", numeration_relpath=numeration_relpath)
    allowed = {"sase1", "sase2", "rare1", "rare2", "RH-Merge", "zero-Merge"}
    assert _py_candidates(
        state, left, right, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        left,
        right,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("left", "right"),
    [
        (8, 9),
        (8, 10),
        (9, 8),
        (10, 8),
        (10, 9),
        (10, 1),
        (10, 3),
        (10, 5),
    ],
)
def test_differential_candidates_japanese2_property_rel_match_perl(
    left: int, right: int
) -> None:
    state = _state(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/03-05-831.num",
    )
    allowed = {"property-Merge", "rel-Merge", "RH-Merge", "zero-Merge"}
    assert _py_candidates(
        state, left, right, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        left,
        right,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "left", "right", "allowed"),
    [
        (
            "japanese2/set-numeration/05-03-09.num",
            1,
            4,
            {"property-da", "RH-Merge", "zero-Merge"},
        ),
        (
            "japanese2/set-numeration/05-04-28b.num",
            3,
            4,
            {"property-da", "RH-Merge", "zero-Merge"},
        ),
        (
            "japanese2/set-numeration/08-05-45.num",
            1,
            5,
            {"P-Merge", "RH-Merge", "zero-Merge"},
        ),
        (
            "japanese2/set-numeration/08-05-45.num",
            3,
            5,
            {"P-Merge", "RH-Merge", "zero-Merge"},
        ),
    ],
)
def test_differential_candidates_japanese2_property_da_pmerge_match_perl(
    numeration_relpath: str,
    left: int,
    right: int,
    allowed: set[str],
) -> None:
    state = _state(grammar_id="japanese2", numeration_relpath=numeration_relpath)
    assert _py_candidates(
        state, left, right, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        left,
        right,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_candidates_japanese2_property_no_synthetic_match_perl() -> None:
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state.base[1][4] = "x1-1"
    state.base[2][3] = ["1,1,N", "2,3,N"]

    allowed = {"property-no", "J-Merge", "RH-Merge"}
    assert _py_candidates(
        state, 1, 2, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        1,
        2,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_candidates_japanese2_partitioning_match_perl() -> None:
    state = _state(grammar_id="japanese2", numeration_relpath="japanese2/set-numeration/08-05-45.num")
    allowed = {"P-Merge", "RH-Merge", "zero-Merge", "Partitioning"}
    assert _py_candidates(
        state, 1, 5, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        1,
        5,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_candidates_japanese2_pickup_synthetic_match_perl() -> None:
    state = _synthetic_pickup_state()
    allowed = {"Pickup"}
    assert _py_candidates(
        state, 1, 2, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        1,
        2,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_candidates_japanese2_landing_synthetic_match_perl() -> None:
    state = _synthetic_landing_state()
    allowed = {"Landing"}
    assert _py_candidates(
        state, 1, 2, allowed_rule_names=allowed
    ) == _perl_candidates(
        state,
        1,
        2,
        grammar_no=1,
        allowed_rule_names=allowed,
    )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    "state_factory",
    [
        _state_japanese2_080115_rh,
        _state_japanese2_property_da,
        _state_japanese2_zero_merge,
        _state_japanese2_partitioning,
        _state_japanese2_pickup,
        _state_japanese2_landing,
    ],
)
def test_differential_candidates_japanese2_derived_states_match_perl(state_factory) -> None:
    state = state_factory()
    allowed = {
        rule.name
        for rule in load_rule_catalog(grammar_id="japanese2", legacy_root=_legacy_root())
    }
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            assert _py_candidates(
                state, left, right, allowed_rule_names=allowed
            ) == _perl_candidates(
                state,
                left,
                right,
                grammar_no=1,
                allowed_rule_names=allowed,
            )


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_candidates_imi03_multistep_states_match_perl() -> None:
    state = _state_t0()
    allowed = {rule.name for rule in load_rule_catalog(grammar_id="imi03", legacy_root=_legacy_root())}
    queue: deque[tuple[DerivationState, int]] = deque([(state, 0)])
    visited = {_state_key(state)}
    max_depth = 2
    max_states = 20
    max_checks = 220
    checked = 0

    while queue and len(visited) < max_states and checked < max_checks:
        current, depth = queue.popleft()
        for left in range(1, current.basenum + 1):
            for right in range(1, current.basenum + 1):
                if left == right:
                    continue
                assert _py_candidates(
                    current, left, right, allowed_rule_names=allowed
                ) == _perl_candidates(
                    current, left, right, grammar_no=5, allowed_rule_names=allowed
                )
                checked += 1
                if checked >= max_checks:
                    break
            if checked >= max_checks:
                break

        if depth >= max_depth or checked >= max_checks:
            continue

        for left in range(1, current.basenum + 1):
            for right in range(1, current.basenum + 1):
                if left == right:
                    continue
                candidates = list_merge_candidates(
                    state=current,
                    left=left,
                    right=right,
                    legacy_root=_legacy_root(),
                )
                for candidate in candidates:
                    if candidate.rule_kind == "single":
                        next_state = execute_single_merge(
                            state=current,
                            rule_name=candidate.rule_name,
                            check=candidate.check,
                        )
                    else:
                        next_state = execute_double_merge(
                            state=current,
                            rule_name=candidate.rule_name,
                            left=candidate.left,
                            right=candidate.right,
                        )
                    key = _state_key(next_state)
                    if key not in visited and len(visited) < max_states:
                        visited.add(key)
                        queue.append((next_state, depth + 1))

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "max_states", "max_checks"),
    [
        ("japanese2/set-numeration/03-05-831.num", 14, 180),
        ("japanese2/set-numeration/08-05-45.num", 14, 180),
    ],
)
def test_differential_candidates_japanese2_multistep_states_match_perl(
    numeration_relpath: str, max_states: int, max_checks: int
) -> None:
    state = _state(grammar_id="japanese2", numeration_relpath=numeration_relpath)
    allowed = {
        rule.name for rule in load_rule_catalog(grammar_id="japanese2", legacy_root=_legacy_root())
    }
    queue: deque[tuple[DerivationState, int]] = deque([(state, 0)])
    visited = {_state_key(state)}
    max_depth = 2
    checked = 0

    while queue and len(visited) < max_states and checked < max_checks:
        current, depth = queue.popleft()
        for left in range(1, current.basenum + 1):
            for right in range(1, current.basenum + 1):
                if left == right:
                    continue
                assert _py_candidates(
                    current, left, right, allowed_rule_names=allowed
                ) == _perl_candidates(
                    current, left, right, grammar_no=1, allowed_rule_names=allowed
                )
                checked += 1
                if checked >= max_checks:
                    break
            if checked >= max_checks:
                break

        if depth >= max_depth or checked >= max_checks:
            continue

        for left in range(1, current.basenum + 1):
            for right in range(1, current.basenum + 1):
                if left == right:
                    continue
                candidates = list_merge_candidates(
                    state=current,
                    left=left,
                    right=right,
                    legacy_root=_legacy_root(),
                )
                for candidate in candidates:
                    if candidate.rule_kind == "single":
                        next_state = execute_single_merge(
                            state=current,
                            rule_name=candidate.rule_name,
                            check=candidate.check,
                        )
                    else:
                        next_state = execute_double_merge(
                            state=current,
                            rule_name=candidate.rule_name,
                            left=candidate.left,
                            right=candidate.right,
                            rule_version="01",
                        )
                    key = _state_key(next_state)
                    if key not in visited and len(visited) < max_states:
                        visited.add(key)
                        queue.append((next_state, depth + 1))

    assert checked > 0
