# japanese2 P0 125->204 Explicit Experiment (2026-03-02)

- [確認済み事実] 条件: grammar_id=japanese2, explicit numeration, P0固定, 125->204のみ差し替え
- [確認済み事実] budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10

## Summary

| sentence | P0 unresolved_min | P0(125->204) unresolved_min | delta |
|---|---:|---:|---:|
| S2 | 1 | 1 | 0 |
| S3 | 2 | 1 | -1 |
| S4 | 7 | 6 | -1 |

## Details

### S2: わたあめを食べているひつじがいる
- [確認済み事実] P0 IDs: [265, 23, 266, 267, 19, 271, 125]
- [確認済み事実] P0_swap IDs: [265, 23, 266, 267, 19, 271, 204]
- [確認済み事実] P0 metrics: status=unknown, reason=timeout, actions=10069, depth=10, leaf_min=1
- [確認済み事実] P0 residual totals: {'sy:17': 10}
- [確認済み事実] P0 residual source top: {'sy:17': [{'count': 10, 'item_id': 'x3-1', 'category': 'V', 'phono': '', 'raw': '2,17,N,,,left,nonhead', 'slot_index': '1'}]}
- [確認済み事実] P0_swap metrics: status=unknown, reason=timeout, actions=9921, depth=9, leaf_min=1
- [確認済み事実] P0_swap residual totals: {'sy:17': 10}
- [確認済み事実] P0_swap residual source top: {'sy:17': [{'count': 10, 'item_id': 'x3-1', 'category': 'V', 'phono': '', 'raw': '2,17,N,,,left,nonhead', 'slot_index': '1'}]}
- [確認済み事実] delta: {'best_leaf_unresolved_min_before': 1, 'best_leaf_unresolved_min_after': 1, 'best_leaf_unresolved_min_delta': 0, 'best_leaf_residual_family_totals_delta': {'sy:17': 0}, 'fact_status': '確認済み事実'}

### S3: ひつじと話しているうさぎがいる
- [確認済み事実] P0 IDs: [267, 268, 269, 270, 19, 271, 125]
- [確認済み事実] P0_swap IDs: [267, 268, 269, 270, 19, 271, 204]
- [確認済み事実] P0 metrics: status=unknown, reason=timeout, actions=9586, depth=11, leaf_min=2
- [確認済み事実] P0 residual totals: {'sy:17': 18, 'sy:11': 10, 'se:33': 6, 'sy:1': 2}
- [確認済み事実] P0 residual source top: {'se:33': [{'count': 2, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': 'Agent:2,33,ga', 'slot_index': '1'}, {'count': 2, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': '相手:2,33,to', 'slot_index': '1'}, {'count': 2, 'item_id': 'x6-1', 'category': 'V', 'phono': '', 'raw': 'Theme:2,33,ga', 'slot_index': '1'}], 'sy:1': [{'count': 2, 'item_id': 'x7-1', 'category': 'T', 'phono': '', 'raw': '2,1,V', 'slot_index': '1'}], 'sy:11': [{'count': 10, 'item_id': 'x6-1', 'category': 'V', 'phono': '', 'raw': '2,11,to', 'slot_index': '1'}], 'sy:17': [{'count': 10, 'item_id': 'x2-1', 'category': 'J', 'phono': 'と', 'raw': '0,17,N,,,right,nonhead', 'slot_index': '1'}, {'count': 8, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': '0,17,N,,,left,nonhead', 'slot_index': '1'}]}
- [確認済み事実] P0_swap metrics: status=unknown, reason=timeout, actions=9914, depth=9, leaf_min=1
- [確認済み事実] P0_swap residual totals: {'se:33': 18, 'sy:17': 17, 'sy:11': 10, 'sy:1': 2}
- [確認済み事実] P0_swap residual source top: {'se:33': [{'count': 6, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': 'Agent:2,33,ga', 'slot_index': '1'}, {'count': 6, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': '相手:2,33,to', 'slot_index': '1'}, {'count': 6, 'item_id': 'x6-1', 'category': 'V', 'phono': '', 'raw': 'Theme:2,33,ga', 'slot_index': '1'}], 'sy:1': [{'count': 2, 'item_id': 'x7-1', 'category': 'T', 'phono': '-ru', 'raw': '2,1,V', 'slot_index': '1'}], 'sy:11': [{'count': 10, 'item_id': 'x6-1', 'category': 'V', 'phono': '', 'raw': '2,11,to', 'slot_index': '1'}], 'sy:17': [{'count': 10, 'item_id': 'x2-1', 'category': 'J', 'phono': 'と', 'raw': '0,17,N,,,right,nonhead', 'slot_index': '1'}, {'count': 7, 'item_id': 'x3-1', 'category': 'V', 'phono': '話している', 'raw': '0,17,N,,,left,nonhead', 'slot_index': '1'}]}
- [確認済み事実] delta: {'best_leaf_unresolved_min_before': 2, 'best_leaf_unresolved_min_after': 1, 'best_leaf_unresolved_min_delta': -1, 'best_leaf_residual_family_totals_delta': {'se:33': 12, 'sy:1': 0, 'sy:11': 0, 'sy:17': -1}, 'fact_status': '確認済み事実'}

### S4: ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
- [確認済み事実] P0 IDs: [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 125]
- [確認済み事実] P0_swap IDs: [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204]
- [確認済み事実] P0 metrics: status=unknown, reason=timeout, actions=8442, depth=13, leaf_min=7
- [確認済み事実] P0 residual totals: {'se:33': 30, 'sy:17': 20, 'sy:11': 10}
- [確認済み事実] P0 residual source top: {'se:33': [{'count': 10, 'item_id': 'x10-1', 'category': 'V', 'phono': '', 'raw': 'Theme:2,33,ga', 'slot_index': '1'}, {'count': 10, 'item_id': 'x7-1', 'category': 'V', 'phono': '話している', 'raw': 'Agent:2,33,ga', 'slot_index': '1'}, {'count': 10, 'item_id': 'x7-1', 'category': 'V', 'phono': '話している', 'raw': '相手:2,33,to', 'slot_index': '1'}], 'sy:11': [{'count': 10, 'item_id': 'x10-1', 'category': 'V', 'phono': '', 'raw': '2,11,to', 'slot_index': '1'}], 'sy:17': [{'count': 10, 'item_id': 'x1-1', 'category': 'A', 'phono': 'ふわふわした', 'raw': '0,17,N,,,left,nonhead', 'slot_index': '1'}, {'count': 10, 'item_id': 'x6-1', 'category': 'J', 'phono': 'と', 'raw': '0,17,N,,,right,nonhead', 'slot_index': '1'}]}
- [確認済み事実] P0_swap metrics: status=unknown, reason=timeout, actions=8673, depth=13, leaf_min=6
- [確認済み事実] P0_swap residual totals: {'se:33': 30, 'sy:11': 10, 'sy:17': 10}
- [確認済み事実] P0_swap residual source top: {'se:33': [{'count': 10, 'item_id': 'x10-1', 'category': 'V', 'phono': '', 'raw': 'Theme:2,33,ga', 'slot_index': '1'}, {'count': 10, 'item_id': 'x7-1', 'category': 'V', 'phono': '話している', 'raw': 'Agent:2,33,ga', 'slot_index': '1'}, {'count': 10, 'item_id': 'x7-1', 'category': 'V', 'phono': '話している', 'raw': '相手:2,33,to', 'slot_index': '1'}], 'sy:11': [{'count': 10, 'item_id': 'x10-1', 'category': 'V', 'phono': '', 'raw': '2,11,to', 'slot_index': '1'}], 'sy:17': [{'count': 10, 'item_id': 'x6-1', 'category': 'J', 'phono': 'と', 'raw': '0,17,N,,,right,nonhead', 'slot_index': '1'}]}
- [確認済み事実] delta: {'best_leaf_unresolved_min_before': 7, 'best_leaf_unresolved_min_after': 6, 'best_leaf_unresolved_min_delta': -1, 'best_leaf_residual_family_totals_delta': {'se:33': 0, 'sy:11': 0, 'sy:17': -10}, 'fact_status': '確認済み事実'}

## 未確認

- [未確認] 各ケースは budget 上限内観測であり、unknown を unreachable と断定できない。
