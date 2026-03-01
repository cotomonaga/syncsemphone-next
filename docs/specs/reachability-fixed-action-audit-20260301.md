# Reachability fixed-action A/B 監査（2026-03-01）

対象:
- 文法: `imi01`
- 例文: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- `search_signature_mode=structural`
- `imi_fast_path_enabled=true`

目的:
- 固定 action 予算で、`global deficit-aware ordering` の `OFF/ON` を比較する。
- 速度改善と質改善を分離して評価する。
- 再訪率・cross-parent 重複率を直接観測する。

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

## 1. サマリ（固定action予算）

| Budget | Ordering | status | actions | leaf unresolved min | revisit ratio | cross-parent duplicate ratio |
|---:|---|---|---:|---:|---:|---:|
| 25k | OFF | unknown | 25000 | 9 | 0.000000 | 0.000000 |
| 25k | ON  | unknown | 25000 | 9 | 0.000000 | 0.000000 |
| 50k | OFF | unknown | 50000 | 9 | 0.000060 | 0.000060 |
| 50k | ON  | unknown | 50000 | 9 | 0.000060 | 0.000060 |
| 100k | OFF | unknown | 100000 | 9 | 0.114570 | 0.118039 |
| 100k | ON  | unknown | 100000 | 9 | 0.114570 | 0.118039 |

観測:
- 同一 action 予算では `OFF/ON` の結果が実質同一。
- `unresolved_min` は全予算で `9` のまま。
- 100k 時点で再訪率・cross-parent 重複率が顕在化（約11〜12%）。

## 2. 正規化時間指標（aggregates）

| Budget | Ordering | rule_expand_per_descriptor_ms | post_filter_per_finalized_ms | execute_per_materialized_ms |
|---:|---|---:|---:|---:|
| 25k | OFF | 0.003917 | 0.361775 | 0.238225 |
| 25k | ON  | 0.003884 | 0.363034 | 0.238121 |
| 50k | OFF | 0.003911 | 0.367819 | 0.245865 |
| 50k | ON  | 0.003908 | 0.369116 | 0.245209 |
| 100k | OFF | 0.003237 | 0.373266 | 0.259681 |
| 100k | ON  | 0.003243 | 0.373904 | 0.258948 |

観測:
- `global deficit-aware ordering` の ON/OFFで、時間指標の差は誤差範囲。
- この段階では「速くなる」「質が良くなる」のいずれも確認できない。

## 3. 質指標（best leaf）

全 run で共通:
- `best_samples[*].unresolved = 9`
- `history_len = 12`
- `deficit_33 = {}` / `deficit_25 = {}`
- `demand_33_total = 4`, `provider_33_total = 4`

解釈:
- 33/25 の不足は best leaf では発生していない。
- したがって、未解釈残差の主因は 33/25 以外（別系統制約）にある可能性が高い。
- ordering を 33/25 deficit に寄せても質が動かなかった事実と整合する。

## 4. 判定

確認できたこと:
1. `global_deficit_ordering_enabled` は候補集合を変えない（`action_key` 集合一致テストで固定）。
2. fixed-action 比較で ON/OFF の差は現時点で出ない。
3. 100k で再訪/重複が約11〜12%まで増える。

結論:
- 現段階で先に強化すべきは ordering よりも、再訪/重複を抑える安全側制御（Pareto front 等）の検討。
- ただし到達性契約（reachable/unreachable/unknown）は維持し、unsafe な hard prune は導入しない。

## 5. 次アクション（提案）

1. `Pareto(remaining_depth, zero_delta_streak)` を structural キーで導入し、cross-parent 重複局面を圧縮する。
2. fixed-action 比較を継続し、`unresolved_min` と `best_samples` の変化を再測定する。
3. 変化がない場合は、探索器側でなく grammar/lexicon 側（残差制約）へ切り分けを進める。
