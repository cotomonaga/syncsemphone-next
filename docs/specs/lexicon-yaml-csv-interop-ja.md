# Lexicon YAML/CSV 併用仕様（Perl互換固定）

## 0. 目的
この仕様は、以下を同時に満たすための実装方針を固定する。

1. CSV（実体はタブ区切り）を Perl 正本互換の保存形式として維持する
2. 編集時は可読性の高い YAML を使えるようにする
3. YAML/CSV の相互変換で情報欠落を起こさない
4. 変換後も Perl 実行結果互換（候補・派生・観察）を壊さない

## 1. 非交渉条件（CSV互換）

1. `lexicon-all.csv` は既存 Perl 実装の読み取り形式を厳守する
2. 列順・区切り（TAB）・空欄運用を変更しない
3. 既存 `no`（語彙ID）は再採番しない
4. `read_lexicon` で読めない出力は保存失敗として扱う
5. 変換後 CSV に対して Perl differential test を必須実行する

根拠:
- `read_lexicon` は固定列を TAB で読む実装である
- 参照: `/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-common.pl:77`

## 2. 形式の役割分担

1. CSV（TSV）
- 互換正本
- 実行系（Perl/Python）が参照する形式

2. YAML
- 編集正本（人が読む/編集する）
- コメントを保持する形式
- 保存時に CSV へコンパイルしてから反映

## 3. YAML スキーマ（編集用）

```yaml
meta:
  grammar_id: "imi03"
  source_csv: "lexicon-all.csv"
  generated_at: "2026-02-26T00:00:00Z"
  schema_version: 1

entries:
  - no: 60
    entry: "ジョン"
    phono: "ジョン"
    category: "N"
    predication: []
    sync:
      - "3,53,target,id"
    idslot: "id"
    semantics:
      - attr: "Name"
        value: "ジョン"
    note: "固有名"
```

制約:
1. `entries[].no` は整数かつ一意
2. `predication` は 3 要素タプル配列
3. `sync` は文字列配列（Perl 既存feature表記をそのまま保持）
4. `semantics` は `{attr, value}` の配列
5. 不明列は `extensions` に隔離し、CSVへは出力しない

## 4. CSV <-> YAML マッピング

1. CSV -> YAML
- 固定列を読み取って `entries[]` へ展開
- `sem` は `attr:value` へ分解
- 空欄は YAML では空配列/空文字へ正規化

2. YAML -> CSV
- 既存 Perl 列定義へ再構成
- 可変長領域（pred/sync/sem）は既存上限/列位置に詰める
- 上限超過は保存拒否（明示エラー）

3. ラウンドトリップ要件
- `CSV -> YAML -> CSV` でバイト同一を目標
- 最低限、Perl 読み取り結果同値（構造同一）を必須

## 5. 操作フロー（UI/API）

1. 閲覧
- `GET /v1/lexicon/{grammar_id}?format=yaml|csv`
- デフォルトは YAML（可読性重視）

2. 編集
- `PATCH /v1/lexicon/{grammar_id}/entries/{no}`
- `POST /v1/lexicon/{grammar_id}/entries`（新規追加、`no` 自動採番）
- `DELETE` は禁止（互換性維持のため）

3. 検証
- `POST /v1/lexicon/{grammar_id}/validate`
- 構文検証 + 互換検証 + 影響検証（代表ケース）

4. 保存
- `POST /v1/lexicon/{grammar_id}/commit`
- 実行内容:
  1. YAML検証
  2. CSV生成（tmp）
  3. Perl `read_lexicon` 検証
  4. 差分/回帰テスト
  5. 原子置換
- 失敗時はロールバック

## 6. 互換検証（必須テスト）

1. フォーマット検証
- parser roundtrip test（YAML/CSV）
- ID重複・欠損・型不整合テスト

2. Perl互換検証
- `read_lexicon` 読み取り成功
- 代表 `.num` の `T0` 一致
- `candidates/execute/tree/tree_cat/lf/sr` の差分テスト

3. 回帰検証
- 既存 golden/differential が全件通過
- 追加語彙を使う新規ケースが通過

## 7. DDD 反映

1. 新コンテキスト
- `LexiconEditingContext`

2. 主要モデル
- `LexiconEntryDraft`（YAML編集中）
- `LexiconEntryCanonical`（CSV書出し正規形）
- `LexiconCommitReport`（検証結果・差分要約）

3. ドメインサービス
- `LexiconYamlCodec`
- `LexiconCsvCodec`
- `LexiconCompatibilityValidator`

## 8. 失敗時ポリシー

1. CSV 生成失敗: 反映しない
2. Perl 検証失敗: 反映しない
3. 差分テスト失敗: 反映しない
4. 常に直前バックアップへ復元可能

## 9. 段階導入

1. Phase A: 読み取り専用
- CSV->YAML エクスポート
- 閲覧 UI

2. Phase B: 編集（未保存）
- エントリ単位編集
- 検証レポート表示

3. Phase C: 保存
- YAML->CSV 書き戻し
- 互換テスト自動実行

4. Phase D: 運用
- 変更履歴（誰が、どのIDを、なぜ変更したか）
- 実験再現メタデータの付与

## 10. 実装上の注意

1. `csv` という拡張子でも実体は TAB なので、UI表示では「TSV互換CSV」と明示する
2. `note` 以外の自由記述は原則禁止（互換列を壊すため）
3. 既存 `.num` 参照IDが存在しなくなる変更は禁止
4. ID追加は末尾採番のみ（欠番再利用はしない）
