# 到達判定を維持したまま自然さを評価する設計（DAGベース）

更新日: 2026-02-28  
対象: `syncsemphone-next` (`/v1/derivation/reachability*`, Renewed UI Step2)

## 1. 目的
- 既存の到達判定契約（`reachable / unreachable / unknown / failed`）は変更しない。
- その上で、`reachable` 証拠の中から「言語学的に自然な導出」を見やすく提示する。
- 到達性（解の存在判定）と自然さ（解の品質評価）を分離し、誤判定を避ける。

## 2. 背景と問題
- 現在の到達判定は、Perl互換の未解釈素性カウント（`,数字`）が `0` になるかで判定する。
- この判定は「到達可否」を扱うには正しいが、導出の自然さは保証しない。
- 実際に `ジョンが本を読んだ` では、`reachable` でも `zero-Merge` が複数回入る導出が上位に出ることがある。
- 研究用途では、到達可否だけでなく「どの到達証拠が自然か」を比較できる必要がある。

## 3. 設計原則
- 原則1: 到達判定（status）は既存ロジックを維持する。
- 原則2: 自然さ評価は「証拠整形フェーズ」でのみ付与し、探索木（DAG）や遷移可否に介入しない。
- 原則3: `unreachable` 判定条件は維持する（完走時のみ）。自然さ評価は `unreachable` を覆さない。
- 原則4: 自然さ評価の内訳を必ず返し、なぜその順位なのかを説明可能にする。

## 4. 用語整理
- 到達判定: 未解釈素性が最終状態で `0` かを判定する機能。
- 証拠: `rule_sequence + tree_root + process_text` を持つ `reachable` 導出。
- 自然さ評価: 証拠に対するスコアリング（罰点方式）と説明ラベルの付与。
- DAG: 探索中に同値状態を共有して持つ有向非巡回グラフ。探索空間圧縮の基盤。

## 5. 対象範囲（今回）
- 対象に含む:
  - APIレスポンスに自然さメタデータを追加する設計。
  - 証拠の並び順に自然さ優先を追加する設計。
  - UIで自然さ内訳を表示する設計。
- 対象に含まない:
  - ルール適用可否や候補列挙条件の変更。
  - `status` 判定ロジックの変更。
  - Perl互換ロジック（`list_merge_candidates` / `execute_*`）の変更。

## 6. 自然さ評価モデル（罰点方式）

### 6.1 基本式
- `natural_penalty = Σ(weight_i * feature_i)`
- `natural_score = max(0, 1000 - natural_penalty)`（表示用）
- 罰点が小さいほど自然。順位は `natural_penalty` 昇順。

### 6.2 feature 定義（初版）
- `zero_merge_count`: `zero-Merge` の適用回数。
  - 意図: 空要素注入が多い導出を下げる。
- `single_rule_count`: 単項規則（`zero-Merge`, `Pickup`, `Landing`, `Partitioning`）総回数。
  - 意図: 付加的操作への依存を下げる。
- `late_case_binding_count`: 格助詞結合が遅れるパターン数。
  - 意図: 局所的な `N+J` 結合を優先する。
- `detour_merge_count`: 同一終端に対する遠回り遷移（規則列パターンで検出）。
  - 意図: 同到達でも冗長な順序を下げる。
- `step_count`: 総手数。
  - 意図: 同品質なら短い導出を優先する。

### 6.3 重み（初期値）
- `zero_merge_count`: 120
- `single_rule_count`: 60
- `late_case_binding_count`: 40
- `detour_merge_count`: 30
- `step_count`: 10

注: 重みは設定ファイル化し、固定値をテストでスナップショット管理する。

## 7. API設計（差分）

### 7.1 `ReachabilityEvidenceResponse` 追加項目
- `naturalness`:
  - `score`: `int`（0..1000）
  - `penalty`: `int`
  - `grade`: `A|B|C|D`
  - `breakdown`: `[{key, count, weight, subtotal, note}]`
  - `warnings`: `string[]`（例: `zero-Mergeが2回含まれます`）

### 7.2 `counts` 追加項目
- `natural_sort_applied`: `bool`
- `natural_score_min`: `int | null`
- `natural_score_max`: `int | null`

### 7.3 EvidenceページングAPIのクエリ追加
- `sort_mode`:
  - `default`（現行互換: `steps_to_goal -> tree_signature`）
  - `natural`（`penalty -> steps_to_goal -> tree_signature`）

### 7.4 互換性
- 既存クライアント互換のため、`sort_mode` 未指定時は `default`。
- `status` と `count_status` は完全互換。

## 8. UI設計（Step2）
- 現行の「候補を提案」導線は維持。
- 到達結果表示に以下を追加:
  - 並び替えトグル: `到達手順優先 / 自然さ優先`
  - 各証拠カードに `自然さスコア` と `主な減点理由` を表示
  - 詳細展開で `breakdown` を確認可能にする
- 既定は `到達手順優先`（既存運用を壊さないため）。

## 9. 実装順序（次工程）
- Phase A: 自然さ評価関数を追加（API内部のみ、表示未反映）
- Phase B: APIレスポンスへ `naturalness` 追加
- Phase C: `/evidences` に `sort_mode=natural` 追加
- Phase D: Step2 UIにソートトグルと内訳表示追加
- Phase E: 回帰テスト・E2Eテスト追加

## 10. テスト設計

### 10.1 到達性不変テスト（必須）
- 既存 `reachable-confirmed-sets` 全件で、変更前後の `status` が一致すること。
- `unknown/unreachable` の条件が変わらないこと。

### 10.2 自然さ評価テスト
- 同一 `status=reachable` の複数証拠で、`zero-Merge` 多い方が `natural_score` 低いこと。
- `sort_mode=natural` で `penalty` 昇順になること。
- `breakdown` 合計が `penalty` と一致すること。

### 10.3 UIテスト
- ソートトグル切替で並び順が変わること。
- `自然さスコア` と `警告` が表示されること。
- 既存操作（候補を提案、探索を続ける）が壊れないこと。

## 11. 想定リスクと対策
- リスク: 「自然さ」を強制制約と誤解して `reachable` が変わると誤読される。
  - 対策: UI文言に「自然さは並び替え評価。到達判定は不変」を明記。
- リスク: 重み調整で順位が頻繁に変わる。
  - 対策: 重みを設定化し、変更時はリリースノートと比較表を残す。
- リスク: 証拠整形フェーズの負荷増。
  - 対策: `max_evidences` 範囲内のみ評価し、ページ外を遅延評価しない。

## 12. 受け入れ条件（実装時）
- 到達判定結果 (`status`, `count_status`) が既存回帰と一致する。
- `reachable` の各証拠に自然さ情報が付く。
- 自然さ優先表示で、`zero-Merge` 多用導出が下位に移動する。
- Step2で研究者が「到達可否」と「導出の自然さ」を分けて観察できる。

---

この設計は「到達判定を厳密に維持する」ことを最優先にしつつ、証拠比較の実務で必要な自然さ評価を追加するためのものです。  
探索器の可否判定はそのまま、証拠の見せ方だけを改善する方針です。
