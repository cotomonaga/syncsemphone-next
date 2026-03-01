# Reachable確認済みセット（ルールセット / 文章 / Numeration）

最終更新: 2026-02-28

目的:
- 到達判定器改善の回帰基準として、`reachable` を確認済みのセットを固定する。
- APIテスト `test_derivation_reachability_known_reachable_sets` と対応づける。

## 1. imi01

1. 文章: ジョンがメアリをスケートボードで追いかけた
   - Lexicon IDs: `60,19,103,23,61,168,187,203`
   - Numeration 1行目:
     - `ジョンがメアリをスケートボードで追いかけた\t60\t19\t103\t23\t61\t168\t187\t203`

2. 文章: うさぎがいる
   - Lexicon IDs: `270,19,271,204`
   - Numeration 1行目:
     - `うさぎがいる\t270\t19\t271\t204`

3. 文章: うさぎがいる
   - Lexicon IDs: `270,19,271,308`
   - Numeration 1行目:
     - `うさぎがいる\t270\t19\t271\t308`

## 2. imi03

4. 文章: ジョンがメアリを追いかけた
   - Lexicon IDs: `60,19,103,23,187,203`
   - Numeration 1行目:
     - `ジョンがメアリを追いかけた\t60\t19\t103\t23\t187\t203`

## 3. japanese2

5. 文章: メアリはかわいい
   - Lexicon IDs: `103,22,4,114`
   - Numeration 1行目:
     - `メアリはかわいい\t103\t22\t4\t114`

6. 文章: メアリはかわいかった
   - Lexicon IDs: `103,22,4,115`
   - Numeration 1行目:
     - `メアリはかわいかった\t103\t22\t4\t115`

7. 文章: 椅子は木製だ
   - Lexicon IDs: `26,22,105,117`
   - Numeration 1行目:
     - `椅子は木製だ\t26\t22\t105\t117`

8. 文章: 大学生はバイトだった
   - Lexicon IDs: `69,22,87,118`
   - Numeration 1行目:
     - `大学生はバイトだった\t69\t22\t87\t118`

9. 文章: メアリは学生です
   - Lexicon IDs: `103,22,39,123`
   - Numeration 1行目:
     - `メアリは学生です\t103\t22\t39\t123`

10. 文章: メアリは学生でした
    - Lexicon IDs: `103,22,39,121`
    - Numeration 1行目:
      - `メアリは学生でした\t103\t22\t39\t121`

11. 文章: ジョンが本を読むる
    - Lexicon IDs: `60,19,227,23,226,204`
    - Numeration 1行目:
      - `ジョンが本を読むる\t60\t19\t227\t23\t226\t204`

12. 文章: ジョンが本を読むる
    - Lexicon IDs: `60,19,227,23,226,125`
    - Numeration 1行目:
      - `ジョンが本を読むる\t60\t19\t227\t23\t226\t125`

## 4. 関連テスト

- `apps/api/tests/test_derivation.py`
  - `test_derivation_reachability_enumerator_keeps_subj_t_path_for_japanese2_yomu_ru`
  - `test_derivation_reachability_known_reachable_sets`

