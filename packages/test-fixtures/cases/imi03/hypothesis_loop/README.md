# Hypothesis Loop Fixtures (imi03)

Current automated coverage:
- HL-IMI03-A-BASE-01:
  - baseline numeration `imi03/set-numeration/04.num`
  - candidate expectation with RH/LH `_03`
- HL-IMI03-B-SWAP-01:
  - same numeration
  - candidate expectation with RH/LH `_04` swap
- HL-IMI03-C-TIMING-01:
  - T0/T1/T2 snapshot progression with `execute`
- HL-IMI03-C-RESUME-01:
  - resume export/import roundtrip for T0/T1/T2
- HL-IMI03-C-TREE-01:
  - T1/T2 state から tree/tree_cat CSV を取得し比較観察
- HL-IMI03-C-TREE-RESUME-01:
  - resume export/import 前後で tree/tree_cat CSV が不変であることを確認
- HL-IMI03-C-LFSR-01:
  - T1 state から LF(list representation) / SR(truth-conditional meaning) を取得
  - `2,33`（case-linked semantics）が `Theme:xN-1` へ解決されることを確認
  - execute 後 state snapshot を Perl 実行結果と比較（LH/RH 代表4ケース）
  - execute の多段探索（depth 2, single含む）でも Perl 差分ゼロを確認
- HL-IMI03-D-T0-ALL-NUM-01:
  - `imi03/set-numeration` の全 `.num` に対して、T0候補の execute 結果を Perl と全件差分比較
- Related differential extension:
  - imi01/imi02 でも execute（T0全ペア）の Perl 差分一致を確認

Mapped tests:
- `packages/domain/tests/test_hypothesis_loop.py`
- `packages/domain/tests/test_execute_and_resume.py`
- `packages/domain/tests/test_observation_tree.py`
- `packages/domain/tests/test_tree_resume_persistence.py`
- `packages/domain/tests/test_differential_tree_perl.py` (Perl differential)
- `packages/domain/tests/test_differential_execute_perl.py` (Perl differential)
  - includes: imi01/imi02 T0全ペア execute differential
  - includes: imi03 multistep execute differential exploration (single含む)
  - includes: imi03 all numeration T0 candidates execute differential
- `packages/domain/tests/test_differential_semantics_perl.py` (Perl differential)
- `packages/domain/tests/test_differential_candidates_perl.py` (Perl differential)
- `apps/api/tests/test_derivation.py::test_derivation_candidates_hypothesis_loop_pairs`
- `apps/api/tests/test_derivation.py::test_derivation_execute_and_resume_roundtrip`
- `apps/api/tests/test_e2e_hypothesis_loop.py::test_api_e2e_hypothesis_loop_imi03_a_b_c`
- `apps/api/tests/test_observation.py`
- `packages/domain/tests/test_semantics.py`
- `apps/api/tests/test_semantics.py`

Planned IDs:
- HL-IMI03-A-BASE-01
- HL-IMI03-B-SWAP-01
- HL-IMI03-C-TIMING-01
- HL-IMI03-C-RESUME-01
- HL-IMI03-C-LFSR-01
- HL-IMI03-C-TREE-RESUME-01
