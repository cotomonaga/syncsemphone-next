# japanese2 Lexical Fact Extract (2026-03-02)

## 1. 結論

- [確認済み事実] A/B/C 判定: **C**
- [確認済み事実] 理由: japanese2 固定で existing/new lexical 実験の多くが unknown のため、lexicalのみで十分とは断定不可。追加観測または最小rule差分検討が必要。
- [未確認] unknown は探索打切りであり unreachable 断定ではない

## 2. japanese2 baseline

- [確認済み事実] 条件: `grammar_id=japanese2`, `auto_add_ga_phi=false`, Step.1 自動生成をそのまま使用。
| sentence | baseline生成 | token列 | baseline lexicon IDs | 自動選択 entry(category) | 選択根拠コード |
|---|---|---|---|---|---|
| S1 | failed: Unknown token for lexicon lookup: うさぎ |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |
| S2 | failed: Unknown token for lexicon lookup: わたあめ |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |
| S3 | failed: Unknown token for lexicon lookup: ひつじ |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |
| S4 | failed: Unknown token for lexicon lookup: ふわふわした |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |
| S5 | failed: Unknown token for lexicon lookup: ふわふわした |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |
| S6 | failed: Unknown token for lexicon lookup: ふわふわした |  |  |  | packages/domain/src/domain/numeration/generator.py:_resolve_token |

## 3. japanese2 rule catalog

| rule_number | rule_name | kind | file | runtime有効 | S2/S3/S4初期候補で出現 | RC/head-gap関連 |
|---:|---|---|---|---|---|---|
| 1 | sase1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase1_01.pl | True | False | [未確認] |
| 2 | sase2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/sase2_02.pl | True | False | [未確認] |
| 3 | rare2 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare2_01.pl | True | False | [未確認] |
| 4 | rare1 | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rare1_01.pl | True | False | [未確認] |
| 5 | property-no | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-no_01.pl | True | False | [未確認] |
| 6 | property-da | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-da_01.pl | True | False | [未確認] |
| 7 | J-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/J-Merge_01.pl | True | False | [未確認] |
| 8 | P-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/P-Merge_01.pl | True | False | [未確認] |
| 9 | property-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/property-Merge_01.pl | True | False | [未確認] |
| 10 | rel-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/rel-Merge_01.pl | True | False | [未確認] |
| 11 | RH-Merge | double | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/RH-Merge_01.pl | True | False | [未確認] |
| 12 | Pickup | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Pickup_01.pl | True | False | [未確認] |
| 13 | Landing | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Landing_02.pl | True | False | [未確認] |
| 14 | zero-Merge | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/zero-Merge_01.pl | True | False | [未確認] |
| 15 | Partitioning | single | /Users/tomonaga/Documents/syncsemphoneIMI/MergeRule/Partitioning_01.pl | True | False | [未確認] |

- [確認済み事実] 差分（S2/S3/S4に効きそうな rule 名比較）
  - [確認済み事実] japanese2 vs imi01: japanese2_only=['J-Merge', 'Landing', 'P-Merge', 'Partitioning', 'Pickup', 'property-Merge', 'property-da', 'property-no', 'rare1', 'rare2', 'rel-Merge', 'sase1', 'sase2', 'zero-Merge'], missing_from_japanese2=['LH-Merge']
  - [確認済み事実] japanese2 vs imi02: japanese2_only=['J-Merge', 'Landing', 'P-Merge', 'Partitioning', 'Pickup', 'property-Merge', 'property-da', 'property-no', 'rare1', 'rare2', 'rel-Merge', 'sase1', 'sase2'], missing_from_japanese2=['LH-Merge']
  - [確認済み事実] japanese2 vs imi03: japanese2_only=['J-Merge', 'Landing', 'P-Merge', 'Partitioning', 'Pickup', 'property-Merge', 'property-da', 'property-no', 'rare1', 'rare2', 'rel-Merge', 'sase1', 'sase2'], missing_from_japanese2=['LH-Merge']

## 4. lexical candidate 棚卸し

| surface | lexicon_id | entry | category | idslot | auto選択対象 | baseline選択済み | meaningful(japanese2) | reason_codes | used_in_reachable_examples |
|---|---:|---|---|---|---|---|---|---|---|
| ふわふわした |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| わたあめ |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| を | 23 | を | J | zero | False | False | meaningful | - | True |
| を | 181 | を | Z | 2,22 | False | False | meaningful | - | False |
| を | 189 | を | Z | 2,22 | False | False | meaningful | - | False |
| を | 197 | を | J | zero | False | False | meaningful | - | False |
| 食べている |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| ひつじ |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| と | 171 | と | Z | 2,22 | False | False | meaningful | - | False |
| 話している |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| うさぎ |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| が | 19 | が | J | zero | False | False | meaningful | - | True |
| が | 196 | が | J | zero | False | False | meaningful | - | False |
| いる |  | - | - | - | False | False | candidate_not_found | not_in_lexicon_all | False |
| る | 125 | る | T | 0,24 | False | False | meaningful | - | True |
| る | 204 | る | T | 0,24 | False | False | meaningful | - | True |
| φ | 195 | φ | N | id | False | False | meaningful | - | False |
| φ | 196 | が | J | zero | False | False | meaningful | - | False |
| φ | 197 | を | J | zero | False | False | meaningful | - | False |

## 5. S2/S3/S4 の role discharge 表

- [確認済み事実] 自然解釈の固定役割
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

| role_key | 要求側 | 要求ラベル | 供給側 | 供給ラベル | merge方向 | rule候補 | execute分岐 | 現行lexiconで理論上可能 | 実測観測 |
|---|---|---|---|---|---|---|---|---|---|
| eat_theme_wo | 食べている(266) | Theme:2,33,wo | を(23) または wo供給を持つNP | 4,11,wo / 2,11,wo | 要求側（predicate）を head、供給側を non-head として結合 | RH-Merge,J-Merge,rel-Merge,property-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33) | False | 未確認 |
| eat_agent_ga_by_hitsuji | 食べている(266) | Agent:2,33,ga | ひつじ(267) | 4,11,ga / 2,11,ga | 要求側（predicate）を head、供給側（ひつじ）を non-head として結合 | RH-Merge,J-Merge,rel-Merge,property-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33) | False | 未確認 |
| talk_partner_to_by_hitsuji | 話している(269) | 相手:2,33,to | ひつじ(267) | 4,11,to / 2,11,to | 要求側（predicate）を head、供給側（ひつじ）を non-head として結合 | RH-Merge,J-Merge,rel-Merge,property-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33) | False | 未確認 |
| talk_agent_ga_by_usagi | 話している(269) | Agent:2,33,ga | うさぎ(270) | 4,11,ga / 2,11,ga | 要求側（predicate）を head、供給側（うさぎ）を non-head として結合 | RH-Merge,J-Merge,rel-Merge,property-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 (number==33) | False | 未確認 |

## 6. persistent residual provenance

### S2 baseline
- [確認済み事実] status=failed reason=generation_failed actions=0 depth=0 leaf_min=None
- [確認済み事実] best_leaf_residual_family_totals={}
- [確認済み事実] best_mid_residual_family_totals={}
| type | family | exact_label | current_node | item_id | surface | initial_slot | count_in_top10 | history_len | tree/process |
|---|---|---|---|---|---|---:|---:|---|---|

### S3 baseline
- [確認済み事実] status=failed reason=generation_failed actions=0 depth=0 leaf_min=None
- [確認済み事実] best_leaf_residual_family_totals={}
- [確認済み事実] best_mid_residual_family_totals={}
| type | family | exact_label | current_node | item_id | surface | initial_slot | count_in_top10 | history_len | tree/process |
|---|---|---|---|---|---|---:|---:|---|---|

### S4 baseline
- [確認済み事実] status=failed reason=generation_failed actions=0 depth=0 leaf_min=None
- [確認済み事実] best_leaf_residual_family_totals={}
- [確認済み事実] best_mid_residual_family_totals={}
| type | family | exact_label | current_node | item_id | surface | initial_slot | count_in_top10 | history_len | tree/process |
|---|---|---|---|---|---|---:|---:|---|---|

## 7. existing-candidate-only 実験

| sentence | proposal | lexicon_ids | baselineと同一か | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top | history上位 |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| S2 | P0_baseline_auto |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S2 | P1_existing_reselect |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S2 | P2_existing_reselect_plus_phi272_275 |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S2 | P3_existing_reselect_particle_variants |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S3 | P0_baseline_auto |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S3 | P1_existing_reselect |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S3 | P2_existing_reselect_plus_phi272_275 |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S3 | P3_existing_reselect_particle_variants |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S4 | P0_baseline_auto |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S4 | P1_existing_reselect |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S4 | P2_existing_reselect_plus_phi272_275 |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |
| S4 | P3_existing_reselect_particle_variants |  | True | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 | - | [未確認] unknown/unreachable で evidence なし |

## 8. 新規 lexical item 提案（必要時のみ）

- [確認済み事実] existing-candidate-only で reachable 未観測のため、新規 lexical 提案（最大3行）を実測
```tsv
9101	ひつじ	ひつじ	N	0				2	4,11,ga	4,11,to				id	1	ひつじ	T											japanese2-probe20260302	0
9102	うさぎ	うさぎ	N	0				1	4,11,ga					id	1	うさぎ	T											japanese2-probe20260302	0
9103	わたあめ	わたあめ	N	0				1	4,11,wo					id	1	わたあめ	T											japanese2-probe20260302	0
```
| sentence | proposal | lexicon_ids | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| S2 | P4_new_lexical_addition_max3 |  | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 |
| S3 | P4_new_lexical_addition_max3 |  | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 |
| S4 | P4_new_lexical_addition_max3 |  | failed | generation_failed | 0 | 0 | None | 0.0 | 0.0 | 0.0 |

## 9. yes/no 判定

| Q | yes/no | 必要rule | 必要lexical | 最小成功例/反例 | 不成立局所条件 | code path |
|---:|---|---|---|---|---|---|
| 1 | No | [未確認] | [266, 23] | {'error': 'Unknown lexicon id at slot=1: 266'} | [確認済み事実] japanese2 lexicon に要求側 lexical item（食べている）が存在しない | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33 |
| 2 | No | [未確認] | [266, 267] | {'error': 'Unknown lexicon id at slot=1: 266'} | [確認済み事実] japanese2 lexicon に要求側 lexical item（食べている）と供給側 lexical item（ひつじ）が存在しない | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33 |
| 3 | No | [未確認] | [269, 267] | {'error': 'Unknown lexicon id at slot=1: 269'} | [確認済み事実] japanese2 lexicon に要求側 lexical item（話している）と供給側 lexical item（ひつじ）が存在しない | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33 |
| 4 | No | [未確認] | [269, 270] | {'error': 'Unknown lexicon id at slot=1: 269'} | [確認済み事実] japanese2 lexicon に要求側 lexical item（話している）と供給側 lexical item（うさぎ）が存在しない | packages/domain/src/domain/derivation/execute.py:_process_se_imi03 number==33 |
| 5 | No | [未確認] | [未確認] | {'sentence_key': 'S2/S3/S4', 'proposal_ids_checked': ['P1_existing_reselect', 'P2_existing_reselect_plus_phi272_275', 'P3_existing_reselect_particle_variants'], 'result': 'sy17_avg が baseline 以上（減少未観測）'} | [確認済み事実] existing-candidate-only の同一予算比較で sy:17 減少が未観測 | apps/api/scripts/reachability_japanese2_lexical_fact_extract_20260302.py (A/B集計) |

## 10. A/B/C 最終結論

- [確認済み事実] C: japanese2 固定で existing/new lexical 実験の多くが unknown のため、lexicalのみで十分とは断定不可。追加観測または最小rule差分検討が必要。
- [未確認] unknown は探索打切りであり unreachable 断定ではない

## 11. 未確認事項

- [未確認] `unknown` ケースでは `tree/process` 参照が得られないため、本レポートでは residual provenance と history を代替提示。
- [未確認] 現行予算外での探索継続結果（`unknown -> reachable/unreachable`）は未観測。
- [未確認] `relative clause` の最終的な自然導出が現行 `japanese2` でどこまで到達可能かは、予算拡張なしでは断定不可。
