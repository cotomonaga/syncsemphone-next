from __future__ import annotations

from pathlib import Path

from domain.common.types import DerivationState
from domain.lexicon.legacy_loader import load_legacy_lexicon
from domain.numeration.parser import NUMERATION_SLOT_COUNT, parse_numeration_text


def _to_int(value: str, default: int = 0) -> int:
    raw = value.strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _append_plus_feature(grammar_id: str, plus_value: str, sy_features: list[str | None]) -> None:
    # imi01/imi02 の plus_to_numeration は空実装で、空値は push されない。
    if grammar_id in {"imi01", "imi02"} and plus_value.strip() == "":
        return
    if grammar_id == "imi03" and plus_value == "target":
        sy_features.append("3,53,target,id")
        return
    sy_features.append(plus_value)


def build_initial_derivation_state(
    grammar_id: str, numeration_text: str, legacy_root: Path
) -> DerivationState:
    lexicon = load_legacy_lexicon(legacy_root=legacy_root, grammar_id=grammar_id)
    rows = parse_numeration_text(numeration_text=numeration_text)

    base: list[object | None] = [None]
    j = 1
    for slot in range(1, NUMERATION_SLOT_COUNT + 1):
        no = rows.lexicon_slot(slot)
        if no == "":
            continue

        newnum = j
        lexicon_id = _to_int(no, default=-1)
        if lexicon_id < 0 or lexicon_id not in lexicon:
            raise ValueError(f"Unknown lexicon id at slot={slot}: {no}")

        idx_value = _to_int(rows.idx_slot(slot), default=0)
        if idx_value < 1:
            idx_value = j

        entry = lexicon[lexicon_id]
        sync_features: list[str] = []
        beta = False
        for feature in entry.sync_features:
            if feature == "3,103":
                sync_features.append(f"3,103,{newnum}")
                beta = True
            else:
                sync_features.append(feature)

        lexical_id = f"β{newnum}" if beta else f"x{idx_value}-1"
        sy_raw = [feature.replace("id", lexical_id) for feature in sync_features]
        sy_features: list[str | None] = [None, *sy_raw] if len(sy_raw) > 0 else []
        _append_plus_feature(
            grammar_id=grammar_id, plus_value=rows.plus_slot(slot), sy_features=sy_features
        )

        predicates: list[list[str] | None] = []
        if len(entry.predicates) > 0:
            predicates.append(None)
        for i_part, s_part, p_part in entry.predicates:
            predicates.append(
                [
                    i_part.replace("id", lexical_id),
                    s_part.replace("id", lexical_id),
                    p_part.replace("id", lexical_id),
                ]
            )

        sem_values = [feature.replace("id", lexical_id) for feature in entry.semantics]
        if len(sem_values) > 0:
            sem_values = [None, *sem_values]

        base_item = [
            lexical_id,  # id
            entry.category,  # ca
            predicates,  # pr
            sy_features,  # sy
            entry.idslot.replace("id", lexical_id),  # sl
            sem_values,  # se
            entry.phono,  # ph
            None,  # wo
            "",  # nb
        ]
        base.append(base_item)
        j += 1

    return DerivationState(
        grammar_id=grammar_id,
        memo=rows.memo,
        newnum=j,
        basenum=j - 1,
        history="",
        base=base,
    )
