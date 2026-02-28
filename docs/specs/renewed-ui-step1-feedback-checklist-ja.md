# Renewed UI Step1 指摘チェックリスト（ID対応）

更新日: 2026-02-26

目的:
- Step1の違和感をIDで固定し、実装プランと1対1対応で管理する。

対応プラン:
- [renewed-ui-step1-improvement-plan-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step1-improvement-plan-ja.md)

## 1. 文法表示・文法編集
- [x] `S1-GRM-01` 文法セレクトの表示重複（例: `imi03(imi03)`）を解消する。
- [x] `S1-GRM-02` 各文法の中身を閲覧・編集できる画面を追加する。

## 2. Step1 の文言・配置
- [x] `S1-LBL-01` `Refresh Grammars` を日本語表記へ変更する。
- [x] `S1-LBL-02` `Refresh Grammars` ボタンの位置ずれを修正する。
- [x] `S1-LBL-03` Step1主要操作の文言を日本語へ統一する。
- [x] `S1-LBL-04` `Generate .num` を日本語ラベルへ変更する。
- [x] `S1-LBL-05` `Init T0` を日本語ラベルへ変更し、`?` で解説を表示する。
- [x] `S1-LBL-06` `Init from .num` を日本語ラベルへ変更し、`?` で解説を表示する。
- [x] `S1-LBL-07` `Load set-numeration` を日本語ラベルへ変更する（Step2へ移動後に適用）。

## 3. 入力モデル（形態素解析前提）
- [x] `S1-INP-01` `Sentence` 初期値から単語区切り（空白）を除去する。
- [x] `S1-INP-02` `Manual Tokens` の別入力を廃止し、観察文（Sentence）を手動分割の入力元とする。
- [x] `S1-INP-03` 単語区切り結果をパステルカラーのタグ表示にする。

## 4. 導線の明確化
- [x] `S1-FLW-01` `Sentence/Token` と無関係な操作をStep1から分離する。
- [x] `S1-FLW-02` Step1内で「何に効く操作か」を明示する説明を追加する。

## 5. 操作反応の可視化
- [x] `S1-GRM-03` `文法定義を閲覧・編集` 押下で、文法編集パネルに確実に遷移し、一覧自動読込と表示更新が起こるようにする。

## 6. 自動読込と文言統一（参照）
- [x] `S1-AUTO-01` `文法一覧を更新` ボタンを押さなくても、初期表示時に文法一覧を自動取得する。
- [x] `S1-AUTO-02` `Load Feature/Rule Docs` 系ボタンを押さなくても、参照パネル表示時に一覧と本文を自動取得する。
- [x] `S1-LBL-08` 参照パネルの英語ボタン名（Feature/Rule Docs系）を日本語に統一する。

## 7. メニュー文言
- [x] `S1-LBL-09` Menu の3項目文言を次に統一する。
  - `仮説検証ステップ`
  - `素性とルールの確認`
  - `語彙の編集`

## 8. UIモード切替
- [x] `S1-UI-01` デフォルト表示を `Renewed UI` に変更する。
- [x] `S1-UI-02` UIモード切替ボタン文言から括弧説明を削除する（`Legacy UI` / `Renewed UI`）。
- [x] `S1-UI-03` UIモード切替ボタンを画面右上端へ移動し、サイズを小さくする。

## 9. 分割UIと操作
- [x] `S1-SPL-01` Step1で `文法 → 観察文 → 分割結果` を縦並びにする。
- [x] `S1-SPL-02` 分割結果ヘッダに `手動 / 自動（Sudachi）` ボタンを並べ、選択中を強調表示する。
- [x] `S1-SPL-03` 手動モードでは観察文の内容をベースにした分割結果表示を行う。
- [x] `S1-SPL-04` 自動モードではSudachi分割モード選択のみを表示する。
- [x] `S1-SPL-05` 自動モードに切り替えた時点で形態素解析を実行し、分割モード切替時もその場で分割結果を更新する。
- [x] `S1-SPL-07` `Lexiconから組み立てる` の `手動` では別入力欄を廃止し、観察文（Sentence）を手動分割の元データとして再利用する。
- [x] `S1-SPL-08` 手動モード初期表示および観察文変更時は分割結果を観察文1塊として表示する。
- [x] `S1-SPL-09` 分割結果をクリックで編集し、Enter/blurで確定するとパステルタグへ戻る。
- [x] `S1-SPL-10` `Lexiconから組み立てる` 画面では分割モード初期値を `自動（Sudachi）` にする。

## 10. Step1 操作ヘルプ
- [x] `S1-HLP-01` Step1操作列の `?` アイコンをボタンの高さ方向中央に揃える。
- [x] `S1-HLP-02` `?` アイコン押下で、その場に説明ポップアップを表示する（hover title依存をやめる）。
- [x] `S1-HLP-03` `.num生成 / 文からT0初期化 / .numからT0初期化` の違いが分かるよう、操作名と補助説明を明確化する。

## 11. 用語説明（T0）
- [x] `S1-TERM-01` Step1 画面上に `T0` の平易な説明を常設表示し、「規則適用前の初期状態」であることを明示する。
- [x] `S1-TERM-02` 用語集の `T0` 定義を、起点・操作対象・派生遷移（T0→T1→T2）が分かる説明へ拡張する。

## 12. 後続対応（登録のみ）
- [x] `S1-SPL-06` Sudachi 分割モード A/B/C で結果が実際に変わることを、実装確認とテストで固定する。  
  参考: [renewed-ui-step1-goal-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step1-goal-ja.md)
- [x] `S1-GOL-01` Step1「入力と初期化」のゴールを明文化し、`.num作成` と `既存ファイル読込` の導線が混在しないUI構成に再整理する。  
  参考: [renewed-ui-step1-goal-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/renewed-ui-step1-goal-ja.md)

## 13. Legacy 分離とPerl同一性
- [x] `LEG-ISO-01` Legacy UI を Renewed UI と完全分離し、Legacy表示は Perl 原本HTMLの埋め込みに切り替える。
- [x] `LEG-HTML-01` Legacy API が返す `index-IMI.cgi` HTMLが、Perl直接実行のHTML bodyと一致することをテストで確認する。
- [x] `LEG-HTML-02` Legacy API が返す `syncsemphone.cgi` HTMLが、Perl直接実行のHTML bodyと一致することをテストで確認する。
- [x] `LEG-HTML-03` Legacy API が返す静的資産（`syncsem.css`）が原本と一致することをテストで確認する。
- [x] `LEG-HTML-04` 同一性確認の手順・ハッシュ・結果をレポート化し、再検証可能な形で保存する。

## 14. ファイル選択の確実性
- [x] `S1-UPL-01` `numファイルをアップロード` を `input` と `label` の連携に切替え、`input.click()` 依存を外してOSファイル選択ダイアログ起動をより確実化する。
- [x] `S1-UPL-02` `.num` ファイルアップロードの再現は Playwright MCP ではなく Chrome 手動で確認する運用とする。

## 15. .num語彙情報参照
- [x] `S1-NUM-01` `.num` テキスト（Step1/Step2）から `語彙ID` と `指標` を抽出し、同一面内で語彙情報表を提示する。
- [x] `S1-NUM-02` 語彙辞書にないIDを「見つかりません」と表示し、未参照時の不整合を把握できるようにする。
- [x] `S1-NUM-03` `.num` テキスト下の語彙情報表で、`slot / 語彙ID / 指標 / plus` を各行に同時表示し、入力と参照結果の対応を視認可能にする。
- [x] `S1-NUM-04` `Lexiconから組み立てる` 画面でも、分割結果に応じた語彙候補（生成されたNumeration）を下部の `numerationの語彙情報参照` に表示する。
- [x] `S1-NUM-05` `numerationの語彙情報参照` の表示内容とデザインを、Perl版のNumeration表示（行レイアウト・強調色・下部`.num`表示）に合わせる。
- [x] `S1-NUM-06` Perl版実ページ（`index-IMI.cgi`→`syncsemphone.cgi`）をPlaywrightで確認し、表示項目の順序（slot / x-lab / cat / sy / se / 下部`.num`）を根拠付きで合わせる。

## 16. 例文選択モード
- [x] `S1-EXM-01` 例文選択モードでは観察文入力欄を表示しない。
- [x] `S1-EXM-02` 例文選択モードで例文を選ぶと `numerationの語彙情報参照` を表示し、選択結果の語彙IDを確認できる。
- [x] `S1-EXM-03` 例文選択モードの選択肢を、固定5文配列ではなく `set-numeration` の実データ（memo）から生成する。
- [x] `S1-EXM-04` 例文選択モードの選択肢表示をレガシーUI準拠にし、項目ラベルを `memo` のみ（`[memo]`）で統一する。
- [x] `S1-EXM-05` Step1で `例文から選ぶ` に入った時、候補が未取得なら `set-numeration` 一覧を自動読込して空欄状態を防ぐ。
- [x] `S1-EXM-06` 例文候補が未取得時はプレースホルダと案内文を表示し、空の`select`だけが見える状態を回避する。

## 17. CORS（ローカル開発）
- [x] `S1-CORS-01` Webが `5173` 以外（例: `5174`）で起動してもAPIがCORS拒否しないよう、localhost/127.0.0.1 の可変ポートを許可する。

## 18. 事故報告
- [x] `S1-INC-01` Step1例文候補消失の発生条件・原因・修正・再発防止を事故報告として文書化する。
  - 参照: [2026-02-26-step1-example-options-incident-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/incidents/2026-02-26-step1-example-options-incident-ja.md)

## 19. Perl表示準拠（Step1 numeration語彙参照）
- [x] `S1-NUM-07` `sy` と `se` の表示を、Perl `show_feature` の実行表示（例: `+N(right)(nonhead)`, `ga(★)`, `★wo`）に合わせる。
- [x] `S1-NUM-08` `idslot=id` を `xN-M` 表示へ解決し、意味素性は `attribute: value` 形式（例: `Name: ジョン`）に統一する。
- [x] `S1-NUM-09` `f1/f4/f5/f6` と `feature/orange` の色・下線・背景マーカーを `syncsem.css` に合わせる（`#009900`, `#aaccdd`, `#eeeeff`, `#EE33CC`, `#ff0000`, `#ffcc99`）。
- [x] `S1-NUM-10` `.num` 表示を Perl 同様に `\t` を明示する文字列表現へ揃える（解析入力は実タブ/`\t` の両方受理）。

## 20. Step2導線（Grammar適用）
- [x] `S2-GRM-01` `Numerationを形成` 実行後に `.num` から `T0` を初期化し、`【Step.2】Grammarの適用` へ自動遷移する。
- [x] `S2-GRM-02` `【Step.2】Grammarの適用` は「解釈不可能性を消す」ことを目的として明示し、手動（left/right + rule 選択）モードを維持する。

## 21. Step2 左右選択アシスト
- [x] `S2-HDA-01` Perl原本のStep2（`syncsemphone.cgi`）で `left/right` 選択→`rule`→`Apply` の反復を実操作し、解釈不可能性が残る/減る分岐を確認して知見化する。
- [x] `S2-HDA-02` `POST /v1/derivation/head-assist` を追加し、全`left/right`組の候補規則を試行して「未解釈素性の減少量」が正の候補のみを順位付きで返す。
- [x] `S2-HDA-03` `【Step.2】Grammarの適用` に `左右候補を提案` UIを追加し、提案行から `left/right` をセットして `Load Candidates` 相当を実行できるようにする（手動モード維持）。
- [x] `S2-HDA-04` API/UIテストを追加し、アシスト候補の順位整列・Step2での反映（`left/right` セット + 候補読込）を回帰テスト化する。

## 22. Step2 操作性改善（語彙参照整合 + 最短手順提案）
- [x] `S2-HDA-05` Step2の対象一覧デザインを `numerationの語彙情報参照` と同系統に揃え、left/right選択も同じ行コンテキスト内で行えるようにする。
- [x] `S2-HDA-06` `Load Candidates` ボタンを廃止し、left/right 両選択時に候補規則を自動読込する。
- [x] `S2-HDA-07` 文言を更新する（`左右候補を提案`→`候補を提案`、`Execute`→`実行`）。
- [x] `S2-HDA-08` `head-assist` を「削減量最大」優先から「grammatical到達までの最短手順」優先へ更新し、上位5件のみ返す。
- [x] `S2-HDA-09` 提案候補を順に実行したとき、例文で grammatical 到達できることをAPI回帰テストで固定する。

## 23. Step2 出力互換（Perl target相当）
- [x] `S2-OUT-01` Perl `syncsemphone.cgi` の `target` 出力部（`folder/memo/newnum/basenum/history/json`）を根拠に、同等の process 出力APIを追加する。
- [x] `S2-OUT-02` `【Step.2】Grammarの適用` に process 出力テキスト欄を追加し、規則適用後の状態をPerl互換フォーマットで確認できるようにする。
- [x] `S2-OUT-03` IMI01 の具体例（白いギターの箱）で3手適用後の process 出力をAPIテストで固定する。
- [x] `S2-OUT-04` Perl `plus_to_numeration` 挙動差分を修正し、`imi01/imi02` で空plusが `sy` に不要追加されないようにする。
- [x] `S1-NUM-11` `numerationの語彙情報参照` の素性表示色（赤/橙/背景色）について、既存クラス定義（`perl-f*`,`numeration-feature-*`）の変更有無を確認する。

## 24. 追加整合（Perl表示・process細部）
- [x] `S2-OUT-05` `process` 出力で `pr` が空文字の節点は `[]` へ変換せず `\"\"` を維持し、Perl `target` 出力の配列形に合わせる。
- [x] `S2-OUT-06` `process` 出力の `sy` 空要素を節点ごとに正規化し、`[] / [\"\"] / [null,\"\"]` の出し分けをPerl実行例（IMI01 3手）と一致させる。
- [x] `S2-UI-01` Step2表示用の `sy/se` で `null` プレースホルダを文字列表示しないように整形し、Perl同様に空要素は非表示扱いにする。
- [x] `S1-NUM-12` `show_feature` 相当の表示で `34/26/27/70/71` 系の記号（★/● + 下付き・注記）をPerl寄りに描画する。

## 25. Step2 操作導線の再配置
- [x] `S2-LYT-01` 適用対象パネルの直下に `適用可能ルール` テーブルを固定表示し、実行導線を最短化する。
- [x] `S2-UNDO-01` `実行` の横に `やりなおし` を配置し、直前の実行を取り消せるようにする。
- [x] `S2-LYT-02` `候補を提案` ボタンを実行導線の下へ移動し、候補一覧も提案ボタンの下へ配置する。
- [x] `S2-HDA-10` 提案候補の操作文言を `この候補を実行` に変更し、選択のみで止めず直接実行する。
- [x] `S2-VIS-01` `適用対象` と `numerationの語彙情報参照` の `sy/sl/se` 描画ロジックを統一し、色・記号（黒丸/赤丸等）の差異を解消する。

## 26. Step2 候補表示・提案の不具合修正
- [x] `S2-RUL-01` `【Step.2】Grammarの適用` で適用対象を手動選択しなくても、初期表示で left/right を自動補完して `適用可能ルール` を表示する。
- [x] `S2-HDA-11` Step2 の候補自動読込を global `loading` から分離し、`候補を提案` ボタン押下時に提案結果が表示されない不具合を解消する。
- [x] `S2-LYT-03` Step2 の適用対象一覧で罫線が途中で切れる/文字が中央揃えでない表示を修正し、行の境界と整列を安定化する。

## 27. Step1 初期分割表示の再修正
- [x] `S1-SPL-11` Step0開始直後に `setAutoPreviewTokens([])` で分割結果が消えたままになる経路を除去し、初期表示の `分割結果` が自動モードで表示されるようにする。
- [x] `S1-SPL-12` 回帰テストを追加し、「Step0開始後にモード切替なしで分割結果が表示される」挙動を固定する。

## 28. Step2 提案停止の再発防止
- [x] `S2-HDA-12` `head-assist` で探索時間の上限（deadline）を導入し、実データ（IMI01）で応答が返らずUIが停止する事象を防止する。
- [x] `S2-HDA-13` Web側 `head-assist` 呼び出しにタイムアウトを導入し、サーバ遅延時でも `候補を提案` 操作が復帰可能な状態を維持する。
- [x] `S2-REG-01` 回帰テストを追加する（API: IMI01初期状態でhead-assistが予算時間内に応答する / UI: 候補自動読込中でも `候補を提案` を押せる）。
- [x] `S2-LYT-04` Step2適用対象一覧の行高さ・中央寄せ・罫線接続を再調整し、表示崩れ（線の途中切れ/文字位置ずれ）を解消する。

## 29. Step2 適用対象ペイン縦線の下端接続
- [x] `S2-LYT-05` left/right 選択セルの縦線が行下端まで届くよう、`step2-selection-row` と `step2-side-select` の縦方向伸長を再調整する。
- [x] `S2-REG-02` Playwrightで `Step0→Step1→Step2` 実操作を再検証し、縦線が途中で終わらないことを確認する。

## 30. Step2 到達手順探索の方式更新
- [x] `S2-HDA-14` `head-assist` の到達手順探索を「候補ごとの独立探索」から「first action を保持した優先度付きグラフ探索（weighted best-first + transposition）」へ置換し、`ジョンがメアリを追いかけた` で到達手順を返せるようにする。
- [x] `S2-HDA-15` 探索アルゴリズム選定の根拠をWeb調査（A*/Dijkstra系の一次資料）で確認し、方式選定に反映する。
- [x] `S2-REG-03` 回帰テストを更新し、`head-assist` 系APIとWeb UIテストを再実行して手戻りを防止する。

## 31. Step2 到達探索の再強化（A*/Dijkstra系）
- [x] `S2-HDA-16` Web調査（Dijkstra/A*/IDA* 一次資料）を根拠に、`head-assist` を「初手ラベル付き multi-source A*/Dijkstra 探索 + transposition（(初手,状態)優越管理）」へ更新し、初手ごとの到達手順欠落を防ぐ。
  - 参照: https://eudml.org/doc/131436 , https://dans.world/repository/hartFormalBasis1968/ , https://www.bibsonomy.org/bibtex/b7a1e82d14f55255be120ae8c25a46a7
- [x] `S2-HDA-17` 例文「ジョンがメアリを追いかけた」を `init/from-sentence` で生成したNumerationに対して、提案追従で grammatical に到達できることをAPI回帰テスト化する。
- [x] `S2-REG-04` 探索更新後に API/Web の全件テストを再実行し、手戻りがないことを確認する。

## 32. Step2 ルール適用後出力のPerl一致
- [x] `S2-OUT-07` ルール適用ごとの形式出力（例: `([x1-1 x2-1] LH-Merge)`）をPython版でもPerl同様に更新し、同一操作で履歴テキストが一致するようにする。
- [x] `S2-VIS-02` Step2の適用対象ペインを、適用後は「合体後ノード（親と子の入れ子表示）」へ更新し、適用前の元要素だけが残る表示を廃止する。
- [x] `S2-REG-05` Perl原本の対象例（`x1-1 N ...` + `x2-1 J ...` を `LH-Merge`）で、Python版の表示と形式出力が一致することをテストで固定する。

## 33. Step2 長文到達失敗の原因分析
- [x] `S2-HDA-18` 例文「ジョンがメアリをスケートボードで追いかけた」で `init/from-sentence` から `head-assist` 追従実行を再検証し、`basenum=1` まで進んだ後に未解釈素性2件（`0,17,N,,,right,nonhead`）が残って候補枯渇することを確認する。
- [x] `S2-HDA-19` 探索予算拡張（60秒）・global探索（180秒）・語彙候補差し替え（`で`/`追いかける`/`た`）を実測し、現行アルゴリズム設定では到達可能候補が出ないことを確認する。

## 34. head-assist 並列化（コア指定）
- [x] `S2-HDA-20` head-assist 探索にコア指定付き並列実行を実装し、「未指定は2コア」「指定時はその値（今回4コア）を上限内で反映」する。
- [x] `S2-REG-06` 並列コア方針（default=2, override=4, clamp）をテストで固定し、既存API全件テストを再実行して手戻りがないことを確認する。

## 35. 成功例/失敗例の差分考察 + Perl原本検証
- [x] `S2-ANL-01` 「ジョンがメアリを追いかけた」と「ジョンがメアリをスケートボードで追いかけた」の差分を、残存未解釈素性・規則適用順・語彙選択の観点で考察し、grammatical化の手順案を作成する。
- [x] `S2-ANL-02` Perl原本（`syncsemphone.cgi`）で該当手順を実操作し、「スケートボードで」あり文の grammatical 到達可否を確認して記録する。
  - 記録: [playwright-mcp-manual-replay-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/playwright-mcp-manual-replay-ja.md)

## 36. RH/LHマージ＋素性照合の実装仕様文書化（HPSG/CG対応）
- [x] `DOC-RLH-01` RH/LHマージ＋素性照合の現行Python実装を、コード行参照つきで説明するMarkdown文書を作成する。
- [x] `DOC-RLH-02` HPSG/CG 専門家向けに、共通点と相違点を「理論一般」ではなく「現実装準拠」で明示する。
- [x] `DOC-RLH-03` grammatical判定・候補列挙・実行更新（history/basenum/newnum）の定義を、API/Domainコードと一致する形で固定する。
  - 成果物: [rh-lh-merge-feature-matching-code-aligned-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/rh-lh-merge-feature-matching-code-aligned-ja.md)

## 37. HPSG状態爆発抑制の調査と採用方式選定
- [x] `DOC-HPSG-EXP-01` HPSGの状態爆発抑制手法を一次資料ベースで調査し、LH/RHマージ＋素性照合への適用可能性を整理する。
- [x] `DOC-HPSG-EXP-02` 最有力3手法を比較し、厳密性・効果・実装適合性の観点で1方式へ絞る。
- [x] `DOC-HPSG-EXP-03` 採用方式（Subsumptionパッキング＋選択的アンパック）の実装接続点・テスト方針まで含めてレポート化する。
  - 成果物: [hpsg-state-explosion-application-to-rh-lh-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md)

## 38. HPSG方式の7.5計算量試算（実測）
- [x] `DOC-HPSG-EXP-04` レポート 7.5 に、`raw` と `packed` の実測比較（depth=1/2 全列挙、depth=3 時間上限）を追記する。
- [x] `DOC-HPSG-EXP-05` `Xが状態爆発で求められない場合` の記述形式を明示し、`X不明 / Y既知` の比較結果を文書化する。
  - 成果物: [hpsg-state-explosion-application-to-rh-lh-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md)
- [x] `DOC-HPSG-EXP-06` レポート 7.6 に、`head-assist` 実装反映（`search_signature_mode` 切替と回帰固定項目）を追記する。
  - 成果物: [hpsg-state-explosion-application-to-rh-lh-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/hpsg-state-explosion-application-to-rh-lh-ja.md)

## 39. head-assist への packed 探索実装（7.5の反映）
- [x] `S2-HDA-21` `head-assist` に `search_signature_mode`（`packed`/`structural`）を追加し、比較実験と本番探索の切替を可能にする。
- [x] `S2-HDA-22` 遷移キャッシュと自己遷移判定を `history` 非依存の structural 署名へ置換し、履歴差分による重複探索を抑制する。
- [x] `S2-HDA-23` packed 署名（restrictor核）と Pareto 優越管理を探索トランスポジションへ導入し、状態爆発を抑えつつ到達性を維持する。
- [x] `S2-REG-07` API回帰テストを追加し、`search_signature_mode` 受理/拒否、署名挙動、packed圧縮効果（level2）を固定する。

## 40. 第一層（到達手順探索）方式の再調査
- [x] `DOC-HPSG-EXP-07` 第一層（遷移探索）のみを対象に、状態爆発対策の上位3方式を一次資料で比較する。
- [x] `DOC-HPSG-EXP-08` 適格性を被引用数ベースで明示し、各代表論文の指標を付して方式選定根拠を固定する。
- [x] `DOC-HPSG-EXP-09` 「DPOR-aware IDA*」を採用案として、現行コード接続点まで含めてレポート化する。
  - 成果物: [reachability-first-layer-search-methods-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-first-layer-search-methods-ja.md)

## 41. 第一層レポートの外部レビュー反映
- [x] `DOC-HPSG-EXP-10` 外部エンジニア指摘（独立性依存・dominance危険・IDA*適用条件）をレビューし、論点妥当性を再評価する。
- [x] `DOC-HPSG-EXP-11` 結論の断定（`DPOR-aware IDA*` 単独主軸）を撤回し、判定コア/提案エンジン分離へ改訂する。
- [x] `DOC-HPSG-EXP-12` 判定コアから `dominance` を外し、三値判定（到達あり/未到達証明/不明）方針を明記する。
  - 成果物: [reachability-first-layer-search-methods-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-first-layer-search-methods-ja.md)

## 42. Step1 レイアウト崩れ再発防止（Playwright実測）
- [x] `S1-LYT-06` Playwright実測（1920x1080）で、Renewed UI が横いっぱいに広がらず小さく表示される症状（`.page max-width:1240px`）を再現確認する。
- [x] `S1-LYT-07` Renewed UI の横幅制限を解除し、ビューポート幅に追従するレイアウトへ修正する。
- [x] `S1-REG-13` Playwright E2E（既存全件）にレイアウト健全性アサーションを追加し、各ステップ遷移中も横幅・overflow崩れを検知できるようにする。
- [x] `S1-REG-14` Step1主要UI（観察文/分割結果/Sudachiモード/語彙参照）が可視かつ十分幅で表示されることをE2E回帰テストで固定する。

## 43. 第一層レポートの追加レビュー反映（完全性強化）
- [x] `DOC-HPSG-EXP-13` 未到達判定の前提として、深さ上限の根拠（`basenum` 単調減少時は `B0-1`、非単調遷移混在時は「深さk以内」限定）を明記する。
- [x] `DOC-HPSG-EXP-14` IDDFS + transposition の完全性条件として、深さ情報付きTTと再展開（reopen）必須、深さ情報なし `visited` 禁止を明記する。
- [x] `DOC-HPSG-EXP-15` DPOR独立性の最小安全条件（read/write交差・適用可否干渉・`newnum`含むグローバル書込）と、自動同値検査による保守運用を明記する。
  - 成果物: [reachability-first-layer-search-methods-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-first-layer-search-methods-ja.md)

## 44. 誘導実装の撤去と第一層/第二層の現状明文化
- [x] `S2-HDA-24` `head-assist` から特定例文向け固定手順注入（答え誘導）を削除し、通常探索のみで `reachable_grammatical` を計算する。
- [x] `S2-REG-08` スケートボード文の回帰を「誤って到達可能と判定しない」テストへ更新し、API/Web全件テストを再実行して手戻りがないことを確認する。
- [x] `DOC-HPSG-EXP-16` 「第二層を実装しても未解決、第一層を実装しても未解決」の結果を根拠付きでレポート化する。
  - 成果物: [layer1-layer2-nonconvergence-report-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/layer1-layer2-nonconvergence-report-ja.md)

## 45. 到達失敗の切り分け（7手リプレイ -> 最小完全探索）
- [x] `S2-HDA-25` Perl既知7手をPythonで逐次リプレイし、各手で候補存在・遷移結果・未解釈数を照合する。
- [x] `S2-HDA-26` DPOR/TTを無効化した深さ制限完全探索（baseline）を追加し、深さ7で既知手順の再発見可否を固定する（単純IDDFSで `2,000,004` ノード時点でも depth=4 探索中、再発見不可）。

## 46. 語彙編集ページ再構成（タブ化・検索/ソート・項目統合）
- [x] `LEX-UI-13` 語彙編集ページ見出しを `語彙の編集` に統一し、App上部の `Lexicon` ステップタブ表示を廃止する。
- [x] `LEX-UI-14` 語彙編集ページを上部タブ構成へ変更し、`語彙項目一覧 / 語彙項目編集 / バリュー辞書 / CSV/YAML` を切替表示にする。`num紐付け`・`研究メモ`・`版管理` は語彙項目編集内へ統合する。
- [x] `LEX-UI-15` 語彙項目一覧の検索入力で Enter 実行を有効化し、`category:iA` 形式の絞り込み（entry部分一致併用）を可能にする。一覧下の `新規` ボタンは撤去する。
- [x] `LEX-UI-16` 語彙項目一覧の `id/entry/category` に昇順降順トグル（矢印表示）を追加し、行選択後に `編集` ボタンを表示して語彙項目編集タブへ遷移できるようにする。
- [x] `LEX-UI-17` `id_slot` 候補をマージ規則実使用値（`id/zero/rel/0,23/0,24/2,22/2,24/2,27,target`）とCSV実在値に制限し、末尾カンマの揺れは正規化して不要値を除外する。
- [x] `LEX-API-08` `/v1/lexicon/{grammar_id}/items` に `sort/order` と `q=category:*` 絞り込みを追加し、UIの検索・ソートをAPI契約でサポートする。

## 47. Step2 到達判定の再安定化（unknown回避）
- [x] `S2-HDA-33` `候補を提案` から起動する reachability job の探索予算を UI 側で明示（`budget_seconds=30`, `max_nodes=2_000_000`, `max_depth=28`）し、`ジョンがメアリをスケートボードで追いかけた` が `unknown` に振れにくい設定へ戻す。
- [x] `S2-REG-17` Web回帰テストで reachability job 起動payloadに上記探索予算が含まれることを固定する。
- [x] `S2-REG-18` API回帰テストで `ジョンがを読んだ` が高予算でも `unreachable`（語彙属性/入力条件由来）になることを固定する。

## 46. 到達判定の運用経路回帰（文入力 -> Step2）
- [x] `S2-REG-12` `init/from-sentence`（文入力）で生成した `ジョンがメアリをスケートボードで追いかけた` の state に対し、`/v1/derivation/reachability` が `reachable` を返すことをAPIテストで固定する。
- [x] `S2-REG-13` Playwright実機で `【Step.1】Numerationの形成 -> Numerationを形成 -> 【Step.2】候補を提案` を実行し、到達判定が `reachable` になることを確認する。

## 47. 切り分け判定文言の厳密化（不明/未到達の分離）
- [x] `DOC-HPSG-EXP-17` 9.2 の結果表現を二値 `found=False` から「不明（探索未完了）」へ修正し、未到達と混同しないようにする。
- [x] `DOC-HPSG-EXP-18` 9.3 の判定を「3確定」から「不明（完走前打切り）」へ改め、状態爆発が主因であることを計算量下界（順序爆発試算）付きで明示する。
- [x] `S2-REG-09` `未到達` と `不明(予算切れ)` の返却条件をテストで固定し、判定誤用を防止する。

## 48. head-assist 完全置換（到達正判定 + DAG + 進捗表示）
- [x] `S2-HDA-27` `POST /v1/derivation/head-assist` を提案APIから到達正判定APIへ完全置換する（`reachable/unreachable/unknown/failed` + 証拠返却）。
- [x] `S2-HDA-28` 到達証拠を `rule_sequence + tree_root(JSON) + process_text` で返し、`max_evidences` と `offset/limit` で10件おかわりページングを可能にする。
- [x] `S2-HDA-29` 非同期ジョブAPI（start/status/evidences）を追加し、Web側で API処理中の完了率（progress）を表示する。
- [x] `S2-HDA-30` 件数契約を `count_status/count_unit/count_basis/tree_signature_basis` で固定し、巨大整数は文字列で返す。
- [x] `DOC-HPSG-EXP-19` 設計レポートの用語を「森林」から「DAG（共有DAG）」へ統一し、上界A/Bと進捗率の定義を追記する。

## 49. 単一開発環境（Python 3.9）へ復帰
- [x] `ENV-UNI-01` `apps/api` と `packages/domain` の `requires-python` を `>=3.9` に揃える。
- [x] `ENV-UNI-02` FastAPI/uvicorn/pydantic/pytest/httpx の依存バージョンを 3.9 実動構成へ固定する。
- [x] `ENV-UNI-03` テスト実行スクリプトを単一仮想環境（`apps/api/.venv`）固定に変更し、`python3` 直呼びを排除する。
- [x] `ENV-UNI-04` README のセットアップ手順を単一仮想環境運用に合わせ、`zsh` で壊れないコマンド表記へ修正する。

## 50. Reachability 経路の実装仕上げ（探索削減ルール + UI回帰）
- [x] `S2-HDA-31` Reachability 遷移列挙で探索削減ルールを全適用する（`nohead` 制約、未解釈素性の単調減少、格助詞の直前名詞優先、局所 `V-T` 優先）。
- [x] `S2-HDA-32` API経路を `/v1/derivation/reachability*` に統一したまま、UI文言は `候補を提案` を維持して仮説検証導線を保持する。
- [x] `S2-REG-10` Webユニットテストを非同期ジョブAPI（`/reachability/jobs`）仕様へ更新し、Step2提案UIの回帰を固定する。
- [x] `S2-REG-11` 全件テスト（`apps/web` unit + `apps/api` pytest + `scripts/test-all.sh`）を実行し、回帰なしを確認する。

## 51. Step1 自動モードの活用形後処理（いる + る）
- [x] `S1-MOR-01` Lexiconから組み立てる自動モード（Sudachi）で、`いる`（動詞終止形）を検出したときに時制語彙 `る` を補完し、`うさぎがいる` が `うさぎ / が / いる / る` で扱えるようにする。
- [x] `S1-REG-15` APIテストで `/v1/derivation/numeration/tokenize` が `うさぎがいる -> [うさぎ, が, いる, る]` を返すことを固定する。
- [x] `S2-REG-14` APIテストで `init/from-sentence(うさぎがいる)` -> `reachability/jobs` が `reachable` になることを固定し、Step2の「候補を提案」ボタン相当の経路を回帰化する。

## 52. Step1 自動モードの時制補完拡張（1〜7）
- [x] `S1-MOR-02` Sudachi自動モードで、`い/かった/た/だ/だった/でした/です` の時制語彙を活用形に応じて補完・正規化する。
- [x] `S1-REG-16` APIテストで `numeration/tokenize` が7系列（`い/かった/た/だ/だった/でした/です`）を文ごとに正しく返すことを固定する。
- [x] `S1-REG-17` APIテストで `numeration/generate` が `かわいかった/学生だった/学生でした` を時制語彙ID（`253/258/260`）へ正しく解決することを固定する。

## 53. 7時制の例文回帰（num由来 + 自動モード到達性）
- [x] `S1-REG-18` 7時制（`い/かった/た/だ/だった/です/でした`）について、既存 `.num` 由来で取得可能な例文を探索し、対応表をテスト内に固定する（未存在の時制は `None` 明示）。
- [x] `S2-REG-15` 上記7例文を `init/from-sentence`（自動モード）で分割・初期化し、`reachability` が `reachable` になることを回帰テストで固定する。

## 54. Step1 候補差し替えUI（行内展開）
- [x] `S1-UI-08` Step1「numerationの語彙情報参照」の各行で、複数候補がある場合のみ `候補(n)` を表示し、現行デザインを維持した行内展開UIで候補一覧を確認できるようにする。
- [x] `S1-UI-09` 行内候補から `この候補に差し替え` を実行したとき、`.num` と語彙情報参照を即時更新する（Step1 build_lexicon モード）。
- [x] `S1-REG-19` Webユニットテストで、Step1行内候補UIの表示と差し替え反映（例: `Sem-204 -> Sem-308`）を固定する。

## 55. Step2 候補差し替えUI（適用対象ペイン）
- [x] `S2-UI-03` Step2「適用対象」ペインで、複数候補がある行に `候補(n)` を表示し、行内展開で候補詳細を確認できるようにする。
- [x] `S2-UI-04` Step2行内候補の `この候補に差し替え` 実行で `.num` を再構成し、T0を再初期化してStep2継続できるようにする。
- [x] `S2-REG-16` Webユニットテストで、Step2行内候補差し替え後に適用対象表示が更新されること（例: `Sem-204 -> Sem-308`）を固定する。

## 56. Lexicon全面改訂（選択式編集 + 辞書管理 + 研究支援）
- [x] `LEX-UI-12` Step1/Step2の候補展開で統語素性（`sync_features`）を表示し、`+N(right)(nonhead)` 等を確認できるようにする。
- [x] `LEX-API-01` `/v1/lexicon/{grammar_id}/items` 系の語彙項目CRUD APIを追加する（一覧/取得/作成/更新/削除）。
- [x] `LEX-API-02` `/v1/lexicon/value-dictionary` 系のバリュー辞書CRUD APIを追加する。
- [x] `LEX-API-03` バリュー辞書の使用件数参照と一括置換API、および参照中削除拒否（409）を追加する。
- [x] `LEX-API-04` 語彙項目ごとの num 紐付けAPI（一覧/作成/更新/削除）を追加する。
- [x] `LEX-API-05` 語彙項目ごとの研究メモAPI（現在値/更新/履歴/履歴復元）を追加する。
- [x] `LEX-API-06` Lexicon版情報API（一覧/差分）を追加する。
- [x] `LEX-UI-01` Lexiconページを語彙項目中心の3ペイン構成へ全面改訂する。
- [x] `LEX-UI-02` 構造系プロパティを選択式入力へ統一する（`category/predicates/sync_features/idslot/semantics`）。
- [x] `LEX-UI-03` バリュー辞書管理UI（CRUD + 使用件数 + 一括置換）を実装する。
- [x] `LEX-UI-04` num紐付けUI（語彙項目ごと複数リンク）を実装する。
- [x] `LEX-UI-05` 研究メモUI（改訂履歴・差分・復元）を実装する。
- [x] `LEX-REG-01` 新規Lexicon API群の回帰テストを追加する。
- [x] `LEX-REG-02` Lexicon新UIのWebユニットテストを追加する。
- [x] `LEX-REG-03` Lexicon新UIのE2Eテストを追加する。
- [x] `LEX-API-07` メタDB URL 未設定時、Lexicon読取系API（辞書一覧/num紐付け一覧/メモ取得/履歴一覧）を 500 にせず空結果で返す。
- [x] `UI-PERSIST-01` リロード時にメニュー/ステップが変わらないよう、Renewed UI の表示状態（`uiMode/menu/panel/workflowStarted/grammar`）を保存・復元する。
