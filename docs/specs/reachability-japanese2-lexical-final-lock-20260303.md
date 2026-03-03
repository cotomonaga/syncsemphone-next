# 1. 最終到達レシピ
- [確認済み事実] 追加 row: `264 (japanese2 lookup行)`, `9301 (と の正式行)`。
- [確認済み事実] 既存 row の選択変更: `と -> 9301`、`を -> 181（暫定既定） / 189（比較継続候補）`、`が -> 19（既定） / 183（二段目 fallback）`、`る -> 204固定`。
- [確認済み事実] S4 到達確認済み numeration（9301固定の上での比較）:
  - run181: `[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204]`
  - run189: `[264, 265, 189, 266, 267, 9301, 269, 270, 19, 271, 204]`
- [確認済み事実] 採用 Grammar: `japanese2`。

# 2. 確認済み到達範囲
- [確認済み事実] S4 は **9301固定の上で** `を=181` と `を=189` の両方で reachable が観測された（`S4_after_wo181`, `S4_after_wo189`）。
- [確認済み事実] S2 は `を=181` で reachable だが `best_leaf_unresolved_min=1`、`を=181 + が=183` で `best_leaf_unresolved_min=0`（`S2_after_wo181`, `S2_secondary_wo181_ga183`）。
- [確認済み事実] Step.1 auto は explicit と同じ lexicon IDs を返し、`generation_failed=False`（S2/T3/T1/S4）。
- [確認済み事実] 以上は `budget_seconds=20`, `max_nodes=120000`, `max_depth=28`, `top_k=10` の有限予算実行での観測結果。

# 3. 暫定運用として確定してはいけない理由
- [確認済み事実] `181` と `189` は S2/S4 とも canonical evidence 集合が一致しない（`same_signature_set=false`）。
- [確認済み事実] S4 では semantics difference がある（`semantics_diff_exists_in_common_signatures=true`）。
- [未確認] したがって「181の方が自然」「189を正式除外してよい」は現時点で断定できない。
- [未確認] `status=reachable` と evidence unresolved 再計算値の不一致原因は未切り分け。
- [未確認] `183` は改善例があるが、fallback 条件の副作用は未検証。

# 4. yes/no の最終回答
## Q1: `japanese2` を維持したまま、語彙追加と語彙選択だけで S4 の reachable 観測は得られたか
- [確認済み事実] **yes**。`S4_after_wo181` と `S4_after_wo189` の両 run で `status=reachable`, `reason=timeout` が観測されている。
- [確認済み事実] いずれも `grammar_id=japanese2`・`auto_add_ga_phi=false`・9301固定の上での結果である。
## Q2: `181` を production default として今すぐ固定してよいか
- [確認済み事実] **no**。S2/S4ともに 181/189 の evidence 集合が一致せず、S4 では semantics 差も観測される。
- [未確認] 181優位を意味自然性で支える検証根拠は確立していない。
## Q3: `189` を今すぐ除外してよいか
- [確認済み事実] **no**。`S2_after_wo189` と `S4_after_wo189` の双方で reachable 観測がある。
- [未確認] 除外を正当化する十分な evidence 差分基準は未確立。
## Q4: `183` は default ではなく fallback として保持すべきか
- [確認済み事実] **yes**。S2 では `181+183` が `best_leaf_unresolved_min: 1→0` の改善を示す。
- [確認済み事実] 一方で S4 は `181`（9301固定）で reachable が観測され、183を既定化する根拠は不足。

# 5. 181 vs 189 evidence 比較
## S2
- [確認済み事実] run181 ids=[265, 181, 266, 267, 19, 271, 204] status/reason=reachable/timeout evidence_count=4。
- [確認済み事実] run189 ids=[265, 189, 266, 267, 19, 271, 204] status/reason=reachable/timeout evidence_count=4。
- [確認済み事実] 比較結果: `same_signature_set=false`, `same_strict_evidence=false`, `semantics_diff_exists_in_common_signatures=false`。
## S4
- [確認済み事実] run181 ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] status/reason=reachable/timeout evidence_count=10。
- [確認済み事実] run189 ids=[264, 265, 189, 266, 267, 9301, 269, 270, 19, 271, 204] status/reason=reachable/timeout evidence_count=10。
- [確認済み事実] 比較結果: `same_signature_set=false`, `same_strict_evidence=false`, `semantics_diff_exists_in_common_signatures=true`。
- [確認済み事実] actual evidence の canonical signature/tree/process/history/unresolved/sync・semantics 要約は JSON の `evidence_comparison.S2/S4` に全件格納。

# 6. 183 fallback 条件
- [確認済み事実] 既定値は `が=19` を維持し、`183` は二段目 fallback 候補として保持する。
- [推測] 発火条件は「`を=181/189` 適用後も unresolved が残るケースで、S2型（eat-clause中心）改善確認が必要な場合」。
- [未確認] fallback 発火時の副作用は未検証であり、運用条件は確定前提ではない。

# 7. Step.1 auto vs explicit
- [確認済み事実] S2: auto_ids=[265, 181, 266, 267, 19, 271, 204] / explicit_ids=[265, 181, 266, 267, 19, 271, 204] / same=true / generation_failed=false。
- [確認済み事実] T3: auto_ids=[264, 265, 181, 266, 267, 19, 271, 204] / explicit_ids=[264, 265, 181, 266, 267, 19, 271, 204] / same=true / generation_failed=false。
- [確認済み事実] T1: auto_ids=[265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / explicit_ids=[265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / same=true / generation_failed=false。
- [確認済み事実] S4: auto_ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / explicit_ids=[264, 265, 181, 266, 267, 9301, 269, 270, 19, 271, 204] / same=true / generation_failed=false。

# 8. 最終判断
- [確認済み事実] 最終到達レシピは確定した: `japanese2` 固定、`9301` 採用、`を=181/189比較継続`、`が=19既定・183fallback`、`る=204固定`。
- [確認済み事実] ただし暫定運用の既定化は **まだ確定してはいけない**。
- [確認済み事実] 理由は、181/189のevidence差分が残存し、reachable判定とunresolved再計算の整合監査が未完了だから。

# 9. 未確認事項
- [未確認] status=reachable と evidence unresolved 再計算値の不一致原因。
- [未確認] 181 と 189 の意味自然性差を運用判断へ反映できる判定基準。
- [未確認] 183 fallback 条件の副作用。

## 総括
- [確認済み事実] 到達レシピの結論は出た。
- [確認済み事実] しかし運用既定化の結論はまだ出ていない。
- [確認済み事実] 次段は lexical-only 実装確定ではなく、運用確定のための整合監査である。