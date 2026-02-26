# ドメイン型定義（Phase 1）

この文書は、移植実装で使う Entity / Value Object の基準を定義する。

## 1. Entity

- `DerivationState`
  - 派生時点を表す主Entity。
  - 主な属性: `grammar_id`, `memo`, `newnum`, `basenum`, `history`, `base`
  - Perl互換のため `base[0]` は常に空スロット（`None`）を許容する。

- `RuleCandidate`
  - 候補規則を表すEntity。
  - 主な属性: `rule_number`, `rule_name`, `rule_kind`, `left/right/check`

- `GrammarRule`
  - 文法ファイルから読まれた規則定義を表すEntity。
  - 主な属性: `number`, `name`, `file_name`, `kind`

## 2. Value Object

- `GrammarId`
  - 許可値: `imi01 | imi02 | imi03 | japanese2`
- `RuleKind`
  - 許可値: `double | single`
- `RuleVersion`
  - 許可値: `01 | 03 | 04`
- `TreeMode`
  - 許可値: `tree | tree_cat`
- `BaseSlotName`
  - 許可値: `id | ca | pr | sy | sl | se | ph | wo`
- `DerivationIndex`
  - 1以上の整数インデックス
- `DoubleMergeTarget`
  - `left/right` の組。`left != right` を必須条件とする。
- `SingleMergeTarget`
  - `check` 単独指定
- `RuleRef`
  - `rule_name` または `rule_number` の指定。両方未指定は不可。

## 3. 実装対応

- 実装ファイル:
  - `packages/domain/src/domain/common/domain_types.py`
- 契約テスト:
  - `packages/domain/tests/test_domain_model_types.py`
