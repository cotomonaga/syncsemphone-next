# japanese2 Entry Conditions Facts (2026-03-02)

## 1. 結論

- [確認済み事実] 結論A: {'lookup_ready_for_S1_S6': False, 'reason': 'S1-S6 が token lookup で失敗', 'fact_status': '確認済み事実'}
- [確認済み事実] 結論B: {'explicit_bypass_any_reachable': False, 'reason': 'explicit 経路でも reachable 未観測（unknown/failed）', 'fact_status': '確認済み事実'}

## 2. japanese2 lexical source の実体

- [確認済み事実] lookup_source_files: ['/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv']
- [確認済み事実] related_runtime_files: ['/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2R.pl']
- [確認済み事実] runtime_open_trace_files: ['/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv', '/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2R.pl']
- [確認済み事実] call_path: ['/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/apps/api/app/api/v1/derivation.py:_generate_numeration_with_unknown_token_fallback', 'domain/numeration/generator.py:generate_numeration_from_sentence', '/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/lexicon/legacy_loader.py:load_legacy_lexicon', 'domain/numeration/generator.py:_build_surface_index', '/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/generator.py:_resolve_token']

## 3. raw lookup dump

### ふわふわした
- [確認済み事実] variants=['ふわふわした', 'ふわふわ']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=0

### わたあめ
- [確認済み事実] variants=['わたあめ']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=0

### 食べている
- [確認済み事実] variants=['食べている', '食べ', '食べる']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=1
```text
L175: 152 	食べ		V	0 				0 						id	3 	Theme	2,25,wo,	Agent	2,25,ga,	Kind	食べる								0
```

### ひつじ
- [確認済み事実] variants=['ひつじ']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=0

### 話している
- [確認済み事実] variants=['話している', '話し', '話す']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=1
```text
L180: 154 	話す	hanas-	V	0 				0 						id	2 	Agent	2,25,ga,	Kind	話す										0
```

### うさぎ
- [確認済み事実] variants=['うさぎ']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=0

### いる
- [確認済み事実] variants=['いる']
- [確認済み事実] file=/Users/tomonaga/Documents/syncsemphoneIMI/japanese2/japanese2.csv hits=0

## 4. generation_failed 最小再現

### S1: うさぎがいる
- [確認済み事実] mode=C tokens=['うさぎ', 'が', 'いる', 'る'] failed_token=うさぎ query=うさぎ error=Unknown token for lexicon lookup: うさぎ
- [確認済み事実] mode=B tokens=['うさぎ', 'が', 'いる', 'る'] failed_token=うさぎ query=うさぎ error=Unknown token for lexicon lookup: うさぎ
- [確認済み事実] mode=A tokens=['うさぎ', 'が', 'いる', 'る'] failed_token=うさぎ query=うさぎ error=Unknown token for lexicon lookup: うさぎ
- [確認済み事実] final_error=Unknown token for lexicon lookup: うさぎ

### S2: わたあめを食べているひつじがいる
- [確認済み事実] mode=C tokens=['わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=わたあめ query=わたあめ error=Unknown token for lexicon lookup: わたあめ
- [確認済み事実] mode=B tokens=['わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=わたあめ query=わたあめ error=Unknown token for lexicon lookup: わたあめ
- [確認済み事実] mode=A tokens=['わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=わたあめ query=わたあめ error=Unknown token for lexicon lookup: わたあめ
- [確認済み事実] final_error=Unknown token for lexicon lookup: わたあめ

### S3: ひつじと話しているうさぎがいる
- [確認済み事実] mode=C tokens=['ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ひつじ query=ひつじ error=Unknown token for lexicon lookup: ひつじ
- [確認済み事実] mode=B tokens=['ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ひつじ query=ひつじ error=Unknown token for lexicon lookup: ひつじ
- [確認済み事実] mode=A tokens=['ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ひつじ query=ひつじ error=Unknown token for lexicon lookup: ひつじ
- [確認済み事実] final_error=Unknown token for lexicon lookup: ひつじ

### S4: ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
- [確認済み事実] mode=C tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=B tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=A tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] final_error=Unknown token for lexicon lookup: ふわふわした

### S5: ふわふわしたひつじがいる
- [確認済み事実] mode=C tokens=['ふわふわした', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=B tokens=['ふわふわした', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=A tokens=['ふわふわした', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] final_error=Unknown token for lexicon lookup: ふわふわした

### S6: ふわふわしたわたあめを食べているひつじがいる
- [確認済み事実] mode=C tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=B tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] mode=A tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'が', 'いる', 'る'] failed_token=ふわふわした query=ふわふわした error=Unknown token for lexicon lookup: ふわふわした
- [確認済み事実] final_error=Unknown token for lexicon lookup: ふわふわした

## 5. explicit numeration/state 迂回経路

- [確認済み事実] explicit numeration -> reachability: Yes (apps/api/app/api/v1/derivation.py:/numeration/compose -> _compose_numeration_text -> apps/api/app/api/v1/derivation.py:/init -> build_initial_derivation_state -> apps/api/app/api/v1/derivation.py:/reachability (DerivationReachabilityRequest.state))
- [確認済み事実] working_example={'numeration_lexicon_ids': [60, 19, 125], 'status': 'unreachable', 'reason': 'completed', 'actions_attempted': 58, 'fact_status': '確認済み事実'}
- [確認済み事実] blocked_example={'numeration_lexicon_ids': [265, 23], 'error': 'Unknown lexicon id at slot=1: 265', 'fact_status': '確認済み事実'}

## 6. explicit numeration 実験

- [確認済み事実] temp_legacy_root=/var/folders/pl/hlcy6fbx5qdd9s054ltllyx80000gn/T/j2_explicit_7ic8qvr2
| sentence | proposal | explicit_lexicon_ids | status | reason | actions | depth | leaf_min | se:33(avg) | sy:11(avg) | sy:17(avg) | residual source top |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| S2 | P0_imi_content_ids_switch_grammar_only | 265,23,266,267,19,271,125 | unknown | timeout | 10192 | 10 | 1 | 0.0 | 0.0 | 1.0 | sy:17:x3-1:2,17,N,,,left,nonhead(10) |
| S2 | P1_existing_japanese2_candidates | 265,197,266,267,196,271,125 | unknown | timeout | 9660 | 9 | 2 | 0.0 | 0.0 | 1.0 | sy:17:x3-1:2,17,N,,,left,nonhead(10) |
| S2 | P2_P1_plus_target_phi | 265,197,266,267,196,271,125,272,273,274,275 | unknown | timeout | 7359 | 10 | 7 | 2.0 | 2.0 | 1.0 | se:24:x11-1:α<sub>13</sub>:0,24(10); se:27:x11-1::2,27,target(10); se:33:x3-1:Agent:2,33,ga(10); sy:1:x7-1:2,1,V(10); sy:11:x10-1:2,11,wo(4); sy:17:x3-1:2,17,N,,,left,nonhead(10); sy:53:x10-1:3,53,target, x10-1(4) |
| S2 | P3_new_lexical_item_max3 | 9103,23,266,9101,19,271,125 | unknown | timeout | 8849 | 9 | 3 | 0.0 | 2.0 | 1.0 | sy:1:x7-1:2,1,V(2); sy:11:x6-1:2,11,wo(9); sy:17:x3-1:2,17,N,,,left,nonhead(10) |
| S3 | P0_imi_content_ids_switch_grammar_only | 267,268,269,270,19,271,125 | unknown | timeout | 9871 | 11 | 2 | 0.6 | 1.0 | 1.8 | se:33:x3-1:Agent:2,33,ga(2); sy:1:x7-1:2,1,V(2); sy:11:x6-1:2,11,to(10); sy:17:x2-1:0,17,N,,,right,nonhead(10) |
| S3 | P1_existing_japanese2_candidates | 267,171,269,270,196,271,125 | unknown | timeout | 10466 | 9 | 3 | 0.0 | 0.0 | 2.0 | sy:17:x3-1:0,17,N,,,left,nonhead(10) |
| S3 | P2_P1_plus_target_phi | 267,171,269,270,196,271,125,272,273,274,275 | unknown | timeout | 8028 | 10 | 7 | 2.0 | 2.0 | 1.0 | se:24:x11-1:α<sub>13</sub>:0,24(10); se:27:x11-1::2,27,target(10); se:33:x3-1:Agent:2,33,ga(10); sy:1:x7-1:2,1,V(10); sy:11:x6-1:2,11,ni(8); sy:17:x6-1:2,17,T,,,left,head(10); sy:53:x6-1:3,53,target, x10-1(10) |
| S3 | P3_new_lexical_item_max3 | 9101,268,269,9102,19,271,125 | unknown | timeout | 9143 | 9 | 1 | 2.3 | 2.5 | 1.5 | se:24:x1-1:α<sub>12</sub>:0,24(2); se:33:x3-1:Agent:2,33,ga(10); sy:1:x7-1:2,1,V(5); sy:11:x6-1:2,11,to(16); sy:17:x2-1:0,17,N,,,right,nonhead(10) |
| S4 | P0_imi_content_ids_switch_grammar_only | 264,265,23,266,267,268,269,270,19,271,125 | unknown | timeout | 8474 | 13 | 7 | 3.0 | 1.0 | 2.0 | se:33:x10-1:Theme:2,33,ga(10); sy:11:x10-1:2,11,to(10); sy:17:x1-1:0,17,N,,,left,nonhead(10) |
| S4 | P1_existing_japanese2_candidates | 264,265,197,266,267,171,269,270,196,271,125 | unknown | timeout | 7348 | 10 | 6 | 5.0 | 0.0 | 2.0 | se:24:x1-1:Content:0,24(10); se:33:x10-1:Theme:2,33,ga(10); sy:17:x1-1:0,17,N,,,left,nonhead(10) |
| S4 | P2_P1_plus_target_phi | 264,265,197,266,267,171,269,270,196,271,125,272,273,274,275 | unknown | timeout | 7069 | 14 | 8 | 4.0 | 2.0 | 2.0 | se:24:x1-1:Content:0,24(10); se:27:x15-1::2,27,target(10); se:33:x4-1:Agent:2,33,ga(10); sy:1:x11-1:2,1,V(10); sy:11:x10-1:2,11,ni(8); sy:17:x1-1:0,17,N,,,left,nonhead(10); sy:53:x10-1:3,53,target, x13-1(10) |
| S4 | P3_new_lexical_item_max3 | 264,9103,23,266,9101,268,269,9102,19,271,125 | unknown | timeout | 6553 | 12 | 8 | 2.0 | 2.0 | 3.0 | se:33:x4-1:Agent:2,33,ga(7); sy:11:x10-1:2,11,to(10); sy:17:x1-1:0,17,N,,,left,nonhead(10) |

## 7. yes/no

| Q | yes/no | explicit_lexicon_ids_tested | minimal success/counterexample | required_rule | code_path |
|---:|---|---|---|---|---|
| 1 | Yes | [266, 23] | {'rule_name': 'zero-Merge', 'left': None, 'right': None, 'check': 1, 'before': 1, 'after': 0, 'decreased': True} | zero-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33) |
| 2 | Yes | [266, 267] | {'rule_name': 'RH-Merge', 'left': 1, 'right': 2, 'check': None, 'before': 1, 'after': 0, 'decreased': True} | RH-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33) |
| 3 | Yes | [269, 267] | {'rule_name': 'zero-Merge', 'left': None, 'right': None, 'check': 1, 'before': 1, 'after': 0, 'decreased': True} | zero-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33) |
| 4 | Yes | [269, 270] | {'rule_name': 'RH-Merge', 'left': 1, 'right': 2, 'check': None, 'before': 1, 'after': 0, 'decreased': True} | RH-Merge | packages/domain/src/domain/derivation/execute.py:_process_se_imi03(number==33) |
| 5 | Yes | {'S2': {'P0': [265, 23, 266, 267, 19, 271, 125], 'P1': [265, 197, 266, 267, 196, 271, 125], 'P2': [265, 197, 266, 267, 196, 271, 125, 272, 273, 274, 275]}, 'S3': {'P0': [267, 268, 269, 270, 19, 271, 125], 'P1': [267, 171, 269, 270, 196, 271, 125], 'P2': [267, 171, 269, 270, 196, 271, 125, 272, 273, 274, 275]}, 'S4': {'P0': [264, 265, 23, 266, 267, 268, 269, 270, 19, 271, 125], 'P1': [264, 265, 197, 266, 267, 171, 269, 270, 196, 271, 125], 'P2': [264, 265, 197, 266, 267, 171, 269, 270, 196, 271, 125, 272, 273, 274, 275]}} | {'sentence_key': 'S3', 'baseline_sy17_avg': 1.8, 'p1_sy17_avg': 2.0, 'p2_sy17_avg': 1.0} | [未確認] | apps/api/scripts/reachability_japanese2_entry_conditions_facts_20260302.py: experiments comparison |

## 8. 最終結論

- [確認済み事実] 結論A: {'lookup_ready_for_S1_S6': False, 'reason': 'S1-S6 が token lookup で失敗', 'fact_status': '確認済み事実'}
- [確認済み事実] 結論B: {'explicit_bypass_any_reachable': False, 'reason': 'explicit 経路でも reachable 未観測（unknown/failed）', 'fact_status': '確認済み事実'}

## 9. 未確認事項

- [未確認] explicit実験の unknown は budget上限内の観測であり、unreachable 断定ではない。
- [未確認] tree/process の詳細比較は本レポートでは未収集（history上位のみ）。
