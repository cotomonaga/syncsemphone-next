from __future__ import annotations

from pathlib import Path
import re

from domain.common.types import DerivationState, RuleCandidate
from domain.grammar.profiles import get_grammar_profile, resolve_rule_versions
from domain.grammar.rule_catalog import get_rule_number_by_name


def _rh_merge_applicable(right_category: str, version: str) -> bool:
    if version == "03":
        return True
    if version == "04":
        return right_category != "T"
    if version == "01":
        return True
    raise ValueError(f"Unsupported RH-Merge version: {version}")


def _lh_merge_applicable(right_category: str, version: str) -> bool:
    if version == "03":
        return True
    if version == "04":
        return right_category == "T"
    if version == "01":
        return right_category in {"T", "J"}
    raise ValueError(f"Unsupported LH-Merge version: {version}")


def _item_category(state: DerivationState, index: int) -> str:
    if index < 1 or index > state.basenum:
        raise ValueError(f"index out of range: {index} (basenum={state.basenum})")
    item = state.base[index]
    if not isinstance(item, list) or len(item) < 2:
        raise ValueError(f"Invalid base item at index={index}")
    return str(item[1])


def _item_slot(state: DerivationState, index: int, slot: int) -> str:
    if index < 1 or index > state.basenum:
        raise ValueError(f"index out of range: {index} (basenum={state.basenum})")
    item = state.base[index]
    if not isinstance(item, list) or len(item) <= slot:
        return ""
    return str(item[slot])


def _is_uninterpretable_slot(value: str) -> bool:
    parts = [part.strip() for part in str(value).split(",")]
    return len(parts) > 1 and parts[1].isdigit()


def _feature_number_from_value(value: str) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "" or raw == "zero":
        return None
    if ":" in raw:
        raw = raw.split(":", 1)[1]
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) > 1 and parts[1].isdigit():
        return parts[1]
    return None


def _item_semantics(state: DerivationState, index: int) -> list[str]:
    if index < 1 or index > state.basenum:
        return []
    item = state.base[index]
    if not isinstance(item, list) or len(item) < 6:
        return []
    sem = item[5] if isinstance(item[5], list) else []
    return [str(value) for value in sem if str(value) != ""]


def _item_syntax_features(state: DerivationState, index: int) -> list[str]:
    if index < 1 or index > state.basenum:
        return []
    item = state.base[index]
    if not isinstance(item, list) or len(item) < 4:
        return []
    sy = item[3] if isinstance(item[3], list) else []
    return [str(value) for value in sy if str(value) != ""]


def _zero_merge_applicable(state: DerivationState, check: int) -> bool:
    if check < 1 or check > state.basenum:
        return False
    item = state.base[check]
    if not isinstance(item, list) or len(item) < 6:
        return False

    target_numbers = {"24", "25", "26", "29", "33"}

    sem = item[5] if isinstance(item[5], list) else []
    for value in sem:
        number = _feature_number_from_value(str(value))
        if number in target_numbers:
            return True

    pred = item[2] if isinstance(item[2], list) else []
    for triple in pred:
        if not isinstance(triple, list) or len(triple) < 3:
            continue
        subj_number = _feature_number_from_value(str(triple[1]))
        pred_number = _feature_number_from_value(str(triple[2]))
        if subj_number in target_numbers or pred_number in target_numbers:
            return True
    return False


def _sase1_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "V":
        return False
    if _item_slot(state, right, 6) != "-sase-":
        return False
    return any("Agent" in semantic for semantic in _item_semantics(state, left))


def _sase2_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "V":
        return False
    if _item_slot(state, right, 6) != "-sase-":
        return False
    for semantic in _item_semantics(state, left):
        if ("Theme" in semantic and "ga" in semantic) or (
            "Affectee" in semantic and "ga" in semantic
        ):
            return True
    return False


def _rare1_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "V":
        return False
    if _item_slot(state, right, 6) != "-rare-":
        return False
    if _item_slot(state, right, 4) == "zero":
        return False
    return any("ga" in semantic for semantic in _item_semantics(state, left))


def _rare2_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "V":
        return False
    if _item_slot(state, right, 6) != "-rare-":
        return False
    if _item_slot(state, right, 4) != "zero":
        return False
    semantics = _item_semantics(state, left)
    has_agent_ga = any("Agent:2,25,ga" in semantic for semantic in semantics)
    has_wo = any("wo" in semantic for semantic in semantics)
    return has_agent_ga and has_wo


def _property_merge_applicable(state: DerivationState, left: int, right: int) -> bool:
    left_sl = _item_slot(state, left, 4)
    right_sl = _item_slot(state, right, 4)
    return _is_uninterpretable_slot(left_sl) and _is_uninterpretable_slot(right_sl)


def _rel_merge_applicable(state: DerivationState, left: int, right: int) -> bool:
    return _item_category(state, left) == "T" and _item_category(state, right) == "N"


def _property_no_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "N":
        return False
    if _is_uninterpretable_slot(_item_slot(state, left, 4)):
        return False
    right_sy = _item_syntax_features(state, right)
    has_plus_n = any("1,1,N" in feature for feature in right_sy)
    has_no = any("2,3,N" in feature for feature in right_sy)
    return has_plus_n and has_no


def _property_da_applicable(state: DerivationState, left: int, right: int) -> bool:
    if _item_category(state, left) != "N":
        return False
    if _item_category(state, right) != "T":
        return False
    if _is_uninterpretable_slot(_item_slot(state, left, 4)):
        return False
    right_sy = _item_syntax_features(state, right)
    return any(feature == "da" for feature in right_sy)


def _p_merge_applicable(state: DerivationState, right: int) -> bool:
    return _item_category(state, right) == "P"


def _partitioning_applicable(state: DerivationState, check: int) -> bool:
    for feature in _item_syntax_features(state, check):
        parts = feature.split(",")
        if len(parts) > 1 and parts[1] == "56":
            return True
    return False


def _pickup_applicable(state: DerivationState, check: int, side: int) -> bool:
    if check < 1 or check > state.basenum:
        return False
    item = state.base[check]
    if not isinstance(item, list) or len(item) < 8:
        return False
    wo = item[7]
    if not isinstance(wo, list) or side < 0 or side >= len(wo):
        return False
    daughter = wo[side]
    if daughter == "zero" or not isinstance(daughter, list) or len(daughter) < 4:
        return False
    daughter_sy = daughter[3] if isinstance(daughter[3], list) else []
    has_remaining_feature = any(
        re.search(r",[0-9]", str(value)) is not None for value in daughter_sy
    )
    if not has_remaining_feature:
        return False
    return not any("3,106" in feature for feature in _item_syntax_features(state, check))


def _landing_applicable(state: DerivationState, check: int) -> bool:
    return any("3,106" in feature for feature in _item_syntax_features(state, check))


def list_merge_candidates(
    state: DerivationState,
    left: int,
    right: int,
    legacy_root: Path,
    rh_merge_version: str | None = None,
    lh_merge_version: str | None = None,
) -> list[RuleCandidate]:
    candidates: list[RuleCandidate] = []

    profile = get_grammar_profile(state.grammar_id)
    profile = resolve_rule_versions(profile=profile, legacy_root=legacy_root)
    rh_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="RH-Merge",
        legacy_root=legacy_root,
    )
    lh_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="LH-Merge",
        legacy_root=legacy_root,
    )
    zero_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="zero-Merge",
        legacy_root=legacy_root,
    )
    jmerge_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="J-Merge",
        legacy_root=legacy_root,
    )
    sase1_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="sase1",
        legacy_root=legacy_root,
    )
    sase2_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="sase2",
        legacy_root=legacy_root,
    )
    rare2_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="rare2",
        legacy_root=legacy_root,
    )
    rare1_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="rare1",
        legacy_root=legacy_root,
    )
    property_merge_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="property-Merge",
        legacy_root=legacy_root,
    )
    rel_merge_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="rel-Merge",
        legacy_root=legacy_root,
    )
    property_no_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="property-no",
        legacy_root=legacy_root,
    )
    property_da_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="property-da",
        legacy_root=legacy_root,
    )
    p_merge_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="P-Merge",
        legacy_root=legacy_root,
    )
    partitioning_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="Partitioning",
        legacy_root=legacy_root,
    )
    pickup_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="Pickup",
        legacy_root=legacy_root,
    )
    landing_rule_number = get_rule_number_by_name(
        grammar_id=state.grammar_id,
        rule_name="Landing",
        legacy_root=legacy_root,
    )
    rh_version = rh_merge_version or profile.rh_merge_version
    lh_version = lh_merge_version or profile.lh_merge_version

    if left != right:
        left_category = _item_category(state=state, index=left)
        right_category = _item_category(state=state, index=right)
        if sase1_rule_number is not None and _sase1_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=sase1_rule_number,
                    rule_name="sase1",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if sase2_rule_number is not None and _sase2_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=sase2_rule_number,
                    rule_name="sase2",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if rare2_rule_number is not None and _rare2_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=rare2_rule_number,
                    rule_name="rare2",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if rare1_rule_number is not None and _rare1_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=rare1_rule_number,
                    rule_name="rare1",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if property_merge_rule_number is not None and _property_merge_applicable(
            state, left, right
        ):
            candidates.append(
                RuleCandidate(
                    rule_number=property_merge_rule_number,
                    rule_name="property-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if rel_merge_rule_number is not None and _rel_merge_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=rel_merge_rule_number,
                    rule_name="rel-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if property_no_rule_number is not None and _property_no_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=property_no_rule_number,
                    rule_name="property-no",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if property_da_rule_number is not None and _property_da_applicable(state, left, right):
            candidates.append(
                RuleCandidate(
                    rule_number=property_da_rule_number,
                    rule_name="property-da",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if p_merge_rule_number is not None and _p_merge_applicable(state, right):
            candidates.append(
                RuleCandidate(
                    rule_number=p_merge_rule_number,
                    rule_name="P-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        rh_applicable = rh_rule_number is not None and _rh_merge_applicable(
            right_category=right_category, version=rh_version
        )
        if rh_applicable and rh_version == "01":
            left_sl = _item_slot(state=state, index=left, slot=4)
            right_sl = _item_slot(state=state, index=right, slot=4)
            # Perl RH-Merge_01:
            # - block when left=N and right=J (J-Merge priority)
            # - block when both id-slot are still feature formulas (property-Merge case)
            if (left_category == "N" and right_category == "J") or (
                _is_uninterpretable_slot(left_sl) and _is_uninterpretable_slot(right_sl)
            ):
                rh_applicable = False

        if rh_applicable:
            candidates.append(
                RuleCandidate(
                    rule_number=rh_rule_number,
                    rule_name="RH-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if (
            jmerge_rule_number is not None
            and left_category == "N"
            and right_category == "J"
        ):
            candidates.append(
                RuleCandidate(
                    rule_number=jmerge_rule_number,
                    rule_name="J-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )
        if lh_rule_number is not None and _lh_merge_applicable(
            right_category=right_category, version=lh_version
        ):
            candidates.append(
                RuleCandidate(
                    rule_number=lh_rule_number,
                    rule_name="LH-Merge",
                    rule_kind="double",
                    left=left,
                    right=right,
                )
            )

    if profile.has_zero_merge and zero_rule_number is not None:
        if _zero_merge_applicable(state=state, check=left):
            candidates.append(
                RuleCandidate(
                    rule_number=zero_rule_number,
                    rule_name="zero-Merge",
                    rule_kind="single",
                    check=left,
                )
            )
        if _zero_merge_applicable(state=state, check=right):
            candidates.append(
                RuleCandidate(
                    rule_number=zero_rule_number,
                    rule_name="zero-Merge",
                    rule_kind="single",
                    check=right,
                )
            )
    if partitioning_rule_number is not None:
        if _partitioning_applicable(state=state, check=left):
            candidates.append(
                RuleCandidate(
                    rule_number=partitioning_rule_number,
                    rule_name="Partitioning",
                    rule_kind="single",
                    check=left,
                )
            )
        if _partitioning_applicable(state=state, check=right):
            candidates.append(
                RuleCandidate(
                    rule_number=partitioning_rule_number,
                    rule_name="Partitioning",
                    rule_kind="single",
                    check=right,
                )
            )
    if pickup_rule_number is not None:
        if _pickup_applicable(state=state, check=left, side=0):
            candidates.append(
                RuleCandidate(
                    rule_number=pickup_rule_number,
                    rule_name="Pickup",
                    rule_kind="single",
                    check=left,
                )
            )
        if _pickup_applicable(state=state, check=right, side=1):
            candidates.append(
                RuleCandidate(
                    rule_number=pickup_rule_number,
                    rule_name="Pickup",
                    rule_kind="single",
                    check=right,
                )
            )
    if landing_rule_number is not None:
        if _landing_applicable(state=state, check=left):
            candidates.append(
                RuleCandidate(
                    rule_number=landing_rule_number,
                    rule_name="Landing",
                    rule_kind="single",
                    check=left,
                )
            )
        if _landing_applicable(state=state, check=right):
            candidates.append(
                RuleCandidate(
                    rule_number=landing_rule_number,
                    rule_name="Landing",
                    rule_kind="single",
                    check=right,
                )
            )
    return sorted(candidates, key=lambda row: row.rule_number)
