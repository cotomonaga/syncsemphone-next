# japanese2 Targeted Lexical Probe (2026-03-02)

- [確認済み事実] 固定条件: grammar_id=japanese2, explicit numeration, auto_add_ga_phi=False
- [確認済み事実] 予算: budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10

## 0. Baseline

| sentence | explicit_lexicon_ids | status | reason | actions | depth | leaf_min |
|---|---|---|---|---:|---:|---:|
| S2 | `265,23,266,267,19,271,204` | unknown | timeout | 10400 | 9 | 1 |
| S3 | `267,268,269,270,19,271,204` | unknown | timeout | 10182 | 9 | 1 |
| S4 | `264,265,23,266,267,268,269,270,19,271,204` | unknown | timeout | 9140 | 13 | 6 |

## 1. Candidate Inventory (lexicon-all.csv ∩ japanese2.csv)

### S2-A old_id=266 surface=食べている
- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）

### S3-B old_id=268 surface=と
| lexicon_id | entry | phono | category | idslot |
|---:|---|---|---|---|
| 171 | と | と | Z | 2,22 |

### S4-B old_id=268 surface=と
| lexicon_id | entry | phono | category | idslot |
|---:|---|---|---|---|
| 171 | と | と | Z | 2,22 |

### S3-C old_id=269 surface=話している
- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）

### S4-C old_id=269 surface=話している
- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）

### S3-D old_id=271 surface=いる
- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）

### S4-D old_id=271 surface=いる
- [確認済み事実] 候補なし（両CSV共通IDで同表層なし）

## 2. Targeted Probe Results

### S2: わたあめを食べているひつじがいる
- [確認済み事実] baseline IDs: `265,23,266,267,19,271,204`
- [確認済み事実] baseline residual totals: {'sy:17': 10}
- [確認済み事実] baseline residual source top5: [{'family': 'sy:17', 'exact_label': '2,17,N,,,left,nonhead', 'item_id': 'x3-1', 'surface': '食べている', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}]
- [確認済み事実] S2-A-no-candidate: not_run (no_candidate_in_both_sources)

### S3: ひつじと話しているうさぎがいる
- [確認済み事実] baseline IDs: `267,268,269,270,19,271,204`
- [確認済み事実] baseline residual totals: {'se:33': 18, 'sy:17': 17, 'sy:11': 10, 'sy:1': 2}
- [確認済み事実] baseline residual source top5: [{'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x2-1', 'surface': 'と', 'initial_slot': 2, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}]
- [確認済み事実] S3-B1:268->171 IDs: `267,171,269,270,19,271,204` status=reachable reason=timeout actions=10725 depth=9 leaf_min=0
  residual totals={'sy:17': 18, 'se:33': 9, 'sy:1': 2}; source_top5=[{'family': 'sy:17', 'exact_label': '0,17,N,,,left,nonhead', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 3}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 3}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 3}, {'family': 'sy:17', 'exact_label': '2,17,T,,,left,head', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 3}]
- [確認済み事実] S3-C-no-candidate: not_run (no_candidate_in_both_sources)
- [確認済み事実] S3-D-no-candidate: not_run (no_candidate_in_both_sources)

### S4: ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
- [確認済み事実] baseline IDs: `264,265,23,266,267,268,269,270,19,271,204`
- [確認済み事実] baseline residual totals: {'se:33': 30, 'sy:11': 10, 'sy:17': 10}
- [確認済み事実] baseline residual source top5: [{'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x6-1', 'surface': 'と', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}]
- [確認済み事実] S4-B1:268->171 IDs: `264,265,23,266,267,171,269,270,19,271,204` status=unknown reason=timeout actions=7490 depth=10 leaf_min=6
  residual totals={'se:33': 50, 'sy:17': 20, 'se:24': 10}; source_top5=[{'family': 'se:24', 'exact_label': 'Content:0,24', 'item_id': 'x1-1', 'surface': 'ふわふわした', 'initial_slot': 1, 'current_slot': '1', 'lexicon_id': 264, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x4-1', 'surface': '食べている', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,wo', 'item_id': 'x4-1', 'surface': '食べている', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}]
- [確認済み事実] S4-C-no-candidate: not_run (no_candidate_in_both_sources)
- [確認済み事実] S4-D-no-candidate: not_run (no_candidate_in_both_sources)

## 3. 未確認

- [未確認] 各runは有限予算観測であり、unknown を unreachable と断定できない。
