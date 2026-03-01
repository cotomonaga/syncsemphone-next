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
| DOC-HPSG-EXP-13 | 未到達判定の前提として、深さ上限の根拠（`basenum` 単調減少なら `B0-1`、非単調遷移混在なら「深さk以内」限定）を明文化する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-14 | IDDFS + transposition の完全性条件（深さ情報付きTT、より深い反復でのreopen必須、深さ情報なしvisited禁止）を明記する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-15 | DPOR独立性の最小安全条件（read/write交差、適用可否干渉、`newnum`含むグローバル書込）と自動同値検査の運用を明記する | `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| S1-LYT-06 | Playwright（1920x1080）で Renewed UI が横幅いっぱいに広がらない症状を再現し、原因を特定する（`.page max-width:1240px`） | `apps/web/src/styles.css`, `output/playwright/layout-step0-1920x1080.png` | Playwright実測 |
| S1-LYT-07 | Renewed UI の横幅制限を解除し、ビューポート幅追従レイアウトへ修正する | `apps/web/src/styles.css` | Playwright + E2E |
| S1-REG-13 | Playwright E2E 全件にレイアウト健全性（ページ幅/overflow）アサーションを追加する | `apps/web/e2e/hypothesis-loop.spec.ts` | `npm run test:e2e` |
| S1-REG-14 | Step1主要UIの表示健全性（観察文/分割結果/Sudachiモード/語彙参照/パネル幅）を回帰テスト化する | `apps/web/e2e/hypothesis-loop.spec.ts` | `npm run test:e2e` |
| S2-HDA-24 | `head-assist` から特定例文への固定手順注入（答え誘導）を除去し、通常探索のみで `reachable_grammatical` を算出する | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-REG-08 | スケートボード文の回帰を「誤って到達可能と判定しない」テストへ更新し、API全件・Web全件を再実行する | `apps/api/tests/test_derivation.py` | `pytest`, `vitest`, `playwright` |
| DOC-HPSG-EXP-16 | 「第二層を実装しても未解決、第一層を実装しても未解決」を根拠付きでレポート化する | `docs/specs/layer1-layer2-nonconvergence-report-ja.md`, `docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md`, `docs/specs/reachability-first-layer-search-methods-ja.md` | 文書レビュー |
| S2-HDA-25 | Perl既知7手を Python で逐次リプレイし、各手の候補存在・遷移結果・未解釈数を照合する検証モードを追加する | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py` | `pytest` |
| S2-HDA-26 | DPOR/TTを無効化した深さ制限完全探索（baseline）を追加し、深さ7で既知手順を再発見できるか検証する | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-09 | `未到達` と `不明(予算切れ)` の返却条件をテストで固定し、判定誤用を防止する | `apps/api/tests/test_derivation.py` | `pytest` |
| DOC-HPSG-EXP-17 | 切り分けレポート9.2の結果表現を `found=False` から `不明（探索未完了）` に修正し、二値誤判定を回避する | `docs/specs/layer1-layer2-nonconvergence-report-ja.md` | 文書レビュー |
| DOC-HPSG-EXP-18 | 切り分けレポート9.3の判定を「3確定」から「不明（完走前打切り）」へ改訂し、状態爆発の下界試算（順序爆発）を追記する | `docs/specs/layer1-layer2-nonconvergence-report-ja.md` | 文書レビュー |
| S2-HDA-27 | `POST /v1/derivation/head-assist` を提案APIから到達正判定APIへ完全置換し、`reachable/unreachable/unknown/failed` + 証拠返却へ更新する | `apps/api/app/api/v1/derivation.py`, `apps/api/tests/test_derivation.py` | `pytest` |
| S2-HDA-28 | 到達証拠を `rule_sequence + tree_root + process_text` で返却し、`max_evidences` と `offset/limit`（10件おかわり）に対応する | `apps/api/app/api/v1/derivation.py`, `apps/web/src/types.ts`, `apps/web/src/App.tsx` | `pytest`, `vitest` |
| S2-HDA-29 | 非同期ジョブAPI（start/status/evidences）とWebポーリング進捗バーを実装し、API処理中の完了率を表示する | `apps/api/app/api/v1/derivation.py`, `apps/web/src/App.tsx`, `apps/web/src/api.ts` | `pytest`, `vitest`, `playwright` |
| S2-HDA-30 | 件数契約（`count_status/count_unit/count_basis/tree_signature_basis`）と巨大整数文字列返却を固定する | `apps/api/app/api/v1/derivation.py`, `apps/web/src/types.ts` | `pytest`, `vitest` |
| DOC-HPSG-EXP-19 | 設計レポート用語を「森林」から「DAG（共有DAG）」へ統一し、上界A/Bと進捗率定義を追記する | `docs/RHLHマージ＋素性照合における到達性と文法妥当性検証のための設計レポート.md` | 文書レビュー |
| ENV-UNI-01 | `apps/api` と `packages/domain` の `requires-python` を `>=3.9` に揃え、3.12必須扱いを撤回する | `apps/api/pyproject.toml`, `packages/domain/pyproject.toml` | `pip install -e '.[dev]'`（3.9） |
| ENV-UNI-02 | FastAPI/uvicorn/pydantic/pytest/httpx を 3.9 実動バージョンへ固定する | `apps/api/pyproject.toml`, `packages/domain/pyproject.toml` | `pip check`, `pytest` |
| ENV-UNI-03 | テストスクリプトを単一仮想環境（`apps/api/.venv`）固定へ変更し、`python3` 直呼びを排除する | `scripts/test-all.sh` | `./scripts/test-all.sh` |
| ENV-UNI-04 | README セットアップ手順を単一仮想環境運用に合わせ、`zsh` で壊れない `pip install` 表記へ修正する | `README.md` | 文書レビュー |
| S2-HDA-31 | Reachability遷移列挙で探索削減ルールを全適用する（`nohead` 制約、未解釈素性の単調減少、格助詞の直前名詞優先、局所 `V-T` 優先） | `apps/api/app/api/v1/derivation.py` | `apps/api/tests/test_derivation.py`, `./scripts/test-all.sh` |
| S2-HDA-32 | API経路を `/v1/derivation/reachability*` に統一したまま、Step2の操作文言を `候補を提案` へ維持して仮説検証導線を保持する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-REG-10 | Webユニットテストを非同期ジョブAPI（`/reachability/jobs`）仕様へ更新し、Step2提案UIの回帰を固定する | `apps/web/src/__tests__/App.test.tsx` | `npm test -- src/__tests__/App.test.tsx` |
| S2-REG-11 | 全件テスト（Web unit / API pytest / `scripts/test-all.sh`）を再実行し、手戻りなしを確認する | `apps/web`, `apps/api`, `scripts/test-all.sh` | 実行ログ |
| S2-REG-12 | 文入力経路（`/init/from-sentence`）で生成したスケートボード文の state に対し、`/reachability` が `reachable` を返す回帰テストを追加する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-13 | Playwright実機で `Step1 -> Numerationを形成 -> Step2 候補を提案` を実行し、スケートボード文で `reachable` 判定が表示されることを確認する | `output/playwright`（実機確認） | Playwright |
| S1-MOR-01 | Sudachi自動分割で `いる`（動詞終止形）を検出した場合に時制語彙 `る` を補完し、Step1自動モードで `うさぎ / が / いる / る` を扱えるようにする | `packages/domain/src/domain/numeration/generator.py` | `apps/api/tests/test_derivation.py` |
| S1-REG-15 | `/v1/derivation/numeration/tokenize` の回帰テストで、`うさぎがいる` の自動モード分割が `うさぎ, が, いる, る` になることを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-14 | `init/from-sentence(うさぎがいる)` から `reachability/jobs` を実行し、Step2「候補を提案」相当経路で `reachable` 到達を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-MOR-02 | Sudachi活用形後処理を拡張し、`い/かった/た/だ/だった/でした/です` の7系列を自動モードで補完・正規化する | `packages/domain/src/domain/numeration/generator.py` | `apps/api/tests/test_derivation.py` |
| S1-REG-16 | `/v1/derivation/numeration/tokenize` の回帰テストで、7系列時制語彙の自動分割結果を文ごとに固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-17 | `/v1/derivation/numeration/generate` の回帰テストで、`かわいかった/学生だった/学生でした` が時制語彙ID（`253/258/260`）へ解決されることを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-18 | 7時制の `.num` 例文探索結果（存在/非存在）をテスト表へ固定し、`num` 由来文を優先して自動モード検証に使う | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-15 | 7時制例文を `init/from-sentence`（自動モード）で初期化後、`reachability` が `reachable` になることを回帰テストで固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-UI-08 | Step1「numerationの語彙情報参照」で複数候補行に `候補(n)` を表示し、行内展開で候補詳細を確認できるUIを追加する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| S1-UI-09 | 行内候補から `この候補に差し替え` を実行した際に `.num` と語彙情報参照を即時更新する（build_lexiconモード） | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S1-REG-19 | Webユニットテストで Step1 行内候補UIの表示と差し替え反映（`Sem-204 -> Sem-308`）を固定する | `apps/web/src/__tests__/App.test.tsx` | `npm test` |
| S2-UI-03 | Step2「適用対象」ペインで複数候補行に `候補(n)` を表示し、行内展開で候補詳細を確認できるUIを追加する | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-UI-04 | Step2行内候補 `この候補に差し替え` で `.num` 再構成→`init` によるT0再初期化を行い、Step2で継続できるようにする | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| S2-REG-16 | Webユニットテストで Step2 行内候補差し替え後の表示更新（`Sem-204 -> Sem-308`）を固定する | `apps/web/src/__tests__/App.test.tsx` | `npm test` |
| LEX-UI-12 | Step1/Step2候補展開で `sync_features` を表示し、本体行と同等に `+N(right)(nonhead)` 等の統語素性を確認できるようにする | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| LEX-API-01 | `/v1/lexicon/{grammar_id}/items` の語彙項目CRUD API（一覧/取得/作成/更新/削除）を追加する | `apps/api/app/api/v1/lexicon_ext.py`, `apps/api/app/main.py` | `pytest` |
| LEX-API-02 | `/v1/lexicon/value-dictionary` のバリュー辞書CRUD APIを追加する | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| LEX-API-03 | バリュー辞書の使用件数参照/一括置換/参照中削除拒否（409）を追加する | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| LEX-API-04 | 語彙項目ごとの num 紐付けAPI（一覧/作成/更新/削除）を追加する | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| LEX-API-05 | 語彙項目ごとの研究メモAPI（現在値/更新/履歴/履歴復元）を追加する | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| LEX-API-06 | Lexicon版情報API（一覧/差分）を追加する | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| LEX-UI-01 | Lexiconページを語彙項目中心の3ペイン構成（一覧/編集/研究支援）へ全面改訂する | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, `playwright` |
| LEX-UI-02 | 構造系プロパティを選択式入力へ統一する（`category/predicates/sync_features/idslot/semantics`） | `apps/web/src/LexiconWorkbench.tsx` | `vitest` |
| LEX-UI-03 | バリュー辞書管理UI（CRUD + 使用件数 + 一括置換）を実装する | `apps/web/src/LexiconWorkbench.tsx` | `vitest` |
| LEX-UI-04 | num紐付けUI（語彙項目ごと複数リンク）を実装する | `apps/web/src/LexiconWorkbench.tsx` | `vitest` |
| LEX-UI-05 | 研究メモUI（改訂履歴・差分・復元）を実装する | `apps/web/src/LexiconWorkbench.tsx` | `vitest` |
| LEX-REG-01 | 新規Lexicon API群（`lexicon_ext`）の回帰テストを追加する | `apps/api/tests/test_lexicon_ext.py` | `pytest` |
| LEX-REG-02 | Lexicon新UIのWebユニットテストを追加する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-REG-03 | Lexicon新UIのE2Eテストを追加する | `apps/web/e2e/hypothesis-loop.spec.ts` | `playwright` |
| LEX-API-07 | メタDB URL 未設定時、Lexicon読取系APIを空結果でフォールバックし語彙編集ページを継続利用可能にする | `apps/api/app/api/v1/lexicon_ext.py` | `pytest` |
| UI-PERSIST-01 | リロード時にページ遷移状態が変わらないよう、Renewed UI の表示状態を保存・復元する | `apps/web/src/App.tsx` | `vitest` |

## 実装メモ（2026-02-27）
- `S2-VIS-02`: Step2 適用対象ペインを `base[slot][7]` の子ノード再帰表示に対応し、合体後ノード（親＋子）を描画するよう更新。
- `S2-REG-05`: Web回帰テスト `renders merged parent+children in Step2 target pane after execute` を追加し、`LH-Merge` 後に独立行が消えて親子表示になることを固定。
- `S2-REG-05`: API回帰テスト `test_derivation_execute_lh_merge_outputs_perl_history_and_merged_children` を追加し、形式履歴と `wo` 子ノード形を固定。
- `S1-LYT-06`: Playwright（1920x1080）で Step0/Step1 を再現し、画面が横いっぱいに広がらない症状を確認（`output/playwright/layout-step0-1920x1080.png`, `output/playwright/layout-step1-current-full.png`）。
- `S1-LYT-07`: `.page` の `max-width` 制限を解除し、`renewed` 画面をビューポート幅に追従させる修正を実施。
- `S1-REG-13/S1-REG-14`: E2E既存2本へ共通レイアウト健全性アサーションとStep1表示健全性アサーションを追加。
- `DOC-HPSG-EXP-13`: 第一層判定コアの未到達判定条件を、`basenum` 単調減少時と非単調遷移混在時で分けて明文化。
- `DOC-HPSG-EXP-14`: IDDFS+TTの落とし穴（深さ情報なしvisited）を禁止事項として明記し、深さ情報付きTT+reopen必須を追記。
- `DOC-HPSG-EXP-15`: DPOR独立性の保守条件に `newnum` を含むグローバル書込を追加し、候補ペアの `a→b / b→a` 自動同値検査運用を追記。
- `S2-HDA-24`: `head-assist` に追加されていた特定例文向けの固定手順注入を削除し、探索結果を通常ロジックへ戻した。
- `S2-REG-08`: スケートボード文の回帰を「到達の誤主張をしない」内容へ更新し、`apps/api` 全件 (`79 passed`)・`apps/web` unit (`20 passed`)・E2E (`2 passed`) を再実行して固定。
- `DOC-HPSG-EXP-16`: 第一層/第二層とも現時点で到達性未解決である事実を、根拠付きレポートへ整理。
- `S2-HDA-25/S2-HDA-26/S2-REG-09`: 未解決要因を4仮説で分解し、`7手リプレイ -> 最小完全探索` の順で切り分ける方針を追加。
- `S2-HDA-25`: 診断API `/v1/derivation/head-assist/diagnose` を追加し、既知7手リプレイ（候補存在・未解釈数推移・basenum推移）を自動照合可能にした。
- `S2-HDA-26`: 同診断APIに DPOR/TT 無効の depth制限 baseline 探索を追加し、`imi01/1606324760.num` で単純IDDFS（深さ7）を実測。`2,000,004` ノード時点でも depth=4 探索中で打切りとなり、結論を「不明（探索未完了）」へ修正した。
- `S2-REG-09`: baseline の三値判定（`reachable` / `unreachable` / `unknown`）を API テストで固定し、`unknown` と `unreachable` の混同を防止した。
- `DOC-HPSG-EXP-17/DOC-HPSG-EXP-18`: 9.2/9.3 の文言を厳密化し、`found=False` 断定を廃止。状態爆発の客観値として順序爆発下界（`203,212,800`・`323,237,769`）を追記した。
- `S2-HDA-31`: Reachability候補列挙に `nohead` 制約 + 未解釈素性単調減少 + 格助詞局所優先 + 局所 `V-T` 優先を導入し、状態空間を段階的に絞る実装へ更新した。
- `S2-HDA-32/S2-REG-10`: Step2ボタン文言を `候補を提案` に戻しつつ、Webテストモックを `/reachability/jobs` 非同期フローへ更新した。
- `S2-REG-11`: `apps/web` unit（20件）、`apps/api` pytest（86件）、`./scripts/test-all.sh`（domain+api）を実行し、全件通過を確認した。
- `S2-REG-12`: API回帰 `test_derivation_init_from_sentence_then_reachability_reaches_skateboard_sentence` を追加し、文入力経路でもスケートボード文の到達成功を固定した。
- `S2-REG-13`: Playwright実機で Step1 からスケートボード文を形成し、Step2 の `候補を提案` 実行で `到達判定: reachable` 表示になることを確認した。
- `S1-MOR-01`: `domain.numeration.generator` に活用形後処理を追加し、Sudachi自動分割で `いる`（動詞終止形）を検出した場合に時制語彙 `る` を補完するようにした。
- `S1-REG-15`: API回帰 `test_derivation_numeration_tokenize_auto_mode_supplements_tense_for_iru` を追加し、`うさぎがいる -> [うさぎ, が, いる, る]` を固定した。
- `S2-REG-14`: API回帰 `test_derivation_reachability_jobs_reaches_usagi_ga_iru_with_auto_tense_supplement` を追加し、Step2「候補を提案」相当の jobs 経路で `reachable` 到達を固定した。
- `S1-MOR-02`: Sudachi活用形後処理を7時制へ拡張し、`い/かった/た/だ/だった/でした/です` を文脈（形容詞終止・形容詞過去・助動詞連接）に応じて補完・正規化する実装へ更新した。
- `S1-REG-16/S1-REG-17`: API回帰を追加し、`numeration/tokenize` の7系列分割、および `numeration/generate` の `かわいかった/学生だった/学生でした` の時制語彙解決を固定した。
- `S1-REG-18/S2-REG-15`: 7時制の例文表（既存 `.num` 由来の取得可否を `None` で明示）をテストに固定し、自動モード `init/from-sentence` から `reachability=reachable` を確認する統合回帰を追加した。
- `S1-UI-08`: Step1「numerationの語彙情報参照」に行内 `候補(n)` 展開UIを追加し、複数候補があるslotのみ候補一覧を表示できるようにした。
- `S1-UI-09`: 行内候補の `この候補に差し替え` 実行で、`.num`・生成プレビュー・語彙情報参照が即時更新されるよう `composeNumerationFromTokenEdits` 経路を統一した。
- `S1-REG-19`: Web回帰 `allows replacing a multi-candidate lexicon item in Step1 numeration reference` を追加し、`Sem-204 -> Sem-308` の差し替え反映を固定した。
- `S2-UI-03`: Step2「適用対象」行にも `候補(n)` 展開UIを追加し、Step1と同じ見た目で候補詳細を確認できるようにした。
- `S2-UI-04`: Step2行内候補の差し替えを `.num` 再構成 + `init` 再実行に接続し、T0再初期化後に同じStep2画面で継続できるようにした。
- `S2-REG-16`: Web回帰 `allows replacing a multi-candidate lexicon item in Step2 target panel` を追加し、`Sem-204 -> Sem-308` の反映を固定した。
- `LEX-UI-12`: Step1候補展開テストに `sync_features` 表示アサーションを追加し、候補一覧で `+N(right)(nonhead)` を確認できるようにした。
- `LEX-API-01..06`: 新規ルーター `lexicon_ext.py` を追加し、語彙項目CRUD・バリュー辞書CRUD/置換・num紐付け・研究メモ履歴・版情報APIを実装した。
- `LEX-API-01..06`: `main.py` へルーターを追加し、既存 `/v1/lexicon/*` の互換を維持しつつ拡張エンドポイントを公開した。
- `LEX-UI-01..05`: 新規 `LexiconWorkbench` を追加し、3ペイン（一覧/選択式編集/研究支援タブ）で語彙項目編集を完結できるUIへ置換した。
- `LEX-UI-02`: `category/predicates/sync_features/idslot/semantics` を自由入力から選択式へ統一し、値追加/更新/削除は辞書タブに集約した。
- `LEX-UI-03`: 右ペインにバリュー辞書タブを実装し、CRUD・使用件数参照・一括置換を実行可能にした。
- `LEX-UI-04`: 右ペインにnum紐付けタブを実装し、語彙項目ごとに複数 `.num` 参照を追加/更新/削除できるようにした。
- `LEX-UI-05`: 研究メモタブを実装し、本文更新・履歴一覧・履歴表示・復元をAPI連携で実行可能にした。
- `LEX-REG-01`: `test_lexicon_ext.py` を追加し、語彙項目CRUD・辞書/num紐付け/研究メモ・版情報APIの回帰を固定した。
- `LEX-REG-02`: Webテストに `shows Lexicon 3-pane editor and selection-based fields` を追加し、新UI導線を固定した。
- `LEX-REG-03`: Playwright E2Eに `lexicon workbench shows 3-pane editing tabs` を追加し、実ブラウザ導線を固定した。
- `LEX-API-07`: メタDB URL 未設定時に `value-dictionary / num-links / notes / note-revisions` の読取APIを空結果フォールバックに変更し、`Metadata DB URL is missing...` による画面停止を解消した。
- `UI-PERSIST-01`: `localStorage(syncsemphone-next:ui-state:v1)` へ `uiMode/renewPanel/workflowStarted/grammarId/setupGrammarId/step1EntryMode` を保存し、再読込時に復元するようにした（test環境では無効）。
- `LEX-UI-13..17 / LEX-API-08`: 語彙編集ページを上部タブ構成へ再編し、一覧検索Enter・`category:*` フィルタ・列ソート・編集導線・`id_slot` 候補制限（実使用値＋CSV実在値）を実装した。
- `LEX-RPT-01`: `id_slot` の実測一覧（CSV実在値）と役割説明（コード根拠）を監査レポートへ出力し、`0,23` 非実在/非参照を明示した。
- `S2-HDA-33 / S2-REG-17`: Step2 `候補を提案` の reachability job 起動パラメータに探索予算（`budget_seconds=30`, `max_nodes=2_000_000`, `max_depth=28`）を明示し、Web回帰で固定した。
- `S2-REG-18`: API回帰 `test_derivation_init_from_sentence_marks_john_ga_wo_yonda_as_unreachable` を追加し、`ジョンがを読んだ` が高予算でも `unreachable` になることを固定した。
- `LEX-UI-18`: 語彙項目一覧の `編集` ボタンを選択行右端セルへ移動し、一覧上部の操作密度を下げた。
- `S2-UI-05`: Step2 の `やり直し` を単一ボタンへ統合し、`候補を提案` 左に固定配置した。
- `LEX-API-09`: メタDB未設定時の `value-dictionary` をLexicon実データ由来でフォールバック返却するよう修正した。
- `LEX-UI-19`: 語彙項目一覧の行内 `編集` ボタン配色を調整し、白地白文字の可読性崩れを解消した。
- `LEX-RPT-02`: `id_slot` 値（`0,24` / `2,22` / `2,24` / `2,27,target`）の実処理参照箇所を監査レポートへ追記した。
- `LEX-UI-20`: バリュー辞書で行選択時に `値` 入力へ自動反映し、既存項目の更新を即時実行できるよう修正した。`metadata(JSON)` 入力は撤去した。
- `LEX-API-10`: `使用語彙を表示` を `lexicon_id / entry` を含む一覧へ変更し、メタDB未設定時フォールバックでも返却するようにした。
- `LEX-UI-21`: 行内 `編集` ボタンを既存緑ボタン系の配色（緑背景/白文字）へ統一した。
- `LEX-UI-22`: バリュー辞書 `新規追加` を「同値なしの場合のみ有効」に変更し、重複作成をUIで防止した。
- `LEX-UI-23`: バリュー辞書 `更新` を「同一IDで値が変化した場合のみ有効」に変更し、未変更更新を無効化した。
- `LEX-UI-26`: 語彙項目編集 `semantics` の候補源を `kind=semantic` 辞書値へ固定し、一覧ページ由来の候補混入を廃止した（編集中値は保持のため併記）。
- `LEX-RPT-03`: `0,24 / 2,22 / 2,24 / 2,27,target` の所在（`lexicon-all.csv` の `id_slot/semfeat/predicate`）を監査レポートへ追記した。
- `LEX-DATA-01`: 指示訂正により `lexicon-all.csv` はバックアップから復元し、`id_slot` の `0,24 / 2,22 / 2,24 / 2,27,target` は削除せず維持する方針へ戻した。
- `S1-MOR-03`: Sudachi自動分割後に `X + する + た => Xした` と `動詞 + て + いる => 〜ている` の再構成を追加し、語彙既知形へ寄せる処理を実装した。
- `S1-REG-20`: API回帰で長文例の自動分割結果（`ふわふわした / ... / る`）を固定した。
- `S1-REG-21`: API回帰で同文の `init/from-sentence` が `Unknown token` で落ちず、語彙ID列を返すことを固定した。

## 追加対応表（2026-02-28）

| ID | 実装内容 | 実装先 | 検証 |
|---|---|---|---|
| LEX-UI-13 | 語彙編集見出しを `語彙の編集` へ変更し、App上部の `Lexicon` ステップタブを非表示化 | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/App.tsx` | `vitest`, Playwright |
| LEX-UI-14 | 語彙編集を上部タブ切替へ変更し、`num紐付け/研究メモ/版管理` を語彙項目編集内へ統合（Markdownプレビュー付き） | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| LEX-UI-15 | 一覧検索を Enter 実行対応し、`category:iA` 絞り込み検索を有効化。一覧下 `新規` ボタンを撤去 | `apps/web/src/LexiconWorkbench.tsx`, `apps/api/app/api/v1/lexicon_ext.py` | `vitest`, `pytest` |
| LEX-UI-16 | 一覧 `id/entry/category` ソート矢印トグルを追加し、行選択後の `編集` ボタンで編集タブへ遷移 | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| LEX-UI-17 | `id_slot` 候補をマージ規則実使用値 + CSV実在値へ制限し、末尾カンマ揺れを正規化（`0,23` は非実在/非参照のため除外） | `apps/web/src/LexiconWorkbench.tsx` | `vitest` |
| LEX-API-08 | `/v1/lexicon/{grammar_id}/items` に `sort/order` と `category:*` フィルタを追加 | `apps/api/app/api/v1/lexicon_ext.py`, `apps/api/tests/test_lexicon_ext.py` | `pytest` |
| LEX-RPT-01 | `id_slot` 実測値と役割を監査レポートに整理し、不要値除外の根拠を明示 | `docs/specs/lexicon-idslot-audit-ja.md` | 文書レビュー |
| LEX-UI-18 | 語彙項目一覧の `編集` ボタンを選択行右端セルへ移動（一覧上部から撤去） | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/styles.css`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| S2-UI-05 | Step2 の `やり直し` を各行から撤去し、`候補を提案` 左の単一ボタンへ統合 | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| LEX-API-09 | メタDB未設定時 `value-dictionary` を Lexicon 実データ由来でフォールバック返却 | `apps/api/app/api/v1/lexicon_ext.py`, `apps/api/tests/test_lexicon_ext.py` | `pytest` |
| LEX-UI-19 | 語彙項目一覧の行内 `編集` ボタンを可読配色へ修正（白地白文字を解消） | `apps/web/src/styles.css` | `vitest`, Playwright |
| LEX-RPT-02 | `id_slot` 各値が実際に参照されるマージ処理をコード根拠付きで追記 | `docs/specs/lexicon-idslot-audit-ja.md` | 文書レビュー |
| LEX-UI-20 | バリュー辞書行選択時に `値` へ自動入力し、既存項目を直接更新可能にする。`metadata(JSON)` 入力は廃止 | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/types.ts` | `vitest`, Playwright |
| LEX-API-10 | `使用語彙を表示` で `lexicon_id/entry` を返し、フォールバックでも利用可能にする | `apps/api/app/api/v1/lexicon_ext.py`, `apps/api/tests/test_lexicon_ext.py` | `pytest` |
| LEX-UI-21 | 行内 `編集` ボタンを緑背景/白文字（既存緑ボタン系）へ統一 | `apps/web/src/styles.css` | `vitest`, Playwright |
| LEX-UI-22 | バリュー辞書 `新規追加` を同値なし時のみ有効化し、重複値追加を抑止 | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-UI-23 | バリュー辞書 `更新` を値変更時のみ有効化（同一値更新を無効化） | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-UI-24 | 語彙編集ページの4ペイン（一覧/編集/辞書/CSV-YAML）をタブ切替固定にし、同時縦表示を回帰テストで防止する | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-UI-25 | `CSV/YAML` の表記をタブ名・見出し・説明文で `CSV/YAML管理` に統一する | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-UI-26 | 語彙項目編集 `semantics` 候補を `kind=semantic` の辞書値のみで提示し、候補の一貫性を確保する | `apps/web/src/LexiconWorkbench.tsx`, `apps/web/src/__tests__/App.test.tsx` | `vitest`, Playwright |
| S1S2-UI-01 | Step1/Step2 の候補UIで `候補(1)` も表示し、ID確認導線を常時維持する（複数候補時のみ表示を廃止） | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1S2-UI-02 | Step1/Step2 の候補一覧から `語彙項目を編集` を押して語彙編集画面へ遷移し、対象IDを自動読込できるようにする | `apps/web/src/App.tsx`, `apps/web/src/LexiconWorkbench.tsx` | `vitest`, Playwright |
| S1S2-REG-01 | Web回帰で Step1/Step2 の単一候補表示と候補ID表示、Step2候補から語彙編集遷移が維持されることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| LEX-RPT-03 | `0,24 / 2,22 / 2,24 / 2,27,target` の所在（`lexicon-all.csv` の列）を明示 | `docs/specs/lexicon-idslot-audit-ja.md` | 文書レビュー |
| LEX-DATA-01 | 指示訂正を受け、`lexicon-all.csv` はバックアップから復元して `id_slot` 値を維持（削除しない） | `/Users/tomonaga/Documents/syncsemphoneIMI/lexicon-all.csv`, `/Users/tomonaga/Documents/syncsemphoneIMI/lexicon-all.csv.bak-20260228-130337` | 件数再確認 |
| S1-MOR-03 | Sudachi自動分割後に `X + する + た` と `動詞 + て + いる` を語彙既知形へ再構成する | `packages/domain/src/domain/numeration/generator.py` | `pytest` |
| S1-REG-20 | 長文例の自動分割が `ふわふわした / ... / る` になることを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-21 | 長文例の `init/from-sentence` が語彙ID列を生成して失敗しないことを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-HDA-33 | Step2 `候補を提案` の reachability job 起動時に探索予算（30秒 / 200万ノード / 深さ28）を明示して `unknown` 回避を図る | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S2-REG-17 | Web回帰で reachability job payload の探索予算値を固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S2-REG-18 | `ジョンがを読んだ` を high budget で評価しても `unreachable` であることをAPI回帰に固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-NUM-13 | Step1 `numerationの語彙情報参照` で、`例文から選ぶ/numファイルを選ぶ` 時は `tokenSlotEdits` 候補IDを合成しないようにし、buildモード候補混入を防止する | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1-REG-22 | Web回帰を追加し、buildモードで `ID 60` を保持した後に `例文から選ぶ` へ切替えても slot1 候補が `ID 8` のみになることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S1-PART-01 | Numeration生成時の候補選択に `25/33` 要求の充足優先ロジックを追加し、相方要求を満たしやすい初期選択へ寄せる | `packages/domain/src/domain/numeration/generator.py` | `pytest` |
| S1-PART-02 | Step1 `numerationの語彙情報参照` に、充足不能な相方要求を赤字で理由表示する警告を追加する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1-PART-03 | Step1 `numerationの語彙情報参照` に、差し替えで条件を満たせる相方要求を橙色注意で表示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1-REG-23 | API回帰で `ジョンが本を読む` の `226` が単体系 `ga/wo` 候補を優先することを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-24 | Web回帰で `25(ga/wo)` 条件不一致時に赤警告が表示されることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S2-RCH-19 | Step2 `候補を提案` の再現確認として、`ジョンがメアリをスケートボードで追いかけた` が UI/API の両方で `reachable` になることを確認する | 調査ログ（Playwright/CLI） | Playwright, API実行 |
| S2-RCH-20 | `ジョンが本を読む` で、現行削減探索と削減なし全探索（候補全展開）の両方を実行し、到達不能が探索打ち切りではないことを確認する | 調査スクリプト（一時実行） | API実行 |
| S2-RCH-21 | `ジョンが本を読む` の最小未解釈残差を抽出し、`候補を提案` が `reachable` にならない直接原因を同定する | 調査ログ（CLI） | API実行 |
| S2-RCH-22 | `japanese2` で `ジョン+が` と `本+を` を先に `J-Merge` した局所先行状態から探索しても `unreachable` であることを確認する | 調査ログ（CLI） | API実行 |
| S2-RCH-23 | 局所先行状態の最小未解釈残差を抽出し、`2,1,Num` と `2,1L,T`（`本=227` では `2,1L,T` のみ）が詰まり点であることを確定する | 調査ログ（CLI） | API実行 |
| S1S2-BUG-03 | Step1候補差し替え後に `Numerationを形成` した際、再Generateで初期候補へ巻き戻さず `tokenSlotEdits` の選択値を保持して初期化する | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1S2-REG-02 | Web回帰で `本(227)` 差し替え後に Step2へ進んでも `227` が保持されることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S2-REG-19 | API回帰で `japanese2 / ジョンが本を読む` は `ジョン+が` と `本+を` の先行 `J-Merge` 後でも `unreachable` のままであることを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-MOR-03 | 自動モード（Sudachi）の時制補完は `いる`（動詞終止形）に限定し、`読む` 等の他動詞終止形へ `る` を自動補完しない | `packages/domain/src/domain/numeration/generator.py` | `pytest` |
| S1-PART-02 | `japanese2` の `本` 候補は既定選択を `227` に固定し、`100` を既定から外す | `packages/domain/src/domain/numeration/generator.py` | `pytest` |
| S1-REG-23 | API回帰で `japanese2 / ジョンが本を読む` の `tokenize=ジョン,が,本,を,読む`（`る` 非補完）と `generate本=227` を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-HDA-34 | Reachability探索の強制枝刈り（case-local優先/vt-local優先）を廃止し、候補を保持したまま優先度順に探索する方式へ変更する | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-HDA-35 | 深さ情報付き再訪制御（remaining-depthベース）を導入し、浅い重複探索を抑止しつつ深い再探索は許可する | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-REG-20 | 既知reachableセット12件を parameterized API回帰に固定し、探索器改修後に全件 `reachable` を継続できることを確認する | `apps/api/tests/test_derivation.py` | `pytest` |
| DOC-RCH-01 | 既知reachableセット（文・語彙ID・numeration1行目）を文書化し、回帰テストIDに対応付ける | `docs/specs/reachability-confirmed-sets-ja.md` | 文書レビュー |
| S2-HDA-36 | `POST /v1/derivation/reachability/jobs/{job_id}/continue` を追加し、`timeout/node_limit` で止まった同一jobを予算拡張して再探索できるようにする | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-HDA-37 | continue 再探索の結果を prior evidences と tree署名で統合し、同一jobで証拠を拡張できるようにする | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-REG-21 | `unknown(node_limit)` で停止したjobを continue して `reachable` へ遷移できることを回帰テストで固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-22 | `completed=true` job への continue 要求を `409` で拒否する回帰テストを追加する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-UI-06 | Step2に `探索を続ける` ボタンを追加し、`completed=false` 時のみ有効化して continue API を呼び出す | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1-COMP-01 | Step1 自動候補選択で Step0文法に互換な語彙候補を優先し、非互換候補は手動差し替え対象として残す | `packages/domain/src/domain/numeration/generator.py` | `packages/domain/tests/test_numeration_generator.py`, `apps/api/tests/test_derivation.py` |
| S1-COMP-02 | 互換判定を語彙素性 + 文法ルールカタログから自動推定する（`1L/2L/3L` と参照ルール名ベース、手動表なし） | `packages/domain/src/domain/numeration/generator.py` | `apps/api/tests/test_derivation.py` |
| S1-COMP-03 | 非互換候補を手動選択したときに Step1 `numerationの語彙情報参照` で赤警告を表示する（warn-only） | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| S1-COMP-04 | Step1 候補一覧に `文法非互換` バッジと理由表示を追加し、候補比較時に互換性を確認できるようにする | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| S1-REG-25 | API回帰で `imi01 / ジョンが本を読む` の候補選択が `19/23` へ寄ることと、`183` 非互換理由を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-26 | Web回帰で非互換候補への手動差し替え後に赤警告が表示されることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S1-REG-27 | API回帰で `imi01 / ジョンが本を読んだ`（自動分割）でも `が=19` が選ばれ、`183` が非互換（`J-Merge` 欠落）であることを固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1S2-UI-03 | Step1/Step2 の候補UIで、候補一覧を閉じた状態でも選択中候補の警告サマリ（文法非互換・相方条件不一致）を行内表示する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1S2-REG-03 | Web回帰で Step1/Step2 の候補パネルを閉じた状態でも警告サマリが表示され、詳細は候補展開で確認できることを固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S1S2-TXT-01 | Step1/Step2 の警告文から「未充足」を廃止し、`2,25,wo を満たす語が見つかりません` 系の表現へ統一する | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1-UI-10 | Step1 `numerationの語彙情報参照` 冒頭の警告一覧を廃止し、各slot行内の警告サマリへ集約する | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S2-UI-07 | Step2で全ルールを常時表示し、left/right で実行可能なルールを上位に並べ替える | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S2-UI-08 | Step2ルール一覧を3行分スクロール表示にし、実行不可ルールの実行ボタンを薄色・無効化する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S2-UI-09 | Step2の実行不可ルールに、適用できない理由（未選択/同一選択/適用不可）を表示する | `apps/web/src/App.tsx` | `vitest`, Playwright |
| S1-AUTO-309-01 | `Lexiconから組み立てる` で `2,33,ga` 要求 > `4,11,ga` 供給のときのみ `309(φ)` を不足分自動追加する（`auto_add_ga_phi=true` 経路） | `packages/domain/src/domain/numeration/generator.py`, `apps/api/app/api/v1/derivation.py` | `pytest` |
| S1-AUTO-309-02 | 自動追加注釈（件数/理由/根拠 `.num`）をAPIレスポンスへ追加し、Step1で表示する | `apps/api/app/api/v1/derivation.py`, `apps/web/src/App.tsx`, `apps/web/src/types.ts` | `pytest`, `vitest` |
| S1-AUTO-309-03 | 注釈リンクから `Numeration編集` へ遷移し、根拠 `.num` を読込表示できる導線を追加する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1-NUM-EDIT-01 | `Numeration編集` 画面を `アップロード + ファイルパス + タブ区切りグリッド + 語彙情報参照` に整理し、不要機能を撤去する | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `vitest`, Playwright |
| S1-REG-28 | API回帰で `auto_add_ga_phi=true` 時に `309` 補完と根拠 `.num` 返却を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-29 | API回帰で `auto_add_ga_phi` 未指定時は補完しない挙動を固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S1-REG-30 | Web回帰で自動補完注釈表示と `Numeration編集` への遷移を固定する | `apps/web/src/__tests__/App.test.tsx` | `vitest` |
| S1-OPS-01 | `309` 非表示報告時の切り分けを「コード差分」より先に「旧プロセス残留」を確認する運用へ固定する | `/Users/tomonaga/.codex/skills/restart-playwright-env/scripts/restart_env.sh` | 運用手順 |
| S1-OPS-02 | `restart-playwright-env --force` 後に `POST /v1/derivation/numeration/generate(auto_add_ga_phi=true)` の直叩きで `309,309` を確認する手順を追加する | `curl`, `jq` | 手動確認 |

## 追加対応表（2026-03-01）

| ID | 実装内容 | 実装先 | 検証 |
|---|---|---|---|
| S2-HDA-38 | Reachability探索に「一意供給ラベル（25/33）の早期消失抑止」制約を追加し、唯一の供給ラベルを消費して要求が残る遷移を除外 | `apps/api/app/api/v1/derivation.py` | `pytest -k reachability_known_reachable_sets` |
| S2-HDA-39 | Reachability探索順に `partner deficit` 指標を導入し、相方要求を満たしやすい遷移を優先 | `apps/api/app/api/v1/derivation.py` | `pytest -k skateboard or known_reachable_sets` |
| S2-HDA-40 | imi系のみ `case-local / vt-local` を絞り込み優先として適用（japanese2系には適用しない） | `apps/api/app/api/v1/derivation.py` | `pytest -k known_reachable_sets` |
| S2-RCH-24 | 長文 `ふわふわした...うさぎがいる` の `reachable` 化を継続調査（現時点では `unknown timeout`） | 調査ログ（API直叩き） | CLI実測 |
| S2-HDA-41 | 遷移列挙で `basenum==1` の単項規則を列挙し、終端単項操作経路を探索対象に含める | `apps/api/app/api/v1/derivation.py` | `pytest -k known_reachable_sets` |
| S2-HDA-42 | imi長文局面（`basenum>=10`）で `33/25` 要求と `11/12` 供給が直接一致する遷移を優先順へ追加 | `apps/api/app/api/v1/derivation.py` | `pytest -k known_reachable_sets or reaches_skateboard_sentence` |
| S2-REG-23 | 回帰セット再実行（`known_reachable_sets` + `skateboard/usagi`）で既知reachableの手戻りなしを確認 | `apps/api/tests/test_derivation.py` | `python3 -m pytest -q ...` |
| S2-RCH-25 | 上記調整後も `ふわふわした...` は `unknown(timeout)` 継続で、探索戦略の追加設計が必要 | 調査ログ（API直叩き） | CLI実測 |
| DOC-BRF-01 | 事前知識ゼロの外部専門家向けに、自然さ優先・段階拡張探索の相談ブリーフを作成する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-02 | 外部相談用ブリーフを自己完結化し、用語集・非目標・再現手順・採択条件を追記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-03 | 外部相談用ブリーフに前提語彙項目（ID/素性）、`imi01` のマージルール詳細、解析フローを追記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-04 | 外部相談用ブリーフに、reachable可否の現状根拠、現行探索器仕様、自然さ評価定義抜粋、深さ12停滞ログを追記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-05 | 外部相談用ブリーフを機構重視で全面改稿し、4分類明示、探索器パイプライン、RH/LH擬似コード、刈り込み安全性分類、数値整合、未確定事項を統合する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-06 | 深さ12の解釈を補正し、imi01での導出長上限（basenum-1）と `max_depth_reached=12` の意味を「終端深さ到達済み」として明記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-07 | 探索制御語（`unresolved`, `delta_unresolved`, `state_signature`, `partner_deficit`, `case-local`, `vt-local`, `max_frontier`）を入力/出力/用途/安全性つきで定義表化する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-08 | RH/LH補助関数（`_process_pr/_process_sl/_process_se/_process_sy/_apply_kind_feature_101_on_nonhead/_append_merge_relation_semantic`）の契約と不変量を本文へ追補する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-09 | 3.5の数値ラベルを段階整合に合わせて修正し、`134`（列挙段階）と `max_frontier=79`（枝刈り後段階）の違いを明記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-10 | self-loop判定の説明を整理し、判定本体は structural 固定、packed/structural差は再訪抑制キーにのみ効くことを明記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-11 | `zero_delta_streak` の題材依存の実効性（imi01 double-onlyでの効きの弱さ）を注記する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-12 | `partner_deficit` の式と `case-local/vt-local` の参照領域（base配列隣接）を定義表で明文化する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| DOC-BRF-13 | 4.5擬似コードの変数宣言を補い、`append_merge_relation_semantic` の before-state 参照を明示する | `docs/specs/fuwafuwa-natural-reachability-consulting-brief-ja.md` | 文書レビュー |
| S2-PROF-01 | Reachabilityレスポンス `metrics` に `timing_ms` を追加し、時間消費の内訳（enumerate/sort/unresolved/partner/sibling_dedup）を可視化する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-PROF-02 | `metrics.layer_stats` を追加し、`basenum` 層ごとの候補数・刈り込み数・圧縮数を記録する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-PROF-03 | `metrics.leaf_stats` を追加し、`basenum=1` 終端の `unresolved` 分布（min/max/histogram）を返す | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-HDA-43 | 同一親から生成される兄弟遷移を `next structural signature` で1件へ圧縮する（安全寄りdedup） | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-HDA-44 | 再訪抑制を streak 支配（小さい `zero_delta_streak` が大きい streak を支配）へ強化する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-REG-24 | `apps/api/tests/test_derivation.py` 全件通過を再確認する | `apps/api/tests/test_derivation.py` | `python3 -m pytest tests/test_derivation.py -q` |
| S2-RCH-26 | 長文 `imi01`（ふわふわ…）の `structural/packed` A/B を同条件で取得し、到達状況とleaf分布を比較する | 調査ログ（API直叩き） | CLI実測 |
| S2-HDA-45 | Reachability候補列挙を `enumerate_action_descriptors`（cheap情報）と `materialize_action_descriptor`（実行後情報）に分離する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-PROF-04 | `timing_ms` を `pairs_scan/rule_expand/cheap_feature_extract/execute_double_merge/next_signature/post_filter/descriptor_sort` へ細分化する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| DOC-RCH-02 | 分離後のA/B計測値を `reachability-ab-profile-20260301.md` に記録更新する | `docs/specs/reachability-ab-profile-20260301.md` | 文書レビュー |
| S2-HDA-46 | `iter_action_descriptors` を導入し、pair schedule 順に descriptor を逐次生成する（descriptor全件生成を廃止） | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-HDA-47 | sibling dedup を `execute -> signature -> dedup -> unresolved/partner` に前倒しし、代表 child のみ exact 計算する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-HDA-48 | lazy path の dominance 署名を structural 固定にする（packed は比較メトリクス用途） | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-PROF-05 | `metrics.leaf_stats.best_samples` を追加し、best leaf の残差サマリ（deficit_33/25 等）を返す | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-REG-25 | 変更後に `apps/api/tests/test_derivation.py` 全件通過を再確認する | `apps/api/tests/test_derivation.py` | `python3 -m pytest tests/test_derivation.py -q` |
| S2-HDA-49 | `_search_reachability` の DFS ホットパスから `descriptors=list(...)` を除去し、`_iter_action_descriptors` iterator を逐次消費する実装へ置換する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-REG-26 | 上記ストリーム化後に `apps/api/tests/test_derivation.py` 全件通過を再確認する | `apps/api/tests/test_derivation.py` | `python3 -m pytest tests/test_derivation.py -q` |
| S2-MET-01 | `layer_stats` に `descriptors_emitted/descriptors_exhausted/descriptors_partial` を追加し、lazy列挙メトリクスの exact/lower-bound 判定を明示する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-HDA-50 | `_iter_action_descriptors` に IMI double-only fast path（RH/LH直接emit）を追加し、generic rule 展開呼び出しを回避する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-PROF-06 | `timing_ms.rule_expand_fast_path` を追加し、fast path 適用回数を観測可能にする | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-REG-27 | 上記変更後に `apps/api/tests/test_derivation.py` 全件通過を再確認する | `apps/api/tests/test_derivation.py` | `python3 -m pytest tests/test_derivation.py -q` |
| S2-AUD-01 | A/A 意味同値監査（generic/fast action集合一致）を追加し、13/12/11 + short/medium の代表状態で比較する | `apps/api/tests/test_derivation.py` | `pytest -k imi_fast_path_action_set` |
| S2-AUD-02 | Structural 主系列で long imi01 を `fast OFF/ON` 実測し、総量と正規化指標を比較する | `/tmp/reachability_ab_audit_20260301.json` | 実測スクリプト |
| S2-AUD-03 | best-leaf 比較に残差サマリ（33/25 系）を含め、`unresolved_min` 以外の質指標を併記する | `docs/specs/reachability-ab-audit-20260301.md` | 文書レビュー |
| S2-AUD-04 | short/medium reachable sanity を同実測に含め、到達性回帰の有無を確認する | `/tmp/reachability_ab_audit_20260301.json` | 実測スクリプト |
| DOC-RCH-03 | A/A + A/B + best-leaf + sanity の4部構成監査レポートを保存する | `docs/specs/reachability-ab-audit-20260301.md`, `docs/specs/reachability-ab-audit-20260301.json` | 文書レビュー |
| S2-HDA-51 | Reachability の `post_filter` 計算を `_StateSummary` の exact incremental update（`current-left-right+mother`）へ移行し、full recompute 依存を低減する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-BUG-04 | summary キャッシュキーを `id()` 依存から内容キー（state: structural signature / node: JSON signature）へ修正し、ID再利用による誤判定を防止する | `apps/api/app/api/v1/derivation.py` | `pytest` |
| S2-REG-28 | incremental summary と full recompute の一致を differential audit テストで固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-REG-29 | 上記反映後に `apps/api/tests/test_derivation.py` と API 全体テストを再実行し回帰なしを確認する | `apps/api/tests` | `python3 -m pytest -q` |
| S2-PROF-07 | Reachability `metrics` に `cache_stats`（state/node hit/miss, avg key build ms）を追加し、content-key cache のコストを可視化する | `apps/api/app/api/v1/derivation.py` | `pytest`, A/B実測 |
| S2-REG-30 | summary cache key の回帰（same-content一致 / different-content分離）をテストで固定する | `apps/api/tests/test_derivation.py` | `pytest` |
| S2-AUD-05 | `6cdb979` 基準で long structural A/B（fast OFF/ON）を再計測し、correctness fix 後の新ベースラインを取得する | `docs/specs/reachability-ab-audit-20260301-postfix.json` | 実測スクリプト |
| DOC-RCH-04 | 再ベースライン監査の報告書（postfix版）を保存し、旧 quality 結論の再評価前提を明記する | `docs/specs/reachability-ab-audit-20260301-postfix.md` | 文書レビュー |
| S2-HDA-52 | Reachability探索に `global_deficit_ordering_enabled` を追加し、`33/25` の不足量（multiplicity）に基づく order-only 優先順位へ切替可能にする | `apps/api/app/api/v1/derivation.py` | `pytest`, fixed-action A/B |
| S2-PROF-08 | `cache_stats` に current/child structural の再訪・重複率指標（`revisit_ratio`, `cross_parent_duplicate_child_ratio`）を追加する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-AUD-06 | fixed-action 予算（`25k/50k/100k`）で ordering `OFF/ON` 比較を行う監査スクリプトを追加し、JSONを出力する | `apps/api/scripts/reachability_fixed_action_audit.py`, `docs/specs/reachability-fixed-action-audit-20260301.json` | CLI実測 |
| S2-REG-31 | `global_deficit_ordering_enabled` 切替で descriptor `action_key` 集合が一致する回帰テストを追加する | `apps/api/tests/test_derivation.py` | `pytest` |
| DOC-RCH-05 | fixed-action A/B 結果をMarkdownへ整理し、質が不変（`unresolved_min=9`）であることと次の意思決定条件を明文化する | `docs/specs/reachability-fixed-action-audit-20260301.md` | 文書レビュー |
| S2-HDA-53 | imi01 の child評価段で `min_zero_delta_streak_by_struct_sig` を導入し、dominated child を `partner/unique` 計算前に除外する | `apps/api/app/api/v1/derivation.py` | `pytest`, fixed-action A/B |
| S2-PROF-09 | `cache_stats` に dominance関連指標（`dominated_child_count/ratio`, `dominance_improvement_count`, `post_filter_skipped_by_dominance`, `unique_structural_states_per_100k_actions`）を追加する | `apps/api/app/api/v1/derivation.py` | `pytest`, API実測 |
| S2-AUD-07 | dominance導入後に fixed-action（25k/50k/100k）を再測定し、`revisit/cross-parent duplicate` の改善量を比較する | `docs/specs/reachability-fixed-action-audit-20260301.json` | CLI実測 |
| DOC-RCH-06 | fixed-action 監査レポートを dominance導入後の数値へ更新し、次判断（Pareto先行継続）を追記する | `docs/specs/reachability-fixed-action-audit-20260301.md` | 文書レビュー |
| S2-DIAG-01 | `leaf_stats.best_samples` を `top_k=50` へ拡張し、各サンプルに `residual_family_counts`（`sy:*`,`se:*`）を含める | `apps/api/app/api/v1/derivation.py` | `pytest`, 診断実測 |
| S2-DIAG-02 | `basenum=2/3` の良好状態に対して `best_mid_state_samples`（`min_delta_unresolved`, `materialized_action_count`）を収集する | `apps/api/app/api/v1/derivation.py` | `pytest`, 診断実測 |
| S2-DIAG-03 | residual 診断スクリプトを追加し、`best leaf / best mid-state` の残差族集計と局所死活率をJSON出力する | `apps/api/scripts/reachability_residual_diagnose.py`, `docs/specs/reachability-residual-diagnose-20260301.json` | CLI実測 |
| DOC-RCH-07 | residual 診断結果をMarkdownへ整理し、persistent residual と次の切り分けアクションを記録する | `docs/specs/reachability-residual-diagnose-20260301.md` | 文書レビュー |

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
