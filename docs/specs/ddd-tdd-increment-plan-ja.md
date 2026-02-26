# DDD+TDD 追加開発計画（文章入力→.num→仮説検証ループ）

## 0. 実施状況（2026-02-26）
1. [x] Sprint A（Domain）
2. [x] Sprint B（API）
3. [x] Sprint C（UI）
4. [x] Sprint D（Playwright E2E）
5. [x] Sprint E（ローカル起動受け入れ）
6. 注記: Sprint A/B は `tokens` 明示経路を先行実装。Sudachi 自動解析経路は基盤実装済みで運用検証を継続。

## 1. 目的
この計画は、次の追加要件を DDD+TDD で実装するための固定手順を定義する。

1. 文章入力から `.num` を自動生成できること
2. 文章入力から直接 `T0` を開始できること
3. UI で仮説検証ループを回せること
4. ローカル API/WEB 起動とブラウザ実行確認を DoD に含めること
5. Playwright MCP でブラウザ操作を E2E 再現できること

## 2. 範囲
本計画の対象は `syncsemphone-next` の以下。

1. Domain: Numeration 生成の新規ユースケース
2. API: 文章入力系の新規 2 エンドポイント
3. UI: 文章入力、生成結果確認、`T0` 開始、仮説検証ループ実行導線
4. Test: unit/contract/integration/e2e（Playwright）まで

## 3. DDD 設計方針
### 3.1 追加コンテキスト
1. NumerationGenerationContext（新設）
2. 既存 NumerationContext への橋渡し（`.num` 生成結果を `build_initial_derivation_state` へ接続）

### 3.2 主要モデル
1. `SentenceInput`（文、任意トークン列、解析方式）
2. `GeneratedNumeration`（memo、語彙ID列、`.num` テキスト、候補情報）
3. `TokenResolution`（token、採用語彙ID、候補語彙ID群）

### 3.3 境界
1. 形態素解析器（Sudachi）依存はドメインサービスの抽象境界で隔離する
2. API はドメインユースケースのみ呼ぶ
3. UI は API レスポンスを表示するだけにし、語彙解決規則は持たない

## 4. API 追加計画
### 4.1 `POST /v1/derivation/numeration/generate`
入力:
1. `grammar_id`
2. `sentence`
3. `tokens`（任意、手動分かち）
4. `strategy`（例: `sudachi_a` / `sudachi_c` / `manual_tokens`）

出力:
1. `numeration_text`
2. `memo`
3. `lexicon_ids`
4. `token_resolutions`

### 4.2 `POST /v1/derivation/init/from-sentence`
入力:
1. `grammar_id`
2. `sentence`
3. `tokens`（任意）
4. `strategy`

出力:
1. `numeration`（上記生成結果）
2. `state`（`/v1/derivation/init` 相当の `T0`）

## 5. UI 追加計画
1. 文章入力フォーム（文法選択 + 文章入力）
2. 解析方式選択（Sudachi分割モード）
3. 生成プレビュー（トークンごとの候補語彙IDと採用ID）
4. 手動補正 UI（トークン再分割/候補選択）
5. `T0` 開始ボタン（`init/from-sentence` 呼び出し）
6. 既存 Viewer と接続（A/B、`T0/T1/T2`、`resume`、`tree/tree_cat`、`lf/sr`）

## 6. TDD 実行順
### 6.1 Domain（Red→Green→Refactor）
1. 文章正規化とトークン解決の unit test を先に作る
2. 語彙候補選択ルール（曖昧語処理）の unit test を追加
3. `.num` 出力フォーマットの unit test を追加
4. `GeneratedNumeration -> build_initial_derivation_state` 接続 test を追加

### 6.2 API
1. `/numeration/generate` 契約テスト（正常/異常）
2. `/init/from-sentence` 契約テスト（正常/異常）
3. 既存 `/init` との同値テスト（同一語彙列なら同一 `T0`）

### 6.3 UI
1. コンポーネント単体テスト（フォーム、プレビュー、補正）
2. API モック統合テスト（生成→開始）
3. 仮説検証ループの画面遷移テスト

### 6.4 E2E
1. ローカル API/WEB 起動確認テスト
2. ブラウザで仮説検証ループの主経路を Playwright で実行
3. `resume` 再開後に `tree/tree_cat` と `lf/sr` が観察可能であることを確認

## 7. スプリント順序（固定）
1. Sprint A: Domain モデル・サービス・unit test
2. Sprint B: API 2本・契約テスト
3. Sprint C: UI 文章入力フロー・UIテスト
4. Sprint D: 仮説検証ループ UI 統合・Playwright E2E
5. Sprint E: ローカル起動手順固定・受け入れ確認

## 8. 完了条件（この追加分）
1. 文章入力で `.num` 生成と `T0` 開始が可能
2. UI から仮説検証ループを実行可能
3. ローカル API サーバ起動確認済み
4. ローカル WEB サーバ起動確認済み
5. ブラウザ実操作でループ確認済み
6. Playwright MCP E2E が再現可能
