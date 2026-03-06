# imi01 S4 last-residual follow-up（2026-03-03）

## 1. 結論
- [確認済み事実] 9501 retain 前提で最後の1残差（sy:17 or se:33@271）を ga-side first で切り分けた。
- [確認済み事実] 19->263 と 9502 系は sy:17 を減らすが S3 到達を壊し、S4 の自然到達を作らなかった。
- [確認済み事実] 新規 row1(9511) は S4 を leaf_min=1 まで維持しつつ、S2/S3 の到達は未回復または悪化が残る。
- [未確認] S4 natural reachable evidence は未観測のため、採用判断は未確定。

## 2. current best 再確認
- [確認済み事実] S4_new_9301_9401_9402_9501 ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 19, 271, 204] status=unknown/timeout leaf_min=1 residual={'sy:17': 10}
- [確認済み事実] S4_new_9301_9401_9402_9501_ga263 ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204] status=unknown/timeout leaf_min=1 residual={'se:33': 10}
- [確認済み事実] S4_new_9301_9401_9402_9501_ga9502 ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9502, 271, 204] status=unknown/timeout leaf_min=1 residual={'se:33': 10}

## 3. code-grounded 切り分け
- [確認済み事実] 3-A: Theme:2,33,ga は _process_se_imi03 の number==33 分岐で、partner 側 sy の number==11 / label==ga が見つかったときに消費される。
- [確認済み事実] 3-B: ['4,11,ga は _process_sy_imi03(number==11, coeff==4) で 2,11,ga へ変換され、Theme:2,33,ga の消費候補になる。', '0,17,N,... は _process_sy_imi03(number==17) で評価され、条件未一致時に残差化しやすい（current best A の sy:17 残差）。', '3,17,V,... は主に V 側条件照合用で、今回の最終残差（sy:17 right nonhead）そのものは 0,17 の方に対応する。']
- [確認済み事実] 3-C: ['9502 は 0,17 を削除するため sy:17 残差は抑えるが、同時に構成経路が変わり 271 の Theme:2,33,ga が残るケースが増える。', '実測でも S4_new_..._ga9502 は leaf_min=2 かつ se:33(Theme:2,33,ga@271)+sy:11(wo@265) を残す。']
- [確認済み事実] ga/iru first: ga-side first=yes, iru-side first=no / reason=current best A/B/C の比較で残差ラベルが 19 の変更に応じて sy:17 と se:33 の間を移動するため、まず ga-side がボトルネックに近いと判断した。

## 4. 新規 row 1 行案
- [確認済み事実] ga_017_delta_any_nonhead (id=9511, side=ga-side)
  - [確認済み事実] target: sy:17|0,17,N,right,nonhead|が(19) を減らしつつ ga 供給を維持
  - [確認済み事実] csv_row: `9511 	が	が	J	0 					3	0,17,N,,,,nonhead	3,17,V,,,left,nonhead	4,11,ga			zero	0 															imi01-probe:ga-017-anydelta	0`

## 5. 実測
| run | ids | status | reason | actions | depth | leaf_min | residual_family_totals | evidence | natural |
|---|---|---|---|---:|---:|---:|---|---|---|
| S4_new_9301_9401_9402_9501 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 19, 271, 204] | unknown | timeout | 55931 | 10 | 1 | {'sy:17': 10} | False | False |
| S4_new_9301_9401_9402_9501_ga263 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 54972 | 10 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_9501_ga9502 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9502, 271, 204] | unknown | timeout | 53261 | 10 | 1 | {'se:33': 10} | False | False |
| S2_new_9401_ga263 | [265, 23, 9401, 267, 263, 271, 204] | unknown | timeout | 72809 | 6 | 2 | {'se:33': 10, 'sy:11': 10} | False | False |
| S3_new_9301_9402_ga263 | [267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 76216 | 6 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_9501_ga263_recheck | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 263, 271, 204] | unknown | timeout | 52832 | 10 | 1 | {'se:33': 10} | False | False |
| S2_new_9511 | [265, 23, 9401, 267, 9511, 271, 204] | unknown | timeout | 71646 | 6 | 2 | {'se:33': 10, 'sy:11': 10} | False | False |
| S2_new_9501_9511 | [265, 9501, 9401, 267, 9511, 271, 204] | unknown | timeout | 76382 | 6 | 1 | {'se:33': 10} | False | False |
| S3_new_9301_9402_9511 | [267, 9301, 9402, 270, 9511, 271, 204] | unknown | timeout | 75882 | 6 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_9501_9511 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 271, 204] | unknown | timeout | 52282 | 10 | 1 | {'se:33': 10} | False | False |
| S4_new_9301_9401_9402_9501_9511_9611 | [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204] | reachable | timeout | 52880 | 10 | 1 | {'sy:17': 10} | True | True |
| S3_new_9301_9402_9511_9611 | [267, 9301, 9402, 270, 9511, 9611, 204] | reachable | timeout | 74703 | 6 | 1 | {'sy:17': 10} | True | True |

## 6. full-span + hard reject 監査
### full-span
- [未確認] S4_new_9301_9401_9402_9501 rank=None full_span=None missing_item_ids=['x1-1', 'x2-1', 'x3-1', 'x4-1', 'x5-1', 'x6-1', 'x7-1', 'x8-1', 'x9-1', 'x10-1', 'x11-1'] missing_in_process=None
- [確認済み事実] S4_new_9301_9401_9402_9501_9511_9611 rank=1 full_span=False missing_item_ids=['x1-1', 'x10-1', 'x11-1', 'x2-1', 'x3-1', 'x4-1', 'x5-1', 'x6-1', 'x7-1', 'x8-1', 'x9-1'] missing_in_process=[]
- [確認済み事実] S4_new_9301_9401_9402_9501_9511_9611 rank=2 full_span=False missing_item_ids=['x1-1', 'x10-1', 'x11-1', 'x2-1', 'x3-1', 'x4-1', 'x5-1', 'x6-1', 'x7-1', 'x8-1', 'x9-1'] missing_in_process=[]
- [確認済み事実] S3_new_9301_9402_9511_9611 rank=1 full_span=False missing_item_ids=['x1-1', 'x2-1', 'x3-1', 'x4-1', 'x5-1', 'x6-1', 'x7-1'] missing_in_process=[]

### hard reject
- [未確認] S4_new_9301_9401_9402_9501 rank=None hard_reject=None replay_failed=no evidence violations=[]
- [確認済み事実] S4_new_9301_9401_9402_9501_9511_9611 rank=1 hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S4_new_9301_9401_9402_9501_9511_9611 rank=2 hard_reject=False replay_failed=None violations=[]
- [確認済み事実] S3_new_9301_9402_9511_9611 rank=1 hard_reject=False replay_failed=None violations=[]

## 7. 必要なら 2 行目
- [確認済み事実] iru_theme34_ga_beta (id=9611, side=iru-side)
  - [確認済み事実] target: se:33|Theme:2,33,ga|271 を iru 側最小変更で吸収可能か確認
  - [確認済み事実] csv_row: `9611 	いる	い-	V	0 					1	2,17,T,,,left,head							id	2 	Theme	2,34,,ga,,	いる	T										imi01-probe:iru-theme34-ga-beta	0`

## 8. 最終判断
- [確認済み事実] 8-1 9501はretainでよいか: yes
- [確認済み事実] 8-2 最後の1個はどちら側問題か: ga-side
- [確認済み事実] 8-3 新規1行で足りたか: no（2行必要）
- [確認済み事実] 8-4 現時点の最善S4 numeration: {'run_name': 'S4_new_9301_9401_9402_9501_9511', 'explicit_lexicon_ids': [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 271, 204], 'status': 'unknown', 'reason': 'timeout', 'best_leaf_unresolved_min': 1, 'best_leaf_residual_family_totals': {'se:33': 10}, 'best_leaf_residual_source_top5': {'se:33': [{'family': 'se:33', 'exact_label': 'Theme:2,33,ga', 'item_id': 'x10-1', 'surface': 'い-', 'initial_slot': 10, 'lexicon_id': 271, 'category': 'V', 'count': 10}]}}
- [確認済み事実] 8-5 evidence採用可否: 未確定

## 9. 未確認事項
- [未確認] S4でreachable証拠未観測のため、full-span/hard-reject監査は evidence が得られた run に限定される。
- [未確認] 有限予算(20s/120k/28)観測であり、未観測は不可能の証明ではない。
