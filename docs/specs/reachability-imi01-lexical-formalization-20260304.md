# Reachability IMI01 Lexical Formalization 2026-03-04

## Summary
- formal candidate rows: `9301/9401/9402/9501/9511/9611/204` + existing `264/265/267/270`
- goal/evidence path uses raw-goal + adoptable-goal split with imi01 post-goal continuation
- sentence-literal strict branch removed; particle-partner memo map based hard-reject audit retained

## Before Snapshot (from 2026-03-03 audit)
- S4_new_9301_9401_9402_9501_9511_9611: status=reachable reason=timeout leaf_min=1 evidence_count=2 full_span_before=False
- S3_new_9301_9402_9511_9611: status=reachable reason=timeout leaf_min=1 evidence_count=1 full_span_before=False

## After Explicit Runs
### S4_candidate
- ids: [264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None
- actions=56035 depth=10 leaf_min=1 raw_goal=3 adoptable_goal=2
- rank1: full_span=None basenum=None unresolved_recalc=None hard_reject=None adoptable=None

### S3_candidate
- ids: [267, 9301, 9402, 270, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None
- actions=80198 depth=6 leaf_min=1 raw_goal=1 adoptable_goal=1
- rank1: full_span=None basenum=None unresolved_recalc=None hard_reject=None adoptable=None

## Step.1 Auto Runs (imi01, split_mode=C)
### S2
- sentence: わたあめを食べているひつじがいる
- generation_failed=False
- selected_lexicon_ids=[265, 9501, 9401, 267, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None

### T3
- sentence: ふわふわしたわたあめを食べているひつじがいる
- generation_failed=False
- selected_lexicon_ids=[264, 265, 9501, 9401, 267, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None

### T1
- sentence: わたあめを食べているひつじと話しているうさぎがいる
- generation_failed=False
- selected_lexicon_ids=[265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None

### S4
- sentence: ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
- generation_failed=False
- selected_lexicon_ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]
- status/reason/completed: reachable / timeout / False
- evidence_present=True adoptable_evidence_present=None adoptable_evidence_count=None

## Notes
- S4/S3 are reported as reachable under finite budget observation; reason may remain `timeout` while adoptable evidence is present.
- Status is not rewritten: `unknown` is never converted to `unreachable`.
- Deprecated production candidates are not selected by current imi01 auto lexical priority path (`181/189/263/9502` etc).
