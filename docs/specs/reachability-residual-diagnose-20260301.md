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
- max_depth_reached: `12`（終端深さには到達）

## 2. 残差ベクトル集計（top-k=50）

best leaf 集計（`best_leaf_residual_family_totals`）:
- `se:33 = 200`
- `sy:11 = 200`
- `sy:17 = 50`

best mid-state 集計（`best_mid_residual_family_totals`）:
- `se:33 = 200`
- `sy:11 = 200`
- `sy:17 = 50`

所見:
- best leaf / best mid-state で同じ残差族が固定的に残る。
- `unresolved_min=9` が動かない主因は、探索順よりも residual の導入・解消対応にある可能性が高い。

## 3. 初期スロットと residual 導入元

`initial_slots`（主要な family のみ）:
- `se:33` を導入: slot4 `食べている(266)`, slot7 `話している(269)`, slot10 `いる(271)`
- `sy:11` を導入: slot3 `を(23)`, slot6 `と(268)`, slot9 `が(19)`, slot12/13 `φ(309)`
- `sy:17` を導入: slot1 `ふわふわした(264)`, slot3 `を(23)`, slot4 `食べている(266)`, slot6 `と(268)`, slot7 `話している(269)`, slot9 `が(19)`, slot10 `いる(271)`, slot11 `る(204)`

best leaf の residual source 上位（`best_leaf_residual_source_totals`）:
- `se:33`
  - `x4-1 食べている`: `Agent:2,33,ga`（50）
  - `x4-1 食べている`: `Theme:2,33,wo`（50）
  - `x7-1 話している`: `Agent:2,33,ga`（50）
  - `x7-1 話している`: `相手:2,33,to`（50）
- `sy:11`
  - `x10-1 いる`: `2,11,ga`（67）
  - `x12-1 φ`: `2,11,wo`（50）
  - `x5-1 ひつじ`: `2,11,to`（50）
  - `x13-1 φ`: `4,11,ga`（17）
  - `x8-1 うさぎ`: `2,11,ga`（16）
- `sy:17`
  - `x9-1 が`: `0,17,N,,,right,nonhead`（50）

## 4. 局所死活診断（basenum=2/3）

`best_mid_local_dead_end`:
- `sample_count = 50`
- `non_improving_count = 50`
- `non_improving_ratio = 1.0`

解釈:
- top-k の `basenum=2/3` 良好状態では、`min_delta_unresolved >= 0` が全件。
- つまり、観測された良好状態群では「1手で未解釈を減らす action」が見つかっていない。
- 探索器の局所順序調整より前に、`se:33 / sy:11 / sy:17` の導入元語彙と解消規則の対応を点検すべき段階。

## 5. 次アクション

1. `se:33`（x4/x7/x10）と `sy:11`（x5/x8/x12/x13）について、どの rule/語彙の組で解消される想定かを Perl準拠で対応表化する。
2. `sy:17` が最終残差に残る経路（x9 `が`）を history 単位で抽出し、どの merge 選択で消せなくなるかを特定する。
3. 2) の結果で「局所改善手が本当に存在しない」ことが確定した場合、探索器改修より先に grammar/lexicon 側の妥当性検証へ移る。
