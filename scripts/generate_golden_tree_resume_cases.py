#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT.parent


def _load_modules() -> dict[str, Any]:
    import sys

    domain_src = ROOT / "packages" / "domain" / "src"
    api_src = ROOT / "apps" / "api"
    for path in (str(domain_src), str(api_src)):
        if path not in sys.path:
            sys.path.append(path)
    from domain.common.types import DerivationState
    from domain.derivation.execute import execute_double_merge, execute_single_merge
    from domain.numeration.init_builder import build_initial_derivation_state
    from domain.resume.codec import export_resume_text

    return {
        "DerivationState": DerivationState,
        "execute_double_merge": execute_double_merge,
        "execute_single_merge": execute_single_merge,
        "build_initial_derivation_state": build_initial_derivation_state,
        "export_resume_text": export_resume_text,
    }


def _perl_tree_csv_lines(mode: str, state: Any) -> list[str]:
    grammar_no = 5 if state.grammar_id == "imi03" else 1
    payload = urllib.parse.urlencode(
        {
            "grammar": str(grammar_no),
            "mode": mode,
            "memo": state.memo,
            "newnum": str(state.newnum),
            "basenum": str(state.basenum),
            "history": state.history,
            "base": json.dumps(state.base, ensure_ascii=False),
        }
    )
    env = os.environ.copy()
    env["REQUEST_METHOD"] = "POST"
    env["CONTENT_LENGTH"] = str(len(payload.encode("utf-8")))
    proc = subprocess.run(
        ["perl", "-I.", "syncsemphone.cgi"],
        input=payload.encode("utf-8"),
        cwd=str(LEGACY_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="ignore"))
    html = proc.stdout.decode("utf-8", errors="ignore")
    match = re.search(r'id="source_csv"[^>]*>(.*?)</textarea>', html, re.S)
    if not match:
        raise RuntimeError("source_csv textarea not found in perl output")
    return [line.strip() for line in match.group(1).strip().splitlines() if line.strip()]


def _build_states(mod: dict[str, Any]) -> dict[str, Any]:
    DerivationState = mod["DerivationState"]
    execute_double_merge = mod["execute_double_merge"]
    execute_single_merge = mod["execute_single_merge"]
    build_initial_derivation_state = mod["build_initial_derivation_state"]

    def from_num(grammar_id: str, relpath: str):
        text = (LEGACY_ROOT / relpath).read_text(encoding="utf-8")
        return build_initial_derivation_state(
            grammar_id=grammar_id,
            numeration_text=text,
            legacy_root=LEGACY_ROOT,
        )

    states: dict[str, Any] = {}

    states["imi03_t0"] = from_num("imi03", "imi03/set-numeration/04.num")
    states["imi03_t1"] = execute_double_merge(
        state=states["imi03_t0"], rule_name="LH-Merge", left=5, right=6
    )
    states["imi03_t2"] = execute_double_merge(
        state=states["imi03_t1"], rule_name="RH-Merge", left=1, right=2
    )

    j2_rh = from_num("japanese2", "japanese2/set-numeration/08-01-15.num")
    states["japanese2_rh_080115"] = execute_double_merge(
        state=j2_rh, rule_name="RH-Merge", left=7, right=3, rule_version="01"
    )

    j2_pd = from_num("japanese2", "japanese2/set-numeration/05-03-09.num")
    states["japanese2_property_da"] = execute_double_merge(
        state=j2_pd, rule_name="property-da", left=1, right=4, rule_version="01"
    )

    j2_pm = from_num("japanese2", "japanese2/set-numeration/08-05-45.num")
    states["japanese2_p_merge"] = execute_double_merge(
        state=j2_pm, rule_name="P-Merge", left=1, right=5, rule_version="01"
    )

    j2_zn = from_num("japanese2", "japanese2/set-numeration/05-03-09.num")
    states["japanese2_zero_merge"] = execute_single_merge(
        state=j2_zn, rule_name="zero-Merge", check=4
    )

    j2_pt = from_num("japanese2", "japanese2/set-numeration/08-05-45.num")
    states["japanese2_partitioning"] = execute_single_merge(
        state=j2_pt, rule_name="Partitioning", check=5
    )

    mover = ["x200-1", "N", [], ["1,11,ga"], "x200-1", [], "", ["zero", "zero"]]
    head = ["x201-1", "V", [], ["v"], "x201-1", [], "", ["zero", "zero"]]
    target = ["x1-1", "V", [], [], "x1-1", [], "", [mover, head]]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    pickup_state = DerivationState(
        grammar_id="japanese2",
        memo="synthetic-pickup",
        newnum=300,
        basenum=2,
        history="",
        base=[None, target, filler],
    )
    states["japanese2_pickup"] = execute_single_merge(
        state=pickup_state, rule_name="Pickup", check=1
    )

    mover2 = [
        "x300-1",
        "N",
        [],
        ["3,107,move", "1,11,ga"],
        "x300-1",
        [],
        "",
        ["zero", "zero"],
    ]
    payload = json.dumps(mover2, ensure_ascii=False, separators=(",", ":"))
    target2 = [
        "x1-1",
        "V",
        [],
        [f"3,106,{payload}"],
        "x1-1",
        [],
        "",
        ["zero", "zero"],
    ]
    filler2 = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    landing_state = DerivationState(
        grammar_id="japanese2",
        memo="synthetic-landing",
        newnum=400,
        basenum=2,
        history="",
        base=[None, target2, filler2],
    )
    states["japanese2_landing"] = execute_single_merge(
        state=landing_state, rule_name="Landing", check=1
    )
    return states


def main() -> None:
    mod = _load_modules()
    export_resume_text = mod["export_resume_text"]
    states = _build_states(mod)

    output: dict[str, Any] = {
        "version": "v1",
        "description": "Golden cases for tree/tree_cat + resume persistence",
        "cases": [],
    }

    seq = 1
    for state_id, state in states.items():
        state_json = state.model_dump(mode="json")
        for mode in ("tree", "tree_cat"):
            lines = _perl_tree_csv_lines(mode=mode, state=state)
            output["cases"].append(
                {
                    "id": f"GC-TRR-{seq:03d}",
                    "state_id": state_id,
                    "kind": mode,
                    "state": state_json,
                    "expected_lines": lines,
                }
            )
            seq += 1
        output["cases"].append(
            {
                "id": f"GC-TRR-{seq:03d}",
                "state_id": state_id,
                "kind": "resume",
                "state": state_json,
                "expected_resume_text": export_resume_text(state),
            }
        )
        seq += 1

    if len(output["cases"]) != 30:
        raise RuntimeError(f"Expected 30 cases, got {len(output['cases'])}")

    out_path = ROOT / "packages/test-fixtures/cases/golden/tree-resume-v1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(output['cases'])} cases to {out_path}")


if __name__ == "__main__":
    main()
