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
4. `.num` ファイルアップロードは Playwright MCP のファイルピッカー制約で自動検証しない。Chrome で手動実行する。

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
1. `Sentence` に `ジョン が 本 を 読む -ta` を入力
2. `Numerationを作成` をクリック
3. `文から T0 を初期化（Numeration自動生成）` をクリック

期待:
1. `.num` が生成され `Numeration Preview` が `(未生成)` から変化する
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

## 8. Perl原本 Step2 練習ログ（S2-HDA-01）
`http://127.0.0.1:8000/v1/legacy/perl/syncsemphone.cgi?grammar=3&mode=numeration_select` を Playwright で直接操作し、次を確認した。

1. `04.num`（`[ジョンがメアリを追いかけた]`）選択 -> `numeration` -> `ok` で Step2 へ遷移できる。
2. `left/right` を選んで `rule` を押すと、該当ペアの適用可能規則（例: `RH-Merge`, `LH-Merge`）が列挙される。
3. `Apply` 後に履歴が追記され、未解釈素性（赤字）が残る場合は「grammaticalではありません」が継続表示される。
4. 規則選択によっては未解釈素性が減るが残留し、分岐次第で詰む経路があるため、`left/right` の選び方支援が有効である。

## 9. 成功例/失敗例差分と「スケートボードで」統合手順（S2-ANL-01, S2-ANL-02）
対象:
- 成功例: 「ジョンがメアリを追いかけた」
- 失敗例: 「ジョンがメアリをスケートボードで追いかけた」

差分の要点:
1. 失敗例では語彙 `x5-1 N(スケートボード)` と `x6-1 Z(で)` が追加される。
2. `x6-1` は `+V(left)(nonhead)` を持つため、動詞句に接続して解消する1手が余分に必要になる。
3. つまり、成功例の骨格（主語句・目的語句・述語句の統合）に加えて、「道具句（スケートボードで）」を述語へ統合する手順を明示的に挿入する必要がある。

Perl原本で確認した `grammatical` 到達手順（imi01 / 1606324760.num）:
1. `([x7-1 x8-1] LH-Merge)` で述語幹と時制を統合
2. `([x5-1 x6-1] RH-Merge)` で「スケートボードで」を形成
3. `([x1-1 x2-1] LH-Merge)` で主語句を形成
4. `([x3-1 x4-1] LH-Merge)` で目的語句を形成
5. `([x3-1 x7-1] RH-Merge)` で目的語句を述語に統合（Theme 解決）
6. `([x6-1 x7-1] RH-Merge)` で道具句を述語に統合（Instrument 解決）
7. `([x1-1 x7-1] RH-Merge)` で主語句を述語に統合（Agent 解決）

確認結果:
1. 7手適用後、Perl画面で「解釈不可能素性がなくなったので、この表示は grammatical です。」を確認。
2. 下部 process テキスト先頭行の履歴も同一:
   `([x7-1 x8-1] LH-Merge) ([x5-1 x6-1] RH-Merge) ([x1-1 x2-1] LH-Merge) ([x3-1 x4-1] LH-Merge) ([x3-1 x7-1] RH-Merge) ([x6-1 x7-1] RH-Merge) ([x1-1 x7-1] RH-Merge)`

## 7. 付記: `.num` ファイルアップロードの運用
Playwright MCP は `.num` アップロードを安定的に扱えないため、次の操作は Chrome で手動確認する。

1. Step1 の「numファイルを選ぶ」を選択
2. `numファイルをアップロード` を押して OS の選択ダイアログを開く
3. `.num テキスト入力（アップロード）` に反映される
4. 必要なら `Numerationを作成` を実行する

## 6. 失敗時の確認ポイント
1. `Load Candidates` が無効のままなら `Init T0` が未実行
2. `Import resume` が無効のままなら `Export resume` 未実行
3. `tree/tree_cat/lf/sr` が空なら `execute` 実行漏れを確認
4. 404(`favicon.ico`) は本手順の判定対象外
