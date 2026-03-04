# imi01 core adoptable evidence fix report（2026-03-04）

## 1. 修正後 code path（正式化）
- [確認済み事実] `raw_goal_found` と `adoptable_goal_found` を分離。
- [確認済み事実] imi01 では `unresolved==0 && basenum>1` で bounded post-goal continuation を実行。
- [確認済み事実] adoptable 判定は `unresolved_recalc==0 && basenum==1 && full_span=true && hard_reject=false`。
- [確認済み事実] strict sentence literal gate は使わず、memoベースの partner 抽出で hard-reject 監査。

## 2. 正式候補 numeration
- [確認済み事実] S3: `[267, 9301, 9402, 270, 9511, 9611, 204]`
- [確認済み事実] S4: `[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]`

## 3. Step.1 auto / explicit 実測
### S3_auto
- [確認済み事実] mode=auto lexicon_ids=[267, 9301, 9402, 270, 9511, 9611, 204]
- [確認済み事実] status=reachable reason=timeout completed=False
- [確認済み事実] evidence_present=True adoptable_evidence_present=True adoptable_evidence_count=1
- [確認済み事実] actions_attempted=82265 max_depth_reached=6 best_leaf_unresolved_min=1
- [確認済み事実] raw_goal_found_count=1 adoptable_goal_found_count=1 post_goal_continuation_actions=5
- [確認済み事実] rank1: adoptable=True full_span=True basenum=1 unresolved_recalc=0 hard_reject=False

### S3_explicit
- [確認済み事実] mode=explicit lexicon_ids=[267, 9301, 9402, 270, 9511, 9611, 204]
- [確認済み事実] status=reachable reason=timeout completed=False
- [確認済み事実] evidence_present=True adoptable_evidence_present=True adoptable_evidence_count=1
- [確認済み事実] actions_attempted=81709 max_depth_reached=6 best_leaf_unresolved_min=1
- [確認済み事実] raw_goal_found_count=1 adoptable_goal_found_count=1 post_goal_continuation_actions=5
- [確認済み事実] rank1: adoptable=True full_span=True basenum=1 unresolved_recalc=0 hard_reject=False

### S4_auto
- [確認済み事実] mode=auto lexicon_ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]
- [確認済み事実] status=reachable reason=timeout completed=False
- [確認済み事実] evidence_present=True adoptable_evidence_present=True adoptable_evidence_count=2
- [確認済み事実] actions_attempted=55046 max_depth_reached=10 best_leaf_unresolved_min=1
- [確認済み事実] raw_goal_found_count=3 adoptable_goal_found_count=2 post_goal_continuation_actions=416
- [確認済み事実] rank1: adoptable=True full_span=True basenum=1 unresolved_recalc=0 hard_reject=False

### S4_explicit
- [確認済み事実] mode=explicit lexicon_ids=[264, 265, 9501, 9401, 267, 9301, 9402, 270, 9511, 9611, 204]
- [確認済み事実] status=reachable reason=timeout completed=False
- [確認済み事実] evidence_present=True adoptable_evidence_present=True adoptable_evidence_count=2
- [確認済み事実] actions_attempted=54868 max_depth_reached=10 best_leaf_unresolved_min=1
- [確認済み事実] raw_goal_found_count=3 adoptable_goal_found_count=2 post_goal_continuation_actions=416
- [確認済み事実] rank1: adoptable=True full_span=True basenum=1 unresolved_recalc=0 hard_reject=False

## 4. evidence（adoptable top）
### S3_auto rank1
- [確認済み事実] tree_signature: `{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[{"category":"V","children":[{"category":"Z","children":[{"category":"N","children":[],"item_id":"x1-1","phono":"ひつじ","se":["ひつじ:T"],"sl":"x1-1","sy":[]},{"category":"Z","children":[],"item_id":"x2-1","phono":"と","se":[],"sl":"zero","sy":[]}],"item_id":"x2-1","phono":"","se":["α<sub>8</sub>:x1-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x3-1","phono":"話している","se":[],"sl":"zero","sy":[]}],"item_id":"x3-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[],"item_id":"x4-1","phono":"うさぎ","se":[],"sl":"zero","sy":[]}],"item_id":"x4-1","phono":"","se":["うさぎ:T"],"sl":"x4-1","sy":[]},{"category":"J","children":[],"item_id":"x5-1","phono":"が","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":["α<sub>9</sub>:x4-1"],"sl":"","sy":[]},{"category":"V","children":[{"category":"V","children":[],"item_id":"x6-1","phono":"い-","se":[],"sl":"zero","sy":[]},{"category":"T","children":[],"item_id":"x7-1","phono":"-ru","se":["Time:imperfect"],"sl":"","sy":[]}],"item_id":"x6-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x6-1","phono":"","se":[],"sl":"","sy":[]}`
- [確認済み事実] history_len=6
- [確認済み事実] process: `imi01
ひつじと話しているうさぎがいる
10
1
([x6-1 x7-1] LH-Merge) ([x1-1 x2-1] RH-Merge) ([x2-1 x3-1] RH-Merge) ([x3-1 x4-1] RH-Merge) ([x4-1 x5-1] RH-Merge) ([x5-1 x6-1] RH-Merge) 
[null,["x6-1","V",[],[],"",[],null,[["x5-1","J",[],[],"",[null,"α<sub>9</sub>:x4-1"],null,[["x4-1","N",[],[],"x4-1",[null,"うさぎ:T"],null,[["x3-1","V",[],[],"",[],null,[["x2-1","Z",[],[],"",[null,"α<sub>8</sub>:x1-1"],null,[["x1-1","N",[],[],"x1-1",[null,"ひつじ:T"],"ひつじ",null],["x2-1","Z","",[""],"zero","zero","と",null]]],["x3-1","V","",[""],"zero","zero","話している",null]]],["x4-1","N","",[""],"zero","zero","うさぎ",null]]],["x5-1","J","",[""],"zero","zero","が",null]]],["x6-1","V","",[""],"zero","zero",null,[["x6-1","V","",[""],"zero","zero","い-",null],["x7-1","T",[],[],null,[null,"Time:imperfect"],"-ru",null]]]]]]`

### S3_explicit rank1
- [確認済み事実] tree_signature: `{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[{"category":"V","children":[{"category":"Z","children":[{"category":"N","children":[],"item_id":"x1-1","phono":"ひつじ","se":["ひつじ:T"],"sl":"x1-1","sy":[]},{"category":"Z","children":[],"item_id":"x2-1","phono":"と","se":[],"sl":"zero","sy":[]}],"item_id":"x2-1","phono":"","se":["α<sub>8</sub>:x1-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x3-1","phono":"話している","se":[],"sl":"zero","sy":[]}],"item_id":"x3-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[],"item_id":"x4-1","phono":"うさぎ","se":[],"sl":"zero","sy":[]}],"item_id":"x4-1","phono":"","se":["うさぎ:T"],"sl":"x4-1","sy":[]},{"category":"J","children":[],"item_id":"x5-1","phono":"が","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":["α<sub>9</sub>:x4-1"],"sl":"","sy":[]},{"category":"V","children":[{"category":"V","children":[],"item_id":"x6-1","phono":"い-","se":[],"sl":"zero","sy":[]},{"category":"T","children":[],"item_id":"x7-1","phono":"-ru","se":["Time:imperfect"],"sl":"","sy":[]}],"item_id":"x6-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x6-1","phono":"","se":[],"sl":"","sy":[]}`
- [確認済み事実] history_len=6
- [確認済み事実] process: `imi01
ひつじと話しているうさぎがいる
10
1
([x6-1 x7-1] LH-Merge) ([x1-1 x2-1] RH-Merge) ([x2-1 x3-1] RH-Merge) ([x3-1 x4-1] RH-Merge) ([x4-1 x5-1] RH-Merge) ([x5-1 x6-1] RH-Merge) 
[null,["x6-1","V",[],[],"",[],null,[["x5-1","J",[],[],"",[null,"α<sub>9</sub>:x4-1"],null,[["x4-1","N",[],[],"x4-1",[null,"うさぎ:T"],null,[["x3-1","V",[],[],"",[],null,[["x2-1","Z",[],[],"",[null,"α<sub>8</sub>:x1-1"],null,[["x1-1","N",[],[],"x1-1",[null,"ひつじ:T"],"ひつじ",null],["x2-1","Z","",[""],"zero","zero","と",null]]],["x3-1","V","",[""],"zero","zero","話している",null]]],["x4-1","N","",[""],"zero","zero","うさぎ",null]]],["x5-1","J","",[""],"zero","zero","が",null]]],["x6-1","V","",[""],"zero","zero",null,[["x6-1","V","",[""],"zero","zero","い-",null],["x7-1","T",[],[],null,[null,"Time:imperfect"],"-ru",null]]]]]]`

### S4_auto rank1
- [確認済み事実] tree_signature: `{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[{"category":"V","children":[{"category":"Z","children":[{"category":"N","children":[{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[],"item_id":"x2-1","phono":"わたあめ","se":["わたあめ:T"],"sl":"x2-1","sy":[]},{"category":"J","children":[],"item_id":"x3-1","phono":"を","se":[],"sl":"zero","sy":[]}],"item_id":"x3-1","phono":"","se":["α<sub>12</sub>:x2-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x4-1","phono":"食べている","se":[],"sl":"zero","sy":[]}],"item_id":"x4-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[{"category":"A","children":[],"item_id":"x1-1","phono":"ふわふわした","se":["ふわふわした:T"],"sl":"x5-1","sy":[]},{"category":"N","children":[],"item_id":"x5-1","phono":"ひつじ","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":["ひつじ:T"],"sl":"x5-1","sy":[]},{"category":"Z","children":[],"item_id":"x6-1","phono":"と","se":[],"sl":"zero","sy":[]}],"item_id":"x6-1","phono":"","se":["α<sub>13</sub>:x5-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x7-1","phono":"話している","se":[],"sl":"zero","sy":[]}],"item_id":"x7-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[],"item_id":"x8-1","phono":"うさぎ","se":[],"sl":"zero","sy":[]}],"item_id":"x8-1","phono":"","se":["うさぎ:T"],"sl":"x8-1","sy":[]},{"category":"J","children":[],"item_id":"x9-1","phono":"が","se":[],"sl":"zero","sy":[]}],"item_id":"x9-1","phono":"","se":["α<sub>14</sub>:x8-1"],"sl":"","sy":[]},{"category":"V","children":[{"category":"V","children":[],"item_id":"x10-1","phono":"い-","se":[],"sl":"zero","sy":[]},{"category":"T","children":[],"item_id":"x11-1","phono":"-ru","se":["Time:imperfect"],"sl":"","sy":[]}],"item_id":"x10-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x10-1","phono":"","se":[],"sl":"","sy":[]}`
- [確認済み事実] history_len=10
- [確認済み事実] process: `imi01
ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
15
1
([x10-1 x11-1] LH-Merge) ([x1-1 x5-1] RH-Merge) ([x2-1 x3-1] RH-Merge) ([x3-1 x4-1] RH-Merge) ([x4-1 x5-1] RH-Merge) ([x5-1 x6-1] RH-Merge) ([x6-1 x7-1] RH-Merge) ([x7-1 x8-1] RH-Merge) ([x8-1 x9-1] RH-Merge) ([x9-1 x10-1] RH-Merge) 
[null,["x10-1","V",[],[],"",[],null,[["x9-1","J",[],[],"",[null,"α<sub>14</sub>:x8-1"],null,[["x8-1","N",[],[],"x8-1",[null,"うさぎ:T"],null,[["x7-1","V",[],[],"",[],null,[["x6-1","Z",[],[],"",[null,"α<sub>13</sub>:x5-1"],null,[["x5-1","N",[],[],"x5-1",[null,"ひつじ:T"],null,[["x4-1","V",[],[],"",[],null,[["x3-1","J",[],[],"",[null,"α<sub>12</sub>:x2-1"],null,[["x2-1","N",[],[],"x2-1",[null,"わたあめ:T"],"わたあめ",null],["x3-1","J","",[""],"zero","zero","を",null]]],["x4-1","V","",[""],"zero","zero","食べている",null]]],["x5-1","N","",[""],"zero","zero",null,[["x1-1","A",[],[],"x5-1",[null,"ふわふわした:T"],"ふわふわした",null],["x5-1","N","",[""],"zero","zero","ひつじ",null]]]]],["x6-1","Z","",[""],"zero","zero","と",null]]],["x7-1","V","",[""],"zero","zero","話している",null]]],["x8-1","N","",[""],"zero","zero","うさぎ",null]]],["x9-1","J","",[""],"zero","zero","が",null]]],["x10-1","V","",[""],"zero","zero",null,[["x10-1","V","",[""],"zero","zero","い-",null],["x11-1","T",[],[],null,[null,"Time:imperfect"],"-ru",null]]]]]]`

### S4_explicit rank1
- [確認済み事実] tree_signature: `{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[{"category":"V","children":[{"category":"Z","children":[{"category":"N","children":[{"category":"V","children":[{"category":"J","children":[{"category":"N","children":[],"item_id":"x2-1","phono":"わたあめ","se":["わたあめ:T"],"sl":"x2-1","sy":[]},{"category":"J","children":[],"item_id":"x3-1","phono":"を","se":[],"sl":"zero","sy":[]}],"item_id":"x3-1","phono":"","se":["α<sub>12</sub>:x2-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x4-1","phono":"食べている","se":[],"sl":"zero","sy":[]}],"item_id":"x4-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[{"category":"A","children":[],"item_id":"x1-1","phono":"ふわふわした","se":["ふわふわした:T"],"sl":"x5-1","sy":[]},{"category":"N","children":[],"item_id":"x5-1","phono":"ひつじ","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x5-1","phono":"","se":["ひつじ:T"],"sl":"x5-1","sy":[]},{"category":"Z","children":[],"item_id":"x6-1","phono":"と","se":[],"sl":"zero","sy":[]}],"item_id":"x6-1","phono":"","se":["α<sub>13</sub>:x5-1"],"sl":"","sy":[]},{"category":"V","children":[],"item_id":"x7-1","phono":"話している","se":[],"sl":"zero","sy":[]}],"item_id":"x7-1","phono":"","se":[],"sl":"","sy":[]},{"category":"N","children":[],"item_id":"x8-1","phono":"うさぎ","se":[],"sl":"zero","sy":[]}],"item_id":"x8-1","phono":"","se":["うさぎ:T"],"sl":"x8-1","sy":[]},{"category":"J","children":[],"item_id":"x9-1","phono":"が","se":[],"sl":"zero","sy":[]}],"item_id":"x9-1","phono":"","se":["α<sub>14</sub>:x8-1"],"sl":"","sy":[]},{"category":"V","children":[{"category":"V","children":[],"item_id":"x10-1","phono":"い-","se":[],"sl":"zero","sy":[]},{"category":"T","children":[],"item_id":"x11-1","phono":"-ru","se":["Time:imperfect"],"sl":"","sy":[]}],"item_id":"x10-1","phono":"","se":[],"sl":"zero","sy":[]}],"item_id":"x10-1","phono":"","se":[],"sl":"","sy":[]}`
- [確認済み事実] history_len=10
- [確認済み事実] process: `imi01
ふわふわしたわたあめを食べているひつじと話しているうさぎがいる
15
1
([x10-1 x11-1] LH-Merge) ([x1-1 x5-1] RH-Merge) ([x2-1 x3-1] RH-Merge) ([x3-1 x4-1] RH-Merge) ([x4-1 x5-1] RH-Merge) ([x5-1 x6-1] RH-Merge) ([x6-1 x7-1] RH-Merge) ([x7-1 x8-1] RH-Merge) ([x8-1 x9-1] RH-Merge) ([x9-1 x10-1] RH-Merge) 
[null,["x10-1","V",[],[],"",[],null,[["x9-1","J",[],[],"",[null,"α<sub>14</sub>:x8-1"],null,[["x8-1","N",[],[],"x8-1",[null,"うさぎ:T"],null,[["x7-1","V",[],[],"",[],null,[["x6-1","Z",[],[],"",[null,"α<sub>13</sub>:x5-1"],null,[["x5-1","N",[],[],"x5-1",[null,"ひつじ:T"],null,[["x4-1","V",[],[],"",[],null,[["x3-1","J",[],[],"",[null,"α<sub>12</sub>:x2-1"],null,[["x2-1","N",[],[],"x2-1",[null,"わたあめ:T"],"わたあめ",null],["x3-1","J","",[""],"zero","zero","を",null]]],["x4-1","V","",[""],"zero","zero","食べている",null]]],["x5-1","N","",[""],"zero","zero",null,[["x1-1","A",[],[],"x5-1",[null,"ふわふわした:T"],"ふわふわした",null],["x5-1","N","",[""],"zero","zero","ひつじ",null]]]]],["x6-1","Z","",[""],"zero","zero","と",null]]],["x7-1","V","",[""],"zero","zero","話している",null]]],["x8-1","N","",[""],"zero","zero","うさぎ",null]]],["x9-1","J","",[""],"zero","zero","が",null]]],["x10-1","V","",[""],"zero","zero",null,[["x10-1","V","",[""],"zero","zero","い-",null],["x11-1","T",[],[],null,[null,"Time:imperfect"],"-ru",null]]]]]]`

## 5. 既知課題
- [確認済み事実] `status=reachable` と `reason=timeout` は同居し得る（有限予算で到達証拠先行）。
- [確認済み事実] 本報告対象（S3/S4）では core API 内で adoptable evidence 回収を確認。
