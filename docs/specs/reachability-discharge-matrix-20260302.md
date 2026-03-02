# Reachability discharge matrix（2026-03-02）

条件:
- grammars: `imi01, imi02, imi03`
- split_mode: `A`
- budget_seconds: `120.0`
- max_nodes: `40000`
- max_depth: `28`
- top_k(best_leaf): `20`
- phi_mode: `none`, `plus2`（`309` を +2）

注記:
- `discharge_table` の `estimated_discharged_per_path` は、`initial_count - best_leaf平均残差` の観測値です（証明値ではありません）。

## サマリ

| sentence | grammar | phi | status | reason | actions | depth | leaf_min | residual(avg) |
|---|---|---|---|---|---:|---:|---:|---|
| S1 | imi01 | none | reachable | completed | 160 | 3 | 0 | se:33=0, sy:11=0, sy:17=0.9 |
| S1 | imi01 | plus2 | reachable | node_limit | 40000 | 5 | 0 | se:33=0, sy:11=0.6, sy:17=0 |
| S1 | imi02 | none | reachable | completed | 170 | 3 | 0 | se:33=0, sy:11=0, sy:17=0.9 |
| S1 | imi02 | plus2 | reachable | node_limit | 40000 | 5 | 0 | se:33=0, sy:11=0.5, sy:17=0 |
| S1 | imi03 | none | reachable | completed | 170 | 3 | 0 | se:33=0, sy:11=0, sy:17=0.9 |
| S1 | imi03 | plus2 | reachable | node_limit | 40000 | 5 | 0 | se:33=0, sy:11=0.5, sy:17=0 |
| S2 | imi01 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S2 | imi01 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S2 | imi02 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S2 | imi02 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S2 | imi03 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S2 | imi03 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S3 | imi01 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S3 | imi01 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S3 | imi02 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S3 | imi02 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S3 | imi03 | none | unknown | node_limit | 40000 | 6 | 3 | se:33=2.0, sy:11=1.0, sy:17=0 |
| S3 | imi03 | plus2 | unknown | node_limit | 40000 | 8 | 4 | se:33=2.0, sy:11=2.0, sy:17=0 |
| S4 | imi01 | none | unknown | node_limit | 40000 | 10 | 7 | se:33=4.0, sy:11=2.0, sy:17=1.0 |
| S4 | imi01 | plus2 | unknown | node_limit | 40000 | 12 | 9 | se:33=4.0, sy:11=4.0, sy:17=1.0 |
| S4 | imi02 | none | unknown | node_limit | 40000 | 10 | 7 | se:33=4.0, sy:11=2.0, sy:17=1.0 |
| S4 | imi02 | plus2 | unknown | node_limit | 40000 | 12 | 9 | se:33=4.0, sy:11=4.0, sy:17=1.0 |
| S4 | imi03 | none | unknown | node_limit | 40000 | 10 | 7 | se:33=4.0, sy:11=2.0, sy:17=1.0 |
| S4 | imi03 | plus2 | unknown | node_limit | 40000 | 12 | 9 | se:33=4.0, sy:11=4.0, sy:17=1.0 |

## 詳細（family discharge + source）

### S1 / imi01 / none (reachable, completed)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204]`
- initial families: `se:33=1, sy:11=1, sy:17=4`
- residual(avg): `se:33=0, sy:11=0, sy:17=0.9`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 1 | 0.0 | 1.0 |
| sy:17 | 4 | 0.9 | 3.1 |

- sy:17 source top:
  - `x2-1` 0,17,N,,,right,nonhead (14)
  - `x3-1` 3,17,V,,,left,nonhead (2)
  - `x4-1` 0,17,V,,,right,nonhead (2)

### S1 / imi01 / plus2 (reachable, node_limit)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204, 309, 309]`
- initial families: `se:33=1, sy:11=3, sy:17=4`
- residual(avg): `se:33=0, sy:11=0.6, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 3 | 0.6 | 2.4 |
| sy:17 | 4 | 0.0 | 4.0 |

- sy:11 source top:
  - `x1-1` 2,11,ga (12)

### S1 / imi02 / none (reachable, completed)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204]`
- initial families: `se:33=1, sy:11=1, sy:17=4`
- residual(avg): `se:33=0, sy:11=0, sy:17=0.9`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 1 | 0.0 | 1.0 |
| sy:17 | 4 | 0.9 | 3.1 |

- sy:17 source top:
  - `x2-1` 0,17,N,,,right,nonhead (14)
  - `x3-1` 3,17,V,,,left,nonhead (2)
  - `x4-1` 0,17,V,,,right,nonhead (2)

### S1 / imi02 / plus2 (reachable, node_limit)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204, 309, 309]`
- initial families: `se:33=1, sy:11=3, sy:17=4`
- residual(avg): `se:33=0, sy:11=0.5, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 3 | 0.5 | 2.5 |
| sy:17 | 4 | 0.0 | 4.0 |

- sy:11 source top:
  - `x1-1` 2,11,ga (10)

### S1 / imi03 / none (reachable, completed)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204]`
- initial families: `se:33=1, sy:11=1, sy:17=4`
- residual(avg): `se:33=0, sy:11=0, sy:17=0.9`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 1 | 0.0 | 1.0 |
| sy:17 | 4 | 0.9 | 3.1 |

- sy:17 source top:
  - `x2-1` 0,17,N,,,right,nonhead (14)
  - `x3-1` 3,17,V,,,left,nonhead (2)
  - `x4-1` 0,17,V,,,right,nonhead (2)

### S1 / imi03 / plus2 (reachable, node_limit)
- sentence: `うさぎがいる`
- lexicon_ids: `[270, 19, 271, 204, 309, 309]`
- initial families: `se:33=1, sy:11=3, sy:17=4`
- residual(avg): `se:33=0, sy:11=0.5, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 1 | 0.0 | 1.0 |
| sy:11 | 3 | 0.5 | 2.5 |
| sy:17 | 4 | 0.0 | 4.0 |

- sy:11 source top:
  - `x1-1` 2,11,ga (10)

### S2 / imi01 / none (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (15)
  - `x4-1` 2,11,wo (5)

### S2 / imi01 / plus2 (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (20)
  - `x4-1` 2,11,ga (20)

### S2 / imi02 / none (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (15)
  - `x4-1` 2,11,wo (5)

### S2 / imi02 / plus2 (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (20)
  - `x4-1` 2,11,ga (20)

### S2 / imi03 / none (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (15)
  - `x4-1` 2,11,wo (5)

### S2 / imi03 / plus2 (unknown, node_limit)
- sentence: `わたあめを食べているひつじがいる`
- lexicon_ids: `[265, 23, 266, 267, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` Theme:2,33,wo (20)
- sy:11 source top:
  - `x1-1` 2,11,wo (20)
  - `x4-1` 2,11,ga (20)

### S3 / imi01 / none (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (15)
  - `x4-1` 2,11,to (5)

### S3 / imi01 / plus2 (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (20)
  - `x4-1` 2,11,ga (20)

### S3 / imi02 / none (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (15)
  - `x4-1` 2,11,to (5)

### S3 / imi02 / plus2 (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (20)
  - `x4-1` 2,11,ga (20)

### S3 / imi03 / none (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=3, sy:11=2, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=1.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 2 | 1.0 | 1.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (15)
  - `x4-1` 2,11,to (5)

### S3 / imi03 / plus2 (unknown, node_limit)
- sentence: `ひつじと話しているうさぎがいる`
- lexicon_ids: `[267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=3, sy:11=4, sy:17=7`
- residual(avg): `se:33=2.0, sy:11=2.0, sy:17=0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 3 | 2.0 | 1.0 |
| sy:11 | 4 | 2.0 | 2.0 |
| sy:17 | 7 | 0.0 | 7.0 |

- se:33 source top:
  - `x3-1` Agent:2,33,ga (20)
  - `x3-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x1-1` 2,11,to (20)
  - `x4-1` 2,11,ga (20)

### S4 / imi01 / none (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=5, sy:11=3, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=2.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 3 | 2.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x2-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)

### S4 / imi01 / plus2 (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=5, sy:11=5, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=4.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 5 | 4.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x10-1` 2,11,ga (24)
  - `x12-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
  - `x13-1` 4,11,ga (8)
  - `x8-1` 2,11,ga (8)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)

### S4 / imi02 / none (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=5, sy:11=3, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=2.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 3 | 2.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x2-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)

### S4 / imi02 / plus2 (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=5, sy:11=5, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=4.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 5 | 4.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x10-1` 2,11,ga (24)
  - `x12-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
  - `x13-1` 4,11,ga (8)
  - `x8-1` 2,11,ga (8)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)

### S4 / imi03 / none (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204]`
- initial families: `se:33=5, sy:11=3, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=2.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 3 | 2.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x2-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)

### S4 / imi03 / plus2 (unknown, node_limit)
- sentence: `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- lexicon_ids: `[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204, 309, 309]`
- initial families: `se:33=5, sy:11=5, sy:17=11`
- residual(avg): `se:33=4.0, sy:11=4.0, sy:17=1.0`

| family | initial | residual(avg) | estimated discharged |
|---|---:|---:|---:|
| se:33 | 5 | 4.0 | 1.0 |
| sy:11 | 5 | 4.0 | 1.0 |
| sy:17 | 11 | 1.0 | 10.0 |

- se:33 source top:
  - `x4-1` Agent:2,33,ga (20)
  - `x4-1` Theme:2,33,wo (20)
  - `x7-1` Agent:2,33,ga (20)
  - `x7-1` 相手:2,33,to (20)
- sy:11 source top:
  - `x10-1` 2,11,ga (24)
  - `x12-1` 2,11,wo (20)
  - `x5-1` 2,11,to (20)
  - `x13-1` 4,11,ga (8)
  - `x8-1` 2,11,ga (8)
- sy:17 source top:
  - `x9-1` 0,17,N,,,right,nonhead (20)
