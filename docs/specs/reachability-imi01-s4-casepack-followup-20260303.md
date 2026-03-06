# imi01 S4 casepack follow-up（2026-03-03）

## 1. 結論
- [確認済み事実] S4 current-best（9301/9401/9402基盤）の残差2個を対象に、19->263 と新規row最大2行のみを実測した。
- [確認済み事実] 19->263 は sy:17 を抑えるが、S3既存到達を壊し、S4自然reachableは得られなかった。
- [確認済み事実] 新規1行 9501（wo_casepack_c3）で S4 leaf_min は 2→1 へ改善。S2 は reachable を観測。
- [未確認] S4 の natural reachable evidence は未観測のため、最終採用は未確定。

## 2. current best 再確認
- [確認済み事実] S3_new_9301_9402 ids=[267, 9301, 9402, 270, 19, 271, 204]
  - [確認済み事実] status/reason=reachable/timeout actions=66723 depth=6 leaf_min=0
  - [確認済み事実] residual={}
- [確認済み事実] S4_new_9301_9401_9402 ids=[264, 265, 23, 9401, 267, 9301, 9402, 270, 19, 271, 204]
  - [確認済み事実] status/reason=unknown/timeout actions=51225 depth=10 leaf_min=2
  - [確認済み事実] residual={'sy:11': 10, 'sy:17': 10}

## 3. `19 -> 263` 実測
| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |
|---|---|---|---|---:|---:|---:|---|---|---|
| S2_new_9401_ga263 | [265, 23, 9401, 267, 263, 271, 204] | unknown | timeout | 68570 | 6 | 2 | {'se:33': 10, 'sy:11': 10} | False | False |
| S3_new_9301_9402_ga263 | [267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 74333 | 6 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_ga263 | [264, 265, 23, 9401, 267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 50684 | 10 | 2 | {'se:33': 10, 'sy:11': 10} | False | False |

## 4. `2,11,wo` の code-grounded 切り分け
- [確認済み事実] 生成: {'file': 'packages/domain/src/domain/derivation/execute.py', 'function': '_process_sy_imi03', 'branch': 'nonhead number==11 and coeff==4', 'behavior': '4,11,<label> を 2,11,<label> に変換して mother 側へ移す（na_sy は消去）', 'line_hint': 780}
- [確認済み事実] 消費: {'file': 'packages/domain/src/domain/derivation/execute.py', 'function': '_process_se_imi03', 'branch': 'head sem number==33, target label match, partner sy number==11', 'behavior': '対応する sy:11 を消費し、sem を partner id へ置換', 'line_hint': 405}
- [確認済み事実] 観測: sy:11|2,11,wo|わたあめ(265) / S4 current-best では se:33 側の要求が葉で残らず、2,11,wo の消費機会が尽きて残差化している。
- [確認済み事実] 265に残る理由: 23(を) の 4,11,wo が noun 経由で 2,11,wo として保持され、最終葉で 265 に付着して観測される。

## 5. 必要なら新規 row 案
- [確認済み事実] wo_casepack_c3 (id=9501)
  - [確認済み事実] target: sy:11 | 2,11,wo | わたあめ(265)
  - [確認済み事実] rationale: 4,11,wo 由来の 2,11,wo 残差を削減するため、11番の係数を 3 に切り替えて pack 形を変える。
  - [確認済み事実] csv_row: `9501 	を	を	J	0 					3	0,17,N,,,right,nonhead	3,17,V,,,left,nonhead	3,11,wo			zero	0 															imi01-probe:wo-sy11-c3	0`
- [確認済み事実] ga_no017 (id=9502)
  - [確認済み事実] target: sy:17 | 0,17,N,right,nonhead | が(19)
  - [確認済み事実] rationale: 0,17 側の未解消残差を避けるため、が候補から 0,17 を外して ga 供給を維持できるか確認。
  - [確認済み事実] csv_row: `9502 	が	が	J	0 					2	3,17,V,,,left,nonhead	4,11,ga				zero	0 															imi01-probe:ga-no017	0`

## 6. 新規 row 実測
| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |
|---|---|---|---|---:|---:|---:|---|---|---|
| S2_new_9501 | [265, 9501, 9401, 267, 19, 271, 204] | reachable | timeout | 72235 | 6 | 0 | {} | True | True |
| S4_new_9301_9401_9402_9501 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 19, 271, 204] | unknown | timeout | 53633 | 10 | 1 | {'sy:17': 10} | False | False |
| S2_new_9501_ga263 | [265, 9501, 9401, 267, 263, 271, 204] | unknown | timeout | 73502 | 6 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_9501_ga263 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 49331 | 10 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_ga9502 | [264, 265, 23, 9401, 267, 9301, 9402, 270, 9502, 271, 204] | unknown | timeout | 51204 | 10 | 2 | {'se:33': 10, 'sy:11': 10} | False | False |
| S4_new_9301_9401_9402_9501_ga9502 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9502, 271, 204] | unknown | timeout | 51700 | 10 | 1 | {'se:33': 10} | False | False |

## 7. hard reject 監査
- [確認済み事実] S2_new_9501 rank1: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S2_new_9501 rank2: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S2_new_9501 rank3: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S2_new_9501 rank4: hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S2_new_9501 rank5: hard_reject=False replay_failed=None violations=[]

## 8. 最終判断
- [確認済み事実] 8-1 `19->263` だけで S4 自然reachableになるか: 未確定
- [確認済み事実] 8-2 新規 row 1行で足りるか: 未確定
- [確認済み事実] 8-3 現時点の最善 S4 numeration: {'run_name': 'S4_new_9301_9401_9402_9501_ga263', 'explicit_lexicon_ids': [264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204], 'status': 'unknown', 'reason': 'timeout', 'best_leaf_unresolved_min': 1, 'best_leaf_residual_family_totals': {'se:33': 10}, 'best_leaf_residual_source_top5': {'se:33': [{'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'い-', 'initial_slot': 10, 'lexicon_id': 271, 'category': 'V', 'count': 10}]}}
- [確認済み事実] 8-4 到達証拠の採用可否: 未確定

## 9. 未確認事項
- [未確認] S4 で reachable evidence が未観測のため、hard reject 監査は current-best/new-row の到達runに限定される。
- [未確認] 20s/120k/28 の有限予算下観測であり、未観測=不可能の証明ではない。
