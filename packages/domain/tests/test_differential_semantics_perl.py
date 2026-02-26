import copy
import html
import json
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

import pytest

from domain.common.types import DerivationState
from domain.derivation.execute import execute_double_merge
from domain.numeration.init_builder import build_initial_derivation_state
from domain.semantics.lf_sr import build_sr_layers


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
    from domain.derivation.execute import execute_single_merge

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


def _state_japanese2_beta_synthetic() -> DerivationState:
    return DerivationState(
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


def _state_japanese2_beta_multi_synthetic() -> DerivationState:
    return DerivationState(
        grammar_id="japanese2",
        memo="beta-multi-synth",
        newnum=9,
        basenum=5,
        history="",
        base=[
            None,
            [
                "x2-1",
                "V",
                [],
                [],
                "x2-1",
                ["Agent:x4-1", "Theme:x8-1"],
                "",
                "",
            ],
            [
                "x5-1",
                "N",
                [],
                ["beta#5#Agent(x2-1)"],
                "β5",
                ["Kind:betaA"],
                "",
                "",
            ],
            [
                "x6-1",
                "N",
                [],
                ["beta#6#Theme(x2-1)"],
                "β6",
                ["Kind:betaB"],
                "",
                "",
            ],
            ["x4-1", "N", [], [], "x4-1", ["Name:targetA"], "", ""],
            ["x8-1", "N", [], [], "x8-1", ["Name:targetB"], "", ""],
        ],
    )


def _saved_derivation_filenames() -> list[str]:
    folder = _legacy_root() / "japanese2/derivation"
    return sorted(path.name for path in folder.glob("*.txt"))


def _load_saved_derivation_state(filename: str) -> DerivationState:
    path = _legacy_root() / "japanese2/derivation" / filename
    raw = path.read_bytes()
    text: str | None = None
    for encoding in ("cp932", "utf-8"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError(f"Unable to decode saved derivation file: {filename}")

    lines = text.splitlines()
    if len(lines) < 6:
        raise ValueError(f"Invalid saved derivation line count: {filename}")
    try:
        newnum = int(lines[2].strip())
        basenum = int(lines[3].strip())
    except ValueError as exc:
        raise ValueError(f"Invalid saved derivation integer fields: {filename}") from exc
    try:
        base = json.loads(lines[5])
    except json.JSONDecodeError as exc:
        # 一部の legacy 保存データには、cp932 由来の文字列で
        # JSON 的に不正なバックスラッシュ（例: \3）が混入している。
        # Perl 側はそのまま扱っているため、比較テストでは最小限の補正で読む。
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", lines[5])
        try:
            base = json.loads(fixed)
        except json.JSONDecodeError as exc2:
            raise ValueError(f"Invalid saved derivation base JSON: {filename}") from exc2

    return DerivationState(
        grammar_id="japanese2",
        memo=lines[1],
        newnum=newnum,
        basenum=basenum,
        history=lines[4],
        base=base,
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


def _perl_lf_sr_rows(state) -> list[tuple[int, int, str, tuple[str, ...]]]:
    grammar_no = 5 if state.grammar_id == "imi03" else 1
    params = {
        "grammar": str(grammar_no),
        "mode": "lf",
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(_to_perl_base(state.base), ensure_ascii=False),
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

    html_text = proc.stdout.decode("utf-8", errors="ignore")
    match = re.search(r'name="sr" value="([^"]*)"', html_text)
    if not match:
        raise AssertionError("lf output does not contain hidden sr payload")
    sr_raw = json.loads(html.unescape(match.group(1)))

    rows: list[tuple[int, int, str, tuple[str, ...]]] = []
    for obj in range(1, len(sr_raw)):
        entry = sr_raw[obj]
        if not isinstance(entry, list):
            continue
        kind = "Predication" if len(entry) > 0 and entry[0] == "Predication" else "object"
        for layer in range(1, len(entry)):
            props = entry[layer]
            if not isinstance(props, list):
                continue
            filtered = tuple(value for value in props if value not in ("", None))
            if filtered:
                rows.append((obj, layer, kind, filtered))
    return rows


def _perl_final_sr_rows(state) -> list[tuple[int, int, str, tuple[str, ...]]]:
    grammar_no = 5 if state.grammar_id == "imi03" else 1
    lf_params = {
        "grammar": str(grammar_no),
        "mode": "lf",
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(_to_perl_base(state.base), ensure_ascii=False),
    }
    lf_payload = urllib.parse.urlencode(lf_params)
    env = os.environ.copy()
    env["REQUEST_METHOD"] = "POST"
    env["CONTENT_LENGTH"] = str(len(lf_payload.encode("utf-8")))
    lf_proc = subprocess.run(
        ["perl", "-I.", "syncsemphone.cgi"],
        input=lf_payload.encode("utf-8"),
        cwd=str(_legacy_root()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if lf_proc.returncode != 0:
        raise AssertionError(lf_proc.stderr.decode("utf-8", errors="ignore"))
    lf_html = lf_proc.stdout.decode("utf-8", errors="ignore")
    hidden_match = re.search(r'name="sr" value="([^"]*)"', lf_html)
    if not hidden_match:
        raise AssertionError("lf output does not contain hidden sr payload")
    hidden_sr = html.unescape(hidden_match.group(1))

    sr_params = {
        "grammar": str(grammar_no),
        "mode": "sr",
        "sr": hidden_sr,
        "memo": state.memo,
        "newnum": str(state.newnum),
        "basenum": str(state.basenum),
        "history": state.history,
        "base": json.dumps(_to_perl_base(state.base), ensure_ascii=False),
    }
    sr_payload = urllib.parse.urlencode(sr_params)
    env["CONTENT_LENGTH"] = str(len(sr_payload.encode("utf-8")))
    sr_proc = subprocess.run(
        ["perl", "-I.", "syncsemphone.cgi"],
        input=sr_payload.encode("utf-8"),
        cwd=str(_legacy_root()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if sr_proc.returncode != 0:
        raise AssertionError(sr_proc.stderr.decode("utf-8", errors="ignore"))
    sr_html = sr_proc.stdout.decode("utf-8", errors="ignore")

    rows: list[tuple[int, int, str, tuple[str, ...]]] = []
    object_pattern = re.compile(
        r'<p><span class=(?P<kind>object|Predication)>x(?P<object>\d+)</span>\s*\[(?P<body>.*?)\]<br>',
        re.S,
    )
    layer_pattern = re.compile(
        r'\(<span class="layer">x\d+-(?P<layer>\d+)</span>(?P<props>.*?)\)',
        re.S,
    )
    prop_pattern = re.compile(r'<<span class="f\d+">(.*?)</span>>', re.S)

    for obj_match in object_pattern.finditer(sr_html):
        kind = (
            "Predication"
            if obj_match.group("kind") == "Predication"
            else "object"
        )
        object_id = int(obj_match.group("object"))
        body = obj_match.group("body")
        for layer_match in layer_pattern.finditer(body):
            layer = int(layer_match.group("layer"))
            props_raw = prop_pattern.findall(layer_match.group("props"))
            props = tuple(
                html.unescape(value).strip()
                for value in props_raw
                if html.unescape(value).strip() != ""
            )
            if props:
                rows.append((object_id, layer, kind, props))
    return rows


def _py_sr_rows(state) -> list[tuple[int, int, str, tuple[str, ...]]]:
    rows: list[tuple[int, int, str, tuple[str, ...]]] = []
    for row in build_sr_layers(state):
        rows.append((row.object_id, row.layer, row.kind, tuple(row.properties)))
    return rows


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize(
    "state_factory",
    [
        _state_t0,
        _state_t1,
        _state_t2,
        _state_japanese2_080115_rh,
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
    ],
)
def test_differential_semantics_sr_matches_perl_lf_payload(state_factory) -> None:
    state = state_factory()
    perl_rows = sorted(_perl_lf_sr_rows(state))
    py_rows = sorted(_py_sr_rows(state))
    assert py_rows == perl_rows


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_semantics_sr_beta_synthetic_matches_perl_final_sr() -> None:
    state = _state_japanese2_beta_synthetic()
    perl_rows = sorted(_perl_final_sr_rows(state))
    py_rows = sorted(_py_sr_rows(state))
    assert py_rows == perl_rows


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_differential_semantics_sr_beta_multi_synthetic_matches_perl_final_sr() -> None:
    state = _state_japanese2_beta_multi_synthetic()
    perl_rows = sorted(_perl_final_sr_rows(state))
    py_rows = sorted(_py_sr_rows(state))
    assert py_rows == perl_rows


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
@pytest.mark.parametrize("filename", _saved_derivation_filenames())
def test_differential_semantics_sr_saved_derivation_matches_perl_final_sr(
    filename: str,
) -> None:
    try:
        state = _load_saved_derivation_state(filename)
    except ValueError as exc:
        pytest.skip(str(exc))
    perl_rows = sorted(_perl_final_sr_rows(state))
    py_rows = sorted(_py_sr_rows(state))
    assert py_rows == perl_rows
