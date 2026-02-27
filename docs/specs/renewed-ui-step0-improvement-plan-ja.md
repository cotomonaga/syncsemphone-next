# Renewed UI Step0 改善プラン（ID対応）

更新日: 2026-02-26  
対象チェックリスト:
- [renewed-ui-step0-feedback-checklist-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step0-feedback-checklist-ja.md)

## 実装方針
- Step0を仮説検証ループの入口として固定する。
- `Lexicon/Grammar` の共通選択・内容確認・開始を1画面で完結させる。
- 内容確認は「要約+明細」「規則一覧+規則単位比較」で、長大スクロール依存を回避する。

## ID対応表

| ID | 実装内容 | 実装先 | 検証 |
|---|---|---|---|
| RUI-S0-001 | Step0パネルを追加し、仮説検証メニューの先頭に配置 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-002 | Step0初期選択を `imi01` に固定し開始可能にする | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-003 | `3候補+More` の表示制御を実装 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-004 | Lexicon/Grammar の共通単一選択UIを実装（Legacy互換） | `apps/web/src/App.tsx` | UIテスト |
| RUI-S0-005 | `この設定で開始` で Step1へ遷移・文法反映 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-006 | `候補一覧を更新` ボタンを削除し、Step0操作を簡潔化 | `apps/web/src/App.tsx` | UIテスト |
| RUI-S0-007 | `More` をリスト右下のテキストトグルへ変更し、押下時にチェックマーク表示 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-008 | `More` の配置を選択ボックス右下に移動（ペイン右端基準をやめる） | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| RUI-S0-009 | Step0 の `選択中:` 表示を削除 | `apps/web/src/App.tsx` | UIテスト |
| RUI-S0-010 | `この設定で開始` ボタンを強調スタイルへ変更 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| RUI-S0-011 | ステップナビ文言を `Step 0 LexiconとGrammarの選択` に変更 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-012 | ステップナビのStep0表記を `【Step0】` に変更 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-013 | ステップナビのStep0表記を `【Step.0】LexiconとGrammarの選択` に修正 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S0-014 | Step0内容確認ボタン群（Lexicon内容確認 / Grammar内容確認）の左右位置をMore左側で固定し、右方向の余白移動を防ぐ | `apps/web/src/styles.css` | UI目視 |
| RUI-S0-015 | Moreテキスト切替時にも内容確認ボタン群の位置を固定し、同時移動しない構成にする | `apps/web/src/styles.css` | Playwright位置検証 |
| RUI-CV-001 | 各選択欄に `内容確認` ボタンを追加 | `apps/web/src/App.tsx` | UIテスト |
| RUI-CV-002 | Lexicon内容確認（要約+明細）パネルを追加 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-CV-003 | Grammar規則一覧パネルを追加 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-CV-004 | Lexicon確認画面に `lexicon.cgi` 相当導線を追加 | `apps/web/src/App.tsx`, `apps/api/app/api/v1/reference.py` | API/UIテスト |
| RUI-CV-005 | Lexiconタイプ集計チップをクリックしたカテゴリ絞り込みを実装 | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/api/app/api/v1/reference.py` | `apps/web/src/__tests__/App.test.tsx`, `apps/api/tests/test_reference.py` |
| RUI-CV-006 | 絞り込み解除導線（ボタン/トグル解除）を実装 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-CV-007 | Lexicon内容確認の `語彙を更新` ボタンを削除 | `apps/web/src/App.tsx` | UIテスト |
| RUI-CV-008 | `絞り込み解除` をタイプ集計チップと同サイズ化し、同一行右端へ配置 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| RUI-CV-009 | `Lexicon内容確認` / `Grammar内容確認` ボタンをリスト下行に置き、Moreの左側へ配置（左右順序は不変）、控えめな色・フォント・余白へ調整 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| RUI-CMP-001 | 規則単位比較パネル（Perl/Python）を実装 | `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/api/app/api/v1/reference.py` | `apps/web/src/__tests__/App.test.tsx`, `apps/api/tests/test_reference.py` |
| RUI-CMP-002 | 規則一覧から比較画面へ遷移を追加 | `apps/web/src/App.tsx` | UIテスト |
| RUI-CMP-003 | 参照メニュー上部ナビから `移植前後の比較` タブを外し、Grammar内容確認からの遷移に一本化 | `apps/web/src/App.tsx` | UIテスト |
| RUI-GI-001 | 文法規則パネル表示時に規則一覧を自動ロードし、`規則一覧を更新` ボタンを削除 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-GI-002 | `資料を閲覧` ボタンを 6. ペイン右下へ配置 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | UIテスト |
| RUI-REF-001 | 資料参照パネルを「素性資料 / 規則資料」の2系統に整理 | `apps/web/src/App.tsx` | UI目視 |
| RUI-REF-002 | ルール一覧編集（`.pl` 編集）ブロックを削除し、読み取り専用導線に統一 | `apps/web/src/App.tsx` | UIテスト |
| RUI-REF-003 | 資料参照を「タブ + 単一セレクタ + 単一表示領域」に再構成 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-REF-004 | 参照パネル内の個別再読み込みボタンを廃止し、自動ロード前提に統一 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-REF-005 | 素性資料セレクタの選択肢表示をファイル名ではなく資料タイトルに変更 | `apps/api/app/api/v1/reference.py`, `apps/web/src/App.tsx`, `apps/web/src/types.ts` | `apps/api/tests/test_reference.py`, `apps/web/src/__tests__/App.test.tsx` |
| RUI-OPS-001 | `restart-playwright-env` スキル手順を固定起動プロセスに再整理 | `/Users/tomonaga/.codex/skills/restart-playwright-env/SKILL.md` | 手順レビュー |
| RUI-OPS-002 | 起動スクリプトのPID検出を listener 実測ベースに変更 | `/Users/tomonaga/.codex/skills/restart-playwright-env/scripts/restart_env.sh` | スクリプト実行結果 |
| RUI-OPS-003 | API起動Pythonを仮想環境優先 (`apps/api/.venv/bin/python`) に変更 | `/Users/tomonaga/.codex/skills/restart-playwright-env/scripts/restart_env.sh`, `/Users/tomonaga/.codex/skills/restart-playwright-env/SKILL.md` | スクリプト出力 (`API_PYTHON_BIN`) |
| RUI-S1-001 | Step1ナビ表記を `【Step.1】Numerationの形成` に変更 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-002 | Step1の主操作を `Numerationを形成` に一本化 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-003 | Step1入口を3モード（例文 / upload / レキシコン組立）へ再編 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-004 | 5例文選択（`白いギターの箱`含む）を実装 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-005 | upload入口で `.num` テキスト反映を実装 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-006 | Sudachi機能を「レキシコンから組み立て」モード内に整理 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-007 | Step1入口文言を `numファイルを選ぶ` / `Lexiconから組み立てる` に統一 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-008 | upload入口にファイル入力を追加し、選択ファイルをテキスト欄へ反映 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-009 | uploadテキストのタブ区切り `.num` 形式検証と赤字エラー表示を実装 | `apps/web/src/App.tsx`, `apps/web/src/styles.css` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-010 | 形式エラー時の `Numerationを形成` 実行抑止を実装 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-S1-011 | PlaywrightでStep1操作時のコンソールエラーを再現・原因特定 | `apps/web/src/App.tsx` | Playwright手動検証 |
| RUI-S1-012 | uploadモードのファイル選択反映不具合を修正 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx`, Playwright手動検証 |
| RUI-S1-013 | 修正後のコンソールエラー解消をPlaywrightで再検証 | `apps/web/src/App.tsx` | Playwright手動検証 |
| RUI-S1-014 | 明示的な `numファイルをアップロード` トリガーを追加し、`input.click()` で確実にファイル選択を開く | `apps/web/src/App.tsx` | Playwright手動検証 |
| RUI-S1-015 | 実装後にPlaywrightでStep1関連の一般UIを再検証し、`Numerationを形成` までを確認 | `apps/web/src/App.tsx`, `apps/web/src/__tests__/App.test.tsx` | Playwright手動検証 |
| RUI-S1-016 | `.num` ファイル選択→反映の実運用確認は Chrome 手動検証に切替える | `apps/web/src/App.tsx`, `docs/specs/playwright-mcp-manual-replay-ja.md` | Chrome手動確認 |
| RUI-HDR-001 | ヘッダー小見出し（eyebrow）を廃止 | `apps/web/src/App.tsx` | UIテスト |
| RUI-HDR-002 | メインタイトルを `SYNCSEMPHONE NEXT` に変更 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-HDR-003 | ヘッダー説明文（Perl導線説明）を廃止 | `apps/web/src/App.tsx` | `apps/web/src/__tests__/App.test.tsx` |
| RUI-UX-001 | 明細表を独立スクロール（max-height）化 | `apps/web/src/styles.css` | UI目視 |
| RUI-UX-002 | Step0説明・状態表示を追加し導線可読性を向上 | `apps/web/src/App.tsx` | UI目視 |
| RUI-API-001 | lexicon summary API追加 | `apps/api/app/api/v1/reference.py` | `apps/api/tests/test_reference.py` |
| RUI-API-002 | lexicon items API追加 | `apps/api/app/api/v1/reference.py` | `apps/api/tests/test_reference.py` |
| RUI-API-003 | merge-rules API追加 | `apps/api/app/api/v1/reference.py` | `apps/api/tests/test_reference.py` |
| RUI-API-004 | rule-compare API追加 | `apps/api/app/api/v1/reference.py` | `apps/api/tests/test_reference.py` |
| RUI-TST-001 | APIテスト拡張（summary/items/merge-rules/compare） | `apps/api/tests/test_reference.py` | `pytest` |
| RUI-TST-002 | UIテストをStep0仕様へ更新 | `apps/web/src/__tests__/App.test.tsx` | `vitest` |

## 完了条件
1. Step0で初期選択と開始導線が成立する。  
2. Lexicon/Grammar内容確認が各ボタンから遷移する。  
3. 規則単位のPerl/Python比較が表示される。  
4. API/WEBテストが通る。  
5. チェックリストIDがすべて `完了` である。
