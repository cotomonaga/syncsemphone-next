# Renewed UI Step1 指摘チェックリスト（ID対応）

更新日: 2026-02-26

目的:
- Step1の違和感をIDで固定し、実装プランと1対1対応で管理する。

対応プラン:
- [renewed-ui-step1-improvement-plan-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step1-improvement-plan-ja.md)

## 1. 文法表示・文法編集
- [x] `S1-GRM-01` 文法セレクトの表示重複（例: `imi03(imi03)`）を解消する。
- [x] `S1-GRM-02` 各文法の中身を閲覧・編集できる画面を追加する。

## 2. Step1 の文言・配置
- [x] `S1-LBL-01` `Refresh Grammars` を日本語表記へ変更する。
- [x] `S1-LBL-02` `Refresh Grammars` ボタンの位置ずれを修正する。
- [x] `S1-LBL-03` Step1主要操作の文言を日本語へ統一する。
- [x] `S1-LBL-04` `Generate .num` を日本語ラベルへ変更する。
- [x] `S1-LBL-05` `Init T0` を日本語ラベルへ変更し、`?` で解説を表示する。
- [x] `S1-LBL-06` `Init from .num` を日本語ラベルへ変更し、`?` で解説を表示する。
- [x] `S1-LBL-07` `Load set-numeration` を日本語ラベルへ変更する（Step2へ移動後に適用）。

## 3. 入力モデル（形態素解析前提）
- [x] `S1-INP-01` `Sentence` 初期値から単語区切り（空白）を除去する。
- [x] `S1-INP-02` `Manual Tokens` を `Sudachi Split Mode` の下へ移動する。
- [x] `S1-INP-03` 単語区切り結果をパステルカラーのタグ表示にする。

## 4. 導線の明確化
- [x] `S1-FLW-01` `Sentence/Token` と無関係な操作をStep1から分離する。
- [x] `S1-FLW-02` Step1内で「何に効く操作か」を明示する説明を追加する。

## 5. 操作反応の可視化
- [x] `S1-GRM-03` `文法定義を閲覧・編集` 押下で、文法編集パネルに確実に遷移し、一覧自動読込と表示更新が起こるようにする。

## 6. 自動読込と文言統一（参照）
- [x] `S1-AUTO-01` `文法一覧を更新` ボタンを押さなくても、初期表示時に文法一覧を自動取得する。
- [x] `S1-AUTO-02` `Load Feature/Rule Docs` 系ボタンを押さなくても、参照パネル表示時に一覧と本文を自動取得する。
- [x] `S1-LBL-08` 参照パネルの英語ボタン名（Feature/Rule Docs系）を日本語に統一する。

## 7. メニュー文言
- [x] `S1-LBL-09` Menu の3項目文言を次に統一する。
  - `仮説検証ステップ`
  - `素性とルールの確認`
  - `語彙の編集`

## 8. UIモード切替
- [x] `S1-UI-01` デフォルト表示を `Renewed UI` に変更する。
- [x] `S1-UI-02` UIモード切替ボタン文言から括弧説明を削除する（`Legacy UI` / `Renewed UI`）。
- [x] `S1-UI-03` UIモード切替ボタンを画面右上端へ移動し、サイズを小さくする。

## 9. 分割UIと操作
- [x] `S1-SPL-01` Step1で `文法 → 観察文 → 分割結果` を縦並びにする。
- [x] `S1-SPL-02` 分割結果ヘッダに `手動 / 自動（Sudachi）` ボタンを並べ、選択中を強調表示する。
- [x] `S1-SPL-03` 手動モードでは空白/カンマ区切り入力欄のみを表示する。
- [x] `S1-SPL-04` 自動モードではSudachi分割モード選択のみを表示する。
- [x] `S1-SPL-05` 自動モードに切り替えた時点で形態素解析を実行し、分割モード切替時もその場で分割結果を更新する。

## 10. Step1 操作ヘルプ
- [x] `S1-HLP-01` Step1操作列の `?` アイコンをボタンの高さ方向中央に揃える。
- [x] `S1-HLP-02` `?` アイコン押下で、その場に説明ポップアップを表示する（hover title依存をやめる）。
- [x] `S1-HLP-03` `.num生成 / 文からT0初期化 / .numからT0初期化` の違いが分かるよう、操作名と補助説明を明確化する。

## 11. 用語説明（T0）
- [x] `S1-TERM-01` Step1 画面上に `T0` の平易な説明を常設表示し、「規則適用前の初期状態」であることを明示する。
- [x] `S1-TERM-02` 用語集の `T0` 定義を、起点・操作対象・派生遷移（T0→T1→T2）が分かる説明へ拡張する。

## 12. 後続対応（登録のみ）
- [ ] `S1-SPL-06` Sudachi 分割モード A/B/C で結果が実際に変わることを、実装確認とテストで固定する。
- [ ] `S1-GOL-01` Step1「入力と初期化」のゴールを明文化し、`.num作成` と `既存ファイル読込` の導線が混在しないUI構成に再整理する。

## 13. Legacy 分離とPerl同一性
- [x] `LEG-ISO-01` Legacy UI を Renewed UI と完全分離し、Legacy表示は Perl 原本HTMLの埋め込みに切り替える。
- [x] `LEG-HTML-01` Legacy API が返す `index-IMI.cgi` HTMLが、Perl直接実行のHTML bodyと一致することをテストで確認する。
- [x] `LEG-HTML-02` Legacy API が返す `syncsemphone.cgi` HTMLが、Perl直接実行のHTML bodyと一致することをテストで確認する。
- [x] `LEG-HTML-03` Legacy API が返す静的資産（`syncsem.css`）が原本と一致することをテストで確認する。
- [x] `LEG-HTML-04` 同一性確認の手順・ハッシュ・結果をレポート化し、再検証可能な形で保存する。
