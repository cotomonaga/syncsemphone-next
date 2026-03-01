# Reachability 監査レポート（A/A + A/B）

更新日: 2026-03-01
対象: `apps/api/app/api/v1/derivation.py`
主旨: lazy 化・IMI fast path 導入後に、意味同値性と性能改善の実効を切り分ける。

## 1. A/A 意味同値監査（action集合一致）
- 監査観点: `generic path` と `IMI fast path` で、各親状態から生成される `action_key` の集合が一致すること（順序は不問）。
- 実施テスト: `test_derivation_imi_fast_path_action_set_matches_generic_on_representative_states`
- 対象状態:
  - 長文初期状態（`imi01/set-numeration/1608131500.num`, `basenum=13`）
  - 代表中間状態（同長文から `RH(1,2)` 適用後 `basenum=12`、さらに `LH(2,3)` 適用後 `basenum=11`）
  - 既知 reachable 短文（`imi01/set-numeration/04.num`）
  - 既知 reachable 中程度文（`imi01/set-numeration/1606324760.num`）
- 結果: 全対象で `action_key` 集合一致（テスト通過）。
- 解釈: 今回の fast path は、少なくとも上記監査範囲では「順序最適化」であり、候補集合自体は変えていない。

## 2. Structural 主系列 A/B（long imi01）
実測JSON: `docs/specs/reachability-ab-audit-20260301.json`

同一条件:
- 文: `imi01/set-numeration/1608131500.num`（長文, basenum=13）
- `search_signature_mode=structural`
- `budget_seconds=60`, `max_nodes=2,000,000`, `max_depth=28`

### 2.1 要約
| run | status | actions_attempted | expanded_nodes | generated_nodes | max_depth |
|---|---|---:|---:|---:|---:|
| fastpath OFF | unknown(timeout) | 66,275 | 66,275 | 66,620 | 12 |
| fastpath ON  | unknown(timeout) | 170,393 | 170,393 | 170,717 | 12 |

### 2.2 timing（ms）
| run | rule_expand | execute_double_merge | post_filter |
|---|---:|---:|---:|
| fastpath OFF | 37,794.968 | 15,622.377 | 57,335.710 |
| fastpath ON  | 773.948 | 40,571.756 | 53,100.217 |

### 2.3 正規化指標
| run | rule_expand_ms / descriptors_emitted | execute_ms / children_materialized | post_filter_ms / children_finalized |
|---|---:|---:|---:|
| fastpath OFF | 0.558115 | 0.230694 | 0.846671 |
| fastpath ON  | 0.004471 | 0.234366 | 0.306737 |

### 2.4 lazy メトリクス
| run | descriptors_emitted_total | descriptors_exhausted_states | descriptors_partial_states |
|---|---:|---:|---:|
| fastpath OFF | 67,719 | 66,275 | 1 |
| fastpath ON  | 173,113 | 170,393 | 1 |

解釈:
- `rule_expand` は総量・単位とも大幅に低下（fast path 効果あり）。
- `actions_attempted` は約2.57倍に増加（同時間内の探索前進が増えた）。
- `descriptors_partial_states=1` が両runで観測され、timeout前に iterator 未読了状態があることを確認。
- `post_filter` は依然大きく、次の支配点候補。

## 3. Best Leaf 比較（正規化残差）
長文A/Bの `leaf_stats`:
- 両runとも `unresolved_min=9`（最小値自体は不変）
- leaf数: OFF `35,145` → ON `84,992`（探索量増加）

best sample（両run共通）:
- `unresolved=9`
- `history_len=12`
- `deficit_33={}` / `deficit_25={}`
- `demand_33_total=4`, `provider_33_total=4`

正規化残差（族比較）:
- 33系: demand/provider はbest sampleで同数（不足なし）
- 25系: demand/provider とも0（不足なし）

解釈:
- 今回の改善は主に「速度と探索量」に効いており、best leaf の質（min値）を動かす段階にはまだ到達していない。
- ただし同時間内でのleaf観測数は増えており、次段の順序改善・post_filter最適化の土台はできた。

## 4. short/medium reachable sanity
同JSON内の sanity run:

| run | status | completed | actions_attempted | rule_expand_per_descriptor_ms |
|---|---|---|---:|---:|
| short: `imi01/04.num` | reachable | true | 6,969 | 0.004113 |
| medium: `imi03/04.num` | reachable | true | 5,728 | 0.645371 |

解釈:
- 既知 reachable は維持（到達性回帰なし）。
- imi01 short では fast path が効き、rule_expand単価が低い。
- imi03 medium は zero-Merge を含むため fast path 対象外で、rule_expand単価は高め（期待通り）。

## 結論（今回確定したこと / 未確定）
確定:
- IMI fast path は A/A 監査範囲で action集合を保ったまま `rule_expand` を大幅削減した。
- 同時間内の探索前進（actions_attempted）は増加した。
- 既知 reachable の回帰は発生していない。

未確定:
- 長文で `unresolved_min` を下げる質改善は未達（`min=9`据え置き）。
- 支配点は `post_filter` 側へ移行しており、次段の最適化が必要。

## 次の実装優先順
1. `post_filter` の exact 計算順最適化（代表childのみ重い計算を払う範囲を拡大）
2. Pareto (`remaining_depth`, `zero_delta_streak`) の厳密運用を導入
3. cheap proxy の重み調整を A/B で実施し、best leaf 残差の質改善を狙う
