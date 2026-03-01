# Reachability residual 診断（2026-03-01）

対象:
- 文法: `imi01`
- numeration: `imi01/set-numeration/1608131500.num`
- 設定: `budget_seconds=600`, `max_nodes=100000`, `max_depth=28`, `top_k=50`

出力:
- JSON: [reachability-residual-diagnose-20260301.json](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-residual-diagnose-20260301.json)

## 1. 実行結果

- status: `unknown`
- reason: `node_limit`
- actions_attempted: `100000`
- leaf unresolved: `min=9`, `max=11`

## 2. 残差ベクトル集計（top-k=50）

best leaf 集計（`best_leaf_residual_family_totals`）:
- `se:33 = 200`
- `sy:11 = 200`
- `sy:17 = 50`

best mid-state 集計（`best_mid_residual_family_totals`）:
- `se:33 = 200`
- `sy:11 = 200`
- `sy:17 = 50`

## 3. 局所死活診断（basenum=2/3）

`best_mid_local_dead_end`:
- `sample_count = 50`
- `non_improving_count = 50`
- `non_improving_ratio = 1.0`

解釈:
- top-k の `basenum=2/3` 良好状態では、`min_delta_unresolved >= 0` が全件。
- つまり、観測された良好状態群では「1手で未解釈を減らす action」が見つかっていない。
- 探索順だけでなく、grammar/lexicon 側の persistent residual（`se:33`, `sy:11`, `sy:17`）の構造要因切り分けが必要。

## 4. 次アクション

1. residual 族（`se:33`, `sy:11`, `sy:17`）の導入元 lexical item と、解消規則の対応表を作る。
2. `best_mid_state_samples` の action 列挙ログを追加し、なぜ `min_delta_unresolved < 0` が出ないかを手順単位で確認する。
3. 上記を踏まえ、探索器改修より先に grammar/lexicon 側の妥当性検証へ進む。
