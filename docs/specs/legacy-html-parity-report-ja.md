# Legacy HTML 同一性確認レポート

更新日: 2026-02-26

## 目的
- 切り分けた Legacy 表示が、Perl 正本の HTML 出力と一致しているかを確認する。
- Renewed UI の更新が Legacy 表示へ混入しないことを確認する。

## 検証対象
- `index-IMI.cgi`
- `syncsemphone.cgi`（`grammar=imi03`）
- `syncsem.css`

## 検証方法
1. Perl CGI を直接実行し、`Content-Type` ヘッダ以降の body バイト列を取得。
2. Python API の `/v1/legacy/perl/*` から取得した body と比較。
3. SHA-256 とバイト長で一致を確認。

補足:
- `/v1/legacy/perl/*` の照合では `legacy_root` は API 用パラメータなので、Perl へ転送する query から除外する。

## 結果（SHA-256）
- `index-IMI.cgi`
  - bytes: `2297`
  - direct: `a0f27842c870630dc832f12aa0b370582357541d1fc387537d22b7cc5945c2cf`
  - api:    `a0f27842c870630dc832f12aa0b370582357541d1fc387537d22b7cc5945c2cf`
  - match: `true`

- `syncsemphone.cgi`（`grammar=imi03`）
  - bytes: `2627`
  - direct: `66bf2cd25f97146a61768791d512e9df5af9e6506b613c0f3c0d1b9cf9687021`
  - api:    `66bf2cd25f97146a61768791d512e9df5af9e6506b613c0f3c0d1b9cf9687021`
  - match: `true`

- `syncsem.css`
  - bytes: `3310`
  - direct: `2271df7158a25716e306adc878d12b18b8343ee6b18750eca72c601433f6d623`
  - api:    `2271df7158a25716e306adc878d12b18b8343ee6b18750eca72c601433f6d623`
  - match: `true`

## 実行済みテスト
- `apps/api/tests/test_legacy_perl.py`（3件）
- `apps/web/src/__tests__/App.test.tsx`（Legacy iframe 表示テストを追加）
- `apps/web/e2e/hypothesis-loop.spec.ts`（2件）

## UI実機確認
- Playwright で `Legacy UI` を選択し、iframe 内に Perl 原本画面（`統語意味論デモプログラム（IMI-人文 言語学共同研究用）`）が表示されることを確認。
