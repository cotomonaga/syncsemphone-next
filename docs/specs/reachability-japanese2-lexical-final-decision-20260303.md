# 1. 結論
## 1-A. 到達案
- [確認済み事実] 採用 lexical row 一覧: 9301=採用, 181=暫定既定, 189=保留同格候補, 183=fallback候補, 264(japanese2 lookup行)=採用。
- [確認済み事実] 採用 lexical selection ルール: `と→9301`, `を→181(既定)/189(比較候補)`, `が→19(既定)/183(二段目)`, `る→204固定`。
- [確認済み事実] 採用 numeration(S4): tokens=['ふわふわした', 'わたあめ', 'を', '食べている', 'ひつじ', 'と', '話している', 'うさぎ', 'が', 'いる', 'る'], ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204]。
- [確認済み事実] 採用 Grammar: `japanese2`。
- [確認済み事実] 到達確認済み sentence: S4（9301固定の上で `を=181/189` いずれも reachable 観測）。
- [確認済み事実] 到達確認済み evidence: あり（S4 after_wo181/after_wo189 で evidence 抽出済み）。

## 1-B. 暫定運用判断
- [確認済み事実] **暫定運用としてはまだ確定してはいけない**。
- [確認済み事実] 9301固定の上で S4 は 181/189 とも reachable だが、181優位の確証は evidence差分で未確立。
- [確認済み事実] evidence再計算 unresolved と status=reachable の不一致があり、運用根拠の整合監査が未完了。
- [確認済み事実] 189を正式除外する根拠は不足し、183も fallback 条件の運用定義のみで確定実装根拠は不足。

# 2. 採用 lexical-only 案
## 2-A. 採用 lexical row
- [確認済み事実] `9301`: `採用` / 確認済み事実: S3/T2/T1で有効成分、S4比較でもbaseline前提として機能
- [確認済み事実] `181`: `暫定既定` / 確認済み事実: 9301固定の上で S4 reachable を与える
- [確認済み事実] `189`: `保留候補` / 確認済み事実: 9301固定の上で S4 reachable を与える（181との差分は要追加監査）
- [確認済み事実] `183`: `fallback候補` / 確認済み事実: 181後でも S2/T1 で改善幅を持つが既定化根拠は不足
- [確認済み事実] `264_japanese2_lookup`: `採用` / 確認済み事実: Step.1 auto の generation_failed 解消に必要
## 2-B. 採用 numeration
- [確認済み事実] S4 暫定運用 explicit numeration: `[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204]`
## 2-C. 採用 Grammar
- [確認済み事実] yes: `japanese2` のままで到達例（S4 reachable）は観測済み。
- [未確認] ただし意味自然性と判定整合（reachable vs unresolved再計算）の未解決があり、最終確定は保留。

# 3. 暫定運用可否（yes/no）
- [確認済み事実] 3-A: no (run=['S2_after_wo181', 'S2_after_wo189', 'S4_after_wo181', 'S4_after_wo189'])
- [確認済み事実] 3-B: no (run=['S2_after_wo181_vs_after_wo189', 'S4_after_wo181_vs_after_wo189'])
- [確認済み事実] 3-C: no (run=['S2_after_wo189', 'S4_after_wo189'])
- [確認済み事実] 3-D: yes (run=['S2_secondary_wo181_ga183', 'T1_secondary_wo181_ga183', 'S4_after_wo181'])

# 4. 181 vs 189 evidence 比較
## S2
- [確認済み事実] run181 ids=[265, 181, 266, 267, 19, 271, 204] status/reason=reachable/timeout evidence_count=4
- [確認済み事実] run189 ids=[265, 189, 266, 267, 19, 271, 204] status/reason=reachable/timeout evidence_count=4
- [確認済み事実] comparison: same_signature_set=False, same_strict_evidence=False, semantics_diff_exists=False
- [確認済み事実] signatures_only_in_181=4, signatures_only_in_189=4
- [確認済み事実] actual evidence 本体（tree/process/history/unresolved）は JSON の `evidence_comparison.S2` に全件格納。
## S4
- [確認済み事実] run181 ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] status/reason=reachable/timeout evidence_count=10
- [確認済み事実] run189 ids=[264, 265, 189, 266, 267, 9301, 269, 270, 19, 271, 204] status/reason=reachable/timeout evidence_count=10
- [確認済み事実] comparison: same_signature_set=False, same_strict_evidence=False, semantics_diff_exists=True
- [確認済み事実] signatures_only_in_181=8, signatures_only_in_189=8
- [確認済み事実] actual evidence 本体（tree/process/history/unresolved）は JSON の `evidence_comparison.S4` に全件格納。

# 5. 183 fallback 条件
- [確認済み事実] fallback候補として保持: S2は 181+183 で leaf_min改善、S4は181単独で到達済み。
- [推測] 発火条件: 181適用後も unresolved>0 かつ sy:1 系残差が観測されるとき。
- [推測] 実施位置: Step.1既定変更ではなく reachability 後段二段目評価として扱う。

# 6. Step.1 auto vs explicit
- [確認済み事実] S2: auto_ids=[265, 181, 266, 267, 19, 271, 204] / explicit_ids=[265, 181, 266, 267, 19, 271, 204] / same=True / generation_failed=False
- [確認済み事実] T3: auto_ids=[264, 265, 181, 266, 267, 19, 271, 204] / explicit_ids=[264, 265, 181, 266, 267, 19, 271, 204] / same=True / generation_failed=False
- [確認済み事実] T1: auto_ids=[265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / explicit_ids=[265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / same=True / generation_failed=False
- [確認済み事実] S4: auto_ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / explicit_ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / same=True / generation_failed=False

# 7. 最終判断
## 7-A. ふわふわ文の暫定 lexical-only 案
- [確認済み事実] 採用 lexical row: 9301, 181(暫定既定), 189(保留), 183(fallback), 264 lookup行。
- [確認済み事実] 採用 selection: `と→9301`, `を→181(既定)/189(比較)`, `が→19既定`, `る→204`。
- [確認済み事実] 採用 numeration: `[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204]`。
- [確認済み事実] 採用 Grammar: japanese2。
- [確認済み事実] 到達確認: S4 after_wo181 / after_wo189 とも reachable（9301固定前提）。
## 7-B. 暫定運用として確定すべきか
- [確認済み事実] **まだ確定してはいけない**。
- [確認済み事実] 到達性: reachable 観測はある。 ただし 未確認 として判定整合監査（reachable vs unresolved再計算）が未完。
- [確認済み事実] evidence一致性: 181/189 は同一ではない比較結果が出ており、既定固定判断は保留が妥当。
- [未確認] 意味自然性: 181優位を断定する evidence 根拠は未確立。
- [確認済み事実] auto path 実用性: S2/T3/T1/S4 で generation_failed は解消し、採用列と一致。

# 8. 未確認事項
- [未確認] status=reachable と evidence unresolved 再計算値の不一致原因（判定基準差/集計差）の切り分け。
- [未確認] 181 と 189 の意味自然性差を言語学的評価指標で確定する追加検証。
- [未確認] 183 fallback 発火を運用ルール化した際の副作用。
