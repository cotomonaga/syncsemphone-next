# RH/LHマージ＋素性照合 実装仕様（コード整合版）

更新日: 2026-02-27

## 0. この文書の位置づけ
- この文書は、現行Python実装をそのまま説明した「実装仕様」です。
- 正本は Perl 実行結果です。本書は Python 実装の現状を、HPSG/CGの専門家にも読める形で明示します。
- 参照コードは `syncsemphone-next` 配下です（ファイル:行番号を併記）。

## 1. 状態モデル（DerivationState）
`DerivationState` は次の6要素を持ちます（`packages/domain/src/domain/common/types.py:8`）。

1. `grammar_id`
2. `memo`
3. `newnum`
4. `basenum`
5. `history`
6. `base`

重要点:
- `base[0] = None` を固定し、実データは `base[1]..base[basenum]` に置きます（Perl互換の1始まり、`types.py:14-15`）。
- `base` の1項目は基本的に次の9スロットです（`init_builder.py:85-95`）。
  - `0:id`
  - `1:ca`（範疇）
  - `2:pr`（Predication）
  - `3:sy`（統語素性）
  - `4:sl`（id-slot）
  - `5:se`（意味素性）
  - `6:ph`（音形）
  - `7:wo`（娘ノード）
  - `8:nb`（補助）

## 2. 初期化（.num -> DerivationState）
初期化は `build_initial_derivation_state` が担当します（`init_builder.py:30`）。

- `.num` は3行前提です（lexicon / plus / idx）。未指定行は空で補います（`parser.py:31-47`）。
- `lexicon_id` を辞書参照し、`base_item` を構築します（`init_builder.py:44-96`）。
- `sy` と `se` は Perl互換で先頭に `None` を入れる場合があります（`init_builder.py:64,82-84`）。
- `newnum=j`, `basenum=j-1` で返します（`init_builder.py:99-104`）。
- `plus` の扱い:
  - `imi01/imi02`: 空値は追加しない（`init_builder.py:21-23`）
  - `imi03` の `target`: `3,53,target,id` に変換（`init_builder.py:24-26`）

## 3. 候補列挙（RH/LHを含む）
候補列挙は `list_merge_candidates` です（`packages/domain/src/domain/derivation/candidates.py:227`）。

### 3.1 RH/LH 適用条件（バージョン依存）
- RH (`_rh_merge_applicable`, `candidates.py:11-18`)
  - `03`: 常に可
  - `04`: `right_category != "T"`
  - `01`: 常に可（ただし後述の追加ブロックあり）
- LH (`_lh_merge_applicable`, `candidates.py:21-29`)
  - `03`: 常に可
  - `04`: `right_category == "T"`
  - `01`: `right_category in {"T","J"}`

### 3.2 RH version=01 の追加抑止
`RH-Merge_01` は次を抑止します（`candidates.py:420-430`）。
- `left=N` かつ `right=J`（`J-Merge` 優先）
- `left.sl` と `right.sl` がともに未解釈式（property-Merge系）

### 3.3 列挙順
- すべての候補を集めた後、`rule_number` でソートして返します（`candidates.py:544`）。

## 4. RH/LH の実行意味論（状態遷移）
実行本体は `execute_double_merge` です（`packages/domain/src/domain/derivation/execute.py:1707`）。

### 4.1 RH-Merge
- `head_idx = right`, `nonhead_idx = left`（`execute.py:1718-1721`）
- 母の娘順: `mother[7] = [na, ha]`（`execute.py:1794`）
- `base[head_idx]` を母で置換し、`base[nonhead_idx]` を削除（`execute.py:1795-1796`）

### 4.2 LH-Merge
- `head_idx = left`, `nonhead_idx = right`（`execute.py:1797-1800`）
- 母の娘順: `mother[7] = [ha, na]`（`execute.py:1873`）
- 同様に non-head 側を削除（`execute.py:1874-1875`）

### 4.3 履歴・カウンタ更新
- 履歴トークン:
  - 2項規則: `([left_id right_id] RULE) `（`_build_history`, `execute.py:14-29`）
  - `β` は `beta` に置換して保存（`execute.py:28`）
- 2項規則後の `basenum = state.basenum - 1`（`execute.py:2009`）
- `newnum` は意味拡張時のみ増えることがあります（後述 `4.4`）。

### 4.4 特徴更新パイプライン（RH/LH共通）
`_uses_imi_feature_engine` が真の文法（`imi01/imi02/imi03/japanese2`）では、以下の順で更新します（`execute.py:10-12`, `1726-1793`, `1805-1872`）。

1. `_process_pr_imi03`
2. `_process_sl_imi03`
3. `_process_se_imi03`
4. `_apply_kind_feature_101_on_nonhead`
5. `_process_sy_imi03`
6. `_append_merge_relation_semantic`（条件を満たすと `α<sub>n</sub>:...` 追加 + `newnum` 増分）

## 5. 素性照合の実装実体（番号ごとの処理）
この系は「型付きAVMの単一unification」ではなく、「文字列化された素性式を規則ごとに手続き更新」する実装です。

### 5.1 `pr` 側（`_process_pr_term`）
対応番号（`execute.py:205-265`）:
- `21,22,23,24,25,26,27,29`

### 5.2 `se` 側（`_process_se_imi03`）
head側 `se` の対応番号（`execute.py:367-461`）:
- `21,23,24,25,26,27,29,30,33,34,70,71`

non-head側 `se` の対応番号（`execute.py:463-500`）:
- `22,27,30`

### 5.3 `sy` 側（`_process_sy_imi03`）
head側で明示処理する番号（`execute.py:635-682`）:
- `1,3,5,6,7,12,14,16,17,51,52`

non-head側で明示処理する番号（`execute.py:772-829`）:
- `1,3,5,6,11,12,13,15,17,51,52,58`

`japanese2` 追加ラベル（`execute.py:613-633`, `702-722`, `755-770`）:
- `1L,2L,3L`

### 5.4 `sl` 側（`_process_sl_imi03`）
対応番号（`execute.py:146-181`）:
- head側: `24,26`（それ以外は係数分岐）
- non-head側: `22,24,25,26`

### 5.5 feature 17 の評価式
`#,X,17,α,β,γ,δ,ε` を5条件で評価します（`_eval_feature_17`, `execute.py:69-99`）。
- `α`: 相手範疇
- `β`: 相手sy
- `γ`: 規則名
- `δ`: left/right 位置
- `ε`: head/nonhead 役割

## 6. grammatical 判定（API実装）
`DerivationState` そのものには grammatical フラグはありません。APIで次の規則を使います。

- 正規表現: `_UNINTERPRETABLE_PATTERN = r",[0-9]+"`（`apps/api/app/api/v1/derivation.py:198`）
- 判定: `json.dumps(state.base)` にこのパターンが1件も出なければ grammatical（`derivation.py:261-267`）

つまり現行は「未解釈素性の型付きカウント」ではなく、「Perl互換の文字列近似カウント」です。

## 7. HPSG/CG 観点での対応付け（実装忠実）
ここは理論一般ではなく、現実装との対応です。

### 7.1 HPSGとの対応
共通点:
- どちらも局所結合を繰り返して構造を形成し、制約で不適合を除外する。

相違点（現実装）:
- HPSG主流実装の中心は型付き素性構造の統合（unification）だが、本実装は `sy/pr/se/sl` の文字列規則更新。
- AVM型階層・一般化統合器は持たない。
- 非局所依存（SLASHなど）の専用データ型は未実装。必要なら `sy/se` の番号規則として個別設計する方式。

### 7.2 CG（Combinatory Categorial Grammar）との対応
共通点:
- 方向性（left/right）が規則適用可否に直結する点。

相違点（現実装）:
- CGの中心であるカテゴリ演算（`X/Y`, `Y\X` と関数適用・合成）を、型計算としては持たない。
- RH/LH は「どちらをheadにするか」を明示する遷移規則で、カテゴリ演算そのものとは別物。
- 実際の可否判定はカテゴリ演算より、番号付き素性照合（`_process_*` 系）が支配。

## 8. 研究実務向けの読み替え
- この実装での「素性照合」は、統一的unificationではなく「番号規則の逐次評価」です。
- この実装での「到達可能性」は、`list_merge_candidates` と `execute_*` の反復で定義されます。
- この実装での「grammatical」は、API上は未解釈パターン件数0です。

## 9. 最小再現手順（コード整合確認）
1. `POST /v1/derivation/init` で `.num` から `state` を作る。
2. 任意の `left/right` を指定して `POST /v1/derivation/candidates` で RH/LH 候補を取得する。
3. `POST /v1/derivation/execute` で RH か LH を1手実行する。
4. `history` が `([xA xB] RH-Merge)` 形式で増えることを確認する。
5. `base` の non-head 側が削除され、`basenum` が1減ることを確認する。
6. `POST /v1/derivation/head-assist` では unresolved 件数が `",[0-9]+"` ルールで評価されることを確認する。

## 10. 参照コード一覧
- `packages/domain/src/domain/common/types.py:8`
- `packages/domain/src/domain/numeration/parser.py:31`
- `packages/domain/src/domain/numeration/init_builder.py:30`
- `packages/domain/src/domain/derivation/candidates.py:227`
- `packages/domain/src/domain/derivation/execute.py:14`
- `packages/domain/src/domain/derivation/execute.py:69`
- `packages/domain/src/domain/derivation/execute.py:1707`
- `apps/api/app/api/v1/derivation.py:198`
- `apps/api/app/api/v1/derivation.py:261`
