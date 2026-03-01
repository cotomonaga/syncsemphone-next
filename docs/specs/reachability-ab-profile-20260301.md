# Reachability A/B 計測メモ（2026-03-01）

対象: `imi01 / ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
条件: `budget_seconds=60`, `max_nodes=2_200_000`, `max_depth=24`, `auto_add_ga_phi=true`

## 1. 結果（structural / packed）

### structural
- status: `unknown(timeout)`
- expanded: `78845`
- generated: `80128`
- actions_attempted: `79795`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`

### packed
- status: `unknown(timeout)`
- expanded: `49387`
- generated: `71700`
- actions_attempted: `71386`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`

## 2. time 内訳（ms）

### structural
- enumerate_transitions: `53499.947`
- sort_and_rank: `61.942`
- unresolved_count: `1403.272`
- partner_counts: `1611.356`
- sibling_dedup: `1323.412`

### packed
- enumerate_transitions: `52008.342`
- sort_and_rank: `51.398`
- unresolved_count: `1269.492`
- partner_counts: `1459.309`
- sibling_dedup: `1183.889`

## 3. 層別観測（抜粋）

basenum 13→9 では以下が確認できる。
- raw候補は `134, 132, 120, 108, 80`
- worsening cap 後は `79, 60, 53, 46, 33`
- sibling dedup 後も同数（この層では重複ほぼなし）

## 4. leaf 診断（basenum=1）

### structural
- leaf count: `53076`
- unresolved min/max: `9 / 11`
- histogram: `{9:23067, 10:24326, 11:5683}`

### packed
- leaf count: `35992`
- unresolved min/max: `9 / 11`
- histogram: `{9:12970, 10:16637, 11:6385}`

## 5. 解釈

1. 深さ不足ではない
- `max_depth_reached=12` に到達しており、imi01の導出上限（basenum 13→1）には届いている。

2. 時間支配は `enumerate_transitions`
- 60秒のうち約52〜53秒を遷移列挙側で消費している。
- sort/rank は支配要因ではない。

3. 現状の探索では leaf の最良 `unresolved` が 9 から下がらない
- 現行の候補列挙＋制約＋優先順では、到達証拠（unresolved=0）に接近できていない。
- したがって、次の改善は「探索器の順序だけ」ではなく、遷移生成コスト削減と遷移集合の質改善（必要遷移の可達性確認）を同時に進める必要がある。

