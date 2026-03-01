# Reachability 再ベースライン監査（postfix）

更新日: 2026-03-01  
基準コミット: `6cdb979`  
対象: `apps/api/app/api/v1/derivation.py`

## 1. 背景
- `id()` キーの summary cache は Python のオブジェクトID再利用で stale 参照を起こし得るため、正しさに直結する不具合だった。
- 本計測は `state: structural signature / node: JSON signature` へ修正後の再ベースライン。

## 2. long imi01（structural, 60秒）A/B

| run | status | actions_attempted | expanded_nodes | generated_nodes | max_depth |
|---|---|---:|---:|---:|---:|
| fastpath OFF | unknown(timeout) | 68,789 | 68,780 | 69,102 | 12 |
| fastpath ON | unknown(timeout) | 139,638 | 138,207 | 139,956 | 12 |

### 2.1 timing（ms）
| run | rule_expand | execute_double_merge | post_filter | next_signature |
|---|---:|---:|---:|---:|
| fastpath OFF | 31,809.308 | 17,269.496 | 57,113.094 | 1,275.496 |
| fastpath ON | 480.795 | 35,996.805 | 54,005.356 | 2,705.781 |

### 2.2 正規化指標
| run | rule_expand_ms / descriptor | execute_ms / materialized | post_filter_ms / finalized |
|---|---:|---:|---:|
| fastpath OFF | 0.440048 | 0.238905 | 0.790099 |
| fastpath ON | 0.003295 | 0.246712 | 0.370138 |

### 2.3 cache 統計
| run | state hit/miss | node hit/miss | avg state key build ms | avg node key build ms |
|---|---:|---:|---:|---:|
| fastpath OFF | 68,789/1 | 156,889/59,969 | 0.000000 | 0.009000 |
| fastpath ON | 139,638/1 | 332,975/104,743 | 0.000000 | 0.009133 |

## 3. best leaf（質指標）
- OFF: `unresolved_min=9`, `count=42,446`
- ON : `unresolved_min=9`, `count=86,930`
- 先頭 best sample（ON）:
```json
{
  "unresolved": 9,
  "history_len": 12,
  "deficit_33": {},
  "deficit_25": {},
  "demand_33_total": 4,
  "provider_33_total": 4,
  "demand_25_total": 0,
  "provider_25_total": 0
}
```

## 4. sanity（reachable 回帰）
| run | status | completed | actions_attempted |
|---|---|---|---:|
| imi01 04 | reachable | True | 19,576 |
| imi03 04 | reachable | True | 19,576 |

## 5. 再ベースライン後の結論
- correctness 修正後でも、IMI fast path の `rule_expand` 削減効果は維持。
- 一方で `best leaf unresolved_min` は `9` のまま据え置きで、探索の質改善は未達。
- 次の焦点は `post_filter` と `next_signature/key_build` を含む hot path の再最適化（正しさを維持した incremental 強化）。
