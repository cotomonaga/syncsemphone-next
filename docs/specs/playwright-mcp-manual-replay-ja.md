# Playwright MCP 手動リプレイ手順（仮説検証ループ）

## 0. 目的
この手順書は、ブラウザ上の仮説検証ループを Playwright MCP 操作で再現し、次を確認するためのものです。

1. 観察文入力から `Generate .num` と `Init T0` が動く
2. `candidates` -> `execute` -> `tree/tree_cat` -> `lf/sr` の観察が動く
3. `resume` の export/import が動く
4. `T0/T1/T2` と `A/B` の保存・復元が動く

## 1. 前提
1. macOS でローカル実行できること
2. `syncsemphone-next` の依存がインストール済みであること
3. Playwright MCP が有効であること

## 2. サーバ起動
リポジトリルート（`syncsemphone-next`）を前提に、以下を別プロセスで起動します。

```bash
# API
cd apps/api
PYTHONPATH=../../packages/domain/src:../../apps/api \
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
# Web
cd apps/web
npm run dev -- --host 127.0.0.1 --port 5173
```

起動確認:

```bash
curl http://127.0.0.1:8000/v1/healthz
# -> {"status":"ok"}
```

## 3. MCP 操作の基本
1. `browser_navigate` で `http://127.0.0.1:5173` を開く
2. `browser_snapshot` で最新 ref を取得する
3. `browser_click`/`browser_fill_form` で操作する
4. 画面更新のたびに必要なら `browser_snapshot` を取り直す

## 4. 手動リプレイ手順

### 4.1 観察文から初期化
1. `Manual Tokens` に `ジョン が 本 を 読む -ta` を入力
2. `Generate .num` をクリック
3. `Init T0` をクリック

期待:
1. `Numeration Preview` が `(not generated)` から変化する
2. `basenum/newnum` が `-` から数値表示に変化する

### 4.2 派生実行
1. `left=1`, `right=2`（既定）で `Load Candidates`
2. 先頭の `Execute` を実行

期待:
1. `history` に `RH-Merge` または `LH-Merge` が含まれる

### 4.3 観察
1. `tree`
2. `tree_cat`
3. `lf`
4. `sr`

期待:
1. 4領域すべてが空でない

### 4.4 resume
1. `Export resume`
2. `Import resume`

期待:
1. `resume-text` が空でない
2. import 後も `history` が保持される

### 4.5 T0/T1/T2 と A/B
1. `Save T1`, `Save T2`
2. `Save A`, `Save B`, `Load A`
3. `Load T0` -> `tree` 実行
4. `Load T1` -> `tree` 実行

期待:
1. `A history`/`B history` が表示される
2. `Load T0` と `Load T1` で `tree` 出力が変わる

## 5. 実測結果（2026-02-26）
本環境で Playwright MCP による手動リプレイを実行し、以下を確認済みです。

1. 観察文ループ（Generate->Init->execute->tree/tree_cat/lf/sr->resume）: 成功
2. `T0/T1` 切替で `tree` 表示差分が出ること: 成功
3. `A/B` 保存表示が更新されること: 成功

## 6. 失敗時の確認ポイント
1. `Load Candidates` が無効のままなら `Init T0` が未実行
2. `Import resume` が無効のままなら `Export resume` 未実行
3. `tree/tree_cat/lf/sr` が空なら `execute` 実行漏れを確認
4. 404(`favicon.ico`) は本手順の判定対象外
