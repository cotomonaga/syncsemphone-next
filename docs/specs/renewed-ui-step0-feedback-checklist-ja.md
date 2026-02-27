# Renewed UI Step0 指摘チェックリスト（ID対応）

更新日: 2026-02-26

目的:
- Step0（Lexicon/Grammar選択）を仮説検証ループの正式な入口にし、内容確認と比較導線をID管理で固定する。

対応プラン:
- [renewed-ui-step0-improvement-plan-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step0-improvement-plan-ja.md)

## 1. Step0 導線
- [x] `RUI-S0-001` Step0を仮説検証ステップの先頭に追加し、初期表示をStep0にする。
- [x] `RUI-S0-002` 初期状態で `imi01` を選択済みにし、即時 `開始` 可能にする。
- [x] `RUI-S0-003` 候補は `imi01/imi02/imi03` を既定表示し、`More` で追加候補を展開する。
- [x] `RUI-S0-004` `Lexicon/Grammar` を共通の単一選択UIにする（Legacy互換）。
- [x] `RUI-S0-005` `この設定で開始` の操作で Step1 に遷移し、選択文法を実行系に反映する。
- [x] `RUI-S0-006` `候補一覧を更新` ボタンを廃止し、不要操作を減らす。
- [x] `RUI-S0-007` `More` はリスト右下のクリック可能テキストにし、押下状態でチェックマークを表示する。
- [x] `RUI-S0-008` `More` の位置を選択ボックス基準の右下に移動し、ペイン右端に寄らないようにする。
- [x] `RUI-S0-009` Step0の `選択中:` 表示を削除する。
- [x] `RUI-S0-010` `この設定で開始` ボタンを強調スタイルにして視認性を上げる。
- [x] `RUI-S0-011` ステップナビの表記を `Step 0 選択` から `Step 0 LexiconとGrammarの選択` に変更する。
- [x] `RUI-S0-012` ステップナビのStep0表記を `【Step0】` に変更する。
- [x] `RUI-S0-013` ステップナビのStep0表記を `【Step.0】LexiconとGrammarの選択` に修正する。

## 2. 内容確認導線
- [x] `RUI-CV-001` Step0の Lexicon/Grammar 各選択欄に `内容確認` ボタンを置く。
- [x] `RUI-CV-002` Lexicon内容確認画面を追加する（要約+明細）。
- [x] `RUI-CV-003` Grammar内容確認画面を追加する（規則一覧）。
- [x] `RUI-CV-004` Lexicon内容確認で `lexicon.cgi` 相当導線を表示する。
- [x] `RUI-CV-005` Lexiconタイプ集計（例: `N:120`）をクリックすると、下段語彙一覧をそのタイプで絞り込む。
- [x] `RUI-CV-006` 絞り込み中のタイプを明示し、ワンクリックで解除できる。
- [x] `RUI-CV-007` Lexicon内容確認の `語彙を更新` ボタンを廃止し、不要操作を削除する。
- [x] `RUI-CV-008` `絞り込み解除` をタイプ集計チップと同じサイズにし、同じ行の右端へ配置する。
- [x] `RUI-CV-009` `Lexicon内容確認` と `Grammar内容確認` をステップ0のリスト下に配置し、Moreの左側に置いたまま（左右順序は変更なし）で字/ボタンを小さめ・色を薄めにして目立たせない配慮にした。
- [x] `RUI-S0-014` `Lexicon内容確認` と `Grammar内容確認` が右方向へずれていた位置ずれを修正し、リスト右下付近（Moreの左側、左右順序不変）に維持する。
- [x] `RUI-S0-015` More切替時でも `Lexicon内容確認` と `Grammar内容確認` の座標を固定し、両者を同時に動かさないレイアウトに調整する。

## 3. 規則比較
- [x] `RUI-CMP-001` 規則単位の「移植前（Perl）/移植後（Python）」比較画面を追加する。
- [x] `RUI-CMP-002` Grammar内容確認から規則比較へ遷移できるようにする。
- [x] `RUI-CMP-003` 画面上部ナビから `移植前後の比較` タブを外し、Grammar内容確認内の導線からのみ遷移させる。

## 3.5 文法規則パネル運用
- [x] `RUI-GI-001` 6. 文法規則の内容確認は表示時に自動ロードし、`規則一覧を更新` ボタンを廃止する。
- [x] `RUI-GI-002` `資料を閲覧` ボタンを 6. ペイン右下に移動する。

## 4. レイアウト品質
- [x] `RUI-UX-001` 巨大表をページ全体に流さず、内容確認テーブルを独立スクロール領域にする。
- [x] `RUI-UX-002` モダンで理知的なUIを維持し、Step0で操作目的が読み取れる説明を追加する。

## 4.5 ヘッダー表現
- [x] `RUI-HDR-001` 小見出し `SYNCSEMPHONE NEXT`（eyebrow）を廃止する。
- [x] `RUI-HDR-002` メインタイトルを `SYNCSEMPHONE NEXT` に変更する。
- [x] `RUI-HDR-003` ヘッダー説明文（`Perl版の仮説...再現します。`）を廃止する。

## 5. API追加
- [x] `RUI-API-001` `GET /v1/reference/grammars/{grammar_id}/lexicon-summary`
- [x] `RUI-API-002` `GET /v1/reference/grammars/{grammar_id}/lexicon-items`
- [x] `RUI-API-003` `GET /v1/reference/grammars/{grammar_id}/merge-rules`
- [x] `RUI-API-004` `GET /v1/reference/grammars/{grammar_id}/rule-compare/{rule_number}`

## 6. テスト固定
- [x] `RUI-TST-001` APIテストに lexicon summary/items と merge-rules/rule-compare を追加する。
- [x] `RUI-TST-002` UIテストを Step0起点に更新し、内容確認遷移と比較表示を固定する。

## 7. 資料参照整理
- [x] `RUI-REF-001` 資料参照を「素性資料」と「規則資料」の2系統に整理し、3系統に見える構成を解消する。
- [x] `RUI-REF-002` ルール一覧の閲覧・編集（`.pl` 編集）機能を廃止する。
- [x] `RUI-REF-003` 9. 資料参照のUIを単一ビューに再構成し、重複した操作列を解消する。
- [x] `RUI-REF-004` `機能ドキュメントを再読み込み` / `規則ドキュメントを再読み込み` ボタンを廃止し、自動ロード前提の導線に統一する。
- [x] `RUI-REF-005` 素性資料セレクタの表示をファイル名から資料タイトルへ変更する。

## 8. 開発運用スキル
- [x] `RUI-OPS-001` `restart-playwright-env` スキルの起動手順を再整理し、固定起動コマンドを明記する。
- [x] `RUI-OPS-002` 起動スクリプトで listener PID を実測表示し、PIDファイルを実際のlistenerに同期する。
- [x] `RUI-OPS-003` API起動Pythonは仮想環境 (`apps/api/.venv/bin/python`) を優先し、存在しない場合のみ `python3` を使う。

## 9. Step1 再編（Numeration作成）
- [x] `RUI-S1-001` ステップナビ表記を `【Step.1】Numerationの形成` に変更する。
- [x] `RUI-S1-002` Step1のゴールを「Numeration作成」に統一し、主操作を `Numerationを形成` ボタンに一本化する。
- [x] `RUI-S1-003` Step1の入口を3つ（例文選択 / `.num`アップロード / レキシコンから組み立て）に整理する。
- [x] `RUI-S1-004` 例文入口に5つの例文（`白いギターの箱` を含む）を実装する。
- [x] `RUI-S1-005` `.num`アップロード入口で入力テキストをNumerationへ反映できるようにする。
- [x] `RUI-S1-006` 形態素解析（Sudachi）機能を「レキシコンから組み立て」入口の一部として配置する。
- [x] `RUI-S1-007` Step1の入口文言を `numファイルを選ぶ` / `Lexiconから組み立てる` に統一する。
- [x] `RUI-S1-008` `numファイルを選ぶ` モードにファイル選択入力を追加し、選択ファイル内容をテキスト欄へ自動反映する。
- [x] `RUI-S1-009` uploadテキストがタブ区切り `.num` 形式に不適合な場合、テキスト欄左下に赤字エラーを表示する。
- [x] `RUI-S1-010` 形式エラー時は `Numerationを形成` 実行を抑止し、誤入力での反映を防ぐ。

## 10. Step1 安定化（Playwright確認）
- [x] `RUI-S1-011` PlaywrightでStep1操作時のブラウザコンソールエラーを再現し、原因を特定する（再現時点ではStep1 uploadのコンソールエラーなし）。
- [x] `RUI-S1-012` Step1 uploadモードでファイル選択時に内容がテキスト欄へ反映されない不具合を修正する（`input[type=\"file\"]` クリック時リセットを追加）。
- [x] `RUI-S1-013` 修正後にPlaywrightで再検証し、コンソールエラーが解消していることを確認する（`/tmp/step1-playwright-check5.cjs` で errorCount=0）。
- [x] `RUI-S1-014` `numファイルをアップロード` の明示ボタンを追加し、ボタン操作でOSファイル選択画面を必ず開く動線を実装する。
- [x] `RUI-S1-015` `RUI-S1-014` の実装後にPlaywrightで再検証し、選択→反映が毎回発火することを確認する（`/tmp/step1-filechooser-check.cjs`）。
