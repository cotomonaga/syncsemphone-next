# tree/tree_cat と resume の対保存ルール

この文書は、`tree` / `tree_cat` 観察結果と `resume` 保存データの整合ルールを定義する。

## 1. 保存フォーマット（resume_text）

`resume_text` は次の 6 行で構成する。

1. grammar folder（例: `imi03`, `japanese2`）
2. memo
3. newnum
4. basenum
5. history
6. base JSON（1行）

`base JSON` は `state.base` をそのまま `json.dumps(..., ensure_ascii=False)` した文字列とする。

## 2. 対保存ルール（不変条件）

1. `export -> import` 後に `DerivationState` の各項目は一致する。
1. 同じ state から生成する `tree` / `tree_cat` の CSV は、`export -> import` 前後で一致する。
1. `export -> import -> export` は同一 `resume_text` を返す。
1. 上記は `imi03` の T0/T1/T2 だけでなく、`japanese2` の single/double 規則適用後 state でも成立する。

## 3. 回帰テスト対応

このルールは次のテストで継続検証する。

- `packages/domain/tests/test_tree_resume_persistence.py`
- `apps/api/tests/test_observation.py` の resume-import 後観察一致テスト
