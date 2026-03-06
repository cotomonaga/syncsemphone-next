# japanese2 lexical-only followup (2026-03-02)

## 1. 結論

- [確認済み事実] 固定条件: grammar_id=japanese2, explicit numeration, auto_add_ga_phi=False, budget_seconds=20.0, max_nodes=120000, max_depth=28, top_k=10
- [確認済み事実] S3の `268->171` は leaf_min 1 -> 0 へ改善。
- [確認済み事実] S4の `268->171` は leaf_min 6 -> 6 で改善せず、family差分は {'se:24': 10, 'se:33': 20, 'sy:11': -10, 'sy:17': 10}。
- [確認済み事実] 266/269/271 の同表層 engine-usable 代替候補は今回観測では存在せず、1スロット差し替えprobeは not_run。
- [推測] 266 の sy:17 残差は既存候補の選び直しのみでは縮退しないため、lexical-onlyで狙うなら 266 相当の新規行追加が最小。

## 2. candidate pool（engine-usable / lookup-deployable）

### surface: 食べている
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 266 | 食べている | V | id | True | False | lexicon-all.csv | False |

### surface: と
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 171 | と | Z | 2,22 | True | True | japanese2/japanese2.csv,lexicon-all.csv | False |
| 268 | と | J | zero | True | False | lexicon-all.csv | False |

### surface: 話している
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 269 | 話している | V | id | True | False | lexicon-all.csv | False |

### surface: いる
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 271 | いる | V | id | True | False | lexicon-all.csv | True |

### surface: る
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 125 | る | T | 0,24 | True | True | japanese2/japanese2.csv,lexicon-all.csv | True |
| 204 | る | T | 0,24 | True | True | japanese2/japanese2.csv,lexicon-all.csv | True |
| 308 | る | T | 0,24 | True | False | lexicon-all.csv | True |

### surface: φ
| lexicon_id | entry | category | idslot | engine_usable | lookup_deployable | source_files | used_in_reachable |
|---:|---|---|---|---|---|---|---|
| 195 | φ | N | id | True | True | japanese2/japanese2.csv,lexicon-all.csv | False |
| 196 | が | J | zero | True | True | japanese2/japanese2.csv,lexicon-all.csv | False |
| 197 | を | J | zero | True | True | japanese2/japanese2.csv,lexicon-all.csv | False |
| 236 | Pred | Pred | zero | True | False | lexicon-all.csv | False |
| 272 | φ | N | id | True | False | lexicon-all.csv | False |
| 273 | φ | N | id | True | False | lexicon-all.csv | False |
| 274 | φ | N | id | True | False | lexicon-all.csv | False |
| 275 | φ | N | rel | True | False | lexicon-all.csv | False |
| 309 | φ | N | id | True | False | lexicon-all.csv | False |
| 310 | φ | N | id | True | False | lexicon-all.csv | False |
| 311 | φ | N | id | True | False | lexicon-all.csv | False |

## 3. S3 の `268->171` 成功分析

- [確認済み事実] baseline IDs: `267,268,269,270,19,271,204`
- [確認済み事実] swap IDs: `267,171,269,270,19,271,204`
- [確認済み事実] baseline metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 9749, 'max_depth_reached': 9, 'best_leaf_unresolved_min': 1, 'best_leaf_residual_family_totals': {'se:33': 18, 'sy:17': 17, 'sy:11': 10, 'sy:1': 2}, 'best_mid_residual_family_totals': {'se:33': 18, 'sy:17': 17, 'sy:11': 10, 'se:24': 2, 'sy:1': 2}, 'best_leaf_exact_source_top5': [{'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x2-1', 'surface': 'と', 'initial_slot': 2, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] swap metrics: {'status': 'reachable', 'reason': 'timeout', 'actions_attempted': 10258, 'max_depth_reached': 9, 'best_leaf_unresolved_min': 0, 'best_leaf_residual_family_totals': {'sy:17': 18, 'se:33': 6, 'sy:1': 2}, 'best_mid_residual_family_totals': {'sy:17': 18, 'se:33': 6, 'sy:1': 2}, 'best_leaf_exact_source_top5': [{'family': 'sy:17', 'exact_label': '0,17,N,,,left,nonhead', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '2,17,T,,,left,head', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 3}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 2}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x3-1', 'surface': '話している', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 2}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x6-1', 'surface': 'いる', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 2}], 'history_top': ['([x4-1 x5-1] J-Merge) ([x1-1 x2-1] RH-Merge) ([x3-1 x6-1] RH-Merge) ([x6-1 x2-1] RH-Merge) ([x2-1 x7-1] property-Merge) ([x7-1 x4-1] RH-Merge)', '([x4-1 x5-1] J-Merge) ([x1-1 x2-1] RH-Merge) ([x3-1 x6-1] RH-Merge) ([x6-1 x2-1] RH-Merge) ([x2-1 x7-1] property-Merge) ([x4-1 x7-1] RH-Merge)'], 'fact_status': '確認済み事実'}
- [確認済み事実] diff: {'best_leaf_unresolved_min_before': 1, 'best_leaf_unresolved_min_after': 0, 'best_leaf_unresolved_min_delta': -1, 'family_delta': {'se:33': -12, 'sy:1': 0, 'sy:11': -10, 'sy:17': 1}, 'source_disappeared_top5': ['sy:11|2,11,to|x6-1|いる', 'sy:17|0,17,N,,,right,nonhead|x2-1|と'], 'source_appeared_top5': ['sy:17|0,17,N,,,left,nonhead|x3-1|話している', 'sy:17|2,17,T,,,left,head|x6-1|いる'], 'fact_status': '確認済み事実'}

## 4. S4 の `268->171` 悪化分析

- [確認済み事実] baseline IDs: `264,265,23,266,267,268,269,270,19,271,204`
- [確認済み事実] swap IDs: `264,265,23,266,267,171,269,270,19,271,204`
- [確認済み事実] baseline metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 8804, 'max_depth_reached': 13, 'best_leaf_unresolved_min': 6, 'best_leaf_residual_family_totals': {'se:33': 30, 'sy:11': 10, 'sy:17': 10}, 'best_mid_residual_family_totals': {'se:33': 20, 'sy:17': 20, 'sy:11': 10}, 'best_leaf_exact_source_top5': [{'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x6-1', 'surface': 'と', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] swap metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 7311, 'max_depth_reached': 10, 'best_leaf_unresolved_min': 6, 'best_leaf_residual_family_totals': {'se:33': 50, 'sy:17': 20, 'se:24': 10}, 'best_mid_residual_family_totals': {'se:33': 50, 'sy:17': 20, 'se:24': 10}, 'best_leaf_exact_source_top5': [{'family': 'se:24', 'exact_label': 'Content:0,24', 'item_id': 'x1-1', 'surface': 'ふわふわした', 'initial_slot': 1, 'current_slot': '1', 'lexicon_id': 264, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'いる', 'initial_slot': 10, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x4-1', 'surface': '食べている', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,wo', 'item_id': 'x4-1', 'surface': '食べている', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x7-1', 'surface': '話している', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] diff: {'best_leaf_unresolved_min_before': 6, 'best_leaf_unresolved_min_after': 6, 'best_leaf_unresolved_min_delta': 0, 'family_delta': {'se:24': 10, 'se:33': 20, 'sy:11': -10, 'sy:17': 10}, 'source_disappeared_top5': ['se:33|相手:2,33,to|x7-1|話している', 'sy:11|2,11,to|x10-1|いる', 'sy:17|0,17,N,,,right,nonhead|x6-1|と'], 'source_appeared_top5': ['se:24|Content:0,24|x1-1|ふわふわした', 'se:33|Agent:2,33,ga|x4-1|食べている', 'se:33|Theme:2,33,wo|x4-1|食べている'], 'fact_status': '確認済み事実'}
- [確認済み事実] swap時の `se:24` exact source top5 は `264 ふわふわした`（Content:0,24）であり、171自身のsourceとしては観測されていない。

## 5. `264` 干渉切り分け reduced sentence

### T1: わたあめを食べているひつじと話しているうさぎがいる
- [確認済み事実] baseline IDs: `265,23,266,267,268,269,270,19,271,204`
- [確認済み事実] baseline metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 8975, 'max_depth_reached': 12, 'best_leaf_unresolved_min': 6, 'best_leaf_residual_family_totals': {'se:33': 30, 'sy:11': 10, 'sy:17': 10}, 'best_mid_residual_family_totals': {'se:33': 20, 'sy:17': 20, 'sy:11': 10}, 'best_leaf_exact_source_top5': [{'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x6-1', 'surface': '話している', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x6-1', 'surface': '話している', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x9-1', 'surface': 'いる', 'initial_slot': 9, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x9-1', 'surface': 'いる', 'initial_slot': 9, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x5-1', 'surface': 'と', 'initial_slot': 5, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] swap IDs: `265,23,266,267,171,269,270,19,271,204`
- [確認済み事実] swap metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 9700, 'max_depth_reached': 12, 'best_leaf_unresolved_min': 5, 'best_leaf_residual_family_totals': {'se:33': 20, 'sy:17': 10}, 'best_mid_residual_family_totals': {'se:33': 20, 'sy:17': 20}, 'best_leaf_exact_source_top5': [{'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x6-1', 'surface': '話している', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x6-1', 'surface': '話している', 'initial_slot': 6, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '2,17,N,,,left,nonhead', 'item_id': 'x3-1', 'surface': '食べている', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] diff: {'best_leaf_unresolved_min_before': 6, 'best_leaf_unresolved_min_after': 5, 'best_leaf_unresolved_min_delta': -1, 'family_delta': {'se:33': -10, 'sy:11': -10, 'sy:17': 0}, 'source_disappeared_top5': ['se:33|Theme:2,33,ga|x9-1|いる', 'sy:11|2,11,to|x9-1|いる', 'sy:17|0,17,N,,,right,nonhead|x5-1|と'], 'source_appeared_top5': ['sy:17|2,17,N,,,left,nonhead|x3-1|食べている'], 'fact_status': '確認済み事実'}

### T2: ふわふわしたひつじと話しているうさぎがいる
- [確認済み事実] baseline IDs: `264,267,268,269,270,19,271,204`
- [確認済み事実] baseline metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 9532, 'max_depth_reached': 10, 'best_leaf_unresolved_min': 2, 'best_leaf_residual_family_totals': {'sy:17': 19, 'sy:11': 10, 'se:33': 9}, 'best_mid_residual_family_totals': {'sy:17': 19, 'sy:11': 10, 'se:33': 9}, 'best_leaf_exact_source_top5': [{'family': 'sy:11', 'exact_label': '2,11,to', 'item_id': 'x7-1', 'surface': 'いる', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,right,nonhead', 'item_id': 'x3-1', 'surface': 'と', 'initial_slot': 3, 'current_slot': '1', 'lexicon_id': 268, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '0,17,N,,,left,nonhead', 'item_id': 'x4-1', 'surface': '話している', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 4}, {'family': 'se:33', 'exact_label': 'Agent:2,33,ga', 'item_id': 'x4-1', 'surface': '話している', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 3}, {'family': 'se:33', 'exact_label': '相手:2,33,to', 'item_id': 'x4-1', 'surface': '話している', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 3}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] swap IDs: `264,267,171,269,270,19,271,204`
- [確認済み事実] swap metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 10249, 'max_depth_reached': 10, 'best_leaf_unresolved_min': 3, 'best_leaf_residual_family_totals': {'sy:17': 20}, 'best_mid_residual_family_totals': {'se:33': 30, 'sy:17': 20}, 'best_leaf_exact_source_top5': [{'family': 'sy:17', 'exact_label': '0,17,N,,,left,nonhead', 'item_id': 'x4-1', 'surface': '話している', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 269, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '2,17,T,,,left,head', 'item_id': 'x7-1', 'surface': 'いる', 'initial_slot': 7, 'current_slot': '1', 'lexicon_id': 271, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] diff: {'best_leaf_unresolved_min_before': 2, 'best_leaf_unresolved_min_after': 3, 'best_leaf_unresolved_min_delta': 1, 'family_delta': {'se:33': -9, 'sy:11': -10, 'sy:17': 1}, 'source_disappeared_top5': ['se:33|Agent:2,33,ga|x4-1|話している', 'se:33|相手:2,33,to|x4-1|話している', 'sy:11|2,11,to|x7-1|いる', 'sy:17|0,17,N,,,right,nonhead|x3-1|と'], 'source_appeared_top5': ['sy:17|2,17,T,,,left,head|x7-1|いる'], 'fact_status': '確認済み事実'}

### T3: ふわふわしたわたあめを食べているひつじがいる
- [確認済み事実] baseline IDs: `264,265,23,266,267,19,271,204`
- [確認済み事実] baseline metrics: {'status': 'unknown', 'reason': 'timeout', 'actions_attempted': 10013, 'max_depth_reached': 10, 'best_leaf_unresolved_min': 2, 'best_leaf_residual_family_totals': {'sy:17': 20}, 'best_mid_residual_family_totals': {'sy:17': 20}, 'best_leaf_exact_source_top5': [{'family': 'sy:17', 'exact_label': '0,17,N,,,left,nonhead', 'item_id': 'x1-1', 'surface': 'ふわふわした', 'initial_slot': 1, 'current_slot': '1', 'lexicon_id': 264, 'count_in_top5_samples': 5}, {'family': 'sy:17', 'exact_label': '2,17,N,,,left,nonhead', 'item_id': 'x4-1', 'surface': '食べている', 'initial_slot': 4, 'current_slot': '1', 'lexicon_id': 266, 'count_in_top5_samples': 5}], 'history_top': [], 'fact_status': '確認済み事実'}
- [確認済み事実] swap_268_to_171 は not_applicable（268がbaselineに存在しない）

## 6. `266/269/271` targeted probe

### old_id=266 surface=食べている sentence=S2
- [確認済み事実] baseline IDs: `265,23,266,267,19,271,204`
- [確認済み事実] not_run: no_engine_usable_alternative_candidate

### old_id=269 surface=話している sentence=S3
- [確認済み事実] baseline IDs: `267,268,269,270,19,271,204`
- [確認済み事実] not_run: no_engine_usable_alternative_candidate

### old_id=269 surface=話している sentence=S4
- [確認済み事実] baseline IDs: `264,265,23,266,267,268,269,270,19,271,204`
- [確認済み事実] not_run: no_engine_usable_alternative_candidate

### old_id=271 surface=いる sentence=S3
- [確認済み事実] baseline IDs: `267,268,269,270,19,271,204`
- [確認済み事実] not_run: no_engine_usable_alternative_candidate

### old_id=271 surface=いる sentence=S4
- [確認済み事実] baseline IDs: `264,265,23,266,267,268,269,270,19,271,204`
- [確認済み事実] not_run: no_engine_usable_alternative_candidate

## 7. `171` と `268` の code-grounded 差分

- [確認済み事実] `268`（J/zero）は `sync_features=[0,17,N,,,right,nonhead; 3,17,V,,,left,nonhead; 4,11,to]` を持つ。
- [確認済み事実] `171`（Z/2,22）は `sync_features=[to]`, `semantics=[Content:0,24]` を持つ。
- [確認済み事実] `17` 系消費は `execute.py` の `_process_sy_imi03`（`number == "17"`）で `_eval_feature_17` を通る。
- [確認済み事実] `se:24` 消費は `execute.py` の `_process_se_imi03`（`number == "24"`）で `attr:nb_id` に置換される。
- [確認済み事実] `se:33` 消費は `_process_se_imi03`（`number == "33"`）で相手 `sy` の `11`/`12` ラベル一致を要する。

## 8. `266` lexical-only 可否

- [確認済み事実] yes/no-1: **No**（既存候補の選び直しだけでは不可）。理由: `食べている` の engine-usable 候補は 266 のみ。
- [推測] yes/no-2: **Yes**（新規 lexical item 1行追加で狙うのが妥当）。理由: S2 obstruction が 266由来 sy:17 に局在。
- [推測] yes/no-3: 最小差分は `266` の `sync_features`（17系）を1本変える設計。

## 9. 必要なら新規 lexical item 案

- [推測] 266の17系をhead側一致へ最小変更
```tsv
9201	食べている	食べている	V	0 				1	2,17,N,,,left,head					id	4 	Theme	2,33,wo	Agent	2,33,ga	食べる	T	Aspect	progressive					probe-266-sy17-left-head	0
```
- [推測] 266の17系を反対方向へ最小変更
```tsv
9202	食べている	食べている	V	0 				1	2,17,N,,,right,nonhead					id	4 	Theme	2,33,wo	Agent	2,33,ga	食べる	T	Aspect	progressive					probe-266-sy17-right-nonhead	0
```

## 10. 未確認事項

- [未確認] 有限予算下の unknown は unreachable を意味しない。
- [未確認] 新規 lexical item 案（9201/9202）は未投入・未実測。
