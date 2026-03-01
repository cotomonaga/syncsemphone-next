# Reachability fixed-action A/B 監査（2026-03-01）

対象:
- 文法: `imi01`
- 例文: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- `search_signature_mode=structural`
- `imi_fast_path_enabled=true`

目的:
- 固定 action 予算で、`global_deficit_ordering` の `OFF/ON` 比較を行う。
- 速度と質を分離して評価する。
- 安全側圧縮（`min_zero_delta_streak_by_struct_sig`）導入後の再訪率を再基準化する。

実行コマンド:
```bash
cd apps/api
python3 scripts/reachability_fixed_action_audit.py \
  --search-signature-mode structural \
  --budgets 25000,50000,100000 \
  --budget-seconds 600 \
  --max-depth 28
```

出力:
- JSON: [reachability-fixed-action-audit-20260301.json](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-fixed-action-audit-20260301.json)

## 1. fixed-action 結果（dominance導入後）

| Budget | Ordering | status | actions | leaf min | dominated child ratio | dominance improvement count | post-filter skipped by dominance | revisit ratio | cross-parent duplicate ratio |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 25k | OFF | unknown | 25000 | 9 | 0.000000 | 0 | 0 | 0.000000 | 0.000000 |
| 25k | ON  | unknown | 25000 | 9 | 0.000000 | 0 | 0 | 0.000000 | 0.000000 |
| 50k | OFF | unknown | 50000 | 9 | 0.000060 | 0 | 3 | 0.000000 | 0.000060 |
| 50k | ON  | unknown | 50000 | 9 | 0.000060 | 0 | 3 | 0.000000 | 0.000060 |
| 100k | OFF | unknown | 100000 | 9 | 0.004336 | 4620 | 435 | 0.044260 | 0.050391 |
| 100k | ON  | unknown | 100000 | 9 | 0.004336 | 4620 | 435 | 0.044260 | 0.050391 |

観測:
1. `global_deficit_ordering` は固定action条件では `OFF/ON` で差が出ない（質・速度とも実質同一）。
2. `min_zero_delta_streak_by_struct_sig` 導入により、100kで dominated child が `0.4336%` 発生し、`post_filter` 前で 435 件の後段計算を回避できた。
3. `unresolved_min` は依然 `9` のまま（質は未改善）。

## 2. 100k時点の前回比（dominance導入前 -> 導入後）

| 指標 | 導入前 | 導入後 | 変化 |
|---|---:|---:|---:|
| revisit ratio | 0.114570 | 0.044260 | -0.070310 |
| cross-parent duplicate ratio | 0.118039 | 0.050391 | -0.067648 |
| leaf unresolved min | 9 | 9 | 変化なし |

解釈:
- 安全側圧縮で重複探索は確実に減少した。
- ただし best leaf の質（`unresolved_min`）は動いていない。
- したがって「速くなったが、まだ良い葉には寄れていない」という評価を維持する。

## 3. 正規化時間指標（aggregates）

| Budget | Ordering | rule_expand_per_descriptor_ms | post_filter_per_finalized_ms | execute_per_materialized_ms |
|---:|---|---:|---:|---:|
| 25k | OFF | 0.003841 | 0.358156 | 0.235722 |
| 25k | ON  | 0.003846 | 0.360437 | 0.234991 |
| 50k | OFF | 0.003868 | 0.365355 | 0.243430 |
| 50k | ON  | 0.003864 | 0.366217 | 0.242983 |
| 100k | OFF | 0.003207 | 0.374515 | 0.261529 |
| 100k | ON  | 0.003204 | 0.375979 | 0.260759 |

観測:
- ON/OFF差は誤差範囲。
- 今回の主効果は ordering ではなく dominance 圧縮側にある。

## 4. 判定

確認済み:
1. `global_deficit_ordering_enabled` は action 集合を変えない（回帰テスト固定）。
2. `min_zero_delta_streak_by_struct_sig` によって再訪率・cross-parent重複率が低下。
3. `unresolved_min=9` は不変。

結論:
- 次段は ordering 調整ではなく、`Pareto(remaining_depth, zero_delta_streak)` の構造化実装を優先する方針が妥当。
- ただし到達性契約（`reachable/unreachable/unknown`）は維持し、unsafe hard prune は導入しない。

## 5. 次アクション（提案）

1. `Pareto(remaining_depth, zero_delta_streak)` を structural キーで実装し、dominance 判定を明示化する。
2. fixed-action 比較を継続し、`unresolved_min` と `best_samples`（残差族）の変化を追跡する。
3. 質が不変なら grammar/lexicon 側の残差要因切り分けを先行する。
