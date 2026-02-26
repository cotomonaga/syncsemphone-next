from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from domain.common.types import DerivationState


def _uses_imi_feature_engine(grammar_id: str) -> bool:
    return grammar_id in {"imi01", "imi02", "imi03", "japanese2"}


def _build_history(
    state: DerivationState,
    rule_name: str,
    left: int | None = None,
    right: int | None = None,
    check: int | None = None,
) -> str:
    history = state.history
    if check is not None:
        token = f"([{state.base[check][0]}] {rule_name}) "
    else:
        if left is None or right is None:
            raise ValueError("left/right are required when check is not provided")
        token = f"([{state.base[left][0]} {state.base[right][0]}] {rule_name}) "
    return (history + token).replace("β", "beta")


def _validate_double_indices(state: DerivationState, left: int, right: int) -> None:
    if left == right:
        raise ValueError("left and right must be different")
    if left < 1 or left > state.basenum:
        raise ValueError(f"left index out of range: {left}")
    if right < 1 or right > state.basenum:
        raise ValueError(f"right index out of range: {right}")


def _is_uninterpretable_feature(value: str) -> bool:
    return "," in value and any(ch.isdigit() for ch in value.split(",", 1)[1])


def _split_feature(value: str) -> list[str]:
    # Perlの split(/,/, ...) は前後空白を削らない。
    return value.split(",")


def _rule_match(rule_name: str, feature_parts: list[str], index: int) -> bool:
    return index < len(feature_parts) and feature_parts[index] == rule_name


def _is_positional_match(
    wanted: str,
    *,
    current: int,
    right: int,
    left: int,
) -> bool:
    if wanted == "":
        return True
    if wanted == "right":
        return current == right
    if wanted == "left":
        return current == left
    return False


def _eval_feature_17(
    parts: list[str],
    *,
    other_category: str,
    other_sy: list[str],
    rule_name: str,
    current_index: int,
    right: int,
    left: int,
    expected_role: str,
) -> bool:
    # #,X,17,α,β,γ,δ,ε
    pos = 0
    alpha = parts[2] if len(parts) > 2 else ""
    beta = parts[3] if len(parts) > 3 else ""
    gamma = parts[4] if len(parts) > 4 else ""
    delta = parts[5] if len(parts) > 5 else ""
    epsilon = parts[6] if len(parts) > 6 else ""

    if alpha == "" or other_category == alpha:
        pos += 1
    if beta == "" or any(candidate == beta for candidate in other_sy):
        pos += 1
    if gamma == "" or gamma == rule_name:
        pos += 1
    if _is_positional_match(delta, current=current_index, right=right, left=left):
        pos += 1
    if epsilon == "" or epsilon == expected_role:
        pos += 1
    return pos >= 5


def _normalize_sy(values: list[str]) -> list[str]:
    return [value for value in values if value != ""]


def _normalize_sem(values: list[str]) -> list[str]:
    return [value for value in values if value != ""]


def _parse_attr_value(raw: str) -> tuple[str, str]:
    parts = raw.split(":", 1)
    if len(parts) == 1:
        return raw, ""
    return parts[0], parts[1]


def _compose_attr_value(attr: str, value: str) -> str:
    return f"{attr}:{value}"


def _find_feature_53_index(sy_values: list[str], target: str) -> int:
    for idx, candidate in enumerate(sy_values):
        if not _is_uninterpretable_feature(candidate):
            continue
        parts = _split_feature(candidate)
        if len(parts) > 2 and parts[1] == "53" and parts[2] == target:
            return idx
    return -1


def _process_sl_imi03(
    *,
    hb: list[Any],
    nb: list[Any],
    hb_sy: list[str],
    rule_name: str,
) -> tuple[str | None, str | None, str | None]:
    hb_sl = str(hb[4])
    nb_sl = str(nb[4])
    hb_id = str(hb[0])
    nb_id = str(nb[0])

    mo_sl = hb_sl
    ha_sl = "zero"
    na_sl: str | None = nb_sl

    if _is_uninterpretable_feature(hb_sl):
        parts = _split_feature(hb_sl)
        number = parts[1] if len(parts) > 1 else ""
        if number == "24":
            mo_sl = nb_sl
            ha_sl = "zero"
        elif number == "26":
            if len(parts) > 2 and parts[2] == rule_name:
                mo_sl = nb_id
            else:
                mo_sl = hb_sl
                ha_sl = "zero"
        else:
            coeff = parts[0] if len(parts) > 0 else ""
            if coeff in {"2", "3"}:
                mo_sl = hb_sl
                ha_sl = "zero"
            else:
                mo_sl = "zero"
                ha_sl = hb_sl

    if _is_uninterpretable_feature(nb_sl):
        parts = _split_feature(nb_sl)
        number = parts[1] if len(parts) > 1 else ""
        if number == "22":
            na_sl = hb_id
        elif number == "24":
            # Perl実装では non-head側 24 は未定義のまま残る
            na_sl = None
        elif number == "25":
            if len(parts) > 2 and any(feature == parts[2] for feature in hb_sy):
                na_sl = hb_id
        elif number == "26":
            if len(parts) > 2 and parts[2] == rule_name:
                na_sl = nb_id
    return mo_sl, ha_sl, na_sl


def _process_pr_term(
    *,
    term: str,
    hb_id: str,
    nb_id: str,
    hb_ca: str,
    nb_ca: str,
    hb_sy: list[str],
    nb_sy: list[str],
    rule_name: str,
    side: str,
    role_index: int,
) -> tuple[str, list[str], list[str], bool]:
    if not _is_uninterpretable_feature(term):
        return term, hb_sy, nb_sy, False
    parts = _split_feature(term)
    if len(parts) < 2:
        return term, hb_sy, nb_sy, False
    number = parts[1]
    changed = True

    if number == "21":
        return "2,22", hb_sy, nb_sy, changed
    if number == "22":
        replacement = hb_id if side == "nonhead" else term
        return replacement, hb_sy, nb_sy, changed
    if number == "23":
        return "0,24", hb_sy, nb_sy, changed
    if number == "24":
        replacement = nb_id if side == "head" else hb_id
        if side == "head" and role_index == 1:
            for idx, feature in enumerate(nb_sy):
                if not _is_uninterpretable_feature(feature):
                    continue
                fparts = _split_feature(feature)
                if len(fparts) > 2 and fparts[1] == "11" and fparts[2] == "ga":
                    nb_sy[idx] = ""
        return replacement, hb_sy, nb_sy, changed
    if number == "25":
        target = parts[2] if len(parts) > 2 else ""
        if side == "head":
            if any(feature == target for feature in nb_sy):
                return nb_id, hb_sy, nb_sy, changed
            return term, hb_sy, nb_sy, changed
        if any(feature == target for feature in hb_sy):
            return hb_id, hb_sy, nb_sy, changed
        return term, hb_sy, nb_sy, changed
    if number == "26":
        target_rule = parts[2] if len(parts) > 2 else ""
        if target_rule == rule_name:
            return (nb_id if side == "head" else hb_id), hb_sy, nb_sy, changed
        return term, hb_sy, nb_sy, changed
    if number == "27":
        target = parts[2] if len(parts) > 2 else ""
        if side == "head":
            pos = _find_feature_53_index(nb_sy, target)
            if pos > -1:
                sy_parts = _split_feature(nb_sy[pos])
                nb_sy[pos] = ""
                return (sy_parts[3] if len(sy_parts) > 3 else term), hb_sy, nb_sy, changed
            return term, hb_sy, nb_sy, changed
        pos = _find_feature_53_index(hb_sy, target)
        if pos > -1:
            sy_parts = _split_feature(hb_sy[pos])
            hb_sy[pos] = ""
            return (sy_parts[3] if len(sy_parts) > 3 else term), hb_sy, nb_sy, changed
        return term, hb_sy, nb_sy, changed
    if number == "29" and side == "head":
        target = parts[2] if len(parts) > 2 else ""
        target_rule = parts[3] if len(parts) > 3 else ""
        if target_rule == rule_name:
            if nb_ca == target:
                return nb_id, hb_sy, nb_sy, changed
            for idx, feature in enumerate(nb_sy):
                fparts = _split_feature(feature) if _is_uninterpretable_feature(feature) else []
                if feature == target or (len(fparts) > 2 and fparts[2] == target):
                    nb_sy[idx] = ""
                    return nb_id, hb_sy, nb_sy, changed
        return term, hb_sy, nb_sy, changed

    # passthrough for unsupported features
    return term, hb_sy, nb_sy, False


def _process_pr_imi03(
    *,
    hb: list[Any],
    nb: list[Any],
    hb_sy: list[str],
    nb_sy: list[str],
    rule_name: str,
    grammar_id: str,
) -> tuple[list[Any], str, list[Any], list[str], list[str]]:
    hb_id = str(hb[0])
    nb_id = str(nb[0])
    hb_ca = str(hb[1])
    nb_ca = str(nb[1])
    hb_pr = [list(map(str, triple)) for triple in hb[2] if isinstance(triple, list) and len(triple) == 3]
    nb_pr = [list(map(str, triple)) for triple in nb[2] if isinstance(triple, list) and len(triple) == 3]

    mo_pr = deepcopy(hb_pr)
    ha_pr: str = ""
    na_pr = deepcopy(nb_pr)
    on_flags = [False for _ in na_pr]

    for idx, triple in enumerate(mo_pr):
        for role_index in range(0, 3):
            replacement, hb_sy, nb_sy, changed = _process_pr_term(
                term=triple[role_index],
                hb_id=hb_id,
                nb_id=nb_id,
                hb_ca=hb_ca,
                nb_ca=nb_ca,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                side="head",
                role_index=role_index,
            )
            mo_pr[idx][role_index] = replacement
            if changed:
                ha_pr = ""

    for idx, triple in enumerate(na_pr):
        for role_index in range(0, 3):
            replacement, hb_sy, nb_sy, changed = _process_pr_term(
                term=triple[role_index],
                hb_id=hb_id,
                nb_id=nb_id,
                hb_ca=hb_ca,
                nb_ca=nb_ca,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                side="nonhead",
                role_index=role_index,
            )
            na_pr[idx][role_index] = replacement
            if changed:
                on_flags[idx] = True

    for idx, enabled in enumerate(on_flags):
        if enabled:
            mo_pr.append(na_pr[idx])
            if grammar_id == "japanese2":
                na_pr[idx] = "zero"
            else:
                na_pr[idx] = ["zero", "zero", "zero"]

    # Perlは中間段階で空要素を詰めないため、位置依存の副作用を保つためにそのまま返す。
    return mo_pr, ha_pr, na_pr, hb_sy, nb_sy


def _process_se_imi03(
    *,
    hb: list[Any],
    nb: list[Any],
    hb_sy: list[str],
    nb_sy: list[str],
    rule_name: str,
    na_pr: list[Any] | None = None,
) -> tuple[list[str], str, list[str], list[str], list[str]]:
    hb_se = [str(value) for value in hb[5] if str(value) != ""]
    nb_se = [str(value) for value in nb[5] if str(value) != ""]
    hb_ca = str(hb[1])
    nb_ca = str(nb[1])
    hb_id = str(hb[0])
    nb_id = str(nb[0])

    mo_se = deepcopy(hb_se)
    ha_se: str = "zero"
    na_se = deepcopy(nb_se)

    hb_sy_mut = deepcopy(hb_sy)
    nb_sy_mut = deepcopy(nb_sy)

    for idx, sem in enumerate(hb_se):
        attr, value = _parse_attr_value(sem)
        if not _is_uninterpretable_feature(value):
            continue
        parts = _split_feature(value)
        number = parts[1] if len(parts) > 1 else ""

        if number == "21":
            mo_se[idx] = _compose_attr_value(attr, "2,22")
        elif number == "23":
            mo_se[idx] = _compose_attr_value(attr, "2,24")
        elif number == "24":
            mo_se[idx] = _compose_attr_value(attr, nb_id)
        elif number == "25":
            target = parts[2] if len(parts) > 2 else ""
            if any(feature == target for feature in nb_sy_mut):
                mo_se[idx] = _compose_attr_value(attr, nb_id)
        elif number == "70":
            target = parts[2] if len(parts) > 2 else ""
            # Perl互換: non-head側のsy個数分だけhead側syを同位置参照する。
            for sy_idx in range(0, min(len(hb_sy_mut), len(nb_sy_mut))):
                if hb_sy_mut[sy_idx] == target:
                    mo_se[idx] = _compose_attr_value("", hb_id)
        elif number == "71":
            target = parts[2] if len(parts) > 2 else ""
            pos = _find_feature_53_index(hb_sy_mut, target)
            if pos > -1:
                sy_parts = _split_feature(hb_sy_mut[pos])
                hb_sy_mut[pos] = ""
                replacement = sy_parts[3] if len(sy_parts) > 3 else value
                mo_se[idx] = _compose_attr_value("", replacement)
            else:
                mo_se[idx] = nb_se[idx] if idx < len(nb_se) else ""
        elif number == "33":
            target = parts[2] if len(parts) > 2 else ""
            for sy_idx, sy_value in enumerate(nb_sy_mut):
                if not _is_uninterpretable_feature(sy_value):
                    continue
                sy_parts = _split_feature(sy_value)
                sy_number = sy_parts[1] if len(sy_parts) > 1 else ""
                sy_label = sy_parts[2] if len(sy_parts) > 2 else ""
                if sy_label != target:
                    continue
                if sy_number == "11":
                    nb_sy_mut[sy_idx] = ""
                    mo_se[idx] = _compose_attr_value(attr, nb_id)
                if sy_number == "12":
                    mo_se[idx] = _compose_attr_value(attr, nb_id)
        elif number == "26":
            target_rule = parts[2] if len(parts) > 2 else ""
            if target_rule in {rule_name, "zero-Merge"}:
                mo_se[idx] = _compose_attr_value(attr, nb_id)
        elif number == "27":
            target = parts[2] if len(parts) > 2 else ""
            pos = _find_feature_53_index(nb_sy_mut, target)
            if pos > -1:
                sy_parts = _split_feature(nb_sy_mut[pos])
                nb_sy_mut[pos] = ""
                replacement = sy_parts[3] if len(sy_parts) > 3 else value
                mo_se[idx] = _compose_attr_value(attr, replacement)
        elif number == "29":
            target = parts[2] if len(parts) > 2 else ""
            target_rule = parts[3] if len(parts) > 3 else ""
            if target_rule in {rule_name, "zero-Merge"}:
                if nb_ca == target:
                    mo_se[idx] = _compose_attr_value(attr, nb_id)
                else:
                    for sy_value in nb_sy_mut:
                        sy_parts = _split_feature(sy_value) if _is_uninterpretable_feature(sy_value) else []
                        if sy_value == target or (len(sy_parts) > 2 and sy_parts[2] == target):
                            mo_se[idx] = _compose_attr_value(attr, nb_id)
                            break
        elif number == "30":
            target = parts[2] if len(parts) > 2 else ""
            pos = _find_feature_53_index(nb_sy_mut, target)
            if pos > -1:
                sy_parts = _split_feature(nb_sy_mut[pos])
                nb_sy_mut[pos] = ""
                replacement = sy_parts[3] if len(sy_parts) > 3 else ""
                mo_se[idx] = _compose_attr_value(attr, f"α({replacement})")
        elif number == "34":
            # #,head,34,α,β,γ,δ
            pos = 0
            alpha = parts[2] if len(parts) > 2 else ""
            beta = parts[3] if len(parts) > 3 else ""
            gamma = parts[4] if len(parts) > 4 else ""
            delta = parts[5] if len(parts) > 5 else ""
            if alpha == "" or any(feature == alpha for feature in nb_sy_mut):
                pos += 1
            if beta == "" or any(
                _is_uninterpretable_feature(feature)
                and len(_split_feature(feature)) > 2
                and _split_feature(feature)[2] == beta
                for feature in nb_sy_mut
            ):
                pos += 1
            if gamma == "" or gamma in {rule_name, "zero-Merge"}:
                pos += 1
            if delta == "":
                pos += 1
            if pos >= 4:
                mo_se[idx] = _compose_attr_value(attr, str(nb[4]))

    for idx, sem in enumerate(nb_se):
        attr, value = _parse_attr_value(sem)
        if not _is_uninterpretable_feature(value):
            continue
        parts = _split_feature(value)
        number = parts[1] if len(parts) > 1 else ""
        if number == "22":
            na_se[idx] = _compose_attr_value(attr, hb_id)
        elif number == "27":
            target = parts[2] if len(parts) > 2 else ""
            pos = _find_feature_53_index(hb_sy_mut, target)
            if pos > -1:
                sy_parts = _split_feature(hb_sy_mut[pos])
                hb_sy_mut[pos] = ""
                # Perl互換: non-head側の se feature 27 は本来 se を置換せず、
                # 内部的に $na[$pr][$z][3] へ書き込むバグ挙動を持つ。
                na_se[idx] = nb_se[idx]
                if (
                    na_pr is not None
                    and idx < len(na_pr)
                    and isinstance(na_pr[idx], list)
                ):
                    replacement = sy_parts[3] if len(sy_parts) > 3 else ""
                    row = na_pr[idx]
                    while len(row) < 3:
                        row.append("")
                    if len(row) == 3:
                        row.append(replacement)
                    else:
                        row[3] = replacement
        elif number == "30":
            target = parts[2] if len(parts) > 2 else ""
            pos = _find_feature_53_index(hb_sy_mut, target)
            if pos > -1:
                sy_parts = _split_feature(hb_sy_mut[pos])
                hb_sy_mut[pos] = ""
                replacement = sy_parts[3] if len(sy_parts) > 3 else ""
                na_se[idx] = _compose_attr_value(attr, f"α({replacement})")

    return (
        _normalize_sem(mo_se),
        ha_se,
        _normalize_sem(na_se),
        hb_sy_mut,
        nb_sy_mut,
    )


def _apply_kind_feature_101_on_nonhead(
    *,
    hb_id: str,
    nb_id: str,
    mo_se: list[str],
    nb_sy: list[str],
    na_se: list[str],
) -> tuple[list[str], list[str]]:
    updated_sy: list[str] = []
    updated_se = deepcopy(na_se)

    for feature in nb_sy:
        if not _is_uninterpretable_feature(feature):
            updated_sy.append(feature)
            continue
        parts = _split_feature(feature)
        if len(parts) < 3 or parts[1] != "101":
            updated_sy.append(feature)
            continue

        # Perl互換: 3,101,Kind, は、mother側 se に nb_id を値にもつ属性がある場合、
        # non-head側へ Kind:<attribute>(hb_id) を追加し、当該 sy は消費する。
        derived_attr = ""
        for sem in mo_se:
            attr, value = _parse_attr_value(str(sem))
            if value == nb_id:
                derived_attr = attr
                break
        if derived_attr == "":
            updated_sy.append(feature)
            continue
        kind_attr = parts[2].strip() if len(parts) > 2 else "Kind"
        if kind_attr == "":
            kind_attr = "Kind"
        updated_se.append(f"{kind_attr}:{derived_attr}({hb_id})")

    return _normalize_sy(updated_sy), _normalize_sem(updated_se)


def _append_merge_relation_semantic(
    *,
    mo_se: list[str],
    mo_sl: str,
    na_sl: str,
    nb_id: str,
    nb_sl: str,
    hb_sl: str,
    newnum: int,
    rule_name: str,
    rule_version: str,
) -> tuple[list[str], int]:
    if mo_sl == na_sl:
        return mo_se, newnum

    temp = any(nb_id in semantic for semantic in mo_se)
    if rule_version == "01":
        if _is_uninterpretable_feature(nb_sl) or _is_uninterpretable_feature(hb_sl):
            temp = True
    if rule_name == "RH-Merge" and rule_version == "03":
        if nb_sl == "rel" or hb_sl == "rel":
            temp = True

    if rule_version == "03":
        can_append = (not temp) and (na_sl == nb_id)
    else:
        can_append = not temp

    if can_append:
        updated = deepcopy(mo_se)
        updated.append(f"α<sub>{newnum}</sub>:{nb_id}")
        return updated, newnum + 1
    return mo_se, newnum


def _process_sy_imi03(
    *,
    hb: list[Any],
    nb: list[Any],
    rule_name: str,
    grammar_id: str,
    head_index: int,
    nonhead_index: int,
    left: int,
    right: int,
    both_mode: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    hb_sy = ["" if value is None else str(value) for value in hb[3]] if isinstance(hb[3], list) else []
    nb_sy = ["" if value is None else str(value) for value in nb[3]] if isinstance(nb[3], list) else []
    hb_ca = str(hb[1])
    nb_ca = str(nb[1])
    hb_id = str(hb[0])
    nb_id = str(nb[0])

    mo_sy = deepcopy(hb_sy)
    ha_sy = deepcopy(hb_sy)
    na_sy = deepcopy(nb_sy)
    mosy: list[str] = []

    for z, feature in enumerate(hb_sy):
        if not _is_uninterpretable_feature(feature):
            parts = _split_feature(feature)
            number = parts[1] if len(parts) > 1 else ""
            if grammar_id == "japanese2" and number in {"1L", "2L", "3L"}:
                target = parts[2] if len(parts) > 2 else ""
                if target != "" and nb_ca == target:
                    mo_sy[z] = ""
                    ha_sy[z] = ""
                continue
            if z < len(ha_sy):
                ha_sy[z] = ""
            continue
        parts = _split_feature(feature)
        if len(parts) < 2:
            continue
        number = parts[1]
        coeff = parts[0] if len(parts) > 0 else ""

        if grammar_id == "japanese2" and number in {"1L", "2L", "3L"}:
            target = parts[2] if len(parts) > 2 else ""
            if target != "" and nb_ca == target:
                mo_sy[z] = ""
                ha_sy[z] = ""
            continue

        if number in {"1", "3"} and len(parts) > 2 and nb_ca == parts[2]:
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "5" and _rule_match(rule_name, parts, 2):
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "6" and (_rule_match(rule_name, parts, 2) or _rule_match(rule_name, parts, 3)):
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "7" and _rule_match(rule_name, parts, 2):
            n = int(parts[3]) - 1 if len(parts) > 3 and parts[3].isdigit() else 0
            mo_sy[z] = f"{coeff},7,{parts[2]},{n}"
            ha_sy[z] = ""
        elif number == "12" and len(parts) > 3 and nb_ca == parts[3]:
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "14" and rule_name == "RH-Merge":
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "16" and rule_name == "LH-Merge":
            mo_sy[z] = ""
            ha_sy[z] = ""
        elif number == "17":
            consumed = _eval_feature_17(
                parts=parts,
                other_category=nb_ca,
                other_sy=nb_sy,
                rule_name=rule_name,
                current_index=head_index,
                right=right,
                left=left,
                expected_role="head",
            )
            if consumed:
                mo_sy[z] = ""
                ha_sy[z] = ""
            else:
                if coeff == "0":
                    mo_sy[z] = ""
                else:
                    ha_sy[z] = ""
        elif number == "51":
            ha_sy[z] = ""
            mo_sy[z] = f"3,52,{parts[2] if len(parts) > 2 else ''}"
        elif number == "52":
            ha_sy[z] = ""
            mo_sy[z] = f"3,53,{parts[2] if len(parts) > 2 else ''},{nb_id}"
        else:
            if coeff.isdigit() and int(coeff) >= 2:
                ha_sy[z] = ""
            else:
                mo_sy[z] = ""

    if both_mode:
        mo2_sy = deepcopy(nb_sy)
        na_sy = deepcopy(nb_sy)
        for z, feature in enumerate(nb_sy):
            if not _is_uninterpretable_feature(feature):
                if z < len(na_sy):
                    na_sy[z] = ""
                continue
            parts = _split_feature(feature)
            if len(parts) < 2:
                continue
            number = parts[1]
            coeff = parts[0] if len(parts) > 0 else ""

            if grammar_id == "japanese2" and number in {"1L", "2L", "3L"}:
                target = parts[2] if len(parts) > 2 else ""
                if number == "1L":
                    if target != "" and hb_ca == target:
                        na_sy[z] = ""
                        mo2_sy[z] = ""
                    elif rule_name == "J-Merge":
                        na_sy[z] = ""
                elif number == "2L":
                    if rule_name in {"J-Merge", "property-no"}:
                        na_sy[z] = ""
                    elif target != "" and hb_ca == target:
                        na_sy[z] = ""
                        mo2_sy[z] = ""
                elif number == "3L":
                    if target != "" and hb_ca == target:
                        na_sy[z] = ""
                        mo2_sy[z] = ""
                    elif rule_name == "J-Merge":
                        na_sy[z] = ""
                continue

            if number in {"1", "3"} and len(parts) > 2 and hb_ca == parts[2]:
                na_sy[z] = ""
                mo2_sy[z] = ""
            elif number == "5" and _rule_match(rule_name, parts, 2):
                na_sy[z] = ""
                mo2_sy[z] = ""
            elif number == "6" and (_rule_match(rule_name, parts, 2) or _rule_match(rule_name, parts, 3)):
                na_sy[z] = ""
                mo2_sy[z] = ""
            elif number == "51":
                na_sy[z] = ""
                mo2_sy[z] = f"3,52,{parts[2] if len(parts) > 2 else ''}"
            elif number == "52":
                na_sy[z] = ""
                mo2_sy[z] = f"3,53,{parts[2] if len(parts) > 2 else ''},{hb_id}"
            elif number == "58":
                na_sy[z] = ""
                mo2_sy[z] = f"3,53,{parts[2] if len(parts) > 2 else ''},{hb_id}"
            else:
                if coeff == "3":
                    na_sy[z] = ""
                else:
                    mo2_sy[z] = ""

        mo_sy.extend(mo2_sy)
        return _normalize_sy(mo_sy), _normalize_sy(ha_sy), _normalize_sy(na_sy)

    for z, feature in enumerate(nb_sy):
        if not _is_uninterpretable_feature(feature):
            parts = _split_feature(feature)
            number = parts[1] if len(parts) > 1 else ""
            if grammar_id == "japanese2" and number in {"1L", "2L", "3L"}:
                target = parts[2] if len(parts) > 2 else ""
                if target != "" and hb_ca == target:
                    na_sy[z] = ""
            continue
        parts = _split_feature(feature)
        if len(parts) < 2:
            continue
        number = parts[1]
        coeff = parts[0] if len(parts) > 0 else ""

        if grammar_id == "japanese2" and number in {"1L", "2L", "3L"}:
            target = parts[2] if len(parts) > 2 else ""
            if target != "" and hb_ca == target:
                na_sy[z] = ""
            continue

        if number in {"1", "3"} and len(parts) > 2 and hb_ca == parts[2]:
            na_sy[z] = ""
        elif number == "5" and _rule_match(rule_name, parts, 2):
            na_sy[z] = ""
        elif number == "6" and (_rule_match(rule_name, parts, 2) or _rule_match(rule_name, parts, 3)):
            na_sy[z] = ""
        elif number == "11":
            if coeff == "4":
                na_value = f"2,11,{parts[2] if len(parts) > 2 else ''}"
                mosy.append(na_value)
                na_sy[z] = ""
        elif number == "12":
            if coeff == "5":
                na_value = f"4,12,{parts[2] if len(parts) > 2 else ''},{parts[3] if len(parts) > 3 else ''}"
                mosy.append(na_value)
                na_sy[z] = ""
            elif len(parts) > 3 and hb_ca == parts[3]:
                na_sy[z] = ""
            elif coeff == "4":
                na_value = f"2,12,{parts[2] if len(parts) > 2 else ''},{parts[3] if len(parts) > 3 else ''}"
                mosy.append(na_value)
                na_sy[z] = ""
        elif number == "13" and rule_name == "LH-Merge":
            na_sy[z] = ""
        elif number == "15" and rule_name == "RH-Merge":
            na_sy[z] = ""
        elif number == "17":
            consumed = _eval_feature_17(
                parts=parts,
                other_category=hb_ca,
                other_sy=hb_sy,
                rule_name=rule_name,
                current_index=nonhead_index,
                right=right,
                left=left,
                expected_role="nonhead",
            )
            if consumed:
                na_sy[z] = ""
            else:
                if coeff == "3":
                    mosy.append(na_sy[z])
                    na_sy[z] = ""
                else:
                    if z < len(mo_sy):
                        mo_sy[z] = ""
        elif number == "51":
            na_value = f"3,52,{parts[2] if len(parts) > 2 else ''}"
            mosy.append(na_value)
            na_sy[z] = ""
        elif number == "52":
            na_value = f"3,53,{parts[2] if len(parts) > 2 else ''},{hb_id}"
            mosy.append(na_value)
            na_sy[z] = ""
        elif number == "58":
            na_value = f"3,53,{parts[2] if len(parts) > 2 else ''},{hb_id}"
            mosy.append(na_value)
            na_sy[z] = ""
        else:
            if coeff == "3":
                mosy.append(na_sy[z])
                na_sy[z] = ""

    mo_sy.extend(mosy)
    return _normalize_sy(mo_sy), _normalize_sy(ha_sy), _normalize_sy(na_sy)


def _execute_japanese2_special_left_headed(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
    rule_name: str,
) -> tuple[list[Any], int]:
    head_idx = left
    nonhead_idx = right
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name=rule_name,
        grammar_id=state.grammar_id,
    )

    mo_sy = deepcopy(hb_sy)
    ha_sy: str = ""
    na_sy: str = ""
    mo_sl = str(hb[4])
    ha_sl = "zero"
    na_sl = "zero"

    hb_se = [str(value) for value in hb[5] if str(value) != ""]
    mo_se = deepcopy(hb_se)
    if rule_name == "sase1":
        mo_se = [value.replace("2,25,ga", "2,25,ni") for value in mo_se]
        mo_se.append("Causer:2,25,ga")
    elif rule_name == "sase2":
        updated: list[str] = []
        for value in mo_se:
            attr, sem_value = _parse_attr_value(value)
            if attr in {"Theme", "Affectee"} and sem_value.startswith("2,25,ga"):
                sem_value = sem_value.replace("2,25,ga", "2,25,wo", 1).rstrip(",")
                updated.append(_compose_attr_value(attr, sem_value))
                continue
            updated.append(value)
        mo_se = updated
        mo_se.append("Causer:2,25,ga")
    elif rule_name == "rare1":
        updated = []
        for value in mo_se:
            attr, sem_value = _parse_attr_value(value)
            if sem_value.startswith("2,25,ga"):
                sem_value = sem_value.replace("2,25,ga", "2,25,ni", 1).rstrip(",")
                updated.append(_compose_attr_value(attr, sem_value))
                continue
            updated.append(value)
        mo_se = updated
        mo_se.append("Affectee:2,25,ga")
    elif rule_name == "rare2":
        updated = []
        for value in mo_se:
            original = value
            attr, sem_value = _parse_attr_value(value)
            if "2,25,wo" in sem_value:
                value = _compose_attr_value(attr, "2,25,ga")
            if "Agent:2,25,ga" in original:
                value = ""
            if value != "":
                updated.append(value)
        mo_se = updated

    ha_se = "zero"
    na_se = "zero"

    mother[2] = mo_pr
    mother[3] = _normalize_sy(mo_sy)
    mother[4] = mo_sl
    mother[5] = _normalize_sem(mo_se)
    mother[6] = None
    ha[2] = ha_pr if ha_pr != [] else ""
    ha[3] = ha_sy
    ha[4] = ha_sl
    ha[5] = ha_se
    na[2] = na_pr
    na[3] = na_sy
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [ha, na]

    base[head_idx] = mother
    del base[nonhead_idx]
    return base, state.newnum


def _execute_japanese2_property_merge(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
) -> tuple[list[Any], int]:
    head_idx = right
    nonhead_idx = left
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="property-Merge",
        grammar_id=state.grammar_id,
    )
    hb[3] = hb_sy
    nb[3] = nb_sy
    mo_sy, ha_sy, na_sy = _process_sy_imi03(
        hb=hb,
        nb=nb,
        rule_name="property-Merge",
        grammar_id=state.grammar_id,
        head_index=head_idx,
        nonhead_index=nonhead_idx,
        left=left,
        right=right,
    )

    mo_sl = str(hb[4])
    ha_sl = "zero"
    na_sl = "zero"
    hb_se = [str(value) for value in hb[5] if str(value) != ""]
    nb_se = [str(value) for value in nb[5] if str(value) != ""]
    mo_se = nb_se + hb_se
    ha_se = "zero"
    na_se = "zero"

    mother[2] = ""
    mother[3] = _normalize_sy(mo_sy)
    mother[4] = mo_sl
    mother[5] = _normalize_sem(mo_se)
    mother[6] = None
    ha[2] = ha_pr
    ha[3] = ha_sy
    ha[4] = ha_sl
    ha[5] = ha_se
    na[2] = na_pr
    na[3] = na_sy
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [na, ha]

    base[head_idx] = mother
    del base[nonhead_idx]
    return base, state.newnum


def _execute_japanese2_rel_merge(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
) -> tuple[list[Any], int]:
    head_idx = right
    nonhead_idx = left
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)
    newnum = state.newnum

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="rel-Merge",
        grammar_id=state.grammar_id,
    )
    rel_id = f"x{newnum}-1"
    rel_triplet = [rel_id, str(hb[0]), str(nb[0])]
    if not isinstance(mo_pr, list):
        mo_pr = []
    mo_pr = deepcopy(mo_pr)
    mo_pr.append(rel_triplet)
    newnum += 1

    mo_sl, ha_sl, na_sl = _process_sl_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        rule_name="rel-Merge",
    )
    mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="rel-Merge",
        na_pr=na_pr,
    )
    nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
        hb_id=str(hb[0]),
        nb_id=str(nb[0]),
        mo_se=mo_se,
        nb_sy=nb_sy,
        na_se=na_se,
    )
    mo_se = deepcopy(mo_se)
    mo_se.append(f"α<sub>{newnum}</sub>:{str(nb[4])}")
    newnum += 1

    for idx, feature in enumerate(hb_sy):
        if not _is_uninterpretable_feature(feature):
            continue
        parts = _split_feature(feature)
        if len(parts) > 1 and parts[1] == "54":
            hb_sy[idx] = f"2,56,{rel_id}"

    hb[3] = hb_sy
    nb[3] = nb_sy
    mo_sy, ha_sy, na_sy = _process_sy_imi03(
        hb=hb,
        nb=nb,
        rule_name="rel-Merge",
        grammar_id=state.grammar_id,
        head_index=head_idx,
        nonhead_index=nonhead_idx,
        left=left,
        right=right,
    )

    mother[3] = mo_sy
    mother[2] = mo_pr
    mother[4] = mo_sl
    mother[5] = mo_se
    mother[6] = None
    ha[3] = ha_sy
    ha[2] = ha_pr
    ha[4] = ha_sl
    ha[5] = ha_se
    na[3] = na_sy
    na[2] = na_pr
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [na, ha]

    base[head_idx] = mother
    del base[nonhead_idx]
    newnum += 1
    return base, newnum


def _execute_japanese2_property_no(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
) -> tuple[list[Any], int]:
    head_idx = left
    nonhead_idx = right
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="property-no",
        grammar_id=state.grammar_id,
    )
    mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="property-no",
        na_pr=na_pr,
    )
    nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
        hb_id=str(hb[0]),
        nb_id=str(nb[0]),
        mo_se=mo_se,
        nb_sy=nb_sy,
        na_se=na_se,
    )
    hb[3] = hb_sy
    nb[3] = nb_sy
    mo_sy, ha_sy, na_sy = _process_sy_imi03(
        hb=hb,
        nb=nb,
        rule_name="property-no",
        grammar_id=state.grammar_id,
        head_index=head_idx,
        nonhead_index=nonhead_idx,
        left=left,
        right=right,
        both_mode=True,
    )
    na_sy = [
        value
        for value in na_sy
        if not value.startswith("1,5,J-Merge")
    ]

    mo_sl = "0,24"
    ha_sl = "zero"
    na_sl = "zero"

    mother[3] = mo_sy
    mother[2] = mo_pr
    mother[4] = mo_sl
    mother[5] = mo_se
    mother[6] = None
    ha[3] = ha_sy
    ha[2] = ha_pr
    ha[4] = ha_sl
    ha[5] = ha_se
    na[3] = na_sy
    na[2] = na_pr
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [ha, na]

    base[head_idx] = mother
    del base[nonhead_idx]
    return base, state.newnum


def _execute_japanese2_property_da(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
) -> tuple[list[Any], int]:
    head_idx = right
    nonhead_idx = left
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="property-da",
        grammar_id=state.grammar_id,
    )
    hb[3] = hb_sy
    nb[3] = nb_sy
    mo_sy, ha_sy, na_sy = _process_sy_imi03(
        hb=hb,
        nb=nb,
        rule_name="property-da",
        grammar_id=state.grammar_id,
        head_index=head_idx,
        nonhead_index=nonhead_idx,
        left=left,
        right=right,
    )
    hb_se = [str(value) for value in hb[5] if str(value) != ""]
    nb_se = [str(value) for value in nb[5] if str(value) != ""]
    mo_se = nb_se + hb_se
    mo_sl = "0,24"
    ha_sl = "zero"
    na_sl = "zero"
    ha_se = "zero"
    na_se = "zero"

    mother[3] = mo_sy
    mother[2] = ""
    mother[4] = mo_sl
    mother[5] = _normalize_sem(mo_se)
    mother[6] = None
    ha[3] = ha_sy
    ha[2] = ha_pr
    ha[4] = ha_sl
    ha[5] = ha_se
    na[3] = na_sy
    na[2] = na_pr
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [na, ha]

    base[head_idx] = mother
    del base[nonhead_idx]
    return base, state.newnum


def _execute_japanese2_p_merge(
    *,
    state: DerivationState,
    base: list[Any],
    left: int,
    right: int,
) -> tuple[list[Any], int]:
    head_idx = left
    nonhead_idx = right
    hb = deepcopy(base[head_idx])
    nb = deepcopy(base[nonhead_idx])
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)

    hb_sy = [str(value) for value in hb[3] if str(value) != ""]
    nb_sy = [str(value) for value in nb[3] if str(value) != ""]
    mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="P-Merge",
        grammar_id=state.grammar_id,
    )
    mo_sl, ha_sl, na_sl = _process_sl_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        rule_name="P-Merge",
    )
    mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
        hb=hb,
        nb=nb,
        hb_sy=hb_sy,
        nb_sy=nb_sy,
        rule_name="P-Merge",
        na_pr=na_pr,
    )
    nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
        hb_id=str(hb[0]),
        nb_id=str(nb[0]),
        mo_se=mo_se,
        nb_sy=nb_sy,
        na_se=na_se,
    )
    hb[3] = hb_sy
    nb[3] = nb_sy
    mo_sy, ha_sy, na_sy = _process_sy_imi03(
        hb=hb,
        nb=nb,
        rule_name="P-Merge",
        grammar_id=state.grammar_id,
        head_index=head_idx,
        nonhead_index=nonhead_idx,
        left=left,
        right=right,
        both_mode=True,
    )
    na_sy = [
        value
        for value in na_sy
        if value not in {"1,5,P-Merge", "1,5,P-Merge,"}
    ]

    mother[3] = mo_sy
    mother[2] = mo_pr
    mother[4] = mo_sl
    mother[5] = mo_se
    mother[6] = None
    ha[3] = ha_sy
    ha[2] = ha_pr
    ha[4] = ha_sl
    ha[5] = ha_se
    na[3] = na_sy
    na[2] = na_pr
    na[4] = na_sl
    na[5] = na_se
    mother[7] = [ha, na]

    base[head_idx] = mother
    del base[nonhead_idx]
    return base, state.newnum


def _update_layer_in_value(value: str, delta: int) -> str:
    if not isinstance(value, str):
        return value

    def repl(match):
        prefix = match.group(1)
        layer = int(match.group(2))
        return f"{prefix}{layer + delta}"

    import re

    return re.sub(r"(x\d+-)(-?\d+)", repl, value)


def _adjust_layer_like_perl(value: str, delta: int) -> str:
    parts = str(value).split("-")
    prefix = parts[0] if len(parts) > 0 else str(value)
    if len(parts) > 1 and parts[1] != "":
        try:
            layer = int(parts[1])
        except ValueError:
            layer = 0
    else:
        layer = 0
    return f"{prefix}-{layer + delta}"


def _increment_layers_in_subtree(node: Any, delta: int) -> Any:
    if isinstance(node, str):
        return _update_layer_in_value(node, delta)
    if isinstance(node, list):
        return [_increment_layers_in_subtree(item, delta) for item in node]
    return node


def _find_subtree_path_by_id(node: Any, target_id: str) -> list[int] | None:
    if not isinstance(node, list) or len(node) < 8:
        return None
    if str(node[0]) == target_id:
        return []
    wo = node[7]
    if not isinstance(wo, list):
        return None
    for idx, child in enumerate(wo):
        if child == "zero":
            continue
        child_path = _find_subtree_path_by_id(child, target_id)
        if child_path is not None:
            return [7, idx] + child_path
    return None


def _get_by_path(node: Any, path: list[int]) -> Any:
    cur = node
    for key in path:
        cur = cur[key]
    return cur


def _set_by_path(node: Any, path: list[int], value: Any) -> None:
    cur = node
    for key in path[:-1]:
        cur = cur[key]
    cur[path[-1]] = value


def _single_right_headed_merge(
    *,
    state: DerivationState,
    hb: list[Any],
    nb: list[Any],
    rule_name: str,
    head_index: int,
    nonhead_index: int,
    left: int,
    right: int,
    append_relation_semantic: bool = False,
) -> tuple[list[Any], int]:
    mother = deepcopy(hb)
    ha = deepcopy(hb)
    na = deepcopy(nb)
    newnum = state.newnum

    if _uses_imi_feature_engine(state.grammar_id):
        hb_sy = [str(value) for value in hb[3] if str(value) != ""]
        nb_sy = [str(value) for value in nb[3] if str(value) != ""]
        mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
            hb=hb,
            nb=nb,
            hb_sy=hb_sy,
            nb_sy=nb_sy,
            rule_name=rule_name,
            grammar_id=state.grammar_id,
        )
        mo_sl, ha_sl, na_sl = _process_sl_imi03(
            hb=hb,
            nb=nb,
            hb_sy=hb_sy,
            rule_name=rule_name,
        )
        mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
            hb=hb,
            nb=nb,
            hb_sy=hb_sy,
            nb_sy=nb_sy,
            rule_name=rule_name,
            na_pr=na_pr,
        )
        nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
            hb_id=str(hb[0]),
            nb_id=str(nb[0]),
            mo_se=mo_se,
            nb_sy=nb_sy,
            na_se=na_se,
        )
        hb[3] = hb_sy
        nb[3] = nb_sy
        mo_sy, ha_sy, na_sy = _process_sy_imi03(
            hb=hb,
            nb=nb,
            rule_name=rule_name,
            grammar_id=state.grammar_id,
            head_index=head_index,
            nonhead_index=nonhead_index,
            left=left,
            right=right,
        )
        if append_relation_semantic:
            mo_se, newnum = _append_merge_relation_semantic(
                mo_se=mo_se,
                mo_sl=mo_sl,
                na_sl=na_sl,
                nb_id=str(nb[0]),
                nb_sl=str(nb[4]),
                hb_sl=str(hb[4]),
                newnum=state.newnum,
                rule_name=rule_name,
                rule_version="01",
            )
        mother[3] = mo_sy
        mother[2] = mo_pr
        mother[4] = mo_sl
        mother[5] = mo_se
        mother[6] = None
        ha[3] = ha_sy
        ha[2] = ha_pr
        ha[4] = ha_sl
        ha[5] = ha_se
        na[3] = na_sy
        na[2] = na_pr
        na[4] = na_sl
        na[5] = na_se

    mother[7] = [na, ha]
    return mother, newnum


def _to_perl_pickup_payload_item(item: Any) -> Any:
    if not isinstance(item, list) or len(item) < 8:
        return item
    out = deepcopy(item)
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
                converted.append(_to_perl_pickup_payload_item(child))
        out[7] = converted
    return out


def _from_perl_pickup_payload_item(item: Any) -> Any:
    if not isinstance(item, list) or len(item) < 8:
        return item
    out = deepcopy(item)
    if isinstance(out[2], list) and len(out[2]) > 0 and out[2][0] is None:
        out[2] = out[2][1:]
    if isinstance(out[3], list) and len(out[3]) > 0 and out[3][0] is None:
        out[3] = out[3][1:]
    if isinstance(out[5], list) and len(out[5]) > 0 and out[5][0] is None:
        out[5] = out[5][1:]
    if isinstance(out[7], list):
        converted = []
        for child in out[7]:
            if child == "zero":
                converted.append(child)
            else:
                converted.append(_from_perl_pickup_payload_item(child))
        out[7] = converted
    return out


def execute_single_merge(
    state: DerivationState,
    rule_name: str,
    check: int,
) -> DerivationState:
    if check < 1 or check > state.basenum:
        raise ValueError(f"check index out of range: {check}")
    base = deepcopy(state.base)
    newnum = state.newnum

    if rule_name == "Partitioning":
        hb = deepcopy(base[check])
        if not isinstance(hb, list) or len(hb) < 8:
            raise ValueError("invalid base item for Partitioning")

        hb_sy = [str(value) for value in hb[3] if str(value) != ""]
        tgp = ""
        for idx, feature in enumerate(hb_sy):
            parts = _split_feature(feature) if _is_uninterpretable_feature(feature) else feature.split(",")
            if len(parts) > 1 and parts[1] == "56":
                tgp = parts[2] if len(parts) > 2 else ""
                hb_sy[idx] = ""
        hb[3] = _normalize_sy(hb_sy)

        tgpp = ""
        hb_pr_raw = hb[2] if isinstance(hb[2], list) else []
        hb_pr = [[]] + deepcopy(hb_pr_raw)
        for row in hb_pr:
            if not isinstance(row, list) or len(row) < 3:
                continue
            if str(row[0]) != tgp:
                continue
            tgpp = str(row[2])
            if tgpp != str(hb[0]):
                row[2] = _adjust_layer_like_perl(str(row[2]), +1)
            else:
                row[1] = _adjust_layer_like_perl(str(row[1]), -1)
                row[0] = _adjust_layer_like_perl(str(row[0]), -1)
        hb[2] = hb_pr

        if tgpp != "":
            path = _find_subtree_path_by_id(hb, tgpp)
            if path is not None:
                domain_subtree = _get_by_path(hb, path)
                updated_subtree = _increment_layers_in_subtree(domain_subtree, +1)
                _set_by_path(hb, path, updated_subtree)

        base[check] = hb
    elif rule_name == "zero-Merge":
        hb = deepcopy(base[check])
        if not isinstance(hb, list) or len(hb) < 8:
            raise ValueError("invalid base item for zero-Merge")

        cond_s = ""
        zero_category = ""
        for sem in hb[5] if isinstance(hb[5], list) else []:
            parts = _split_feature(str(sem))
            if len(parts) > 1 and parts[1] in {"25", "29"}:
                cond_s = parts[2] if len(parts) > 2 else ""
                if parts[1] == "29":
                    zero_category = parts[2] if len(parts) > 2 else ""
                break
            if len(parts) > 1 and parts[1] == "33":
                label = parts[2] if len(parts) > 2 else ""
                cond_s = f"3,11,{label}"
                break

        cond_p = ""
        for triple in hb[2] if isinstance(hb[2], list) else []:
            if not isinstance(triple, list) or len(triple) < 3:
                continue
            parts1 = _split_feature(str(triple[1]))
            parts2 = _split_feature(str(triple[2]))
            if len(parts1) > 1 and parts1[1] in {"25", "29"}:
                cond_p = parts1[2] if len(parts1) > 2 else ""
                break
            if len(parts2) > 1 and parts2[1] in {"25", "29"}:
                cond_p = parts2[2] if len(parts2) > 2 else ""
                break

        default_zero_category = "N" if state.grammar_id in {"imi02", "imi03"} else "NP"
        nb_id = f"x{newnum}-1"
        nb = [
            nb_id,
            zero_category if zero_category != "" else default_zero_category,
            [],
            _normalize_sy([cond_s, cond_p]),
            nb_id,
            [],
            "φ",
            None,
        ]
        mother, _ = _single_right_headed_merge(
            state=state,
            hb=hb,
            nb=nb,
            rule_name="zero-Merge",
            head_index=check,
            nonhead_index=state.basenum + 1,
            left=0,
            right=0,
        )
        base[check] = mother
        newnum += 1
    elif rule_name == "Pickup":
        mob = deepcopy(base[check])
        if not isinstance(mob, list) or len(mob) < 8:
            raise ValueError("invalid base item for Pickup")
        wo = mob[7]
        if not isinstance(wo, list) or len(wo) < 1 or wo[0] == "zero":
            raise ValueError("Pickup requires a non-zero left daughter")
        nb = deepcopy(wo[0])
        if not isinstance(nb, list):
            raise ValueError("Pickup payload must be a list item")
        pickup_json = json.dumps(
            _to_perl_pickup_payload_item(nb),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        sy = [str(value) for value in mob[3]] if isinstance(mob[3], list) else []
        sy.append(f"3,106,{pickup_json}")
        mob[3] = sy
        mob[7][0] = "zero"
        base[check] = mob
    elif rule_name == "Landing":
        hb = deepcopy(base[check])
        if not isinstance(hb, list) or len(hb) < 8:
            raise ValueError("invalid base item for Landing")
        hb_sy = [str(value) for value in hb[3]] if isinstance(hb[3], list) else []
        payload = None
        for idx, feature in enumerate(hb_sy):
            if "3,106" in feature:
                payload = feature[6:]
                del hb_sy[idx]
                break
        if payload is None:
            raise ValueError("Landing requires pickup marker 3,106")
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid pickup payload for Landing: {exc}") from exc
        if not isinstance(decoded, list) or len(decoded) < 8:
            raise ValueError("Landing payload is not a valid lexical item")
        nb = _from_perl_pickup_payload_item(decoded)
        nb_sy = [str(value) for value in nb[3]] if isinstance(nb[3], list) else []
        nb[3] = [value for value in nb_sy if "107" not in value and value != ""]
        hb[3] = _normalize_sy(hb_sy)
        mother, _ = _single_right_headed_merge(
            state=state,
            hb=hb,
            nb=nb,
            rule_name="Landing",
            head_index=check,
            nonhead_index=state.basenum + 1,
            left=0,
            right=0,
        )
        base[check] = mother
    else:
        raise ValueError(f"Unsupported single merge rule: {rule_name}")

    return DerivationState(
        grammar_id=state.grammar_id,
        memo=state.memo,
        newnum=newnum,
        basenum=state.basenum,
        history=_build_history(state=state, rule_name=rule_name, check=check),
        base=base,
    )


def execute_double_merge(
    state: DerivationState,
    rule_name: str,
    left: int,
    right: int,
    rule_version: str = "03",
) -> DerivationState:
    _validate_double_indices(state=state, left=left, right=right)
    base = deepcopy(state.base)
    newnum = state.newnum

    if rule_name == "RH-Merge":
        head_idx = right
        nonhead_idx = left
        hb = deepcopy(base[head_idx])
        nb = deepcopy(base[nonhead_idx])
        mother = deepcopy(hb)
        ha = deepcopy(hb)
        na = deepcopy(nb)
        if _uses_imi_feature_engine(state.grammar_id):
            hb_sy = [str(value) for value in hb[3] if str(value) != ""]
            nb_sy = [str(value) for value in nb[3] if str(value) != ""]
            mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
            )
            mo_sl, ha_sl, na_sl = _process_sl_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                rule_name=rule_name,
            )
            mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                na_pr=na_pr,
            )
            nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
                hb_id=str(hb[0]),
                nb_id=str(nb[0]),
                mo_se=mo_se,
                nb_sy=nb_sy,
                na_se=na_se,
            )
            hb[3] = hb_sy
            nb[3] = nb_sy
            mo_sy, ha_sy, na_sy = _process_sy_imi03(
                hb=hb,
                nb=nb,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
                head_index=head_idx,
                nonhead_index=nonhead_idx,
                left=left,
                right=right,
            )
            mo_se, newnum = _append_merge_relation_semantic(
                mo_se=mo_se,
                mo_sl=mo_sl,
                na_sl=na_sl,
                nb_id=str(nb[0]),
                nb_sl=str(nb[4]),
                hb_sl=str(hb[4]),
                newnum=state.newnum,
                rule_name=rule_name,
                rule_version=rule_version,
            )
            mother[3] = mo_sy
            mother[2] = mo_pr
            mother[4] = mo_sl
            mother[5] = mo_se
            mother[6] = None
            ha[3] = ha_sy
            ha[2] = ha_pr
            ha[4] = ha_sl
            ha[5] = ha_se
            na[3] = na_sy
            na[2] = na_pr
            na[4] = na_sl
            na[5] = na_se
        mother[7] = [na, ha]
        base[head_idx] = mother
        del base[nonhead_idx]
    elif rule_name == "LH-Merge":
        head_idx = left
        nonhead_idx = right
        hb = deepcopy(base[head_idx])
        nb = deepcopy(base[nonhead_idx])
        mother = deepcopy(hb)
        ha = deepcopy(hb)
        na = deepcopy(nb)
        if _uses_imi_feature_engine(state.grammar_id):
            hb_sy = [str(value) for value in hb[3] if str(value) != ""]
            nb_sy = [str(value) for value in nb[3] if str(value) != ""]
            mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
            )
            mo_sl, ha_sl, na_sl = _process_sl_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                rule_name=rule_name,
            )
            mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                na_pr=na_pr,
            )
            nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
                hb_id=str(hb[0]),
                nb_id=str(nb[0]),
                mo_se=mo_se,
                nb_sy=nb_sy,
                na_se=na_se,
            )
            hb[3] = hb_sy
            nb[3] = nb_sy
            mo_sy, ha_sy, na_sy = _process_sy_imi03(
                hb=hb,
                nb=nb,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
                head_index=head_idx,
                nonhead_index=nonhead_idx,
                left=left,
                right=right,
            )
            mo_se, newnum = _append_merge_relation_semantic(
                mo_se=mo_se,
                mo_sl=mo_sl,
                na_sl=na_sl,
                nb_id=str(nb[0]),
                nb_sl=str(nb[4]),
                hb_sl=str(hb[4]),
                newnum=state.newnum,
                rule_name=rule_name,
                rule_version=rule_version,
            )
            mother[3] = mo_sy
            mother[2] = mo_pr
            mother[4] = mo_sl
            mother[5] = mo_se
            mother[6] = None
            ha[3] = ha_sy
            ha[2] = ha_pr
            ha[4] = ha_sl
            ha[5] = ha_se
            na[3] = na_sy
            na[2] = na_pr
            na[4] = na_sl
            na[5] = na_se
        mother[7] = [ha, na]
        base[head_idx] = mother
        del base[nonhead_idx]
    elif rule_name == "J-Merge":
        head_idx = left
        nonhead_idx = right
        hb = deepcopy(base[head_idx])
        nb = deepcopy(base[nonhead_idx])
        mother = deepcopy(hb)
        ha = deepcopy(hb)
        na = deepcopy(nb)
        if _uses_imi_feature_engine(state.grammar_id):
            hb_sy = [str(value) for value in hb[3] if str(value) != ""]
            nb_sy = [str(value) for value in nb[3] if str(value) != ""]
            mo_pr, ha_pr, na_pr, hb_sy, nb_sy = _process_pr_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
            )
            mo_sl, ha_sl, na_sl = _process_sl_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                rule_name=rule_name,
            )
            mo_se, ha_se, na_se, hb_sy, nb_sy = _process_se_imi03(
                hb=hb,
                nb=nb,
                hb_sy=hb_sy,
                nb_sy=nb_sy,
                rule_name=rule_name,
                na_pr=na_pr,
            )
            nb_sy, na_se = _apply_kind_feature_101_on_nonhead(
                hb_id=str(hb[0]),
                nb_id=str(nb[0]),
                mo_se=mo_se,
                nb_sy=nb_sy,
                na_se=na_se,
            )
            hb[3] = hb_sy
            nb[3] = nb_sy
            mo_sy, ha_sy, na_sy = _process_sy_imi03(
                hb=hb,
                nb=nb,
                rule_name=rule_name,
                grammar_id=state.grammar_id,
                head_index=head_idx,
                nonhead_index=nonhead_idx,
                left=left,
                right=right,
                both_mode=True,
            )
            na_sy = [
                value
                for value in na_sy
                if value not in {"1,5,J-Merge", "1,5,J-Merge,"}
            ]
            mother[1] = "NP"
            mother[3] = mo_sy
            mother[2] = mo_pr
            mother[4] = mo_sl
            mother[5] = mo_se
            mother[6] = None
            ha[3] = ha_sy
            ha[2] = ha_pr
            ha[4] = ha_sl
            ha[5] = ha_se
            na[3] = na_sy
            na[2] = na_pr
            na[4] = na_sl
            na[5] = na_se
        mother[7] = [ha, na]
        base[head_idx] = mother
        del base[nonhead_idx]
    elif rule_name in {"sase1", "sase2", "rare1", "rare2"}:
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_special_left_headed(
            state=state,
            base=base,
            left=left,
            right=right,
            rule_name=rule_name,
        )
    elif rule_name == "property-Merge":
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_property_merge(
            state=state,
            base=base,
            left=left,
            right=right,
        )
    elif rule_name == "rel-Merge":
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_rel_merge(
            state=state,
            base=base,
            left=left,
            right=right,
        )
    elif rule_name == "property-no":
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_property_no(
            state=state,
            base=base,
            left=left,
            right=right,
        )
    elif rule_name == "property-da":
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_property_da(
            state=state,
            base=base,
            left=left,
            right=right,
        )
    elif rule_name == "P-Merge":
        if state.grammar_id != "japanese2":
            raise ValueError(f"{rule_name} is not supported for grammar: {state.grammar_id}")
        base, newnum = _execute_japanese2_p_merge(
            state=state,
            base=base,
            left=left,
            right=right,
        )
    else:
        raise ValueError(f"Unsupported double merge rule: {rule_name}")

    basenum = state.basenum - 1
    return DerivationState(
        grammar_id=state.grammar_id,
        memo=state.memo,
        newnum=newnum,
        basenum=basenum,
        history=_build_history(state=state, rule_name=rule_name, left=left, right=right),
        base=base,
    )
