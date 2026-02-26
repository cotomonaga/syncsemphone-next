# Perl版とPython版の機能差分（実装反映後）

更新日: 2026-02-26

この文書は、Perl版（`syncsemphone.cgi` 系）との機能差分管理用です。
現在は GAP-01〜09 を実装済みで、判定基準は「研究者がUI/APIから実際に使える操作が同等かどうか」です。

## 実装反映ステータス

| ID | Perl版の機能 | Python版の現状 | 判定 |
|---|---|---|---|
| GAP-01 | tree/tree_cat のグラフィカル描画（vis.js） | SVGグラフ表示を実装（tree source CSV + node/edge 描画） | 実装済み |
| GAP-02 | tree画面でCSVを編集し、DOTへ変換して再描画 | CSVエディタ、`変換` ボタン、DOT出力を実装 | 実装済み |
| GAP-03 | `target` 画面で base 全要素を再帰表示し、left/right をラジオで選択 | base再帰表示 + left/rightラジオ選択を実装 | 実装済み |
| GAP-04 | `target` 画面に grammatical/ungrammatical 表示 | `state.base` から status 表示を実装 | 実装済み |
| GAP-05 | 素性説明（`features/*.html`）・規則説明（`MergeRule/*.html`）を iframe で参照 | `/v1/reference/*` + UI iframe を実装 | 実装済み |
| GAP-06 | Numeration入力で `new / upload / set-numeration選択 / arrange / resume` を同一導線で操作 | set/saved一覧読込、upload適用、arrange編集、resume導線を実装 | 実装済み |
| GAP-07 | 30スロットの語彙手動選択（同形語候補のラジオ再選択、`idx` 編集、plus_feature入力） | 候補再選択 + idx/plus編集 + compose API を実装 | 実装済み |
| GAP-08 | Numerationを `folder/numeration/*.num` へ保存（Perlの保存導線） | `/v1/derivation/numeration/save` + UI保存導線を実装 | 実装済み |
| GAP-09 | 文法プロファイル群（`grammar-list.pl` の39定義） | `grammar-list.pl` 動的読込により profile fallback を拡張 | 実装済み |

## 根拠コード

### GAP-01, GAP-02（tree可視化/変換）
- Perl: `vis.min.js` 読み込み、CSV入力、`変換` ボタン、`vis.network.convertDot`、`new vis.Network(...)`  
  `syncsemphone.cgi:966, 1034, 1049, 1095, 1129`
- Python: treeはAPIでCSV文字列を返し、UIは `<pre>` 表示  
  `apps/api/app/api/v1/observation.py:31-40`  
  `apps/web/src/App.tsx:504-507`

### GAP-03, GAP-04（target観察UI）
- Perl: 文法性表示とleft/rightラジオ選択、base再帰表示  
  `syncsemphone.cgi:690-723`
- Python: left/right数値入力 + 履歴表示のみ  
  `apps/web/src/App.tsx:434-453`

### GAP-05（説明リンク/iframe）
- Perl: featureリンク生成  
  `syncsemphone-common.pl:371-373`
- Perl: feature/rule iframe  
  `syncsemphone.cgi:735, 866-889, 904`
- Python: `App.tsx` には iframe/説明リンク導線なし

### GAP-06（numeration選択/arrange導線）
- Perl: `new/upload/set-numeration/arrange/resume`  
  `syncsemphone.cgi:285, 292-294, 302-313, 342-345, 464-529`
- Python: 文章入力 + `Generate .num` / `Init T0`  
  `apps/web/src/App.tsx:342-396`

### GAP-07（語彙候補再選択 + idx/plus_feature）
- Perl: 30スロット入力、語彙候補ラジオ、`idx` 編集、plus_feature拡張点  
  `syncsemphone.cgi:357-460, 408, 422, 437, 490, 509`
- Python: 候補ID一覧は表示するが選択UIなし。自動選択は先頭候補固定  
  `apps/web/src/App.tsx:414-419`  
  `packages/domain/src/domain/numeration/generator.py:149-156`

### GAP-08（.num保存導線）
- Perl: numeration保存（`folder/numeration/*.num`）  
  `syncsemphone.cgi:531-559`
- Python: 生成APIは `numeration_text` を返す（保存しない）  
  `apps/api/app/api/v1/derivation.py:117-151`

### GAP-09（文法プロファイル数）
- Perl: `grammar-list.pl` は39定義  
  `grammar-list.pl:1, 41`
- Python: `_GRAMMAR_MAP` は4定義  
  `packages/domain/src/domain/grammar/profiles.py:18-46`

## 補足

実装は `apps/api` と `apps/web` に反映済みで、`./scripts/test-all.sh` を含む回帰テストを通過しています。
