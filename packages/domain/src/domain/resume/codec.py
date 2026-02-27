from __future__ import annotations

import json
from typing import Any

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


def _to_perl_process_base_item(item: Any) -> Any:
    if not isinstance(item, list) or len(item) < 8:
        return item

    lexical_id = item[0]
    category = item[1]
    pred = item[2]
    sy = item[3]
    idslot = item[4]
    sem = item[5]
    phono = item[6]
    wo = item[7]

    pred_rows: Any = pred if isinstance(pred, list) else pred
    sy_rows = sy if isinstance(sy, list) else []
    sem_rows = sem if isinstance(sem, list) else sem

    if isinstance(pred_rows, list) and len(pred_rows) > 0 and pred_rows[0] is not None:
        pred_rows = [None, *pred_rows]

    if isinstance(wo, list):
        wo_value: Any = [_to_perl_process_base_item(child) for child in wo]
    else:
        wo_value = None if wo in ("", None) else wo
    phono_value = None if phono in ("", None) else phono

    if isinstance(sem_rows, list):
        cleaned_sem = [value for value in sem_rows if value != ""]
        if len(cleaned_sem) > 0 and cleaned_sem[0] is not None:
            sem_rows = [None, *cleaned_sem]
        else:
            sem_rows = cleaned_sem

    if isinstance(sy_rows, list):
        nonempty_values = [value for value in sy_rows if value not in ("", None)]
        if len(nonempty_values) > 0:
            sy_rows = [None, *nonempty_values]
        else:
            empty_count = len(sy_rows)
            if empty_count == 0:
                sy_rows = [""] if idslot == "zero" else []
            elif empty_count == 1:
                sy_rows = [""]
            else:
                sy_rows = [None] + ["" for _ in range(max(1, empty_count - 1))]

    return [
        lexical_id,
        category,
        pred_rows,
        sy_rows,
        idslot,
        sem_rows,
        phono_value,
        wo_value,
    ]


def export_process_text_like_perl(state: DerivationState) -> str:
    profile = get_grammar_profile(state.grammar_id)
    perl_base: list[Any] = [None]
    for idx in range(1, state.basenum + 1):
        item = state.base[idx] if idx < len(state.base) else None
        perl_base.append(_to_perl_process_base_item(item))

    base_json = json.dumps(
        perl_base,
        ensure_ascii=False,
        separators=(",", ":"),
    )
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
