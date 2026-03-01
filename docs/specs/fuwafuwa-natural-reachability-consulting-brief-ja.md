# 外部相談用ブリーフ（機構重視改稿版）
## 題材: 「ふわふわしたわたあめを食べているひつじと話しているうさぎがいる」

更新日: 2026-03-01  
対象リポジトリ: `syncsemphone-next`

## 0. 変更概要（今回強化した点）
- 体裁中心の説明から、機構中心の説明へ改稿した。
- 本文中の情報を、必ず次の4分類で分離した。
  - 確認済み事実
  - 現行実装の仕様
  - 推測/作業仮説
  - 未確認事項
- 探索器について、候補列挙から枝刈り、優先順、再訪抑制、メトリクス加算、continue統合までをパイプラインで明示した。
- RH/LH-Merge について、節点配列 `[0]..[7]` の入出力・消費・保持・順序依存を擬似コードで示した。
- `initial_basenum=13` と `initial_transition_count=134` の関係を、段階別の実測値で説明した。
- 対象文 reachable 可否は「未確定」であることを明示し、受け入れ基準をその前提と整合させた。
- `max_depth_reached=12` の解釈を「深さ不足」ではなく「終端深さ到達済み（幅問題の可能性）」として明示した。
- `state_signature / unresolved / partner_deficit / local_priority` など、探索制御で使う語を本文内で定義した。
- RH/LH 補助関数（`_process_*`）について、入出力契約・副作用・不変量を表形式で追記した。

---

## 1. 相談の目的と非目標
### 1.1 目的
- 現行契約（`reachable / unreachable / unknown`）を守ったまま、対象文で `unknown(timeout)` が続く問題を改善する。
- 網羅列挙ではなく、自然な導出を優先して、到達証拠の取得を安定化する。

### 1.2 非目標
- 例文専用ハック（固定手順注入）
- `unknown` を `unreachable` に読み替えること
- Perl互換の候補列挙/規則適用ロジックを曖昧に変更すること

### 1.3 判定契約（固定）
- `reachable`: 到達証拠を1件以上発見
- `unreachable`: 探索完了かつ到達証拠0件
- `unknown`: 予算切れで探索未完了

---

## 2. 4分類の定義（本文で使うラベル）
- `[確認済み事実]`: コード、API実行ログ、固定ファイルで確認できた内容
- `[現行実装仕様]`: 現在の実装が実際に行っている処理
- `[作業仮説]`: 観測に基づく推定だが、証明や確証がない内容
- `[未確認]`: まだ観測・証明が不足している内容

注: 本文では断定文の冒頭に上記ラベルを付ける。

---

## 3. 確認済み事実
### 3.1 対象文と再現条件
- `[確認済み事実]` 対象文は次の1文で固定:
  - `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる`
- `[確認済み事実]` Step.1 自動生成（`grammar_id=imi01`, `split_mode=A`, `auto_add_ga_phi=true`）の token と ID:
  - token: `ふわふわした / わたあめ / を / 食べている / ひつじ / と / 話している / うさぎ / が / いる / る / φ / φ`
  - lexicon_id: `[264,265,23,266,267,268,269,270,19,271,204,309,309]`
- `[確認済み事実]` 参照 `.num`:
  - `imi01/set-numeration/1608131495.num`（補完なし）
  - `imi01/set-numeration/1608131500.num`（`φ(309)` 2件補完）

### 3.2 前提語彙項目（対象文で実際に使っているID）
`lexicon-all.csv` の実データ（現行ローダ）から抽出。

| ID | 見出し | 範疇 | idslot | 統語素性（sync_features） | 意味素性（semantics） |
|---|---|---|---|---|---|
| 264 | ふわふわした | A | 2,22 | `0,17,N,,,left,nonhead` | `ふわふわした:T` |
| 265 | わたあめ | N | id | なし | `わたあめ:T` |
| 23 | を | J | zero | `0,17,N,,,right,nonhead` / `3,17,V,,,left,nonhead` / `4,11,wo` | なし |
| 266 | 食べている | V | id | `2,17,N,,,left,nonhead` | `Theme:2,33,wo` / `Agent:2,33,ga` / `食べる:T` / `Aspect:progressive` |
| 267 | ひつじ | N | id | なし | `ひつじ:T` |
| 268 | と | J | zero | `0,17,N,,,right,nonhead` / `3,17,V,,,left,nonhead` / `4,11,to` | なし |
| 269 | 話している | V | id | `0,17,N,,,left,nonhead` | `相手:2,33,to` / `Agent:2,33,ga` / `話す:T` / `Aspect:progressive` |
| 270 | うさぎ | N | id | なし | `うさぎ:T` |
| 19 | が | J | zero | `0,17,N,,,right,nonhead` / `3,17,V,,,left,nonhead` / `4,11,ga` | なし |
| 271 | いる | V | id | `2,17,T,,,left,head` | `Theme:2,33,ga` / `いる:T` |
| 204 | る | T | 0,24 | `0,17,V,,,right,nonhead` | `Time:imperfect` |
| 309 | φ | N | id | `4,11,ga` | なし（注記: 音形なしNPガ） |

- `[確認済み事実]` `309` 自動補完は `imi01` + `auto_add_ga_phi=true` のときのみ有効。
- `[確認済み事実]` 補完条件は「`2,33,ga` 需要 > `4,11,ga` 供給」。

### 3.3 imi01 のルールカタログ
- `[確認済み事実]` `imi01/imi01R.pl` のルールは2件のみ。

| ルール番号 | ルール名 | 実体ファイル | kind |
|---|---|---|---|
| 1 | RH-Merge | `MergeRule/RH-Merge_03.pl` | double |
| 2 | LH-Merge | `MergeRule/LH-Merge_03.pl` | double |

- `[確認済み事実]` `imi01` には `zero-Merge / J-Merge / rel-Merge / Partitioning` は含まれない。

### 3.4 対象文の最新観測ログ
- `[確認済み事実]` `/v1/derivation/reachability`（packed, 60秒, max_nodes=2,000,000, max_depth=35）:
  - `status=unknown`
  - `completed=false`
  - `reason=timeout`
  - `expanded_nodes=8877`
  - `generated_nodes=13379`
  - `max_frontier=79`
  - `max_depth_reached=12`
  - `actions_attempted=13113`

### 3.5 数値整合（13語なのに134遷移になる理由）
対象文初期状態（`basenum=13`）で段階別に実測:

| 段階 | 件数 | 算出根拠 |
|---|---:|---|
| 生の順序付きペア数 | 156 | `13 * 12` |
| ルール展開後の候補数 | 312 | 各ペアで RH/LH の2候補 |
| `nohead` 制約で除外 | 178 | `_passes_nohead_constraint` で除外 |
| nohead通過候補（実行前候補） | 134 | `312 - 178` |

ルール別採用件数:
- RH-Merge: 67
- LH-Merge: 67

- `[確認済み事実]` 上の `134` は「列挙段階で nohead を通過した候補数」であり、DFSが最終的に辿る `ordered` 長そのものではない。
- `[確認済み事実]` `max_frontier=79`（3.4）は、`delta_unresolved`/unique-provider/局所絞り込みを通した後の `ordered` 長の最大値であり、測定段階が異なる。

### 3.6 既知 reachable 回帰（維持対象）
- `[確認済み事実]` 現行で reachable 維持:
  1. `imi01`: ジョンがメアリをスケートボードで追いかけた
  2. `imi03`: ジョンがメアリを追いかけた
  3. `imi01`: うさぎがいる

### 3.7 `max_depth_reached=12` の意味（重要）
- `[確認済み事実]` `imi01` のルールカタログは RH/LH の double merge のみである（3.3）。
- `[確認済み事実]` RH/LH が実行されると `execute_double_merge` で non-head 側が `del` され、`basenum` は必ず `1` 減る。
- `[確認済み事実]` 初期 `basenum=13` の場合、導出長の上限は `12` 手である。
- `[確認済み事実]` したがって `max_depth_reached=12` は「深さが足りず届かなかった」ことを意味しない。少なくとも1本の枝は終端深さに到達している。
- `[作業仮説]` このケースの主因は、深さ不足より「分岐幅の爆発」「同型状態の多重訪問」「優先順の弱さ」の組合せである可能性が高い。
- `[未確認]` 上記は reachable / unreachable を確定する証明ではない。`unknown` の理由は依然として「予算内未完走」である。

---

## 4. 現行実装の仕様
### 4.1 状態表現（DerivationState）
- `[現行実装仕様]` 探索状態:
  - `grammar_id`, `memo`, `newnum`, `basenum`, `history`, `base`
- `[現行実装仕様]` `base[i]` の節点配列スロット:
  - `[0] id`
  - `[1] ca`（範疇）
  - `[2] pr`
  - `[3] sy`
  - `[4] sl`
  - `[5] se`
  - `[6] ph`
  - `[7] wo`（子ノード）

### 4.2 探索パイプライン（reachability）
- `[現行実装仕様]` 処理順は次のとおり。

1. 予算・深さ・上界値を解決する。
2. `dfs(current, remaining_depth, path, zero_delta_streak)` を開始する。
3. 終了判定:
   - 未解釈素性0なら goal。
   - timeout/node_limit なら中断。
4. 遷移列挙:
   - 全 `left/right`（`left != right`）を走査。
   - `list_merge_candidates` で RH/LH 候補を取得。
   - `nohead` 制約を適用。
   - 遷移実行（`execute_double_merge`）で次状態を生成。
5. 枝刈り:
   - `delta_unresolved > 0` を除外。
   - unique-provider 制約違反を除外。
   - `delta_unresolved == 0` は条件付き許可。
6. 並び替え:
   - `delta_unresolved`, `partner_deficit`, `partner_priority`, `local_priority`, `rule_number` などでソート。
7. 遷移適用ループ:
   - 1遷移ごとに `actions_attempted += 1`。
   - 再帰呼び出し。
8. 完了時ステータス決定:
   - 完走 + goalあり -> reachable
   - 完走 + goalなし -> unreachable
   - 非完走 + goalなし -> unknown

### 4.2.1 候補列挙の実装粒度（どこで枝が増えるか）
- `[現行実装仕様]` まず `left/right` の順序付きペアを全列挙する（`left != right`）。
- `[現行実装仕様]` 各ペアで `list_merge_candidates` を呼び、rule候補を展開する。
- `[現行実装仕様]` double候補は次で除外される:
  - `left == right`
  - `nohead` 制約違反（`_passes_nohead_constraint`）
  - 同一 action 重複（キー: `rule_number, rule_name, rule_kind, left, right, check`）
  - 実行後が自己ループ（`_state_structural_signature(next)==_state_structural_signature(current)`）
- `[現行実装仕様]` single候補は `basenum<=1` または `imi*` かつ `basenum<=2` のときのみ列挙対象になる。
- `[確認済み事実]` ただし `imi01` のルールカタログには single規則が無いため、この題材では実質的に double のみが遷移候補になる。

### 4.2.2 枝刈り・並び順の実装粒度（どこで捨てるか）
- `[現行実装仕様]` 各遷移で `delta_unresolved = next_unresolved - current_unresolved` を計算する。
- `[現行実装仕様]` `delta_unresolved > 0` は即除外。
- `[現行実装仕様]` unique-provider 制約違反（`_breaks_unique_partner_provider_constraint`）は除外。
- `[現行実装仕様]` `delta_unresolved == 0` は「構造前進（`basenum` 減少）」または許可単項規則のみ許可し、`zero_delta_streak` 上限（12）で打ち切る。
- `[確認済み事実]` この題材（imi01、doubleのみ）では有効な遷移は常に `basenum` が減るため、`delta_unresolved==0` の許可条件は実質的に多くの遷移で自動成立しやすい。
- `[確認済み事実]` 同じ理由で、この題材では `zero_delta_streak <= 12` は一般設計としては存在するが、実効的な枝刈り強度は高くない可能性がある。
- `[現行実装仕様]` 並び順キーは次:
  - 第1キー: `delta_unresolved<0` 優先
  - 第2キー: `partner_deficit` 小さい順
  - 第3キー: `partner_priority`（0優先）
  - 第4キー: `local_priority`（0: case-local, 1: vt-local, 2: その他）
  - 以降: unresolved, basenum, rule_number, left, right, check
- `[現行実装仕様]` imi系ではさらに局所絞り込みがある:
  - partner-resolving候補・single候補が無い局面で、case-local が存在すればそれだけ残す。
  - case-local が無く partner/single も無い局面で、vt-local が存在すればそれだけ残す。

### 4.2.3 再訪抑制（何を記録し、何をスキップするか）
- `[現行実装仕様]` 再訪管理テーブルは `explored_remaining_depth` を使う。
- `[現行実装仕様]` 記録キーは `(current_signature, zero_delta_streak)`。
  - `current_signature` は `search_signature_mode` に応じて structural か packed。
- `[現行実装仕様]` 記録値は「そのキーで既に探索した最大 `remaining_depth`」。
- `[現行実装仕様]` 既訪キーに対して `best_remaining >= 現在remaining_depth` なら、その状態は再展開しない。
- `[作業仮説]` これは depth-aware な再訪抑制だが、packed署名時の同値化粗さによる取りこぼし可能性は `[未確認]`。
- `[現行実装仕様]` なお、自己ループ除外（`next == current` 判定）は structural 署名で固定実装されており、`search_signature_mode` の切替対象ではない。

### 4.3 メトリクス加算タイミング
- `[現行実装仕様]` `generated_nodes`:
  - 各状態で、ソート後の候補列 `ordered` の長さを加算。
- `[現行実装仕様]` `expanded_nodes`:
  - 各状態で `ordered` を確定した時点で `+1`。
- `[現行実装仕様]` `actions_attempted`:
  - 各候補を実際に1回試行する直前に `+1`。
- `[現行実装仕様]` `max_depth_reached`:
  - 再帰呼び出し時の `len(path)` の最大値。
- `[現行実装仕様]` `max_frontier`:
  - 各展開状態での `len(ordered)` の最大値（探索中の「同時候補幅」の最大）。

### 4.4 continue の仕様
- `[現行実装仕様]` continue は「frontier再開」ではない。
- `[現行実装仕様]` 同じ初期 `state` を、増やした予算で再探索する。
- `[現行実装仕様]` 引き継ぐもの:
  - `state`, `grammar_id`, `search_signature_mode`
  - 予算値は `additional_*` を加算して再計算
- `[現行実装仕様]` 引き継がないもの:
  - 直前探索の frontier / explored キャッシュ
  - 途中経路そのもの
- `[現行実装仕様]` 新旧 evidence は木署名（canonical tree signature）で統合する。
- `[現行実装仕様]` 同じ木が複数手順で出た場合、手数の短い方を残す。

### 4.5 RH/LH-Merge の節点スロット更新（実装準拠擬似コード）
#### RH-Merge（right headed）
- `[現行実装仕様]` ヘッドは `right`、非ヘッドは `left`。

```text
input: state, left, right
head_idx = right
nonhead_idx = left
hb = copy(base[head_idx])   # head before
nb = copy(base[nonhead_idx])# nonhead before
mother = copy(hb)
ha = copy(hb)
na = copy(nb)
hb_id = str(hb[0]); nb_id = str(nb[0])
hb_sl_before = str(hb[4]); nb_sl_before = str(nb[4])

# IMI feature engine branch:
(mo_pr, ha_pr, na_pr, hb_sy, nb_sy) = process_pr(hb, nb, rule=RH)
(mo_sl, ha_sl, na_sl)               = process_sl(hb, nb, hb_sy, rule=RH)
(mo_se, ha_se, na_se, hb_sy, nb_sy) = process_se(hb, nb, hb_sy, nb_sy, rule=RH)
(nb_sy, na_se) = apply_kind101(hb_id, nb_id, mo_se, nb_sy, na_se)
(mo_sy, ha_sy, na_sy) = process_sy(hb, nb, rule=RH, head_idx, nonhead_idx, left, right)
# relation append は before-state の sl（hb_sl_before / nb_sl_before）を参照する。
(mo_se, newnum) = append_merge_relation_semantic(
  mo_se, mo_sl, na_sl, nb_id, nb_sl_before, hb_sl_before, newnum
)

mother[2]=mo_pr; mother[3]=mo_sy; mother[4]=mo_sl; mother[5]=mo_se; mother[6]=None
ha[2]=ha_pr; ha[3]=ha_sy; ha[4]=ha_sl; ha[5]=ha_se
na[2]=na_pr; na[3]=na_sy; na[4]=na_sl; na[5]=na_se
mother[7] = [na, ha]               # RHは非ヘッド→ヘッド順

base[head_idx] = mother
delete base[nonhead_idx]           # basenumを1減らす
history += "([left_id right_id] RH-Merge)"
```

#### LH-Merge（left headed）
- `[現行実装仕様]` ヘッドは `left`、非ヘッドは `right`。
- `[現行実装仕様]` RHと同じ補助関数を使うが、ヘッド/非ヘッド割当と子ノード順が逆。

```text
input: state, left, right
head_idx = left
nonhead_idx = right
(中略: RHと同じ補助処理)
mother[7] = [ha, na]               # LHはヘッド→非ヘッド順
base[head_idx] = mother
delete base[nonhead_idx]
history += "([left_id right_id] LH-Merge)"
```

- `[現行実装仕様]` RH/LH ともに `append_merge_relation_semantic` へ渡す `hb_sl/nb_sl` は before-state の `hb[4]/nb[4]` を使う（`process_sl` 後の `ha_sl/na_sl` とは別）。

### 4.6 スロット別の「入力・消費・保持・順序依存」
| スロット | 主入力 | 消費されるもの | 母ノードで保持されるもの | 順序依存 |
|---|---|---|---|---|
| `[0] id` | head側ID | なし | head側IDを保持 | あり（RH/LHでheadが変わる） |
| `[1] ca` | head側ca | なし | head側caを保持（imi01では） | あり |
| `[2] pr` | hb.pr, nb.pr, hb_sy/nb_sy | 条件一致した未解釈参照 | `mo_pr` | あり（先行マージでsyが変わると結果が変わる） |
| `[3] sy` | hb.sy, nb.sy, rule_name | 解消対象sy、一部転写情報 | `mo_sy` | 強い（`se`処理後に再計算） |
| `[4] sl` | hb.sl, nb.sl, hb_sy | 解消対象sl | `mo_sl` | あり |
| `[5] se` | hb.se, nb.se, hb_sy/nb_sy, na_pr | 解消対象se、参照sy | `mo_se` + 関係付加 | 強い（`se`が`sy`参照を消費） |
| `[6] ph` | hb/nb.ph | 母では非表示化 | motherは `None`、葉で保持 | 弱い（表示順には影響） |
| `[7] wo` | ha, na | なし | 子配列（RHとLHで順序差） | あり（木の線形化順） |

### 4.7 探索制御語の定義（入力/出力/用途/安全性）
| 用語 | 入力 | 出力 | 用途 | 安全性との関係 |
|---|---|---|---|---|
| `unresolved` | `state.base` | `int` (`_count_uninterpretable_like_perl`) | ゴール判定・枝刈り | 正規表現 `",[0-9]+"` 依存。理論意味との同値性は `[未確認]` |
| `delta_unresolved` | `current`, `next` の unresolved | `int` | 悪化遷移の除外、優先順 | `>0` 除外はヒューリスティックであり完全性は `[未確認]` |
| `basenum` の前進 | `current.basenum`, `next.basenum` | `bool` (`next < current`) | plateau許可判定、構造進行検出 | imi01 では多くの遷移で真になるため選別力が弱くなりうる |
| `state_signature (structural)` | `grammar_id,newnum,basenum,base` | `str(JSON)` | 再訪抑制・自己ループ判定 | 情報を多く保持。比較的保守的 |
| `state_signature (packed)` | 各行の `ca/sy_core/se_core/pr_core/sl_core/wo_core` と `grammar_id,newnum,basenum` | `str(JSON)` | 署名圧縮モード | ID/音形/一部素性詳細を落とす。同値化健全性は `[未確認]` |
| `zero_delta_streak` | 再帰引数 + `delta_unresolved` | `int` | plateau連鎖の抑制（上限12） | 上限値は経験則。完全性保証なし |
| `partner_deficit` | `state` 全体の demand/provider カウント | `int` | 並び順キー（小さい順） | `Σ_label max(demand_33-provider_33,0) + Σ_label max(demand_25-provider_25,0)`（全ラベル合計）。近似指標であり意味保存の証明なし |
| `partner_priority` | grammar, basenum, 遷移が partner-resolving か | `0/1` | 並び順キー（0優先） | imi序盤の探索誘導ヒューリスティック |
| `local_priority` | case-local/vt-local 判定 | `0/1/2` | 並び順キー、imi局所絞り込み | 絞り込み時は到達性を落とす可能性があり `[未確認]` |
| `unique-provider` | 遷移前後の demand/provider カウント | `bool`（違反なら除外） | 供給源1件の保護 | 経験則。理論安全は未証明 |
| `case-local` | 現在の `base` 配列上で、J項目の直前にある最も近い名詞 index と結ぶ遷移か | `bool` | 局所優先・局所絞り込み | 表層文字列隣接ではなく「現在状態の配列順」に依存。強い探索誘導で意味保存保証なし |
| `vt-local` | 現在の `base` 配列上で `V/T` の index 差が `1` か | `bool` | 局所優先・局所絞り込み | 現在状態の配列隣接に依存。強い探索誘導で意味保存保証なし |
| `max_frontier` | 各展開での `ordered` 長 | `int` | 幅爆発の監視指標 | 深さとは独立に幅の大きさを示す |

### 4.8 補助関数の契約（`execute_double_merge`）
| 関数 | 主入力 | 主出力 | 副作用/契約 | 未解釈増減への関与 |
|---|---|---|---|---|
| `_process_pr_imi03` | `hb, nb, hb_sy, nb_sy, rule_name, grammar_id` | `mo_pr, ha_pr, na_pr, hb_sy, nb_sy` | `pr` を更新し、一部 feature 消費で `hb_sy/nb_sy` を更新。`japanese2` では `na_pr` の `zero` 化あり | `[未確認]`（増やし得る/減らし得る境界の形式証明なし） |
| `_process_sl_imi03` | `hb, nb, hb_sy, rule_name` | `mo_sl, ha_sl, na_sl` | `sl` を head/non-head で再配分 | `[未確認]` |
| `_process_se_imi03` | `hb, nb, hb_sy, nb_sy, rule_name, na_pr` | `mo_se, ha_se, na_se, hb_sy_mut, nb_sy_mut` | `se` と `sy` を相互参照して更新。feature 27 で `na_pr` へ書込む Perl互換分岐あり | 強く関与（33/25/34等の解消に直結） |
| `_apply_kind_feature_101_on_nonhead` | `mo_se, nb_sy, na_se` | `updated_sy, updated_se` | `3,101,*` を消費し `Kind:*` の意味素性を追加 | 間接関与 |
| `_process_sy_imi03` | `hb, nb, rule_name, grammar_id, head/nonhead index` | `mo_sy, ha_sy, na_sy` | `sy` の解消・転写を実施。rule方向・左右位置で挙動が変わる | 直接関与 |
| `_append_merge_relation_semantic` | `mo_se, mo_sl, na_sl, nb_id, nb_sl, hb_sl, newnum, rule` | `mo_se', newnum'` | 条件成立時に `α<sub>newnum</sub>:nb_id` を追加し `newnum+1` | 解消そのものではなく関係ラベル追加 |

補足:
- `[現行実装仕様]` RH/LH の呼び出し順は `pr -> sl -> se -> kind101 -> sy -> relation append` で固定。
- `[未確認]` 上記順序変更時に到達集合が保存される保証はない。
- `[現行実装仕様]` 実行後の不変量:
  - `grammar_id`, `memo` は不変
  - `history` は1トークン追加
  - double merge 成功時 `basenum` は `-1`
  - `newnum` は relation append 成立時のみ増加

---

## 5. 推測/作業仮説
- `[作業仮説]` 深さ不足よりも、幅爆発（`max_frontier`）、同型状態の多重訪問、優先順の弱さが主因である可能性が高い。
- `[作業仮説]` 対象文は RH/LH のみで到達できる可能性は残るが、現行優先順では有望経路に十分な予算が割り当たっていない可能性がある。
- `[作業仮説]` packed署名は枝圧縮に有利だが、意味保存の厳密性評価が不足しており、同値化粒度の再設計余地がある。

---

## 6. 未確認事項
- `[未確認]` 対象文が現行 grammar/lexicon の下で reachable か unreachable かは未確定。
- `[未確認]` `delta_unresolved > 0` 除外が到達可能性を常に保存する証明はない。
- `[未確認]` `delta_unresolved == 0` の条件付き許可が completeness を保つ証明はない。
- `[未確認]` `(state_signature, zero_delta_streak)` による再訪抑制の完全性証明はない。
- `[未確認]` packed署名同値化が、構造署名と同じ到達集合を保存する保証はない。
- `[未確認]` case-local / vt-local 絞り込みが対象文でどの程度探索成功率を上げるかは定量不足。

---

## 7. 刈り込み・優先化ルールの安全性分類
| ルール | 現在の使い方 | 安全性評価 |
|---|---|---|
| `nohead` 制約 | 違反遷移を列挙段階で除外 | `[現行実装仕様]` 文法制約として実装。到達性保存の形式証明は `[未確認]` |
| `delta_unresolved > 0` 除外 | 直ちに捨てる | `[作業仮説]` 強いヒューリスティック。意味保存を断定不可 |
| `delta_unresolved == 0` の条件付き許可 | 構造前進 or 許可単項規則のみ通す | `[作業仮説]` ヒューリスティック。imi01（doubleのみ）では実質的に許可側へ寄りやすく、フィルタ強度は高くない可能性 |
| unique-provider 保護 | 供給1件を潰す遷移を除外 | `[作業仮説]` 経験則ベース。安全証明なし |
| case-local / vt-local 優先 | imi系で候補集合を絞る場合あり | `[作業仮説]` ヒューリスティック。到達性への影響は未検証 |
| self-loop除外（同一状態） | 次状態が current と同一（structural署名一致）なら除外 | `[現行実装仕様]` self-loop 判定自体は structural 固定。packed/structural 差が効くのは再訪抑制キー側 |
| continue時 evidence統合 | 木署名で重複を統合 | `[現行実装仕様]` 判定には不介入、表示集合の同値化のみ |

注: 「安全」と断定できる項目は現時点で置いていない。証明がないものはヒューリスティック扱いとする。

---

## 8. 自然さ評価（この題材で効く項目/効きにくい項目）
- `[現行実装仕様]` reachability API 本体の判定ロジックには自然さ評価を使っていない。
- `[現行実装仕様]` 自然さは設計文書（`reachability-naturalness-design-ja.md`）で定義済みだが、判定契約とは分離される。

この題材（`imi01`, RH/LHのみ）での実効性:
- `[作業仮説]` 効きやすい:
  - `step_count`
  - `late_case_binding_count`
  - `detour_merge_count`
- `[作業仮説]` 0になりやすい:
  - `zero_merge_count`（imi01では該当規則なし）
  - `single_rule_count`（同上）

---

## 9. 外部相談先に求める議論（4点）
1. 分岐爆発は探索パイプラインのどの段で支配的に増えているか。
2. どの刈り込みが意味保存寄りで、どれがヒューリスティックか。
3. 安全な同値化を設計するために、どの情報が足りないか。
4. 対象文 reachable 未確定のままでも整合する受け入れ基準をどう設計するか。

---

## 10. 受け入れ基準（対象文未確定と整合）
### 10.1 必須（契約不変）
- `reachable / unreachable / unknown` の契約を崩さない。
- `unknown` を `unreachable` と誤報しない。
- 既知 reachable 回帰を壊さない。
- 例文専用ハックを入れない。

### 10.2 外部提案の採否基準（実装前評価）
- `[確認基準]` 提案が、次の3点を本文中の語で説明していること:
  - 分岐増大の主段階（列挙/枝刈り/並べ替え/再訪）をどこに置くか
  - どの刈り込みを「意味保存寄り」扱いし、どれをヒューリスティック扱いするか
  - `structural/packed` 同値化で保持すべき情報と、捨てる情報の根拠
- `[確認基準]` 提案が `unknown` 契約を崩さないこと（未完了時に未到達断定しない）。
- `[確認基準]` 反証可能な計測計画（どのログを追加し、何を比較するか）を含むこと。

### 10.3 実装後評価A: reachable が見つかった場合
- `[確認基準]` 対象文で再現可能な到達証拠（規則列・木・process）を1件以上提示。
- `[確認基準]` どの実装変更が効いたかをメトリクスで説明。

### 10.4 実装後評価B: reachable が見つからない場合
- `[確認基準]` 未到達断定は、完走条件と探索空間定義の根拠付きで提示。
- `[確認基準]` 完走できない場合は `unknown` のまま、追加観測計画を提示。

---

## 11. 再現手順（API）
### 11.1 初期化
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/derivation/init/from-sentence \
  -H 'Content-Type: application/json' \
  -d '{
    "grammar_id":"imi01",
    "sentence":"ふわふわしたわたあめを食べているひつじと話しているうさぎがいる",
    "split_mode":"A",
    "auto_add_ga_phi":true,
    "legacy_root":"/Users/tomonaga/Documents/syncsemphoneIMI"
  }'
```

### 11.2 同期判定
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/derivation/reachability \
  -H 'Content-Type: application/json' \
  -d '{
    "state": <init_response.state>,
    "max_evidences":20,
    "offset":0,
    "limit":10,
    "budget_seconds":60,
    "max_nodes":2000000,
    "max_depth":35,
    "search_signature_mode":"packed",
    "legacy_root":"/Users/tomonaga/Documents/syncsemphoneIMI"
  }'
```

### 11.3 非同期と継続探索
1. `POST /v1/derivation/reachability/jobs`
2. `GET /v1/derivation/reachability/jobs/{job_id}`
3. `POST /v1/derivation/reachability/jobs/{job_id}/continue`
4. `GET /v1/derivation/reachability/jobs/{job_id}/evidences`

---

## 12. 参照実装
- API探索本体: `apps/api/app/api/v1/derivation.py`
- 候補列挙: `packages/domain/src/domain/derivation/candidates.py`
- 規則適用: `packages/domain/src/domain/derivation/execute.py`
- Numeration生成: `packages/domain/src/domain/numeration/generator.py`
- ルールカタログ: `packages/domain/src/domain/grammar/rule_catalog.py`

---

## 13. 未確定事項と、追加で必要な観測
### 13.1 未確定事項
- 対象文の最終判定（reachable/unreachable）は未確定。
- 主要枝刈りの意味保存性は未証明。
- packed同値化の健全性境界は未確定。

### 13.2 追加で必要な観測
1. 深さごとの段階別カウント（候補生成数、各枝刈りでの除外数、採用数）。
2. `delta_unresolved` 分布と `partner_deficit` 分布の時系列。
3. packed/structural 切替時の到達集合差分（同一予算条件）。
4. case-local / vt-local 絞り込み有無での成功率・停止深さ比較。
5. continue 前後での証拠増分と重複統合率。

この5点が揃うと、外部相談先は「どこを変えると安全で、どこが危険か」を具体的に議論できる。
