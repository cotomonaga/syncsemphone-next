# Renewed UI Step1 改善プラン（ID対応）

更新日: 2026-02-26  
対象チェックリスト:
- [renewed-ui-step1-feedback-checklist-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step1-feedback-checklist-ja.md)

## 実装方針
- Step1は「観察文入力と初期化」に限定する。
- `.num` の入出力や保存系はStep2へ移す。
- 文法定義の閲覧編集は Reference パネルに集約し、Step1から遷移できるようにする。

## 対応表（チェックリストID ↔ 実装内容）

| ID | 実装内容 | 実装先 | 検証 |
|---|---|---|---|
| S1-GRM-01 | 文法表示を `display_name===grammar_id` のとき単独表示に統一 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-GRM-02 | 文法ルール原本の一覧・読込・保存UIを追加 | `apps/web/src/App.tsx` | 手動確認 + APIテスト |
| S1-GRM-03 | `文法定義を閲覧・編集` 押下で、Referenceへ遷移・スクロールし、ルール一覧/先頭ルールを自動読込する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-AUTO-01 | 初期表示時に文法一覧を自動取得する（ボタン押下不要） | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-AUTO-02 | 参照パネル表示時にFeature/Rule docsの一覧・本文を自動取得する（ボタン押下不要） | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-LBL-01 | `Refresh Grammars` を `文法一覧を更新` に変更 | `apps/web/src/App.tsx` | UIテスト |
| S1-LBL-02 | 文法ラベルとボタンを同一行上部に整列 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-LBL-03 | Step1主要文言を日本語化 | `apps/web/src/App.tsx` | UIテスト |
| S1-LBL-04 | `Generate .num` を `.num を生成` に変更 | `apps/web/src/App.tsx` | `App.test.tsx`, Playwright |
| S1-LBL-05 | `Init T0` を `T0 を初期化（文→.num）` + `?` ヘルプ | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-LBL-06 | `Init from .num` を `T0 を初期化（.num）` + `?` ヘルプ | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-LBL-07 | `Load set-numeration` を日本語化（Step2へ移動） | `apps/web/src/App.tsx` | UIテスト |
| S1-LBL-08 | 参照パネルの英語ボタン名（Feature/Rule Docs系）を日本語化 | `apps/web/src/App.tsx` | UIテスト |
| S1-LBL-09 | Menu 3項目文言を `仮説検証ステップ / 素性とルールの確認 / 語彙の編集` に統一 | `apps/web/src/App.tsx` | UI目視 |
| S1-UI-01 | 初期表示UIモードを `Renewed UI` に変更 | `apps/web/src/App.tsx` | UI目視 |
| S1-UI-02 | UIモード切替ボタン文言を `Legacy UI / Renewed UI` に簡素化（括弧説明削除） | `apps/web/src/App.tsx` | UI目視 |
| S1-UI-03 | UIモード切替ボタンを右上端へ移動し、コンパクト表示に変更 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-SPL-01 | Step1の入力順を `文法 → 観察文 → 分割結果` の縦並びに整理 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-SPL-02 | 分割結果ヘッダに `手動 / 自動（Sudachi）` ボタンを並べ、選択中を強調表示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| S1-SPL-03 | 手動モード時は手動入力欄（空白/カンマ区切り）のみ表示 | `apps/web/src/App.tsx` | UIテスト |
| S1-SPL-04 | 自動モード時はSudachi分割モード選択のみ表示 | `apps/web/src/App.tsx` | UIテスト |
| S1-SPL-05 | 自動モード切替時に形態素解析を実行し、分割モード変更時も分割結果を即時更新 | `apps/web/src/App.tsx`, `apps/api/app/api/v1/derivation.py`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-HLP-01 | Step1操作列の `?` アイコンをボタンと高さ方向中央で揃える | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UI目視 |
| S1-HLP-02 | `?` アイコンをクリック開閉式のその場ポップアップに変更する | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-HLP-03 | `.num生成 / 文からT0初期化 / .numからT0初期化` の違いがすぐ分かる文言・補助説明へ更新する | `apps/web/src/App.tsx`, `apps/web/e2e/hypothesis-loop.spec.ts` | UIテスト/E2E |
| S1-TERM-01 | Step1 画面に `T0` の常設説明を追加し、「規則適用前の初期状態」であることを明示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-TERM-02 | 用語集の `T0` 定義を、起点・操作対象・派生遷移が分かる形へ拡張する | `docs/specs/glossary-ja.md` | 文書レビュー |
| S1-SPL-06 | Sudachi 分割モード A/B/C で結果差分が出ることを実装確認し、回帰テストで固定する | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py`, `apps/web/src/__tests__/App.test.tsx` | API/UIテスト |
| S1-GOL-01 | Step1のゴール定義を明文化し、`.num作成` と `既存ファイル読込` の導線を分離したUIに再整理する | `apps/web/src/App.tsx`, `docs/specs/renewed-ui-step1-goal-ja.md` | UIレビュー/E2E |
| LEG-ISO-01 | Legacy UI を Renewed UI から分離し、Perl原本HTMLをiframe表示する経路へ切り替える | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| LEG-HTML-01 | Legacy API の `index-IMI.cgi` 出力が Perl 直接実行と同一であることを確認する | `apps/api/app/api/v1/legacy_perl.py`, `apps/api/tests/test_legacy_perl.py` | APIテスト |
| LEG-HTML-02 | Legacy API の `syncsemphone.cgi` 出力が Perl 直接実行と同一であることを確認する | `apps/api/app/api/v1/legacy_perl.py`, `apps/api/tests/test_legacy_perl.py` | APIテスト |
| LEG-HTML-03 | Legacy API の静的資産（`syncsem.css`）が原本と同一であることを確認する | `apps/api/app/api/v1/legacy_perl.py`, `apps/api/tests/test_legacy_perl.py` | APIテスト |
| LEG-HTML-04 | 同一性確認結果（手順・ハッシュ）をレポート化して再検証可能にする | `docs/specs/legacy-html-parity-report-ja.md` | 文書レビュー |
| S1-INP-01 | `Sentence` 初期値の空白を除去 | `apps/web/src/App.tsx` | UI目視 |
| S1-INP-02 | `Manual Tokens` を `Split Mode` の下へ移動 | `apps/web/src/App.tsx` | UI目視 |
| S1-INP-03 | トークン結果をパステルタグで可視化 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| S1-FLW-01 | `.num` ソース読込・保存群をStep2へ移動 | `apps/web/src/App.tsx` | UIテスト |
| S1-FLW-02 | Step1に用途説明（分割結果）を追加 | `apps/web/src/App.tsx` | UI目視 |

## API追加（S1-GRM-02）
- `GET /v1/reference/grammars/{grammar_id}/rule-sources`
- `GET /v1/reference/grammars/{grammar_id}/rule-sources/{rule_number}`
- `POST /v1/reference/grammars/{grammar_id}/rule-sources/{rule_number}`

実装先:
- `apps/api/app/api/v1/reference.py`
- `apps/api/tests/test_reference.py`

## 完了条件
- 上記IDがすべて実装済みで、チェックリストが完了状態であること。
- `apps/web` のunit testとPlaywright E2E、`apps/api` のreferenceテストが通ること。
