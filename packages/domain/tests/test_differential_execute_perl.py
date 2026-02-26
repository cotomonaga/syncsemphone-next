import copy
import html
import json
import os
import re
import shutil
import subprocess
import urllib.parse
from collections import deque
from pathlib import Path
from typing import Any, Optional

import pytest

from domain.common.types import DerivationState
from domain.derivation.candidates import list_merge_candidates
from domain.derivation.execute import execute_double_merge, execute_single_merge
from domain.grammar.rule_catalog import get_rule_number_by_name
from domain.numeration.init_builder import build_initial_derivation_state


_PERL_GRAMMAR_NO = {
    "japanese2": 1,
    "imi01": 3,
    "imi02": 4,
    "imi03": 5,
}


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _state_from_numeration(grammar_id: str, numeration_relpath: str):
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


def _state_t0():
    return _state_from_numeration(
        grammar_id="imi03",
        numeration_relpath="imi03/set-numeration/04.num",
    )


def _to_perl_item(item: Any) -> Any:
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


def _to_perl_base(base: list[Any]) -> list[Any]:
    return [None] + [_to_perl_item(item) for item in base[1:]]


def _normalize_item_from_perl(item: Any) -> Any:
    if not isinstance(item, list):
        return item
    out = copy.deepcopy(item)

    if len(out) > 2 and isinstance(out[2], list):
        if len(out[2]) > 0 and out[2][0] is None:
            out[2] = out[2][1:]
        cleaned_pr = []
        for row in out[2]:
            if isinstance(row, list):
                if len(row) != 3:
                    continue
                if all(value in ("", None) for value in row):
                    continue
                cleaned_pr.append(row)
            elif row not in ("", None):
                cleaned_pr.append(row)
        out[2] = cleaned_pr
    if len(out) > 3 and isinstance(out[3], list):
        if len(out[3]) > 0 and out[3][0] is None:
            out[3] = out[3][1:]
        out[3] = [value for value in out[3] if value not in ("", None)]
    if len(out) > 5 and isinstance(out[5], list):
        if len(out[5]) > 0 and out[5][0] is None:
            out[5] = out[5][1:]
        out[5] = [value for value in out[5] if value not in ("", None)]
    if len(out) > 7 and isinstance(out[7], list):
        converted = []
        for child in out[7]:
            if child == "zero":
                converted.append(child)
            else:
                converted.append(_normalize_item_from_perl(child))
        out[7] = converted
    while isinstance(out, list) and len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _normalize_base_from_perl(base: list[Any]) -> list[Any]:
    return [None] + [_normalize_item_from_perl(item) for item in base[1:]]


def _perl_execute(
    state,
    rule_name: str,
    left: Optional[int],
    right: Optional[int],
    grammar_no: int,
    check: Optional[int] = None,
) -> dict[str, Any]:
    rule_no = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name=rule_name,
        legacy_root=_legacy_root(),
    )
    if rule_no is None:
        raise AssertionError(
            f"rule not found in grammar catalog: {state.grammar_id}/{rule_name}"
        )
    params = {
        "grammar": str(grammar_no),
        "mode": "execute",
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(_to_perl_base(state.base), ensure_ascii=False),
        "choice": "0",
        "rule0": str(rule_no),
    }
    if left is not None:
        params["left0"] = str(left)
    if right is not None:
        params["right0"] = str(right)
    if check is not None:
        params["check0"] = str(check)
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

    html_text = proc.stdout.decode("utf-8", errors="ignore")
    base_values = re.findall(r'name="base" value="([^"]*)"', html_text)
    basenum_values = re.findall(r'name="basenum" value=([^>\\s]+)', html_text)
    newnum_values = re.findall(r'name="newnum" value=([^>\\s]+)', html_text)
    history_values = re.findall(r'name="history" value="([^"]*)"', html_text)
    if not base_values:
        raise AssertionError("failed to parse perl execute hidden base")

    base_json = html.unescape(base_values[-1])
    base = _normalize_base_from_perl(json.loads(base_json))
    return {
        "base": base,
        "basenum": int(basenum_values[-1]),
        "newnum": int(newnum_values[-1]),
        "history": history_values[-1],
    }


def _find_item(base: list[Any], lexical_id: str) -> list[Any]:
    for item in base[1:]:
        if item and item[0] == lexical_id:
            return item
    raise AssertionError(f"item not found: {lexical_id}")


def _normalize_python_item(item: Any) -> Any:
    if not isinstance(item, list):
        return item
    out = copy.deepcopy(item)
    if len(out) > 2 and isinstance(out[2], list):
        cleaned_pr = []
        for row in out[2]:
            if isinstance(row, list):
                if len(row) != 3:
                    continue
                if all(value in ("", None) for value in row):
                    continue
                cleaned_pr.append(row)
            elif row not in ("", None):
                cleaned_pr.append(row)
        out[2] = cleaned_pr
    if len(out) > 3 and isinstance(out[3], list):
        out[3] = [value for value in out[3] if value not in ("", None)]
    if len(out) > 5 and isinstance(out[5], list):
        out[5] = [value for value in out[5] if value not in ("", None)]
    if len(out) > 7 and isinstance(out[7], list):
        converted = []
        for child in out[7]:
            if child == "zero":
                converted.append(child)
            else:
                converted.append(_normalize_python_item(child))
        out[7] = converted
    while isinstance(out, list) and len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _normalize_python_base(base: list[Any]) -> list[Any]:
    return [None] + [_normalize_python_item(item) for item in base[1:]]


def _state_key(state) -> str:
    normalized = _normalize_python_base(state.base)
    payload = {
        "memo": state.memo,
        "newnum": state.newnum,
        "basenum": state.basenum,
        "history": state.history,
        "base": normalized,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _execute_candidate_and_assert_match(state, candidate, grammar_no: int) -> Any:
    if candidate.rule_kind == "single":
        py_state = execute_single_merge(
            state=state,
            rule_name=candidate.rule_name,
            check=candidate.check,
        )
        perl_state = _perl_execute(
            state=state,
            rule_name=candidate.rule_name,
            left=None,
            right=None,
            check=candidate.check,
            grammar_no=grammar_no,
        )
    else:
        py_state = execute_double_merge(
            state=state,
            rule_name=candidate.rule_name,
            left=candidate.left,
            right=candidate.right,
            rule_version="01" if state.grammar_id == "japanese2" else "03",
        )
        perl_state = _perl_execute(
            state=state,
            rule_name=candidate.rule_name,
            left=candidate.left,
            right=candidate.right,
            grammar_no=grammar_no,
        )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]
    return py_state


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_lhmerge_v_plus_wo_matches_perl_core_fields() -> None:
    state = _state_t0()
    py_state = execute_double_merge(state=state, rule_name="LH-Merge", left=5, right=4)
    perl_state = _perl_execute(
        state=state, rule_name="LH-Merge", left=5, right=4, grammar_no=5
    )

    py_item = _find_item(py_state.base, "x5-1")
    perl_item = _find_item(perl_state["base"], "x5-1")

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert py_item[3] == perl_item[3]  # sy
    assert py_item[4] == perl_item[4]  # sl
    assert py_item[5] == perl_item[5]  # se


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_lhmerge_v_plus_t_matches_perl_core_fields() -> None:
    state = _state_t0()
    py_state = execute_double_merge(state=state, rule_name="LH-Merge", left=5, right=6)
    perl_state = _perl_execute(
        state=state, rule_name="LH-Merge", left=5, right=6, grammar_no=5
    )

    py_item = _find_item(py_state.base, "x5-1")
    perl_item = _find_item(perl_state["base"], "x5-1")

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert py_item[3] == perl_item[3]  # sy
    assert py_item[4] == perl_item[4]  # sl
    assert py_item[5] == perl_item[5]  # se


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_rhmerge_n_plus_ga_matches_perl_core_fields() -> None:
    state = _state_t0()
    py_state = execute_double_merge(state=state, rule_name="RH-Merge", left=1, right=2)
    perl_state = _perl_execute(
        state=state, rule_name="RH-Merge", left=1, right=2, grammar_no=5
    )

    py_item = _find_item(py_state.base, "x2-1")
    perl_item = _find_item(perl_state["base"], "x2-1")

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert py_item[3] == perl_item[3]  # sy
    assert py_item[4] == perl_item[4]  # sl
    assert py_item[5] == perl_item[5]  # se


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("rule_name", "left", "right"),
    [
        ("LH-Merge", 5, 6),
        ("LH-Merge", 5, 4),
        ("RH-Merge", 1, 2),
        ("RH-Merge", 3, 4),
    ],
)
def test_differential_execute_state_snapshot_matches_perl(
    rule_name: str, left: int, right: int
) -> None:
    state = _state_t0()
    py_state = execute_double_merge(state=state, rule_name=rule_name, left=left, right=right)
    perl_state = _perl_execute(
        state=state, rule_name=rule_name, left=left, right=right, grammar_no=5
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("grammar_id", "numeration_relpath"),
    [
        ("imi01", "imi01/set-numeration/04.num"),
        ("imi02", "imi02/set-numeration/04.num"),
    ],
)
def test_differential_execute_t0_all_pairs_match_perl_for_imi01_imi02(
    grammar_id: str, numeration_relpath: str
) -> None:
    state = _state_from_numeration(
        grammar_id=grammar_id,
        numeration_relpath=numeration_relpath,
    )
    grammar_no = _PERL_GRAMMAR_NO[grammar_id]

    for rule_name in ("RH-Merge", "LH-Merge"):
        for left in range(1, state.basenum + 1):
            for right in range(1, state.basenum + 1):
                if left == right:
                    continue
                py_state = execute_double_merge(
                    state=state,
                    rule_name=rule_name,
                    left=left,
                    right=right,
                )
                perl_state = _perl_execute(
                    state=state,
                    rule_name=rule_name,
                    left=left,
                    right=right,
                    grammar_no=grammar_no,
                )
                assert py_state.basenum == perl_state["basenum"]
                assert py_state.newnum == perl_state["newnum"]
                assert py_state.history == perl_state["history"]
                assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("grammar_id", "numeration_relpath", "grammar_no"),
    [
        ("imi01", "imi01/set-numeration/04.num", 3),
        ("imi02", "imi02/set-numeration/04.num", 4),
    ],
)
def test_differential_execute_multistep_states_match_perl_for_imi01_imi02(
    grammar_id: str, numeration_relpath: str, grammar_no: int
) -> None:
    root = _legacy_root()
    initial = _state_from_numeration(
        grammar_id=grammar_id,
        numeration_relpath=numeration_relpath,
    )

    max_depth = 2
    max_states = 40
    max_checks = 500

    queue: deque[tuple[Any, int]] = deque([(initial, 0)])
    visited: set[str] = {_state_key(initial)}
    checked = 0

    while queue and len(visited) < max_states and checked < max_checks:
        state, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for left in range(1, state.basenum + 1):
            for right in range(1, state.basenum + 1):
                if left == right:
                    continue

                candidates = list_merge_candidates(
                    state=state,
                    left=left,
                    right=right,
                    legacy_root=root,
                )
                for candidate in candidates:
                    py_state = _execute_candidate_and_assert_match(
                        state=state,
                        candidate=candidate,
                        grammar_no=grammar_no,
                    )

                    checked += 1
                    key = _state_key(py_state)
                    if key not in visited and len(visited) < max_states:
                        visited.add(key)
                        queue.append((py_state, depth + 1))
                    if checked >= max_checks:
                        break
                if checked >= max_checks:
                    break
            if checked >= max_checks:
                break

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_imi03_multistep_states_match_perl() -> None:
    root = _legacy_root()
    initial = _state_t0()

    max_depth = 2
    max_states = 60
    max_checks = 900

    queue: deque[tuple[Any, int]] = deque([(initial, 0)])
    visited: set[str] = {_state_key(initial)}
    checked = 0
    states = 0

    while queue and states < max_states and checked < max_checks:
        state, depth = queue.popleft()
        states += 1
        if depth >= max_depth:
            continue

        for left in range(1, state.basenum + 1):
            for right in range(1, state.basenum + 1):
                if left == right:
                    continue

                candidates = list_merge_candidates(
                    state=state,
                    left=left,
                    right=right,
                    legacy_root=root,
                )
                for candidate in candidates:
                    py_state = _execute_candidate_and_assert_match(
                        state=state,
                        candidate=candidate,
                        grammar_no=_PERL_GRAMMAR_NO["imi03"],
                    )

                    checked += 1

                    key = _state_key(py_state)
                    if key not in visited and len(visited) < max_states:
                        visited.add(key)
                        queue.append((py_state, depth + 1))
                    if checked >= max_checks:
                        break
                if checked >= max_checks:
                    break
            if checked >= max_checks:
                break

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    "numeration_relpath",
    [
        "imi03/set-numeration/00.num",
        "imi03/set-numeration/04.num",
        "imi03/set-numeration/1606324760.num",
        "imi03/set-numeration/1608131495.num",
        "imi03/set-numeration/old/01.num",
        "imi03/set-numeration/old/02.num",
    ],
)
def test_differential_execute_imi03_t0_all_candidates_match_perl(
    numeration_relpath: str,
) -> None:
    state = _state_from_numeration(
        grammar_id="imi03",
        numeration_relpath=numeration_relpath,
    )
    checked = 0
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            candidates = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=_legacy_root(),
            )
            for candidate in candidates:
                _execute_candidate_and_assert_match(
                    state=state,
                    candidate=candidate,
                    grammar_no=_PERL_GRAMMAR_NO["imi03"],
                )
                checked += 1

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "max_states", "max_checks"),
    [
        ("japanese2/set-numeration/00-00-01.num", 22, 320),
        ("japanese2/set-numeration/03-05-831.num", 28, 420),
        ("japanese2/set-numeration/08-05-45.num", 22, 320),
    ],
)
def test_differential_execute_japanese2_multistep_states_match_perl(
    numeration_relpath: str,
    max_states: int,
    max_checks: int,
) -> None:
    root = _legacy_root()
    initial = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath=numeration_relpath,
    )

    max_depth = 2

    queue: deque[tuple[Any, int]] = deque([(initial, 0)])
    visited: set[str] = {_state_key(initial)}
    checked = 0

    while queue and len(visited) < max_states and checked < max_checks:
        state, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for left in range(1, state.basenum + 1):
            for right in range(1, state.basenum + 1):
                if left == right:
                    continue

                candidates = list_merge_candidates(
                    state=state,
                    left=left,
                    right=right,
                    legacy_root=root,
                )
                for candidate in candidates:
                    py_state = _execute_candidate_and_assert_match(
                        state=state,
                        candidate=candidate,
                        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
                    )

                    checked += 1

                    key = _state_key(py_state)
                    if key not in visited and len(visited) < max_states:
                        visited.add(key)
                        queue.append((py_state, depth + 1))
                    if checked >= max_checks:
                        break
                if checked >= max_checks:
                    break
            if checked >= max_checks:
                break

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_rhmerge_candidate_pairs_match_perl() -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/00-00-01.num",
    )
    checked = 0
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            candidates = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=_legacy_root(),
            )
            if not any(candidate.rule_name == "RH-Merge" for candidate in candidates):
                continue

            py_state = execute_double_merge(
                state=state,
                rule_name="RH-Merge",
                left=left,
                right=right,
                rule_version="01",
            )
            perl_state = _perl_execute(
                state=state,
                rule_name="RH-Merge",
                left=left,
                right=right,
                grammar_no=_PERL_GRAMMAR_NO["japanese2"],
            )

            assert py_state.basenum == perl_state["basenum"]
            assert py_state.newnum == perl_state["newnum"]
            assert py_state.history == perl_state["history"]
            assert _normalize_python_base(py_state.base) == perl_state["base"]
            checked += 1

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(("left", "right"), [(3, 7), (7, 1), (7, 3)])
def test_differential_execute_japanese2_rhmerge_kind_feature_101_match_perl(
    left: int, right: int
) -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/08-01-15.num",
    )
    py_state = execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=left,
        right=right,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="RH-Merge",
        left=left,
        right=right,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_080115_all_candidates_match_perl() -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/08-01-15.num",
    )
    checked = 0
    for left in range(1, state.basenum + 1):
        for right in range(1, state.basenum + 1):
            if left == right:
                continue
            candidates = list_merge_candidates(
                state=state,
                left=left,
                right=right,
                legacy_root=_legacy_root(),
            )
            for candidate in candidates:
                if candidate.rule_kind == "single":
                    py_state = execute_single_merge(
                        state=state,
                        rule_name=candidate.rule_name,
                        check=candidate.check,
                    )
                    perl_state = _perl_execute(
                        state=state,
                        rule_name=candidate.rule_name,
                        left=None,
                        right=None,
                        check=candidate.check,
                        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
                    )
                else:
                    py_state = execute_double_merge(
                        state=state,
                        rule_name=candidate.rule_name,
                        left=candidate.left,
                        right=candidate.right,
                        rule_version="01",
                    )
                    perl_state = _perl_execute(
                        state=state,
                        rule_name=candidate.rule_name,
                        left=candidate.left,
                        right=candidate.right,
                        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
                    )

                assert py_state.basenum == perl_state["basenum"]
                assert py_state.newnum == perl_state["newnum"]
                assert py_state.history == perl_state["history"]
                assert _normalize_python_base(py_state.base) == perl_state["base"]
                checked += 1

    assert checked > 0


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(("left", "right"), [(1, 2), (3, 4)])
def test_differential_execute_japanese2_jmerge_pairs_match_perl(
    left: int, right: int
) -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/00-00-01.num",
    )
    py_state = execute_double_merge(
        state=state,
        rule_name="J-Merge",
        left=left,
        right=right,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="J-Merge",
        left=left,
        right=right,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "rule_name", "left", "right"),
    [
        ("japanese2/set-numeration/03-01-29.num", "sase1", 7, 8),
        ("japanese2/set-numeration/03-05-831.num", "sase1", 7, 8),
        ("japanese2/set-numeration/03-05-831.num", "sase2", 9, 8),
        ("japanese2/set-numeration/03-05-831.num", "rare1", 7, 9),
        ("japanese2/set-numeration/03-05-831.num", "rare1", 8, 9),
        ("japanese2/set-numeration/03-05-832.num", "sase1", 7, 8),
        ("japanese2/set-numeration/03-05-832.num", "rare2", 7, 9),
    ],
)
def test_differential_execute_japanese2_special_rules_match_perl(
    numeration_relpath: str, rule_name: str, left: int, right: int
) -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath=numeration_relpath,
    )
    py_state = execute_double_merge(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("rule_name", "left", "right"),
    [
        ("property-Merge", 8, 9),
        ("property-Merge", 8, 10),
        ("property-Merge", 9, 8),
        ("property-Merge", 10, 8),
        ("property-Merge", 10, 9),
        ("rel-Merge", 10, 1),
        ("rel-Merge", 10, 3),
        ("rel-Merge", 10, 5),
    ],
)
def test_differential_execute_japanese2_property_rel_match_perl(
    rule_name: str, left: int, right: int
) -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/03-05-831.num",
    )
    py_state = execute_double_merge(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_se_feature_70_matches_perl() -> None:
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state.base[1][3] = ["sync-anchor"]
    state.base[2][3] = ["marker70"]
    state.base[2][5] = ["Role:2,70,marker70"]

    py_state = execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_se_feature_71_matches_perl() -> None:
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state.base[1][3] = ["sync-anchor"]
    state.base[2][3] = ["3,53,marker71,x9-1"]
    state.base[2][5] = ["Role:2,71,marker71"]
    state.base[1][5] = ["Fallback:x1-1"]

    py_state = execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_nonhead_se_feature_27_bug_compat_matches_perl() -> None:
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    # RH-Merge: right(2)=head, left(1)=non-head
    state.base[1][3] = ["sync-anchor"]
    state.base[1][2] = [["nh-a", "nh-b", "nh-c"]]
    state.base[1][5] = ["Role:2,27,m27"]
    state.base[2][3] = ["3,53,m27,x9-1"]
    state.base[2][2] = [["h-a", "h-b", "h-c"]]

    py_state = execute_double_merge(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="RH-Merge",
        left=1,
        right=2,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]

    # Perl互換: non-head側 se27 解決時に daughter の pr[0] に4番目の要素が追記される。
    nonhead_daughter = py_state.base[1][7][0]
    assert nonhead_daughter[2][0][3] == "x9-1"


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    ("numeration_relpath", "rule_name", "left", "right"),
    [
        ("japanese2/set-numeration/05-03-09.num", "property-da", 1, 4),
        ("japanese2/set-numeration/05-04-28b.num", "property-da", 3, 4),
        ("japanese2/set-numeration/08-05-45.num", "P-Merge", 1, 5),
        ("japanese2/set-numeration/08-05-45.num", "P-Merge", 3, 5),
    ],
)
def test_differential_execute_japanese2_property_da_pmerge_match_perl(
    numeration_relpath: str, rule_name: str, left: int, right: int
) -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath=numeration_relpath,
    )
    py_state = execute_double_merge(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name=rule_name,
        left=left,
        right=right,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_property_no_synthetic_match_perl() -> None:
    state = build_initial_derivation_state(
        grammar_id="japanese2",
        numeration_text="synthetic\t60\t19\n\t\t\n\t1\t2",
        legacy_root=_legacy_root(),
    )
    state.base[1][4] = "x1-1"
    state.base[2][3] = ["1,1,N", "2,3,N"]

    py_state = execute_double_merge(
        state=state,
        rule_name="property-no",
        left=1,
        right=2,
        rule_version="01",
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="property-no",
        left=1,
        right=2,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_partitioning_match_perl() -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/08-05-45.num",
    )
    py_state = execute_single_merge(
        state=state,
        rule_name="Partitioning",
        check=5,
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="Partitioning",
        left=None,
        right=None,
        check=5,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_zero_merge_match_perl() -> None:
    state = _state_from_numeration(
        grammar_id="japanese2",
        numeration_relpath="japanese2/set-numeration/05-03-09.num",
    )
    py_state = execute_single_merge(
        state=state,
        rule_name="zero-Merge",
        check=4,
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="zero-Merge",
        left=None,
        right=None,
        check=4,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_pickup_match_perl() -> None:
    state = _synthetic_pickup_state()
    py_state = execute_single_merge(
        state=state,
        rule_name="Pickup",
        check=1,
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="Pickup",
        left=None,
        right=None,
        check=1,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_execute_japanese2_landing_match_perl() -> None:
    state = _synthetic_landing_state()
    py_state = execute_single_merge(
        state=state,
        rule_name="Landing",
        check=1,
    )
    perl_state = _perl_execute(
        state=state,
        rule_name="Landing",
        left=None,
        right=None,
        check=1,
        grammar_no=_PERL_GRAMMAR_NO["japanese2"],
    )

    assert py_state.basenum == perl_state["basenum"]
    assert py_state.newnum == perl_state["newnum"]
    assert py_state.history == perl_state["history"]
    assert _normalize_python_base(py_state.base) == perl_state["base"]
