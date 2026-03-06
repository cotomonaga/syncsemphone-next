# imi01語彙追加可否 事実抽出レポート（2026-03-02）

## 結論

- [確認済み事実] 最終判定: **C**
- [確認済み事実] 判定理由: 全案が unknown のため、語彙追加のみ不可と断定する根拠は不足（unreachable確証なし）
- [未確認] 未知探索領域が残るため B の断定条件を満たさない

## 確認済み事実

- [確認済み事実] Grammar固定: imi01、auto_add_ga_phi=false、探索器改修なし。
- [確認済み事実] S2/S3/S4 × 4提案（baseline+3）を同一予算で実測。

## 未確認

- [未確認] unknown は探索打切りであり、unreachable確定ではない。
- [未確認] best-sample 由来の source には process/tree 参照が含まれない。

## 推測

- [推測] なし（本レポートは原則として実測・コード・CSVのみ）。

## S2/S3/S4 の role discharge 表

### 目標役割割当（作業前提）
| sentence | predicate | role | target NP |
|---|---|---|---|
| S2 | 食べている | Theme | わたあめ |
| S2 | 食べている | Agent | ひつじ |
| S2 | いる | Theme | ひつじ |
| S3 | 話している | 相手 | ひつじ |
| S3 | 話している | Agent | うさぎ |
| S3 | いる | Theme | うさぎ |
| S4 | 食べている | Theme | わたあめ |
| S4 | 食べている | Agent | ひつじ |
| S4 | 話している | 相手 | ひつじ |
| S4 | 話している | Agent | うさぎ |
| S4 | いる | Theme | うさぎ |

- [確認済み事実] 上表はユーザー依頼の自然解釈ターゲットとして固定。

### code-grounded discharge 条件
| role | 要求側 item/label | 供給側 item/label | merge方向 | execute分岐 | 現行lexiconに供給候補 | 実測確認 |
|---|---|---|---|---|---|---|
| S2/S4: 食べている(266) Agent | 食べている(266) / Agent:2,33,ga | ひつじ(267) / ひつじ(9001) / 4,11,ga (or 2,11,ga after sy処理) | verbがhead, supply側がnon-head（RH:右head or LH:左head） | _process_se_imi03 number==33 (execute.py:395-409) | False | 確認済み事実 |
| S3/S4: 話している(269) Agent | 話している(269) / Agent:2,33,ga | うさぎ(270) / うさぎ(9002) / 4,11,ga (or 2,11,ga) | verbがhead, supply側がnon-head（RH:右head or LH:左head） | _process_se_imi03 number==33 (execute.py:395-409) | False | 確認済み事実 |
| S3/S4: 話している(269) 相手 | 話している(269) / 相手:2,33,to | と(268) / ひつじ(9001) / 4,11,to (or 2,11,to) | verbがhead, supply側がnon-head（RH:右head or LH:左head） | _process_se_imi03 number==33 (execute.py:395-409) | True | 確認済み事実 |

## 候補 lexical item 棚卸し（を/と/が/る/φ）

| surface | lexicon_id | entry | category | classification | reason_codes | sync_features | semantics |
|---|---:|---|---|---|---|---|---|
| を | 23 | を | J | imi01_meaningful_candidate | - | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,wo | - |
| を | 181 | を | Z | imi01_meaningless_candidate | requires_japanese2_l_feature | 2,1,N<br>2,3L,V<br>wo | 状況:0,24 |
| を | 197 | を | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - |
| を | 297 | を | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - |
| と | 171 | と | Z | imi01_meaningful_candidate | - | to | Content:0,24 |
| と | 268 | と | J | imi01_meaningful_candidate | - | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,to | - |
| が | 19 | が | J | imi01_meaningful_candidate | - | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,ga | - |
| が | 183 | が | J | imi01_meaningless_candidate | missing_required_rule | 2,1,N<br>ga<br>1,5,J-Merge | - |
| が | 196 | が | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - |
| が | 263 | が | J | imi01_meaningful_candidate | - | - | - |
| が | 294 | が | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - |
| る | 125 | る | T | imi01_meaningful_candidate | - | 2,1,V | Time:imperfect |
| る | 204 | る | T | imi01_meaningful_candidate | - | 0,17,V,,,right,nonhead | Time:imperfect |
| る | 308 | る | T | imi01_meaningful_candidate | - | 2,1,V | Time:imperfect |
| φ | 195 | φ | N | imi01_meaningful_candidate | - | - | - |
| φ | 196 | が | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - |
| φ | 197 | を | J | imi01_meaningless_candidate | missing_required_rule,requires_japanese2_l_feature | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - |
| φ | 236 | Pred | Pred | imi01_meaningful_candidate | - | 2,56,id | - |
| φ | 272 | φ | N | imi01_meaningful_candidate | - | 3,53,target, id<br>4,11,ga | - |
| φ | 273 | φ | N | imi01_meaningful_candidate | - | 3,53,target, id<br>4,11,wo | - |
| φ | 274 | φ | N | imi01_meaningful_candidate | - | 3,53,target, id<br>4,11,ni | - |
| φ | 275 | φ | N | imi01_meaningful_candidate | - | 2,17,N,,,left,nonhead | :2,27,target<br>＝:2,22 |
| φ | 309 | φ | N | imi01_meaningful_candidate | - | 4,11,ga | - |
| φ | 310 | φ | N | imi01_meaningful_candidate | - | 4,11,wo | - |
| φ | 311 | φ | N | imi01_meaningful_candidate | - | 4,11,ni | - |

### 提案CSV行（新規ID）
- [確認済み事実] 以下3行を temporary lexicon-all.csv に追記して A/B 実測。
```tsv
9001	ひつじ	ひつじ	N	0				2	4,11,ga	4,11,to				id	1	ひつじ	T											probe20260302	0
9002	うさぎ	うさぎ	N	0				1	4,11,ga					id	1	うさぎ	T											probe20260302	0
9003	が	が	J	0				4	0,17,N,,,right,nonhead	3,17,V,,,left,nonhead	4,11,ga	4,11,ga		zero	0													probe20260302	0
```

## A/B 実測表（imi01固定）

| sentence | proposal_id | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top(se:33) | history上位 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| S2 | baseline_auto | unknown | node_limit | 40000 | 6 | 4 | 2.0 | 1.0 | 1.0 | x3-1:Agent:2,33,ga(10); x3-1:Theme:2,33,wo(10) | [未確認] unreachable/unknown でevidence無し |
| S2 | lex_add_headnoun_features | unknown | node_limit | 40000 | 6 | 4 | 2.0 | 1.0 | 1.0 | x3-1:Agent:2,33,ga(10); x3-1:Theme:2,33,wo(10) | [未確認] unreachable/unknown でevidence無し |
| S2 | lex_add_particle_ga_double | unknown | node_limit | 40000 | 6 | 4 | 2.0 | 1.0 | 1.0 | x3-1:Agent:2,33,ga(10); x3-1:Theme:2,33,wo(10) | [未確認] unreachable/unknown でevidence無し |
| S2 | lex_add_combined | unknown | node_limit | 40000 | 6 | 4 | 2.0 | 1.0 | 1.0 | x3-1:Agent:2,33,ga(10); x3-1:Theme:2,33,wo(10) | [未確認] unreachable/unknown でevidence無し |
| S3 | baseline_auto | unknown | node_limit | 40000 | 6 | 5 | 2.0 | 2.2 | 0.8 | x3-1:Agent:2,33,ga(10); x3-1:相手:2,33,to(10) | [未確認] unreachable/unknown でevidence無し |
| S3 | lex_add_headnoun_features | unknown | node_limit | 40000 | 6 | 5 | 2.0 | 2.2 | 0.8 | x3-1:Agent:2,33,ga(10); x3-1:相手:2,33,to(10) | [未確認] unreachable/unknown でevidence無し |
| S3 | lex_add_particle_ga_double | unknown | node_limit | 40000 | 6 | 5 | 2.0 | 2.2 | 0.8 | x3-1:Agent:2,33,ga(10); x3-1:相手:2,33,to(10) | [未確認] unreachable/unknown でevidence無し |
| S3 | lex_add_combined | unknown | node_limit | 40000 | 6 | 5 | 2.0 | 2.2 | 0.8 | x3-1:Agent:2,33,ga(10); x3-1:相手:2,33,to(10) | [未確認] unreachable/unknown でevidence無し |
| S4 | baseline_auto | unknown | node_limit | 40000 | 10 | 10 | 4.0 | 5.0 | 1.0 | x4-1:Agent:2,33,ga(10); x4-1:Theme:2,33,wo(10); x7-1:Agent:2,33,ga(10) | [未確認] unreachable/unknown でevidence無し |
| S4 | lex_add_headnoun_features | unknown | node_limit | 40000 | 10 | 10 | 4.0 | 5.0 | 1.0 | x4-1:Agent:2,33,ga(10); x4-1:Theme:2,33,wo(10); x7-1:Agent:2,33,ga(10) | [未確認] unreachable/unknown でevidence無し |
| S4 | lex_add_particle_ga_double | unknown | node_limit | 40000 | 10 | 10 | 4.0 | 5.0 | 1.0 | x4-1:Agent:2,33,ga(10); x4-1:Theme:2,33,wo(10); x7-1:Agent:2,33,ga(10) | [未確認] unreachable/unknown でevidence無し |
| S4 | lex_add_combined | unknown | node_limit | 40000 | 10 | 10 | 4.0 | 5.0 | 1.0 | x4-1:Agent:2,33,ga(10); x4-1:Theme:2,33,wo(10); x7-1:Agent:2,33,ga(10) | [未確認] unreachable/unknown でevidence無し |

### Yes/No 判定（3問）
| question | yes/no | 最小反例 | status/reason | residual source | code path |
|---|---|---|---|---|---|
| 食べている(266) Agent:2,33,ga は S2/S4 で head noun ひつじにより imi01 RH/LHだけで dischargeできるか | No | S2 + lex_add_combined | unknown/node_limit | Agent:2,33,ga が残存 | _process_se_imi03 number==33 requires matching sy label on non-head |
- [未確認] 局所不成立の正確なmerge地点: どの手順で不成立になったかは best-sample では未取得（history/tree不足）
| 話している(269) Agent:2,33,ga は S3/S4 で head noun うさぎにより imi01 RH/LHだけで dischargeできるか | No | S3 + lex_add_combined | unknown/node_limit | Agent:2,33,ga が残存 | _process_se_imi03 number==33 requires matching sy label on non-head |
- [未確認] 局所不成立の正確なmerge地点: どの手順で不成立になったかは best-sample では未取得（history/tree不足）
| 話している(269) 相手:2,33,to は S3/S4 で ひつじにより dischargeできるか | No | S3 + lex_add_combined | unknown/node_limit | 相手:2,33,to が残存 | _process_se_imi03 number==33 requires matching sy label on non-head |
- [未確認] 局所不成立の正確なmerge地点: どの手順で不成立になったかは best-sample では未取得（history/tree不足）
## 最終結論

- [確認済み事実] 3択判定: **C**
- [確認済み事実] 全案が unknown のため、語彙追加のみ不可と断定する根拠は不足（unreachable確証なし）
- [未確認] 未知探索領域が残るため B の断定条件を満たさない
