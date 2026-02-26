# 用語集（確定版・平易）

この文書は、移植作業で使う主要用語の基準です。  
意味を曖昧にしないため、実装・テストで使う語を固定しています。

## 用語の適用範囲（定義）
- `仕様（正本）`
  - Perl 実装の実行結果です。判定根拠は differential / golden / characterization テストです。
- `仕様文書`
  - `syncsemphone-next/docs/specs/*.md` の文書群です。正本の説明補助として扱います。
- `管理文書`
  - 進捗と運用を記録する文書です（例: `移植プロジェクト進捗管理.md`）。

## 文法セット
- `imi01`
  - IMI文法セットの初期版です。
- `imi02`
  - IMI文法セットの中間版です。
- `imi03`
  - IMI文法セットの拡張版です。
- `japanese2`
  - 日本語向けの規則が多い文法セットです。

## 派生時点と状態
- `T0`
  - 規則適用前の初期状態です。
  - 観察文や `.num` から最初に作る出発点で、Step3 の `Load Candidates` / `Execute` はこの状態を起点に進みます。
  - 通常は `history` が空で、`base` には初期語彙項目が入り、ここから `T1` `T2` へ派生が進みます。
- `T1`
  - 1回規則を適用した状態です。
- `T2`
  - 2回規則を適用した状態です。
- `DerivationState`
  - 派生の1時点を表すデータです。`memo/newnum/basenum/history/base` を持ちます。
- `base`
  - 各 lexical item / phrase の配列本体です。
- `newnum`
  - 新しいIDを発行するための連番カウンタです。
- `basenum`
  - `base` で現在有効な項目数です。
- `history`
  - 規則適用履歴の文字列です。

## 規則と指定方法
- `rule_name`
  - 規則名で実行する指定です。
- `rule_number`
  - 規則番号で実行する指定です。
- `left / right`
  - 2項規則の対象インデックスです。
- `check`
  - 1項規則の対象インデックスです。

## 主な規則名
- `RH-Merge`
  - 右側を head として結合します。
- `LH-Merge`
  - 左側を head として結合します。
- `J-Merge`
  - `japanese2` で使う結合規則です。
- `zero-Merge`
  - 空要素を伴う1項規則です。
- `Partitioning`
  - 層構造の再分配を行う1項規則です。
- `Pickup`
  - 部分構造を一時退避する1項規則です。
- `Landing`
  - `Pickup` で退避した構造を再結合する1項規則です。
- `property-Merge`
  - 性質付与系の結合規則です。
- `property-no`
  - `no` 系の性質規則です。
- `property-da`
  - `da` 系の性質規則です。
- `P-Merge`
  - `P` 系の結合規則です。
- `rel-Merge`
  - 関係構築系の規則です。
- `sase1 / sase2 / rare1 / rare2`
  - `japanese2` 特有の規則群です。

## 観察出力
- `tree`
  - ID中心の木構造CSVです。
- `tree_cat`
  - カテゴリ中心の木構造CSVです。
- `LF (list representation)`
  - 意味・述語情報を列挙した表示です。
- `SR (truth-conditional meaning)`
  - 真理条件的意味の層表示です。

## 内部スロット（base項目）
- `id`
  - 項目IDです（例: `x7-1`）。
- `ca`
  - カテゴリです（例: `N`, `V`, `T`）。
- `pr`
  - Predication（三項）です。
- `sy`
  - 統語素性です。
- `sl`
  - ID参照スロットです。
- `se`
  - 意味素性です。
- `ph`
  - 表層語形です。
- `wo`
  - 子ノード（木構造）です。

## 保存と再開
- `resume`
  - 派生状態をテキスト化して保存・再開する機能です。
- `resume_text`
  - 6行形式の保存文字列です（grammar/memo/newnum/basenum/history/base JSON）。
- `export -> import`
  - 保存して再読み込みする往復操作です。
- `対保存ルール`
  - 保存前後で `state` と `tree/tree_cat` が一致するという不変条件です。

## テスト用語
- `characterization test`
  - 現行挙動を固定し、将来の意図しない変更を検知するテストです。
- `differential test`
  - Python実装とPerl参照実装を比較するテストです。
- `golden case`
  - 期待値をfixtureとして固定した比較ケースです。
- `snapshot`
  - ある時点の状態を丸ごと比較する検証方法です。
- `hypothesis loop`
  - 規則差し替えと観察を反復する検証ループです。
