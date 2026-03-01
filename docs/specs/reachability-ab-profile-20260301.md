# Reachability A/B 計測メモ（2026-03-01）

対象: `imi01 / ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
条件: `budget_seconds=60`, `max_nodes=2_200_000`, `max_depth=24`, `auto_add_ga_phi=true`

## 0. 変更点（今回）
- 候補列挙を二層化:
  - `enumerate_action_descriptors(...)`
  - `materialize_action_descriptor(...)`
- 同一親の兄弟 `next structural signature` を1件へ圧縮
- `zero_delta_streak` 支配再訪抑制を導入
- `timing_ms` を詳細化（pairs/rule_expand/execute/signature など）

## 1. 結果（structural / packed）

### structural
- status: `unknown(timeout)`
- expanded: `60595`
- generated: `60921`
- actions_attempted: `60597`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`

### packed
- status: `unknown(timeout)`
- expanded: `47235`
- generated: `70860`
- actions_attempted: `70541`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`

## 2. time 内訳（ms）

### structural
- pairs_scan: `437.064`
- rule_expand: `34563.335`
- cheap_feature_extract: `179.329`
- execute_double_merge: `15018.122`
- next_unresolved: `1138.477`
- next_signature: `1097.490`
- post_filter: `19107.680`
- descriptor_sort: `56.439`
- sibling_exact_dedup: `1022.276`
- partner_counts: `1444.593`

### packed
- pairs_scan: `371.527`
- rule_expand: `29133.144`
- cheap_feature_extract: `193.538`
- execute_double_merge: `17866.587`
- next_unresolved: `1272.278`
- next_signature: `1289.039`
- post_filter: `22440.633`
- descriptor_sort: `56.855`
- sibling_exact_dedup: `1178.066`
- partner_counts: `1545.033`

## 3. leaf 診断（basenum=1）

### structural
- leaf count: `32798`
- unresolved min/max: `9 / 12`
- histogram: `{9:13523, 10:15468, 11:3806, 12:1}`

### packed
- leaf count: `35720`
- unresolved min/max: `9 / 12`
- histogram: `{9:13408, 10:17001, 11:5308, 12:3}`

## 4. 解釈

1. 深さ不足ではない
- `max_depth_reached=12` に到達しており、imi01の導出上限（basenum 13→1）には届いている。

2. 支配時間は `rule_expand` + `execute_double_merge` + `post_filter`
- 単純な sort 改善では効果が薄く、候補展開コストと実行後評価の削減が必要。

3. 現状順序では leaf 最良が `unresolved=9` から下がらない
- 到達証拠（unresolved=0）へ近づいていないため、
  次は descriptor 順序（cheap overlap）と materialize 数の制御（lazy化）を実測で詰める必要がある。

4. packed/structural の差は「現予算で第一支配項ではない」
- 両者とも timeout。署名粒度の優劣断定は保留。

