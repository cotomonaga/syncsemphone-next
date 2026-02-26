# Golden Cases (tree/resume)

- Fixture file: `tree-resume-v1.json`
- Case count: 30
- Scope:
  - `tree` CSV
  - `tree_cat` CSV
  - `resume_text`
- State set:
  - `imi03`: T0/T1/T2
  - `japanese2`: RH/property-da/P-Merge/zero-Merge/Partitioning/Pickup/Landing

Regeneration:

```bash
PYTHONPATH=packages/domain/src:apps/api \
python3 scripts/generate_golden_tree_resume_cases.py
```
