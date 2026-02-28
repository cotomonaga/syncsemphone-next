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

## 4. 役割（コード根拠付き）
- `id`  
  語彙項目の `id` プレースホルダを `xN-M` 形式へ置換して初期状態に入れる。  
  根拠: [init_builder.py:91](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/init_builder.py:91)

- `zero`  
  空/解消済みスロットとして扱う基準値。候補判定や派生で頻出。  
  根拠: [candidates.py:140](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/candidates.py:140), [execute.py:1165](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1165)

- `rel`  
  関係付与（`rel-Merge` 系）で追加意味素性を許可する判定に使う。  
  根拠: [execute.py:572](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:572)

- `0,24`  
  一部マージ後の母ノード `sl` に設定される中間スロット値。  
  根拠: [execute.py:1164](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1164), [execute.py:1228](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1228)

- `2,22` / `2,24`  
  意味素性処理で `uninterpretable` 番号を解消する際に代入される参照値。  
  根拠: [execute.py:370](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:370), [execute.py:372](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:372)

- `2,27,target`  
  `target` 系の参照ラベルとして語彙側に現れる値（`rel` 系意味連鎖で利用）。  
  根拠: [init_builder.py:24](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/numeration/init_builder.py:24), [execute.py:1061](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/packages/domain/src/domain/derivation/execute.py:1061)

## 5. 対応結論
- `id_slot` 候補は、実在値と実装参照値に限定する。
- `0,23` は **CSV実在なし + 実装参照なし** のため、候補から除外する。
- `0,22` は従来どおり候補に出さない。
