from __future__ import annotations

from typing import Any, Literal

from domain.common.types import DerivationState

TreeMode = Literal["tree", "tree_cat"]


def _is_branch(wo_value: Any) -> bool:
    return isinstance(wo_value, list)


def _ensure_item(item: Any) -> list[Any]:
    if not isinstance(item, list) or len(item) < 8:
        raise ValueError("Invalid base item for tree rendering")
    return item


def _append_tree_node(
    tree: list[dict[str, Any]],
    treerel: dict[int, list[int]],
    node_id: int,
    level: int,
    head_id: str,
    label: str,
    flag: str = "",
) -> None:
    tree.append(
        {
            "id": node_id,
            "edge": "",
            "flag": flag,
            "label": label,
            "level": level,
            "head_id": head_id,
        }
    )
    treerel.setdefault(level, []).append(node_id)


def _build_tree_nodes_recursive(
    item: list[Any],
    mode: TreeMode,
    tree: list[dict[str, Any]],
    treerel: dict[int, list[int]],
    level: int,
    counter: list[int],
) -> None:
    current_id = counter[0]
    lexical_id = str(item[0])
    category = str(item[1])
    phono = str(item[6])
    wo = item[7]

    if mode == "tree":
        label = lexical_id if _is_branch(wo) else f"{lexical_id}&lt;br&gt;{phono}"
    else:
        label = category if _is_branch(wo) else f"{category}&lt;br&gt;{phono}"
    _append_tree_node(
        tree=tree,
        treerel=treerel,
        node_id=current_id,
        level=level,
        head_id=lexical_id,
        label=label,
    )

    if not _is_branch(wo):
        return

    for child in wo:
        counter[0] += 1
        child_id = counter[0]
        if child == "zero":
            trace_label = "[\t]" if mode == "tree" else "trace"
            _append_tree_node(
                tree=tree,
                treerel=treerel,
                node_id=child_id,
                level=level + 1,
                head_id="",
                label=trace_label,
                flag="0",
            )
            continue
        child_item = _ensure_item(child)
        _build_tree_nodes_recursive(
            item=child_item,
            mode=mode,
            tree=tree,
            treerel=treerel,
            level=level + 1,
            counter=counter,
        )


def build_treedrawer_csv_lines(
    state: DerivationState,
    mode: TreeMode,
) -> list[str]:
    if mode not in ("tree", "tree_cat"):
        raise ValueError(f"Unsupported tree mode: {mode}")

    tree: list[dict[str, Any]] = []
    treerel: dict[int, list[int]] = {}
    counter = [0]

    for index in range(1, state.basenum + 1):
        item = _ensure_item(state.base[index])
        root_id = counter[0]
        _build_tree_nodes_recursive(
            item=item,
            mode=mode,
            tree=tree,
            treerel=treerel,
            level=0,
            counter=counter,
        )
        # Perl互換: top-levelノードのみ初期flagは "R"。
        tree[root_id]["flag"] = "R"
        counter[0] += 1

    for idx in range(len(tree)):
        if idx + 1 >= len(tree):
            continue
        current_level = tree[idx]["level"]
        next_level = tree[idx + 1]["level"]
        if next_level != current_level + 1:
            continue
        level_nodes = treerel.get(current_level + 1, [])
        if len(level_nodes) < 2:
            continue
        left = level_nodes.pop(0)
        right = level_nodes.pop(0)
        tree[idx]["edge"] = f"{left} {right}"

        parent_head_id = tree[idx]["head_id"]
        left_head_id = tree[left]["head_id"]
        right_head_id = tree[right]["head_id"]
        if parent_head_id != "" and parent_head_id in left_head_id:
            tree[left]["flag"] = "1"
            tree[right]["flag"] = "0"
        if parent_head_id != "" and parent_head_id in right_head_id:
            tree[right]["flag"] = "1"
            tree[left]["flag"] = "0"

    return [
        f"{node['id']},{node['edge']},{node['flag']},{node['label']}" for node in tree
    ]
