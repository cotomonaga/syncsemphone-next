# Reachability A/B 計測メモ（2026-03-01）

対象: `imi01 / ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
条件: `budget_seconds=60`, `max_nodes=2_200_000`, `max_depth=24`, `auto_add_ga_phi=true`

## 0. 実装段階

### Stage-A
- descriptor/materialize 分離前（旧実装）

### Stage-B
- descriptor/materialize 分離後
- `iter_action_descriptors` 導入（pair schedule 順に rule_expand）
- sibling dedup の順序を `execute -> signature -> dedup -> unresolved/partner` へ前倒し
- dominance は structural 固定
- leaf best sample（残差サマリ）を追加

## 1. Stage-B 実測（最新）

### structural
- status: `unknown(timeout)`
- expanded: `66875`
- generated: `67224`
- actions_attempted: `66874`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`
- timing(ms):
  - rule_expand: `37438.582`
  - execute_double_merge: `15926.539`
  - post_filter: `17665.472`
  - descriptor_sort: `62.254`
- leaf: `min=9`, `max=11`

### packed
- status: `unknown(timeout)`
- expanded: `67940`
- generated: `68285`
- actions_attempted: `67939`
- max_frontier: `79`
- max_depth_reached: `12`
- evidences: `0`
- timing(ms):
  - rule_expand: `36797.919`
  - execute_double_merge: `16472.163`
  - post_filter: `18206.735`
  - descriptor_sort: `63.422`
- leaf: `min=9`, `max=11`

## 2. best leaf サンプル（上位）

- unresolved=`9`, history_len=`12`
- `deficit_33={}` / `deficit_25={}`
- `demand_33_total=4`, `provider_33_total=4`
- `demand_25_total=0`, `provider_25_total=0`

解釈:
- 33/25 の不足そのものは best leaf で既に解消されている。
- にもかかわらず unresolved が 9 残るため、残差の主因は 33/25 以外（例: sy 側の別制約）にある可能性が高い。

## 3. 結論（現時点）

1. 深さ不足ではない
- `max_depth_reached=12` は維持。

2. 支配時間は依然 `rule_expand`（最大）
- lazy 化の第一段（descriptor iterator）だけでは、rule_expand 支配をまだ崩せていない。

3. 次の焦点
- imi fast path（RH/LH double 専用 expander）で `rule_expand` を直接削る。
- best leaf の残差ラベルを 33/25 以外（sy由来）まで展開し、grammar/lexicon 側要因と探索順要因を分離する。

