from __future__ import annotations

import json

from domain.common.types import DerivationState
from domain.grammar.profiles import get_grammar_id_from_folder, get_grammar_profile


def export_resume_text(state: DerivationState) -> str:
    profile = get_grammar_profile(state.grammar_id)
    base_json = json.dumps(state.base, ensure_ascii=False)
    return "\n".join(
        [
            profile.folder,
            state.memo,
            str(state.newnum),
            str(state.basenum),
            state.history,
            base_json,
        ]
    )


def import_resume_text(resume_text: str) -> DerivationState:
    lines = resume_text.splitlines()
    if len(lines) < 6:
        raise ValueError(f"Resume text must contain at least 6 lines. got={len(lines)}")

    folder = lines[0].strip()
    grammar_id = get_grammar_id_from_folder(folder)
    memo = lines[1]
    try:
        newnum = int(lines[2].strip())
        basenum = int(lines[3].strip())
    except ValueError as exc:
        raise ValueError("Invalid resume integer fields (newnum/basenum)") from exc
    history = lines[4]
    base_json = lines[5]
    try:
        base = json.loads(base_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid resume base JSON") from exc

    state = DerivationState(
        grammar_id=grammar_id,
        memo=memo,
        newnum=newnum,
        basenum=basenum,
        history=history,
        base=base,
    )
    if not isinstance(state.base, list) or len(state.base) <= basenum:
        raise ValueError("Resume base length does not match basenum")
    return state
