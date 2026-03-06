# Reachability 事実抽出レポート（2026-03-02）

## 1. 概要

- [確認済み事実] 実測条件: grammar=`imi01, imi02, imi03`, split_mode=`A`, budget_seconds=`120.0`, max_nodes=`40000`, max_depth=`28`, top_k=`10`
- [確認済み事実] 依頼1〜7の抽出値は `code/csv/実測ログ` 起点で JSON に保存。
- [未確認] process/tree 参照は現抽出経路で null のまま。

## 2. 語彙候補一覧

- [確認済み事実] `lexicon-all.csv` 候補と、Step.1自動生成（実測）での選択有無。

| surface | lexicon_id | 見出し | 範疇 | idslot | sync_features | semantics | auto選択(imi01/02/03) | reachable既知セット使用 |
|---|---:|---|---|---|---|---|---|---|
| ふわふわした | 264 | ふわふわした | A | 2,22 | 0,17,N,,,left,nonhead | ふわふわした:T | 1 / 1 / 1 | False |
| わたあめ | 265 | わたあめ | N | id | - | わたあめ:T | 1 / 1 / 1 | False |
| を | 23 | を | J | zero | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,wo | - | 1 / 1 / 1 | True |
| を | 181 | を | Z | 2,22 | 2,1,N<br>2,3L,V<br>wo | 状況:0,24 | 0 / 0 / 0 | False |
| を | 197 | を | J | zero | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| を | 297 | を | J | zero | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| 食べている | 266 | 食べている | V | id | 2,17,N,,,left,nonhead | Theme:2,33,wo<br>Agent:2,33,ga<br>食べる:T<br>Aspect:progressive | 1 / 1 / 1 | False |
| ひつじ | 267 | ひつじ | N | id | - | ひつじ:T | 1 / 1 / 1 | False |
| と | 171 | と | Z | 2,22 | to | Content:0,24 | 0 / 0 / 0 | False |
| と | 268 | と | J | zero | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,to | - | 1 / 1 / 1 | False |
| 話している | 269 | 話している | V | id | 0,17,N,,,left,nonhead | 相手:2,33,to<br>Agent:2,33,ga<br>話す:T<br>Aspect:progressive | 1 / 1 / 1 | False |
| うさぎ | 270 | うさぎ | N | id | - | うさぎ:T | 1 / 1 / 1 | True |
| が | 19 | が | J | zero | 0,17,N,,,right,nonhead<br>3,17,V,,,left,nonhead<br>4,11,ga | - | 1 / 1 / 1 | True |
| が | 183 | が | J | zero | 2,1,N<br>ga<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| が | 196 | が | J | zero | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| が | 263 | が | J | - | - | - | 0 / 0 / 0 | False |
| が | 294 | が | J | zero | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| いる | 271 | いる | V | id | 2,17,T,,,left,head | Theme:2,33,ga<br>いる:T | 1 / 1 / 1 | True |
| る | 125 | る | T | 0,24 | 2,1,V | Time:imperfect | 0 / 0 / 0 | True |
| る | 204 | る | T | 0,24 | 0,17,V,,,right,nonhead | Time:imperfect | 1 / 1 / 1 | True |
| る | 308 | る | T | 0,24 | 2,1,V | Time:imperfect | 0 / 0 / 0 | True |
| φ | 195 | φ | N | id | - | - | 0 / 0 / 0 | False |
| φ | 196 | が | J | zero | 2,1,N<br>2,1L,T<br>ga<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| φ | 197 | を | J | zero | 2,1,N<br>2,3L,V<br>wo<br>1,5,J-Merge | - | 0 / 0 / 0 | False |
| φ | 236 | Pred | Pred | zero | 2,56,id | - | 0 / 0 / 0 | False |
| φ | 272 | φ | N | id | 3,53,target, id<br>4,11,ga | - | 0 / 0 / 0 | False |
| φ | 273 | φ | N | id | 3,53,target, id<br>4,11,wo | - | 0 / 0 / 0 | False |
| φ | 274 | φ | N | id | 3,53,target, id<br>4,11,ni | - | 0 / 0 / 0 | False |
| φ | 275 | φ | N | rel | 2,17,N,,,left,nonhead | :2,27,target<br>＝:2,22 | 0 / 0 / 0 | False |
| φ | 309 | φ | N | id | 4,11,ga | - | 0 / 0 / 0 | False |
| φ | 310 | φ | N | id | 4,11,wo | - | 0 / 0 / 0 | False |
| φ | 311 | φ | N | id | 4,11,ni | - | 0 / 0 / 0 | False |

## 3. Grammar 候補一覧

- [確認済み事実] `load_rule_catalog` で読める grammar は完全表を掲載。
- [未確認] rule file 不在 grammar はエラーを併記。
- [推測] `rc_related_guess` は rule_name 文字列ベース。

### primary
- grammar `imi01`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| imi01 | 1 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_03.pl | False | False |
| imi01 | 2 | LH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/LH-Merge_03.pl | False | False |
- grammar `imi02`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| imi02 | 1 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_03.pl | False | False |
| imi02 | 2 | LH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/LH-Merge_03.pl | False | False |
| imi02 | 3 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_02.pl | True | False |
- grammar `imi03`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| imi03 | 1 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_03.pl | False | False |
| imi03 | 2 | LH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/LH-Merge_03.pl | False | False |
| imi03 | 3 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_02.pl | True | False |
### others
- grammar `chinese1`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/chinese1/chinese1R.pl`
- grammar `chinese2`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/chinese2/chinese2R.pl`
- grammar `chinese3`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/chinese3/chinese3R.pl`
- grammar `ex1`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/ex1/ex1R.pl`
- grammar `ex2`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/ex2/ex2R.pl`
- grammar `japanese1`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| japanese1 | 1 | sase1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase1_01.pl | True | False |
| japanese1 | 2 | sase2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase2_01.pl | True | False |
| japanese1 | 3 | rare2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare2_01.pl | True | False |
| japanese1 | 4 | rare1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare1_01.pl | True | False |
| japanese1 | 5 | property-no | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-no_01.pl | True | True |
| japanese1 | 6 | property-da | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-da_02.pl | True | True |
| japanese1 | 7 | property-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-Merge_01.pl | True | True |
| japanese1 | 8 | rel-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rel-Merge_02.pl | True | True |
| japanese1 | 9 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_02.pl | False | False |
| japanese1 | 10 | LH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/LH-Merge_02.pl | False | False |
| japanese1 | 11 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_01.pl | True | False |
- grammar `japanese2`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| japanese2 | 1 | sase1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase1_01.pl | True | False |
| japanese2 | 2 | sase2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase2_02.pl | True | False |
| japanese2 | 3 | rare2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare2_01.pl | True | False |
| japanese2 | 4 | rare1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare1_01.pl | True | False |
| japanese2 | 5 | property-no | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-no_01.pl | True | True |
| japanese2 | 6 | property-da | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-da_01.pl | True | True |
| japanese2 | 7 | J-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/J-Merge_01.pl | True | True |
| japanese2 | 8 | P-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/P-Merge_01.pl | True | False |
| japanese2 | 9 | property-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-Merge_01.pl | True | True |
| japanese2 | 10 | rel-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rel-Merge_01.pl | True | True |
| japanese2 | 11 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_01.pl | False | False |
| japanese2 | 12 | Pickup | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Pickup_01.pl | True | True |
| japanese2 | 13 | Landing | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Landing_02.pl | True | True |
| japanese2 | 14 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_01.pl | True | False |
| japanese2 | 15 | Partitioning | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Partitioning_01.pl | True | True |
- grammar `japanese3`
| grammar_id | rule_number | rule_name | rule_kind | 実体ファイル | 非RH/LH | rc_related_guess |
|---|---:|---|---|---|---|---|
| japanese3 | 1 | sase1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase1_01.pl | True | False |
| japanese3 | 2 | sase2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase2_02.pl | True | False |
| japanese3 | 3 | rare2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare2_01.pl | True | False |
| japanese3 | 4 | rare1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare1_01.pl | True | False |
| japanese3 | 5 | property-no | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-no_01.pl | True | True |
| japanese3 | 6 | property-da | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-da_01.pl | True | True |
| japanese3 | 7 | J-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/J-Merge_01.pl | True | True |
| japanese3 | 8 | P-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/P-Merge_01.pl | True | False |
| japanese3 | 9 | property-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-Merge_01.pl | True | True |
| japanese3 | 10 | rel-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rel-Merge_01.pl | True | True |
| japanese3 | 11 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_01.pl | False | False |
| japanese3 | 12 | LH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/LH-Merge_07.pl | False | False |
| japanese3 | 13 | Pickup | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Pickup_01.pl | True | True |
| japanese3 | 14 | Landing | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Landing_02.pl | True | True |
| japanese3 | 15 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_01.pl | True | False |
| japanese3 | 16 | Partitioning | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Partitioning_01.pl | True | True |
- grammar `jpf0`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf0/jpf0R.pl`
- grammar `jpf0e`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf0e/jpf0eR.pl`
- grammar `jpf1`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1/jpf1R.pl`
- grammar `jpf1a`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1a/jpf1aR.pl`
- grammar `jpf1b`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1b/jpf1bR.pl`
- grammar `jpf1c`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1c/jpf1cR.pl`
- grammar `jpf1d`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1d/jpf1dR.pl`
- grammar `jpf1d2`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1d2/jpf1d2R.pl`
- grammar `jpf1e`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1e/jpf1eR.pl`
- grammar `jpf1f`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1f/jpf1fR.pl`
- grammar `jpf1g`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf1g/jpf1gR.pl`
- grammar `jpf2`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf2/jpf2R.pl`
- grammar `jpf201801`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf201801/jpf201801R.pl`
- grammar `jpf201802`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf201802/jpf201802R.pl`
- grammar `jpf201803`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf201803/jpf201803R.pl`
- grammar `jpf201804`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf201804/jpf201804R.pl`
- grammar `jpf202001`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf202001/jpf202001R.pl`
- grammar `jpf202002`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf202002/jpf202002R.pl`
- grammar `jpf3`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf3/jpf3R.pl`
- grammar `jpf3few`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf3few/jpf3fewR.pl`
- grammar `jpf3minus`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf3minus/jpf3minusR.pl`
- grammar `jpf3more`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf3more/jpf3moreR.pl`
- grammar `jpf4`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf4/jpf4R.pl`
- grammar `jpf5`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf5/jpf5R.pl`
- grammar `jpf6`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/jpf6/jpf6R.pl`
- grammar `otago0`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/otago0/otago0R.pl`
- grammar `otago1`
  - [未確認] rules 読込失敗: `Rule file not found: /Users/tomonaga/Documents/syncsemphoneIMI/otago1/otago1R.pl`

## 4. reduced sentence ごとの residual 比較

| sentence | grammar | phi_mode | status | reason | actions_attempted | best_leaf_unresolved_min | best_leaf_residual_family_totals | best_mid_residual_family_totals | non_improving_ratio |
|---|---|---|---|---|---:|---:|---|---|---:|
| S1 | imi01 | none | reachable | completed | 160 | 0 | {"sy:17": 8} | {"sy:17": 17, "se:33": 1, "sy:11": 1} | 0.7 |
| S1 | imi01 | plus2 | reachable | node_limit | 40000 | 0 | {"sy:11": 2} | {"sy:11": 10} | 1.0 |
| S1 | imi02 | none | reachable | completed | 170 | 0 | {"sy:17": 8} | {"sy:17": 17, "se:33": 1, "sy:11": 1} | 0.7 |
| S1 | imi02 | plus2 | reachable | node_limit | 40000 | 0 | {} | {"sy:11": 10} | 1.0 |
| S1 | imi03 | none | reachable | completed | 170 | 0 | {"sy:17": 8} | {"sy:17": 17, "se:33": 1, "sy:11": 1} | 0.7 |
| S1 | imi03 | plus2 | reachable | node_limit | 40000 | 0 | {} | {"sy:11": 10} | 1.0 |
| S2 | imi01 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S2 | imi01 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S2 | imi02 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S2 | imi02 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S2 | imi03 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S2 | imi03 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S3 | imi01 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S3 | imi01 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S3 | imi02 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S3 | imi02 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S3 | imi03 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.4 |
| S3 | imi03 | plus2 | unknown | node_limit | 40000 | 4 | {"se:33": 20, "sy:11": 20} | {"se:33": 20, "sy:11": 20, "sy:17": 10} | 0.0 |
| S4 | imi01 | none | unknown | node_limit | 40000 | 7 | {"se:33": 40, "sy:11": 20, "sy:17": 10} | {"se:33": 40, "sy:11": 20, "sy:17": 10} | 1.0 |
| S4 | imi01 | plus2 | unknown | node_limit | 40000 | 9 | {"se:33": 40, "sy:11": 40, "sy:17": 10} | {"se:33": 40, "sy:11": 40, "sy:17": 10} | 1.0 |
| S4 | imi02 | none | unknown | node_limit | 40000 | 7 | {"se:33": 40, "sy:11": 20, "sy:17": 10} | {"se:33": 40, "sy:11": 20, "sy:17": 10} | 1.0 |
| S4 | imi02 | plus2 | unknown | node_limit | 40000 | 9 | {"se:33": 40, "sy:11": 40, "sy:17": 10} | {"se:33": 40, "sy:11": 40, "sy:17": 10} | 1.0 |
| S4 | imi03 | none | unknown | node_limit | 40000 | 7 | {"se:33": 40, "sy:11": 20, "sy:17": 10} | {"se:33": 40, "sy:11": 20, "sy:17": 10} | 1.0 |
| S4 | imi03 | plus2 | unknown | node_limit | 40000 | 9 | {"se:33": 40, "sy:11": 40, "sy:17": 10} | {"se:33": 40, "sy:11": 40, "sy:17": 10} | 1.0 |
| S5 | imi01 | none | reachable | completed | 1484 | 0 | {"sy:17": 8} | {"sy:17": 16} | 0.8 |
| S5 | imi01 | plus2 | unknown | node_limit | 40000 | 1 | {"sy:11": 10} | {"sy:11": 10, "sy:17": 10} | 0.0 |
| S5 | imi02 | none | reachable | completed | 1608 | 0 | {"sy:17": 8} | {"sy:17": 16} | 0.8 |
| S5 | imi02 | plus2 | unknown | node_limit | 40000 | 1 | {"sy:11": 10} | {"sy:11": 10, "sy:17": 10} | 0.0 |
| S5 | imi03 | none | reachable | completed | 1608 | 0 | {"sy:17": 8} | {"sy:17": 16} | 0.8 |
| S5 | imi03 | plus2 | unknown | node_limit | 40000 | 1 | {"sy:11": 10} | {"sy:11": 10, "sy:17": 10} | 0.0 |
| S6 | imi01 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.7 |
| S6 | imi01 | plus2 | unknown | node_limit | 40000 | 6 | {"sy:11": 30, "se:33": 20, "sy:17": 10} | {"sy:11": 30, "se:33": 20, "sy:17": 10} | 1.0 |
| S6 | imi02 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.7 |
| S6 | imi02 | plus2 | unknown | node_limit | 40000 | 6 | {"sy:11": 30, "se:33": 20, "sy:17": 10} | {"sy:11": 30, "se:33": 20, "sy:17": 10} | 1.0 |
| S6 | imi03 | none | unknown | node_limit | 40000 | 3 | {"se:33": 20, "sy:11": 10} | {"se:33": 20, "sy:11": 10, "sy:17": 10} | 0.7 |
| S6 | imi03 | plus2 | unknown | node_limit | 40000 | 6 | {"sy:11": 30, "se:33": 20, "sy:17": 10} | {"sy:11": 30, "se:33": 20, "sy:17": 10} | 1.0 |

- [確認済み事実] 加法性比較（依頼4）は JSON: `request4.additivity_rows` に全件。

## 5. persistent residual の exact source attribution

- [確認済み事実] best leaf上位10件 / best mid上位10件の source を各ケースで JSON に格納。
- [確認済み事実] ここでは各ケースの best leaf 先頭3件のみ表示（全件はJSON）。

### S1 / imi01 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 3,17,V,,,left,nonhead | x3-1 | x3-1 | いる | 3 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |

### S1 / imi01 / plus2
- status=`reachable` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:11 | 2,11,ga | x1-1 | x1-1 | うさぎ | 1 | 5 | None | None |
| sy:11 | 2,11,ga | x1-1 | x1-1 | うさぎ | 1 | 5 | None | None |

### S1 / imi02 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 3,17,V,,,left,nonhead | x3-1 | x3-1 | いる | 3 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |

### S1 / imi02 / plus2
- status=`reachable` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|

### S1 / imi03 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 3,17,V,,,left,nonhead | x3-1 | x3-1 | いる | 3 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |
| sy:17 | 0,17,V,,,right,nonhead | x4-1 | x4-1 | る | 4 | 3 | None | None |

### S1 / imi03 / plus2
- status=`reachable` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|

### S2 / imi01 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 6 | None | None |

### S2 / imi01 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 8 | None | None |

### S2 / imi02 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 6 | None | None |

### S2 / imi02 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 8 | None | None |

### S2 / imi03 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 6 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 6 | None | None |

### S2 / imi03 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| se:33 | Theme:2,33,wo | x3-1 | x3-1 | 食べている | 3 | 8 | None | None |
| sy:11 | 2,11,wo | x1-1 | x1-1 | わたあめ | 1 | 8 | None | None |

### S3 / imi01 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 6 | None | None |

### S3 / imi01 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 8 | None | None |

### S3 / imi02 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 6 | None | None |

### S3 / imi02 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 8 | None | None |

### S3 / imi03 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 6 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 6 | None | None |

### S3 / imi03 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| se:33 | 相手:2,33,to | x3-1 | x3-1 | 話している | 3 | 8 | None | None |
| sy:11 | 2,11,to | x1-1 | x1-1 | ひつじ | 1 | 8 | None | None |

### S4 / imi01 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 10 | None | None |

### S4 / imi01 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 12 | None | None |

### S4 / imi02 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 10 | None | None |

### S4 / imi02 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 12 | None | None |

### S4 / imi03 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 10 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 10 | None | None |

### S4 / imi03 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 12 | None | None |
| se:33 | Agent:2,33,ga | x7-1 | x7-1 | 話している | 7 | 12 | None | None |

### S5 / imi01 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |

### S5 / imi01 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |

### S5 / imi02 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |

### S5 / imi02 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |

### S5 / imi03 / none
- status=`reachable` reason=`completed`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |
| sy:17 | 0,17,N,,,left,nonhead | x1-1 | x1-1 | ふわふわした | 1 | 4 | None | None |

### S5 / imi03 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |
| sy:11 | 2,11,ga | x2-1 | x2-1 | ひつじ | 2 | 6 | None | None |

### S6 / imi01 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| sy:11 | 2,11,wo | x2-1 | x2-1 | わたあめ | 2 | 7 | None | None |

### S6 / imi01 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| sy:11 | 2,11,ga | x10-1 | x10-1 | φ | 10 | 9 | None | None |

### S6 / imi02 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| sy:11 | 2,11,wo | x2-1 | x2-1 | わたあめ | 2 | 7 | None | None |

### S6 / imi02 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| sy:11 | 2,11,ga | x10-1 | x10-1 | φ | 10 | 9 | None | None |

### S6 / imi03 / none
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 7 | None | None |
| sy:11 | 2,11,wo | x2-1 | x2-1 | わたあめ | 2 | 7 | None | None |

### S6 / imi03 / plus2
- status=`unknown` reason=`node_limit`
| family | exact_label | current_holding_node | item_id | surface | initial_slot | history_len | process_ref | tree_ref |
|---|---|---|---|---|---:|---:|---|---|
| se:33 | Agent:2,33,ga | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| se:33 | Theme:2,33,wo | x4-1 | x4-1 | 食べている | 4 | 9 | None | None |
| sy:11 | 2,11,ga | x10-1 | x10-1 | φ | 10 | 9 | None | None |

## 6. discharge capability matrix

| feature | 導入元 lexical item | 消費関与関数 | 局所条件 | imi01 RH/LH 理論可否 | imi01 実測可否 | imi02/imi03 | 根拠コード |
|---|---|---|---|---|---|---|---|
| se:33:* | 食べている(266), 話している(269), いる(271) | packages/domain/src/domain/derivation/execute.py:339 (_process_se_imi03) | head側se の number=33 かつ non-head側 sy で label 一致（sy_number=11 or 12） | 条件を満たす pair が作れれば消費分岐は実行される | 未確認（best residual に継続残存） | RH/LH実行経路は同関数（_uses_imi_feature_engine）を使用 | packages/domain/src/domain/derivation/execute.py:395-409<br>packages/domain/src/domain/derivation/execute.py:1728-1753<br>packages/domain/src/domain/derivation/execute.py:1807-1832 |
| sy:11:* | が(19), を(23), と(268), φ(309) | packages/domain/src/domain/derivation/execute.py:587 (_process_sy_imi03), packages/domain/src/domain/derivation/execute.py:339 (_process_se_imi03) | non-head側 sy number=11, coeff=4 のとき `2,11,label` へ変換しつつnaから除去；se:33 側とlabel一致で消費対象 | 分岐条件は存在（pair条件を満たす必要あり） | 未確認（sy:11 が persistent residual として観測） | RH/LH処理は同一系；追加ruleの有無は grammar catalog 依存 | packages/domain/src/domain/derivation/execute.py:780-784<br>packages/domain/src/domain/derivation/execute.py:395-409 |
| sy:17:* | ふわふわした(264), が(19), を(23), と(268), る(204) ほか | packages/domain/src/domain/derivation/execute.py:69 (_eval_feature_17), packages/domain/src/domain/derivation/execute.py:587 (_process_sy_imi03) | alpha(相手category)/beta(相手sy)/gamma(rule)/delta(left-right位置)/epsilon(head|nonhead) の5条件一致 | _eval_feature_17 条件を満たす pair で消費分岐に入る | 未確認（x9 が由来の sy:17 が persistent residual） | RH/LH部は同関数使用 | packages/domain/src/domain/derivation/execute.py:69-95<br>packages/domain/src/domain/derivation/execute.py:659-677<br>packages/domain/src/domain/derivation/execute.py:800-820 |
| engine path parity (imi01/imi02/imi03) |  | packages/domain/src/domain/derivation/execute.py:10 (_uses_imi_feature_engine), packages/domain/src/domain/derivation/execute.py:1728-1772 (RH), packages/domain/src/domain/derivation/execute.py:1807-1851 (LH) | grammar_id in {imi01, imi02, imi03} で同一 feature engine を通る | 確認済み | 確認済み（同コード経路） | rule catalog に含まれる追加rule候補は異なる可能性あり | packages/domain/src/domain/derivation/execute.py:10<br>packages/domain/src/domain/derivation/execute.py:1728<br>packages/domain/src/domain/derivation/execute.py:1807 |

## 7. φ 比較

| sentence | grammar | status(none->plus2) | reason(none->plus2) | Δse:33 | Δsy:11 | Δsy:17 | source_diff件数(se:33/sy:11/sy:17) |
|---|---|---|---|---:|---:|---:|---|
| S1 | imi01 | reachable->reachable | completed->node_limit | 0.0 | 0.2 | -0.8 | 0/1/3 |
| S2 | imi01 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S3 | imi01 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S4 | imi01 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 0.0 | 0/5/0 |
| S5 | imi01 | reachable->unknown | completed->node_limit | 0.0 | 1.0 | -0.8 | 0/1/1 |
| S6 | imi01 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 1.0 | 0/5/1 |
| S1 | imi02 | reachable->reachable | completed->node_limit | 0.0 | 0.0 | -0.8 | 0/0/3 |
| S2 | imi02 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S3 | imi02 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S4 | imi02 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 0.0 | 0/5/0 |
| S5 | imi02 | reachable->unknown | completed->node_limit | 0.0 | 1.0 | -0.8 | 0/1/1 |
| S6 | imi02 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 1.0 | 0/5/1 |
| S1 | imi03 | reachable->reachable | completed->node_limit | 0.0 | 0.0 | -0.8 | 0/0/3 |
| S2 | imi03 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S3 | imi03 | unknown->unknown | node_limit->node_limit | 0.0 | 1.0 | 0.0 | 0/1/0 |
| S4 | imi03 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 0.0 | 0/5/0 |
| S5 | imi03 | reachable->unknown | completed->node_limit | 0.0 | 1.0 | -0.8 | 0/1/1 |
| S6 | imi03 | unknown->unknown | node_limit->node_limit | 0.0 | 2.0 | 1.0 | 0/5/1 |

## 8. リポジトリ内の類例

| numeration | sentence | grammar | status | reason | actions | rule_sequence(到達時) |
|---|---|---|---|---|---:|---|
| imi01/set-numeration/1608131495.num | ふわふわしたわたあめを食べているひつじと話しているうさぎがいる | imi01 | unknown | node_limit | 15000 | - |
| imi01/set-numeration/1608131500.num | ふわふわしたわたあめを食べているひつじと話しているうさぎがいる[2] | imi01 | unknown | node_limit | 15000 | - |
| imi02/set-numeration/1608131495.num | ふわふわしたわたあめを食べているひつじと話しているうさぎがいる | imi02 | unknown | node_limit | 15000 | - |
| imi03/set-numeration/1608131495.num | ふわふわしたわたあめを食べているひつじと話しているうさぎがいる | imi03 | unknown | node_limit | 15000 | - |
| japanese2/set-numeration/07-02-17.num | かわいいリボンをつけた犬を抱いた女の子が立っている（7.2節 (17)） | japanese2 | unknown | node_limit | 15000 | - |
| japanese2/set-numeration/07-01-03b.num | 父が楽しそうに笑っている写真（7.1節 (3b)） | japanese2 | reachable | node_limit | 15000 | J-Merge(x1-1,x2-1); RH-Merge(x1-1,x5-1); RH-Merge(x5-1,x4-1); RH-Merge(x3-1,x4-1); zero-Merge(x4-1,x4-1) |
| japanese2/set-numeration/08-01-15.num | ジョンがどこが勝ったか知りたがっている（8.1節 (15)-(21), 付録 B.5） | japanese2 | unknown | node_limit | 15000 | - |
| japanese2/set-numeration/08-02-24.num | ジョンが何人の学生が勝ったか知りたがっている（8.2節 (24)） | japanese2 | unknown | node_limit | 15000 | - |

## 9. 断定できること / 断定できないこと

### [確認済み事実]
- 6文×3Grammar×2phi の同一予算実測を実行し、status/reason/actions/残差集計をJSON化した。
- persistent residual の source attribution（best leaf/mid top10）を、item_id・exact_label・initial_slot付きで保存した。
- imi01/imi02/imi03 の RH/LH 実行経路が同一 feature engine（_uses_imi_feature_engine）を通ることをコードで確認した。

### [未確認]
- 対象文（S4/S6 など）で、imi01 RH/LH のみで最終的に residual を全消費できる経路が存在するかは、今回条件下では未確定。
- best sample から process/tree への直接参照は現行抽出経路では未取得（null）。

### [推測]
- rule_name ベースの `rc_related_guess` は、規則名の語彙的手掛かりによる分類であり、形式意味論上の保証ではない。
- repo内 RC候補ファイルは手掛かりになり得るが、流用可否は rule/lexicon整合の追加検証が必要。
