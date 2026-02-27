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
| S1-SPL-03 | 手動モード時は観察文ベースの分割結果表示を行う | `apps/web/src/App.tsx` | UIテスト |
| S1-SPL-04 | 自動モード時はSudachi分割モード選択のみ表示 | `apps/web/src/App.tsx` | UIテスト |
| S1-SPL-05 | 自動モード切替時に形態素解析を実行し、分割モード変更時も分割結果を即時更新 | `apps/web/src/App.tsx`, `apps/api/app/api/v1/derivation.py`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-SPL-07 | `Lexiconから組み立てる` で手動入力欄を廃止し、観察文（Sentence）を手動分割の元データとして再利用 | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-SPL-08 | 手動モードの初期状態を観察文1塊表示にし、観察文変更時は未分割へリセット | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-SPL-09 | 分割結果表示をクリックで編集可能にし、Enter / blur で確定してパステルタグへ戻す | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-SPL-10 | `Lexiconから組み立てる` 画面の分割モード初期値を `自動（Sudachi）` に変更する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
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
| S1-INP-02 | `Manual Tokens` 別入力を廃止し、観察文（Sentence）を手動分割の元データに統合 | `apps/web/src/App.tsx` | UIテスト |
| S1-INP-03 | トークン結果をパステルタグで可視化 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| S1-FLW-01 | `.num` ソース読込・保存群をStep2へ移動 | `apps/web/src/App.tsx` | UIテスト |
| S1-FLW-02 | Step1に用途説明（分割結果）を追加 | `apps/web/src/App.tsx` | UI目視 |
| S1-NUM-01 | `.num` テキスト（Step1/Step2）から語彙IDを抽出し、選択文法の語彙情報を同一UI内表で表示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| S1-NUM-02 | 辞書未登録IDを「見つかりません」と視認できる形（赤字とメッセージ）で表示する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-NUM-03 | `.num` 入力直下の語彙参照表へ `slot / 指標 / plus` を同時表示して、各語彙IDの対応を明示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| S1-NUM-04 | `Lexiconから組み立てる` 画面でも分割結果からNumerationプレビューを生成し、下部の語彙情報参照を更新する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-NUM-05 | `numerationの語彙情報参照` をPerl版表示に合わせ、行単位レイアウトと色分け強調、下部`.num`表示を実装する | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-NUM-06 | Perl版実ページをPlaywrightで検証し、表示順と要素（slot/x/cat/sy/se/下部`.num`）の一致を確認して反映する | `apps/web/src/App.tsx`, `docs/specs/renewed-ui-step1-feedback-checklist-ja.md` | Playwright |
| S1-NUM-07 | `.num` 語彙参照の `sy/se` を Perl `show_feature` 準拠で文字列化し、`+N(right)(nonhead)` 等の実表示に揃える | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-NUM-08 | `idslot=id` を `xN-M` に置換し、意味素性を `attribute: value` で表示して Perl 表示順に統合する | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S1-NUM-09 | `syncsem.css` の `f1/f4/f5/f6` と `feature/orange` に色・背景・下線を合わせ、`(left)(nonhead)` 等の色分離を再現する | `apps/web/src/styles.css`, `apps/web/src/App.tsx` | Playwright |
| S1-NUM-10 | `.num` を Perl と同じく `\t` 明示表示へ変更し、パース側は実タブ/`\t` の両入力を許容する | `apps/web/src/App.tsx` | UIテスト |
| S2-GRM-01 | `Numerationを形成` で `.num` 確定後に `/v1/derivation/init` を呼び、`T0` 初期化と `【Step.2】Grammarの適用` への遷移を一連処理化する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S2-GRM-02 | Grammar適用ページの主目的を「解釈不可能性の消去」に明示し、手動適用（left/right + rule）操作を維持する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | UIテスト |
| S2-HDA-01 | Perl原本Step2をPlaywrightで再実操作し、`left/right` 選択と規則適用で「未解釈素性が減る/残る」分岐を確認してアシスト要件へ反映する | `docs/specs/playwright-mcp-manual-replay-ja.md` | Playwright操作記録 |
| S2-HDA-02 | `POST /v1/derivation/head-assist` を追加し、全 `left/right` の候補を試行して未解釈素性減少量が正の候補を順位付き返却する | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-03 | Step2に `左右候補を提案` テーブルを追加し、提案行から `left/right` を自動セットして候補読込に接続する | `apps/web/src/App.tsx`, `apps/web/src/types.ts` | `apps/web/src/__tests__/App.test.tsx` |
| S2-HDA-04 | アシスト候補の順位整列とStep2反映フローをAPI/UIテストで固定する | `apps/api/tests/test_derivation.py`, `apps/web/src/__tests__/App.test.tsx` | `pytest`, `vitest` |
| S2-HDA-05 | Step2対象行の表示を `numerationの語彙情報参照` と揃え、同じ行内で left/right を選択できるUIへ統一する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx`, Playwright |
| S2-HDA-06 | `Load Candidates` を廃止し、left/right が揃ったタイミングで候補規則を自動読込する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-HDA-07 | 文言を日本語へ統一する（`左右候補を提案`→`候補を提案`、`Execute`→`実行`） | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-HDA-08 | `head-assist` を最短手順優先へ変更し、grammatical到達可能性と手数を返し、返却上限を5件に制限する | `apps/api/app/api/v1/derivation.py`, `apps/web/src/types.ts` | `apps/api/tests/test_derivation.py` |
| S2-HDA-09 | 提案上位を順次実行した場合に例文でgrammaticalへ到達できることを回帰テスト化する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-OUT-01 | Perl `target` 相当の `process` テキスト（folder/memo/newnum/basenum/history/base-json）を返すAPIを追加する | `packages/domain/src/domain/resume/codec.py`, `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-OUT-02 | Step2に process 出力テキスト欄を追加し、規則適用後の状態をPerl互換フォーマットで可視化する | `apps/web/src/App.tsx`, `apps/web/src/types.ts` | `apps/web/src/__tests__/App.test.tsx` |
| S2-OUT-03 | IMI01「白いギターの箱」で3手適用後の process 出力（履歴・compact JSON）を回帰テストで固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-OUT-04 | Perl `plus_to_numeration` 準拠で、`imi01/imi02` は空plusを `sy` へ追加しない挙動に修正する | `packages/domain/src/domain/numeration/init_builder.py` | `apps/api/tests/test_derivation.py` |
| S1-NUM-11 | `numerationの語彙情報参照` の色クラス (`perl-f*`, `numeration-feature-*`) 変更有無を確認し、未変更であることを検証する | `apps/web/src/styles.css`, `apps/web/src/App.tsx` | Playwright確認 |
| S2-OUT-05 | `process` 変換で `pr` がスカラ空文字の節点は `\"\"` のまま保持し、Perl `target` 出力の入れ子配列形へ合わせる | `packages/domain/src/domain/resume/codec.py` | `apps/api/tests/test_derivation.py::test_derivation_process_export_formats_like_perl_target_output` |
| S2-OUT-06 | `process` 変換で `sy` 空要素の正規化規則を調整し、IMI01 3手後の `[]/[\"\"]/[null,\"\"]` 出力をPerl実行例へ一致させる | `packages/domain/src/domain/resume/codec.py` | `apps/api/tests/test_derivation.py::test_derivation_process_export_formats_like_perl_target_output` |
| S2-UI-01 | Step2表示データ生成時に `sy/se` の `null` を空文字へ正規化し、`null` 文字列の混入表示を防ぐ | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx`, Playwright |
| S1-NUM-12 | `show_feature` 相当描画を拡張し、`34/26/27/70/71` の★/●下付き注記をPerl表示に寄せる | `apps/web/src/App.tsx` | Playwright |
| S2-LYT-01 | Step2で `適用可能ルール` テーブルを `適用対象` の直下へ再配置し、実行導線を固定表示する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx`, Playwright |
| S2-UNDO-01 | Step2候補行の `実行` 横に `やりなおし` を追加し、直前実行の取り消し（undo stack）を実装する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-LYT-02 | `候補を提案` ボタンと提案一覧を、実行導線の下に移動して表示順を整理する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx`, Playwright |
| S2-HDA-10 | 提案候補ボタンを `この候補を実行` に変更し、`left/right` セット後に直接 execute を呼ぶ | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S2-VIS-01 | `適用対象` の `sy/sl/se` 描画を `numerationの語彙情報参照` と同一処理へ統一し、色・記号差分をなくす | `apps/web/src/App.tsx` | Playwright |
| S1-EXM-03 | 例文選択モードを固定文例配列ではなく `set-numeration` 一覧に差し替える | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-EXM-04 | 例文選択モードの表示ラベルをレガシー互換の `memo` 表示に揃える（`[memo]`） | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-EXM-05 | Step1で `例文から選ぶ` に入った時、候補が未取得なら `set-numeration` 一覧を自動読込する | `apps/web/src/App.tsx` | Playwright |
| S1-EXM-06 | 例文候補未取得時にプレースホルダと案内文を出し、空の選択欄表示を避ける | `apps/web/src/App.tsx` | Playwright |
| S1-UPL-01 | `numファイルをアップロード` を `input` と `label` のネイティブ連携へ変更し、ファイル選択ダイアログ起動を安定化する | `apps/web/src/App.tsx` | Playwright |
| S1-UPL-02 | `.num` アップロードは Playwright MCP ではなくChrome手動確認として運用方針へ切替える | `docs/specs/playwright-mcp-manual-replay-ja.md` | 運用確認 |
| S1-CORS-01 | localhost/127.0.0.1 の可変ポート（例: 5174）からのAPI呼び出しをCORS許可する | `apps/api/app/main.py`, `apps/api/tests/test_cors.py` | `pytest` |
| S1-INC-01 | Step1例文候補消失の事故報告（再現条件・原因・修正・再発防止）を文書化する | `docs/specs/incidents/2026-02-26-step1-example-options-incident-ja.md` | 文書レビュー |
| S2-RUL-01 | Step2初期表示で left/right を自動補完し、適用対象未選択でも `適用可能ルール` を表示する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| S2-HDA-11 | Step2候補自動読込を global `loading` から分離し、`候補を提案` で候補が表示されない不具合を解消する | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| S2-LYT-03 | Step2適用対象一覧の罫線接続と文字中央寄せを調整し、行境界の崩れを修正する | `apps/web/src/styles.css`, `apps/web/src/App.tsx` | Playwright |
| S1-SPL-11 | Step0開始時に `setAutoPreviewTokens([])` で分割結果が消えたままになる経路を除去し、開始直後に自動分割を表示できるようにする | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1-SPL-12 | Step0開始後、モード切替なしで分割結果が表示される回帰テストを追加する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S2-HDA-12 | `head-assist` 探索に deadline と評価件数上限を導入し、実データで応答停止しないようにする | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-13 | Web側 `head-assist` 呼び出しへタイムアウトを導入し、遅延時にUIが操作不能へ張り付かないようにする | `apps/web/src/api.ts`, `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-REG-01 | 再発防止テストを追加する（API: IMI01でhead-assist応答時間を検証 / UI: 候補自動読込中でも提案ボタンが押せる） | `apps/api/tests/test_derivation.py`, `apps/web/src/__tests__/App.test.tsx` | `pytest`, `vitest` |
| S2-LYT-04 | Step2適用対象一覧の行高さ・中央寄せ・罫線接続を再調整して表示崩れを解消する | `apps/web/src/styles.css` | Playwright |
| S2-LYT-05 | left/right 選択セルの縦線が下端まで接続するよう、Step2適用対象行の縦方向伸長を調整する | `apps/web/src/styles.css` | Playwright |
| S2-HDA-14 | `head-assist` を first action 付き weighted best-first 探索へ更新し、例文「ジョンがメアリを追いかけた」で到達手順を返せるようにする | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-15 | A*/Dijkstra系一次資料のWeb調査を根拠に探索方式を再選定し、実装方針へ反映する | `docs/specs/renewed-ui-step1-feedback-checklist-ja.md` | 調査確認 |
| S2-REG-03 | 既存回帰（API/Web）を再実行し、探索ロジック変更後の手戻りを防止する | `apps/api/tests/test_derivation.py`, `apps/web/src/__tests__/App.test.tsx` | `pytest`, `vitest`, Playwright |
| S2-HDA-16 | `head-assist` 探索を「初手ラベル付き multi-source A*/Dijkstra + transposition（(初手,状態)優越管理）」へ更新し、初手間で同一状態に収束した場合でも到達手順が欠落しないようにする | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-17 | 「ジョンがメアリを追いかけた」を `init/from-sentence` で生成したNumerationで、提案追従により grammatical 到達できる回帰テストを追加する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-04 | 探索更新後に API/Web の全件テストを再実行し、既存機能の手戻りを防止する | `apps/api/tests`, `apps/web/src/__tests__/App.test.tsx` | `pytest`, `vitest`, `playwright` |
| S2-OUT-07 | ルール適用ごとの形式出力（例: `([x1-1 x2-1] LH-Merge)`）をPerlと一致させるため、Pythonの履歴更新ロジックをPerl実装準拠へ修正する | `packages/domain/src/domain/derivation/execute.py`, `packages/domain/src/domain/resume/codec.py`, `apps/api/tests/test_derivation.py` | `pytest` |
| S2-VIS-02 | Step2適用対象を「適用前要素一覧」ではなく「適用後の合体ノード表示（親子入れ子）」へ更新し、Perl target表示に揃える | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| S2-REG-05 | Perl原本の具体例（`x1-1 N ...` + `x2-1 J ...` -> `LH-Merge`）で、形式出力と適用対象表示が一致する回帰テストを追加する | `apps/api/tests/test_derivation.py`, `apps/web/src/__tests__/App.test.tsx` | `pytest`, `vitest`, Playwright |
| S2-HDA-18 | 「ジョンがメアリをスケートボードで追いかけた」の到達失敗を再現し、未解釈素性残存パターン（`0,17,N,,,right,nonhead`）と候補枯渇条件を記録する | `apps/api/app/api/v1/derivation.py`, `docs/specs/renewed-ui-step1-feedback-checklist-ja.md` | API実測 |
| S2-HDA-19 | 探索予算拡張・global探索・語彙候補差し替え実験を行い、現行アルゴリズム設定で到達不能となる範囲を確定する | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py` | API実測 |
| S2-HDA-20 | head-assist 探索をプロセス並列化し、`parallel_cores` 指定を導入する（未指定2コア、指定時は上限内で反映） | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-06 | 並列コア方針（default/override/clamp）の回帰テストを追加し、API全件テストで手戻りがないことを確認する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-ANL-01 | 成功例/失敗例の差分（`スケートボードで` 追加）を未解釈素性・規則順・語彙選択で考察し、grammatical化手順案を作成する | `docs/specs/playwright-mcp-manual-replay-ja.md` | 9章に差分考察と7手手順を記録 |
| S2-ANL-02 | Perl原本 `syncsemphone.cgi` を実操作して、「スケートボードで」あり文の grammatical 到達可否を確認する | `docs/specs/playwright-mcp-manual-replay-ja.md` | Playwright実操作で grammatical 到達確認済み |
| DOC-RLH-01 | RH/LHマージ＋素性照合の実装仕様を、コード行参照つきで記述した文書を作成する | `docs/specs/rh-lh-merge-feature-matching-code-aligned-ja.md` | 文書レビュー |
| DOC-RLH-02 | HPSG/CG向けに、共通点と相違点を現実装（候補列挙・実行・判定）に限定して説明する | `docs/specs/rh-lh-merge-feature-matching-code-aligned-ja.md` | 文書レビュー |
| DOC-RLH-03 | grammatical判定・history更新・RH/LHのhead/non-head規則を、API/Domainコードと整合する形で固定記述する | `docs/specs/rh-lh-merge-feature-matching-code-aligned-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-01 | HPSGの状態爆発抑制手法を一次資料ベースで調査し、LH/RH適用観点で整理する | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-02 | 上位3手法を比較し、厳密性を維持した最適方式を1つに絞る | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-03 | 採用方式（Subsumptionパッキング＋選択的アンパック）の実装接続点・テスト計画を定義する | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-04 | レポート 7.5 に、`raw` と `packed` の実測比較（depth=1/2 全列挙、depth=3 時間上限）を追記する | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-05 | `Xが状態爆発で求められない場合` の許容記述に合わせ、`X不明 / Y既知` 形式の試算結果を明示する | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-06 | レポート 7.6 に、`head-assist` 実装反映（`search_signature_mode` 切替と回帰固定項目）を追記する | `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md` | 文書レビュー |
| S2-HDA-21 | `head-assist` に `search_signature_mode`（`packed`/`structural`）を追加し、比較実験と本番探索の切替を可能にする | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-22 | 遷移キャッシュ・自己遷移判定を `history` 非依存の structural 署名へ置換し、履歴差分重複探索を抑制する | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-HDA-23 | packed 署名と Pareto 優越管理をトランスポジションへ導入し、状態爆発抑制と到達性維持を両立する | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py` |
| S2-REG-07 | API回帰テストを追加し、`search_signature_mode` 受理/拒否、署名挙動、packed圧縮効果（level2）を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| DOC-HPSG-EXP-07 | 第一層（遷移探索）のみを対象に、状態爆発対策の上位3方式（SAT系/DPOR/A*系）を一次資料で比較する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-08 | 適格性基準を被引用数ベースで明示し、代表論文ごとの指標（citation）を付して方式選定根拠を固定する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-09 | 採用方式を「DPOR-aware IDA*」に絞り、現行コード接続点と完全性条件をレポート化する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-10 | 外部レビュー（独立性依存・dominance危険・IDA*条件）を反映し、第一層結論の妥当性を再評価する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-11 | 結論を「DPOR-aware IDA*単独主軸」から「判定コア/提案エンジン分離」へ改訂する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-12 | 判定コアは dominance を使わない方針と三値判定（到達あり/未到達証明/不明）を明文化する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| S1-LYT-06 | Playwright（1920x1080）で Renewed UI が横幅いっぱいに広がらない症状を再現し、原因を特定する（`.page max-width:1240px`） | `apps/web/src/styles.css`, `output/playwright/layout-step0-1920x1080.png` | Playwright実測 |
| S1-LYT-07 | Renewed UI の横幅制限を解除し、ビューポート幅追従レイアウトへ修正する | `apps/web/src/styles.css` | Playwright + E2E |
| S1-REG-13 | Playwright E2E 全件にレイアウト健全性（ページ幅/overflow）アサーションを追加する | `apps/web/e2e/hypothesis-loop.spec.ts` | `npm run test:e2e` |
| S1-REG-14 | Step1主要UIの表示健全性（観察文/分割結果/Sudachiモード/語彙参照/パネル幅）を回帰テスト化する | `apps/web/e2e/hypothesis-loop.spec.ts` | `npm run test:e2e` |

## 実装メモ（2026-02-27）
- `S2-VIS-02`: Step2 適用対象ペインを `base[slot][7]` の子ノード再帰表示に対応し、合体後ノード（親＋子）を描画するよう更新。
- `S2-REG-05`: Web回帰テスト `renders merged parent+children in Step2 target pane after execute` を追加し、`LH-Merge` 後に独立行が消えて親子表示になることを固定。
- `S2-REG-05`: API回帰テスト `test_derivation_execute_lh_merge_outputs_perl_history_and_merged_children` を追加し、形式履歴と `wo` 子ノード形を固定。
- `S1-LYT-06`: Playwright（1920x1080）で Step0/Step1 を再現し、画面が横いっぱいに広がらない症状を確認（`output/playwright/layout-step0-1920x1080.png`, `output/playwright/layout-step1-current-full.png`）。
- `S1-LYT-07`: `.page` の `max-width` 制限を解除し、`renewed` 画面をビューポート幅に追従させる修正を実施。
- `S1-REG-13/S1-REG-14`: E2E既存2本へ共通レイアウト健全性アサーションとStep1表示健全性アサーションを追加。

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
