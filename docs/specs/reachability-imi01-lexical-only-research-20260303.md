# imi01 lexical-only 再調査レポート（2026-03-03）

## 1. 結論

- [確認済み事実] imi01固定で baseline/proposal を同一予算で実測した（runs=36）。
- [確認済み事実] 既存候補のみで自然条件を満たすreachable: 未観測。
- [未確認] unknown は探索打切りであり unreachable 断定ではない。
- [確認済み事実] 新規row(<=3)追加実測で最良は S3_new_9301_9402 / leaf_min=0 だが、S4自然reachableは未観測。

## 2. imi01 baseline

### S1: うさぎがいる
- [確認済み事実] tokens: ['うさぎ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [270, 19, 271, 204]
- [確認済み事実] status/reason: reachable / completed (generation_failed=False)

### S2: わたあめを食べているひつじがいる
- [確認済み事実] tokens: ['わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [265, 23, 266, 267, 19, 271, 204]
- [確認済み事実] status/reason: unknown / timeout (generation_failed=False)

### S3: ひつじと話しているうさぎがいる
- [確認済み事実] tokens: ['ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [267, 268, 269, 270, 19, 271, 204]
- [確認済み事実] status/reason: unknown / timeout (generation_failed=False)

### S4: ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
- [確認済み事実] tokens: ['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204]
- [確認済み事実] status/reason: unknown / timeout (generation_failed=False)

### S5: ふわふわしたひつじがいる
- [確認済み事実] tokens: ['ふわふわした', 'ひつじ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [264, 267, 19, 271, 204]
- [確認済み事実] status/reason: reachable / completed (generation_failed=False)

### S6: ふわふわしたわたあめを食べているひつじがいる
- [確認済み事実] tokens: ['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る']
- [確認済み事実] lexicon_ids: [264, 265, 23, 266, 267, 19, 271, 204]
- [確認済み事実] status/reason: unknown / timeout (generation_failed=False)

## 3. lexical candidate 棚卸し

| surface | lexicon_id | entry | category | idslot | step1_auto_may_select | used_in_past_reachable_examples | selected_in_current_baseline |
|---|---:|---|---|---|---|---|---|
| ふわふわした | 264 | ふわふわした | A | 2,22 | True | False | True |
| わたあめ | 265 | わたあめ | N | id | True | False | True |
| を | 23 | を | J | zero | True | True | True |
| を | 181 | を | Z | 2,22 | False | False | False |
| を | 197 | を | J | zero | False | False | False |
| を | 297 | を | J | zero | False | False | False |
| 食べている | 266 | 食べている | V | id | True | False | True |
| ひつじ | 267 | ひつじ | N | id | True | False | True |
| と | 171 | と | Z | 2,22 | True | False | False |
| と | 268 | と | J | zero | True | False | True |
| 話している | 269 | 話している | V | id | True | False | True |
| うさぎ | 270 | うさぎ | N | id | True | True | True |
| が | 19 | が | J | zero | True | True | True |
| が | 183 | が | J | zero | False | False | False |
| が | 196 | が | J | zero | False | False | False |
| が | 263 | が | J | - | True | False | False |
| が | 294 | が | J | zero | False | False | False |
| いる | 271 | いる | V | id | True | True | True |
| る | 125 | る | T | 0,24 | True | False | False |
| る | 204 | る | T | 0,24 | True | True | True |
| る | 308 | る | T | 0,24 | True | True | False |
| φ | 195 | φ | N | id | True | False | False |
| φ | 196 | が | J | zero | False | False | False |
| φ | 197 | を | J | zero | False | False | False |
| φ | 236 | Pred | Pred | zero | True | False | False |
| φ | 272 | φ | N | id | True | False | False |
| φ | 273 | φ | N | id | True | False | False |
| φ | 274 | φ | N | id | True | False | False |
| φ | 275 | φ | N | rel | True | False | False |
| φ | 309 | φ | N | id | True | False | False |
| φ | 310 | φ | N | id | True | False | False |
| φ | 311 | φ | N | id | True | False | False |

## 4. explicit numeration 候補一覧

### S2
- [確認済み事実] `baseline` ids=[265, 23, 266, 267, 19, 271, 204] / 狙い=baseline auto-generated IDs / 期待=baseline behavior observation / hard_reject想定=未確認
- [確認済み事実] `wo_181` ids=[265, 181, 266, 267, 19, 271, 204] / 狙い=わたあめ-を-食べている の局所case packaging / 期待=食べている Theme:2,33,wo 側の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197` ids=[265, 197, 266, 267, 19, 271, 204] / 狙い=わたあめ-を-食べている の局所case packaging / 期待=食べている Theme:2,33,wo 側の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_297` ids=[265, 297, 266, 267, 19, 271, 204] / 狙い=わたあめ-を-食べている の局所case packaging / 期待=食べている Theme:2,33,wo 側の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_183` ids=[265, 23, 266, 267, 183, 271, 204] / 狙い=ひつじ-が-いる の主語case packaging / 期待=Agent/Theme の ga 要求解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_196` ids=[265, 23, 266, 267, 196, 271, 204] / 狙い=ひつじ-が-いる の主語case packaging / 期待=Agent/Theme の ga 要求解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_263` ids=[265, 23, 266, 267, 263, 271, 204] / 狙い=ひつじ-が-いる の主語case packaging / 期待=Agent/Theme の ga 要求解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_294` ids=[265, 23, 266, 267, 294, 271, 204] / 狙い=ひつじ-が-いる の主語case packaging / 期待=Agent/Theme の ga 要求解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_181_ga_183` ids=[265, 181, 266, 267, 183, 271, 204] / 狙い=わたあめ-を と ひつじ-が を同時調整 / 期待=食べている/いる の 33 要求同時解消 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_181_ga_196` ids=[265, 181, 266, 267, 196, 271, 204] / 狙い=わたあめ-を と ひつじ-が を同時調整 / 期待=食べている/いる の 33 要求同時解消 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197_ga_183` ids=[265, 197, 266, 267, 183, 271, 204] / 狙い=わたあめ-を と ひつじ-が を同時調整 / 期待=食べている/いる の 33 要求同時解消 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197_ga_196` ids=[265, 197, 266, 267, 196, 271, 204] / 狙い=わたあめ-を と ひつじ-が を同時調整 / 期待=食べている/いる の 33 要求同時解消 / hard_reject想定=確認済み事実
- [確認済み事実] `ru_308` ids=[265, 23, 266, 267, 19, 271, 308] / 狙い=いる-T の時制側選び直し / 期待=2,1L,T など時制要求の影響確認 / hard_reject想定=確認済み事実
- [確認済み事実] `ru_125` ids=[265, 23, 266, 267, 19, 271, 125] / 狙い=いる-T の時制側選び直し / 期待=2,1L,T など時制要求の影響確認 / hard_reject想定=確認済み事実
- [確認済み事実] `phi_plus1_309` ids=[265, 23, 266, 267, 19, 271, 204, 309] / 狙い=比較用: φを1件追加 / 期待=count補完比較（採用前提なし） / hard_reject想定=未確認

### S3
- [確認済み事実] `baseline` ids=[267, 268, 269, 270, 19, 271, 204] / 狙い=baseline auto-generated IDs / 期待=baseline behavior observation / hard_reject想定=未確認
- [確認済み事実] `to_171` ids=[267, 171, 269, 270, 19, 271, 204] / 狙い=ひつじ-と-話している の局所case packaging / 期待=話している 相手:2,33,to の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_183` ids=[267, 268, 269, 270, 183, 271, 204] / 狙い=うさぎ-が-いる の主語case packaging / 期待=話している Agent:2,33,ga の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_196` ids=[267, 268, 269, 270, 196, 271, 204] / 狙い=うさぎ-が-いる の主語case packaging / 期待=話している Agent:2,33,ga の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_263` ids=[267, 268, 269, 270, 263, 271, 204] / 狙い=うさぎ-が-いる の主語case packaging / 期待=話している Agent:2,33,ga の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_294` ids=[267, 268, 269, 270, 294, 271, 204] / 狙い=うさぎ-が-いる の主語case packaging / 期待=話している Agent:2,33,ga の解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `to_171_ga_183` ids=[267, 171, 269, 270, 183, 271, 204] / 狙い=ひつじ-と と うさぎ-が を同時調整 / 期待=話している 相手/Agent の同時解消 / hard_reject想定=確認済み事実
- [確認済み事実] `ru_308` ids=[267, 268, 269, 270, 19, 271, 308] / 狙い=いる-T の時制側選び直し / 期待=時制要求の影響確認 / hard_reject想定=確認済み事実
- [確認済み事実] `ru_125` ids=[267, 268, 269, 270, 19, 271, 125] / 狙い=いる-T の時制側選び直し / 期待=時制要求の影響確認 / hard_reject想定=確認済み事実
- [確認済み事実] `phi_plus1_309` ids=[267, 268, 269, 270, 19, 271, 204, 309] / 狙い=比較用: φを1件追加 / 期待=count補完比較（採用前提なし） / hard_reject想定=未確認

### S4
- [確認済み事実] `baseline` ids=[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204] / 狙い=baseline auto-generated IDs / 期待=baseline behavior observation / hard_reject想定=未確認
- [確認済み事実] `wo_181` ids=[264, 265, 181, 266, 267, 268, 269, 270, 19, 271, 204] / 狙い=わたあめ-を-食べている を局所調整 / 期待=食べている Theme:2,33,wo 解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197` ids=[264, 265, 197, 266, 267, 268, 269, 270, 19, 271, 204] / 狙い=わたあめ-を-食べている を局所調整 / 期待=食べている Theme:2,33,wo 解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_297` ids=[264, 265, 297, 266, 267, 268, 269, 270, 19, 271, 204] / 狙い=わたあめ-を-食べている を局所調整 / 期待=食べている Theme:2,33,wo 解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `to_171` ids=[264, 265, 23, 266, 267, 171, 269, 270, 19, 271, 204] / 狙い=ひつじ-と-話している を局所調整 / 期待=話している 相手:2,33,to 解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `ga_183` ids=[264, 265, 23, 266, 267, 268, 269, 270, 183, 271, 204] / 狙い=うさぎ-が-いる の主語case packaging / 期待=話している/いる の ga 要求解消支援 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_181_to_171` ids=[264, 265, 181, 266, 267, 171, 269, 270, 19, 271, 204] / 狙い=食べ-clause と 話す-clause のcase同時調整 / 期待=33要求パケット同時圧縮 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197_to_171` ids=[264, 265, 197, 266, 267, 171, 269, 270, 19, 271, 204] / 狙い=食べ-clause と 話す-clause のcase同時調整 / 期待=33要求パケット同時圧縮 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_181_to_171_ga_183` ids=[264, 265, 181, 266, 267, 171, 269, 270, 183, 271, 204] / 狙い=を/と/が の三者同時調整 / 期待=S4全体の33要求圧縮 / hard_reject想定=確認済み事実
- [確認済み事実] `wo_197_to_171_ga_183` ids=[264, 265, 197, 266, 267, 171, 269, 270, 183, 271, 204] / 狙い=を/と/が の三者同時調整 / 期待=S4全体の33要求圧縮 / hard_reject想定=確認済み事実
- [確認済み事実] `phi_plus2_309_311` ids=[264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204, 309, 311] / 狙い=比較用: φを2件追加 / 期待=count補完比較（採用前提なし） / hard_reject想定=未確認

## 5. 実測結果

| sentence | proposal | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural_evidence |
|---|---|---|---|---|---:|---:|---:|---|---|---|
| S2 | baseline | [265, 23, 266, 267, 19, 271, 204] | unknown | timeout | 63994 | 6 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S2 | wo_181 | [265, 181, 266, 267, 19, 271, 204] | unknown | timeout | 66234 | 6 | 3 | {'se:33': 20, 'sy:17': 8} | False | False |
| S2 | wo_197 | [265, 197, 266, 267, 19, 271, 204] | unknown | timeout | 68441 | 6 | 4 | {'se:33': 20, 'sy:17': 10, 'sy:5': 10} | False | False |
| S2 | wo_297 | [265, 297, 266, 267, 19, 271, 204] | unknown | timeout | 65769 | 6 | 4 | {'se:33': 20, 'sy:17': 10, 'sy:5': 10} | False | False |
| S2 | ga_183 | [265, 23, 266, 267, 183, 271, 204] | unknown | timeout | 65079 | 6 | 5 | {'se:33': 30, 'sy:11': 10, 'sy:5': 10} | False | False |
| S2 | ga_196 | [265, 23, 266, 267, 196, 271, 204] | unknown | timeout | 67675 | 6 | 6 | {'se:33': 30, 'sy:11': 10, 'sy:5': 10} | False | False |
| S2 | ga_263 | [265, 23, 266, 267, 263, 271, 204] | unknown | timeout | 68361 | 6 | 4 | {'se:33': 30, 'sy:11': 10} | False | False |
| S2 | ga_294 | [265, 23, 266, 267, 294, 271, 204] | unknown | timeout | 63678 | 6 | 6 | {'se:33': 30, 'sy:11': 10, 'sy:17': 10, 'sy:5': 10} | False | False |
| S2 | wo_181_ga_183 | [265, 181, 266, 267, 183, 271, 204] | unknown | timeout | 67834 | 6 | 5 | {'se:33': 30, 'sy:17': 10, 'sy:5': 10} | False | False |
| S2 | wo_181_ga_196 | [265, 181, 266, 267, 196, 271, 204] | unknown | timeout | 69779 | 6 | 6 | {'se:33': 30, 'sy:5': 10} | False | False |
| S2 | wo_197_ga_183 | [265, 197, 266, 267, 183, 271, 204] | unknown | timeout | 69742 | 6 | 6 | {'se:33': 30, 'sy:5': 20, 'sy:17': 10} | False | False |
| S2 | wo_197_ga_196 | [265, 197, 266, 267, 196, 271, 204] | unknown | timeout | 70921 | 6 | 7 | {'se:33': 30, 'sy:5': 20, 'sy:17': 10} | False | False |
| S2 | ru_308 | [265, 23, 266, 267, 19, 271, 308] | unknown | timeout | 64257 | 6 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S2 | ru_125 | [265, 23, 266, 267, 19, 271, 125] | unknown | timeout | 59132 | 6 | 3 | {'se:33': 20, 'sy:11': 10, 'sy:17': 2} | False | False |
| S2 | phi_plus1_309 | [265, 23, 266, 267, 19, 271, 204, 309] | unknown | timeout | 60112 | 7 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S3 | baseline | [267, 268, 269, 270, 19, 271, 204] | unknown | timeout | 63900 | 6 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S3 | to_171 | [267, 171, 269, 270, 19, 271, 204] | unknown | timeout | 68087 | 6 | 2 | {'se:33': 20} | False | False |
| S3 | ga_183 | [267, 268, 269, 270, 183, 271, 204] | unknown | timeout | 64847 | 6 | 5 | {'se:33': 30, 'sy:11': 10, 'sy:5': 10} | False | False |
| S3 | ga_196 | [267, 268, 269, 270, 196, 271, 204] | unknown | timeout | 60214 | 6 | 6 | {'se:33': 30, 'sy:11': 10, 'sy:5': 10} | False | False |
| S3 | ga_263 | [267, 268, 269, 270, 263, 271, 204] | unknown | timeout | 65024 | 6 | 4 | {'se:33': 30, 'sy:11': 10} | False | False |
| S3 | ga_294 | [267, 268, 269, 270, 294, 271, 204] | unknown | timeout | 62263 | 6 | 6 | {'se:33': 30, 'sy:11': 10, 'sy:17': 10, 'sy:5': 10} | False | False |
| S3 | to_171_ga_183 | [267, 171, 269, 270, 183, 271, 204] | unknown | timeout | 67069 | 6 | 4 | {'se:33': 30, 'sy:5': 10} | False | False |
| S3 | ru_308 | [267, 268, 269, 270, 19, 271, 308] | unknown | timeout | 64319 | 6 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S3 | ru_125 | [267, 268, 269, 270, 19, 271, 125] | unknown | timeout | 58635 | 6 | 3 | {'se:33': 20, 'sy:11': 10, 'sy:17': 2} | False | False |
| S3 | phi_plus1_309 | [267, 268, 269, 270, 19, 271, 204, 309] | unknown | timeout | 59803 | 7 | 3 | {'se:33': 20, 'sy:11': 10} | False | False |
| S4 | baseline | [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204] | unknown | timeout | 46471 | 10 | 7 | {'se:33': 40, 'sy:11': 20, 'sy:17': 10} | False | False |
| S4 | wo_181 | [264, 265, 181, 266, 267, 268, 269, 270, 19, 271, 204] | unknown | timeout | 45262 | 10 | 8 | {'se:33': 40, 'sy:17': 20, 'sy:11': 10} | False | False |
| S4 | wo_197 | [264, 265, 197, 266, 267, 268, 269, 270, 19, 271, 204] | unknown | timeout | 47356 | 10 | 8 | {'se:33': 40, 'sy:17': 20, 'sy:11': 10, 'sy:5': 10} | False | False |
| S4 | wo_297 | [264, 265, 297, 266, 267, 268, 269, 270, 19, 271, 204] | unknown | timeout | 44864 | 10 | 8 | {'se:33': 40, 'sy:17': 20, 'sy:11': 10, 'sy:5': 10} | False | False |
| S4 | to_171 | [264, 265, 23, 266, 267, 171, 269, 270, 19, 271, 204] | unknown | timeout | 46974 | 10 | 6 | {'se:33': 40, 'sy:11': 10, 'sy:17': 10} | False | False |
| S4 | ga_183 | [264, 265, 23, 266, 267, 268, 269, 270, 183, 271, 204] | unknown | timeout | 45615 | 10 | 11 | {'se:33': 50, 'sy:17': 30, 'sy:11': 20, 'sy:5': 10} | False | False |
| S4 | wo_181_to_171 | [264, 265, 181, 266, 267, 171, 269, 270, 19, 271, 204] | unknown | timeout | 46243 | 10 | 7 | {'se:33': 40, 'sy:17': 20} | False | False |
| S4 | wo_197_to_171 | [264, 265, 197, 266, 267, 171, 269, 270, 19, 271, 204] | unknown | timeout | 40093 | 10 | 7 | {'se:33': 40, 'sy:17': 10, 'sy:5': 10} | False | False |
| S4 | wo_181_to_171_ga_183 | [264, 265, 181, 266, 267, 171, 269, 270, 183, 271, 204] | unknown | timeout | 45894 | 10 | 8 | {'se:33': 50, 'sy:17': 10, 'sy:5': 10} | False | False |
| S4 | wo_197_to_171_ga_183 | [264, 265, 197, 266, 267, 171, 269, 270, 183, 271, 204] | unknown | timeout | 45036 | 10 | 8 | {'se:33': 50, 'sy:5': 20} | False | False |
| S4 | phi_plus2_309_311 | [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 204, 309, 311] | unknown | timeout | 42518 | 12 | 9 | {'se:33': 40, 'sy:11': 40, 'sy:17': 10} | False | False |

## 6. hard reject 監査


## 7. 新規 lexical item 案

- [確認済み事実] proposal: to_171_lite (id=9301)
  - [確認済み事実] csv_row: `9301 	と	と	Z	0 					1	to							2,22	0 															imi01-probe:171-lite	0`
  - [確認済み事実] rationale: 171 の Content:0,24 を外し、S3 で観測された局所改善（to側）を維持しつつ、S4 の 24系副作用を避ける狙い。
- [確認済み事実] proposal: eat_progressive_rc_lite (id=9401)
  - [確認済み事実] csv_row: `9401 	食べている	食べている	V	0 					1	0,17,N,,,left,nonhead							id	3 	Theme	2,33,wo	食べる	T	Aspect	progressive							imi01-probe:eat-rc-lite	0`
  - [確認済み事実] rationale: 266 の Agent 要求を lexical 側で緩和し、S2/S4 の se:33 パケット（食べ-clause側）を縮められるかを確認する狙い。
- [確認済み事実] proposal: talk_progressive_rc_lite (id=9402)
  - [確認済み事実] csv_row: `9402 	話している	話している	V	0 					1	0,17,N,,,left,nonhead							id	3 	相手	2,33,to	話す	T	Aspect	progressive							imi01-probe:talk-rc-lite	0`
  - [確認済み事実] rationale: 269 の Agent 要求を lexical 側で緩和し、S3/S4 の se:33 パケット（話す-clause側）を縮められるかを確認する狙い。

### 新規 row 実測

| proposal | sentence | ids | status | reason | actions | depth | leaf_min | evidence | natural_evidence |
|---|---|---|---|---|---:|---:|---:|---|---|
| S2_new_9401 | S2 | [265, 23, 9401, 267, 19, 271, 204] | unknown | timeout | 64537 | 6 | 1 | False | False |
| S3_new_9301_9402 | S3 | [267, 9301, 9402, 270, 19, 271, 204] | reachable | timeout | 69434 | 6 | 0 | True | True |
| S4_new_9301_9401_9402 | S4 | [264, 265, 23, 9401, 267, 9301, 9402, 270, 19, 271, 204] | unknown | timeout | 51032 | 10 | 2 | False | False |
| S4_new_9301_9401_9402_wo181 | S4 | [264, 265, 181, 9401, 267, 9301, 9402, 270, 19, 271, 204] | unknown | timeout | 50879 | 10 | 3 | False | False |

### 新規 row hard reject 監査
- [確認済み事実] S3_new_9301_9402:rank1: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S3_new_9301_9402:rank2: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S3_new_9301_9402:rank3: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S3_new_9301_9402:rank4: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S3_new_9301_9402:rank5: hard_reject=False replay_failed=None violations=[]

## 8. 最終判断

- [確認済み事実] 8-1 既存 lexical item だけで到達可能か: no_or_unconfirmed
- [確認済み事実] 8-2 最善 explicit numeration: {'status': '未確認', 'value': '既存候補のみの自然reachable未観測。新規rowは leaf_min 改善のみ確認。'}
- [確認済み事実] 8-3 最小新規 lexical item 案: {'status': '確認済み事実', 'value': {'proposal_id': 'S3_new_9301_9402', 'sentence_key': 'S3', 'explicit_lexicon_ids': [267, 9301, 9402, 270, 19, 271, 204], 'best_leaf_unresolved_min': 0, 'status': 'reachable', 'reason': 'timeout'}}
- [確認済み事実] 8-4 到達証拠の採用可否: 未確定

## 9. 未確認事項

- [未確認] hard reject 条件の一部（名詞句完成前の判定）は rule_sequence だけでは厳密定義が不足する。
- [未確認] candidate compatibility の『選ばれうる』は文脈依存であり、単一トークン判定は近似。
- [未確認] best_samples 由来 residual source は leaf上位の集約であり、全探索の証明ではない。
