from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from domain.common.types import DerivationState

_IDSLOT_RE = re.compile(r"^x(?P<object>\d+)-(?P<layer>\d+)$")
_BETA_SLOT_RE = re.compile(r"^(?:β|beta)(?P<object>\d+)$")
_BETA_MARKER_RE = re.compile(r"^beta#(?P<object>\d+)#(?P<derived>.+)$")
_DERIVED_COMPLEX_RE = re.compile(
    r"^(?P<attribute>[^()]+)\((?P<host>x\d+-\d+)\)$"
)


@dataclass(frozen=True)
class LFItem:
    lexical_id: str
    category: str
    idslot: str
    syntax_features: list[str]
    semantics: list[str]
    predication: list[list[str]]


@dataclass(frozen=True)
class SRLayer:
    object_id: int
    layer: int
    kind: str
    properties: list[str]


def _node_wo(node: list[Any]) -> Any:
    # canonical format: [..., ph, wo]
    if len(node) > 7 and isinstance(node[7], list):
        return node[7]
    # Perl show_lf/show_tree互換:
    # 7要素 legacy ノードでは wo(=index 7) が存在しないため再帰しない。
    return None


def _walk_items(item: list[Any]) -> list[list[Any]]:
    nodes = [item]
    wo = _node_wo(item)
    if isinstance(wo, list):
        for child in wo:
            if child == "zero":
                continue
            if isinstance(child, list) and len(child) >= 7:
                nodes.extend(_walk_items(child))
    return nodes


def _parse_object_layer(idslot: str) -> tuple[int, int] | None:
    match = _IDSLOT_RE.match(idslot)
    if not match:
        return None
    return int(match.group("object")), int(match.group("layer"))


def build_lf_items(state: DerivationState) -> list[LFItem]:
    items: list[LFItem] = []
    for index in range(1, state.basenum + 1):
        root = state.base[index]
        if not isinstance(root, list) or len(root) < 6:
            continue
        for node in _walk_items(root):
            # Perl show_lf互換:
            # sl または se が "zero" のノードは LF/SR 登録対象にしない。
            if str(node[4]) == "zero" or str(node[5]) == "zero":
                continue
            lexical_id = str(node[0])
            category = str(node[1])
            idslot = str(node[4])
            sy = node[3] if isinstance(node[3], list) else []
            sem = node[5] if isinstance(node[5], list) else []
            pr = node[2] if isinstance(node[2], list) else []
            items.append(
                LFItem(
                    lexical_id=lexical_id,
                    category=category,
                    idslot=idslot,
                    syntax_features=[
                        str(value) for value in sy if value not in ("", None)
                    ],
                    semantics=[
                        str(value) for value in sem if value not in ("", None)
                    ],
                    predication=[
                        [str(part) for part in triple]
                        for triple in pr
                        if isinstance(triple, list) and len(triple) == 3
                    ],
                )
            )
    return items


def _extract_beta_bindings(items: list[LFItem]) -> dict[int, str]:
    bindings: dict[int, str] = {}
    for item in items:
        for feature in item.syntax_features:
            matched = _BETA_MARKER_RE.match(feature.strip())
            if matched is None:
                continue
            bindings[int(matched.group("object"))] = matched.group("derived")
    return bindings


def _replace_beta_tokens(text: str, bindings: dict[int, str]) -> str:
    replaced = str(text)
    for object_id, derived in bindings.items():
        replaced = replaced.replace(f"β{object_id}", derived)
    return replaced


def _parse_beta_slot(idslot: str) -> int | None:
    matched = _BETA_SLOT_RE.match(idslot.strip())
    if matched is None:
        return None
    return int(matched.group("object"))


def _apply_beta_postprocess(
    slots: dict[tuple[int, int], SRLayer],
    beta_meta: dict[int, str],
) -> None:
    for beta_object_id, derived_complex in beta_meta.items():
        beta_key = (beta_object_id, 1)
        beta_slot = slots.get(beta_key)
        if beta_slot is None:
            continue

        matched = _DERIVED_COMPLEX_RE.match(derived_complex.strip())
        if matched is None:
            slots.pop(beta_key, None)
            continue

        attribute = matched.group("attribute")
        host_slot = _parse_object_layer(matched.group("host"))
        target_slot: tuple[int, int] | None = None
        if host_slot is not None:
            host_layer = slots.get(host_slot)
            if host_layer is not None:
                for prop in host_layer.properties:
                    if ":" not in prop:
                        continue
                    prop_attr, prop_value = prop.split(":", 1)
                    if prop_attr != attribute:
                        continue
                    parsed_target = _parse_object_layer(prop_value.strip())
                    if parsed_target is not None:
                        target_slot = parsed_target
                    break

        if target_slot is not None:
            target_layer = slots.get(target_slot)
            if target_layer is None:
                slots[target_slot] = SRLayer(
                    object_id=target_slot[0],
                    layer=target_slot[1],
                    kind="object",
                    properties=[],
                )
                target_layer = slots[target_slot]
            target_layer.properties.extend(beta_slot.properties)

        # Perl互換: β側の一時オブジェクトは最終SRで消す。
        slots.pop(beta_key, None)


def build_sr_layers(state: DerivationState) -> list[SRLayer]:
    lf_items = build_lf_items(state)
    slots: dict[tuple[int, int], SRLayer] = {}
    beta_bindings = _extract_beta_bindings(lf_items)
    beta_meta: dict[int, str] = {}

    for item in lf_items:
        semantics = [
            _replace_beta_tokens(value, beta_bindings) for value in item.semantics
        ]
        parsed = _parse_object_layer(item.idslot)
        if parsed is not None:
            obj, layer = parsed
            key = (obj, layer)
            if key not in slots:
                slots[key] = SRLayer(
                    object_id=obj,
                    layer=layer,
                    kind="object",
                    properties=[],
                )
            slots[key].properties.extend(semantics)
        else:
            beta_object = _parse_beta_slot(item.idslot)
            if beta_object is not None and beta_object in beta_bindings:
                key = (beta_object, 1)
                if key not in slots:
                    slots[key] = SRLayer(
                        object_id=beta_object,
                        layer=1,
                        kind="object",
                        properties=[],
                    )
                slots[key].properties.extend(semantics)
                beta_meta[beta_object] = beta_bindings[beta_object]

        for pred in item.predication:
            pred_triplet = [_replace_beta_tokens(part, beta_bindings) for part in pred]
            pred_slot = _parse_object_layer(pred_triplet[0])
            if pred_slot is None:
                continue
            pobj, player = pred_slot
            key = (pobj, player)
            slots[key] = SRLayer(
                object_id=pobj,
                layer=player,
                kind="Predication",
                properties=[f"Subject: {pred_triplet[1]}", f"Predicate: {pred_triplet[2]}"],
            )

    _apply_beta_postprocess(slots, beta_meta)
    visible_layers = [row for row in slots.values() if len(row.properties) > 0]
    return sorted(visible_layers, key=lambda row: (row.object_id, row.layer))
