# id_slot 監査レポート（LEX-UI-17）

更新日: 2026-02-28  
対象: `lexicon-all.csv`（`imi01/imi02/imi03`）

## 1. 目的
- `id_slot` 候補から不要値を除外できているか確認する。
- CSVに実在する `id_slot` の役割を、現行Python実装に即して説明する。

## 2. 調査方法
- 語彙ロード実装: [legacy_loader.py](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/lexicon/legacy_loader.py)
- 初期状態での `id_slot` 展開: [init_builder.py:91](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/init_builder.py:91)
- 参照コマンド（実行済み）  
`PYTHONPATH=packages/domain/src apps/api/.venv/bin/python ... load_legacy_lexicon(...)`

## 3. 実測結果（CSV実在値）
`imi01/imi02/imi03` で共通:

- `id`
- `zero`
- `rel`
- `0,24`
- `2,22`
- `2,24`
- `2,27,target`

確認結果:
- `0,22` は **CSV実在なし**
- `0,23` は **CSV実在なし**

### 3.1 所在（どこに書かれているか）
- レキシコンCSV本体: [lexicon-all.csv](/Users/tomonaga/Documents/syncsemphoneIMI/lexicon-all.csv)
- 主な出現箇所:
  - `id_slot` 列（14番スロット）に `0,24 / 2,22 / 2,24 / 2,27,target` が実際に書かれている。
  - `semfeat` / `predicate` 側にも `0,24 / 2,22 / 2,24 / 2,27,target` が語彙仕様として出現する行がある。
- `id_slot` 列での現行件数（`lexicon-all.csv`）:
  - `0,24`: 59件
  - `2,22`: 44件
  - `2,24`: 2件
  - `2,27,target`: 2件
- 方針:
  - これらは現行CSVに保存されている語彙仕様値のため、今回削除しない。

## 4. 役割（コード根拠付き）
まず結論として、`id_slot` 値は「表示用ラベル」ではなく、`execute_*` のマージ処理中に `sl`（id-slot）として直接判定される。
特に `0,24 / 2,22 / 2,24 / 2,27,target` は、`RH/LH-Merge` 系の途中で中間値として代入され、次の規則で具体IDへ解決される。

| 値 | どこで使われるか | 実際の振る舞い |
|---|---|---|
| `0,24` | `property-no/property-da` 実行後の母ノード `sl` | `mo_sl = "0,24"` が代入され、次段マージで `24` 系解決分岐の対象になる。 |
| `2,22` | `SE` 処理 (`feature_no == 21`) | `attr:2,22` へ一旦変換し、後続で head/non-head のID解決に進む。 |
| `2,24` | `SE` 処理 (`feature_no == 23`) | `attr:2,24` へ一旦変換し、後続で `24` 系のID置換処理に進む。 |
| `2,27,target` | `init` の `plus=target` 展開 + `PR/SE` 処理 (`feature_no == 27`) | `3,53,target,id` と組みで参照され、一致時に `sy[53]` から取り出したIDへ置換される。 |

- `id`  
  初期化時に語彙項目内の `id` プレースホルダを `xN-M` へ置換して `sl` に入る。  
  その後のマージではこの `xN-M` が「どの語彙由来か」を指す参照IDとして使われる。  
  根拠: [init_builder.py:91](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/init_builder.py:91)

- `zero`  
  「この位置は解釈済み・空扱い」を表す値。  
  マージ後に head/non-head の `sl` を `zero` へ落とす処理があり、候補判定でも `zero` かどうかを直接分岐に使う。  
  根拠: [candidates.py:140](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/candidates.py:140), [execute.py:1165](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1165)

- `rel`  
  関係付与用のフラグ値。  
  `RH-Merge(imi03)` で `sl` が `rel` の要素が関わると、関係付与意味（`α<sub>n</sub>:...`）の追加可否判定が変わる。  
  根拠: [execute.py:572](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:572)

- `0,24`  
  マージ処理（特に `property-no` / `property-da`）で、母ノード `sl` に代入される中間参照値。  
  文字列の2番目要素が数値（`24`）なので、候補側では「未解釈スロット」として判定される。  
  根拠: [execute.py:1164](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1164), [execute.py:1228](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1228)

- `2,22`  
  意味素性処理で feature番号 `21` を解決する際に代入される参照値（`attr:2,22`）。  
  この値は後続処理でさらに具体IDに解決される中間表現として機能する。  
  根拠: [execute.py:370](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:370), [execute.py:372](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:372)

- `2,24`  
  意味素性処理で feature番号 `23` を解決する際に代入される参照値（`attr:2,24`）。  
  `2,22` と同様、最終IDへ進む前段の中間値として使われる。  
  根拠: [execute.py:372](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:372)

- `2,27,target`  
  `target` 参照を伴うラベル値。  
  `imi03` では `plus=target` から `3,53,target,id` を生成し、`rel-Merge` 時に `α<sub>n</sub>:<sl>` を追加する流れで使われる。  
  根拠: [init_builder.py:24](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/init_builder.py:24), [execute.py:1061](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1061)

## 5. 対応結論
- `id_slot` 候補は、実在値と実装参照値に限定する。
- `0,23` は **CSV実在なし + 実装参照なし** のため、候補から除外する。
- `0,22` は従来どおり候補に出さない。
