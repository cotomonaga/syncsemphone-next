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

## 46. Step1 候補混入バグ修正（例文モード）
- [x] `S1-NUM-13` `Lexiconから組み立てる` で生成した `tokenSlotEdits` が `例文から選ぶ` の `numerationの語彙情報参照` に混入しないよう、候補ID合成をモード別に分離する。
- [x] `S1-REG-22` 回帰テストを追加し、`白いギターの箱` の slot1 候補に `ID 60 ジョン` が混入しないこと（`選択中: 8`）を固定する。

## 46. 語彙編集ページ再構成（タブ化・検索/ソート・項目統合）
- [x] `LEX-UI-13` 語彙編集ページ見出しを `語彙の編集` に統一し、App上部の `Lexicon` ステップタブ表示を廃止する。
- [x] `LEX-UI-14` 語彙編集ページを上部タブ構成へ変更し、`語彙項目一覧 / 語彙項目編集 / バリュー辞書 / CSV/YAML` を切替表示にする。`num紐付け`・`研究メモ`・`版管理` は語彙項目編集内へ統合する。
- [x] `LEX-UI-15` 語彙項目一覧の検索入力で Enter 実行を有効化し、`category:iA` 形式の絞り込み（entry部分一致併用）を可能にする。一覧下の `新規` ボタンは撤去する。
- [x] `LEX-UI-16` 語彙項目一覧の `id/entry/category` に昇順降順トグル（矢印表示）を追加し、行選択後に `編集` ボタンを表示して語彙項目編集タブへ遷移できるようにする。
- [x] `LEX-UI-17` `id_slot` 候補をマージ規則実使用値（`id/zero/rel/0,24/2,22/2,24/2,27,target`）とCSV実在値に制限し、末尾カンマの揺れは正規化して不要値を除外する。
- [x] `LEX-API-08` `/v1/lexicon/{grammar_id}/items` に `sort/order` と `q=category:*` 絞り込みを追加し、UIの検索・ソートをAPI契約でサポートする。
- [x] `LEX-RPT-01` `id_slot` の実測一覧（CSV実在値）と役割説明（コード根拠付き）を監査レポートとして出力する。
  - 成果物: [lexicon-idslot-audit-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/lexicon-idslot-audit-ja.md)

## 47. Step2 到達判定の再安定化（unknown回避）
- [x] `S2-HDA-33` `候補を提案` から起動する reachability job の探索予算を UI 側で明示（`budget_seconds=30`, `max_nodes=2_000_000`, `max_depth=28`）し、`ジョンがメアリをスケートボードで追いかけた` が `unknown` に振れにくい設定へ戻す。
- [x] `S2-REG-17` Web回帰テストで reachability job 起動payloadに上記探索予算が含まれることを固定する。
- [x] `S2-REG-18` API回帰テストで `ジョンがを読んだ` が高予算でも `unreachable`（語彙属性/入力条件由来）になることを固定する。

## 58. 次件着手前の優先修正（4件）
- [x] `LEX-UI-18` 語彙項目一覧の `編集` ボタンを一覧上部から撤去し、選択中行の右端セルへ移動する。
- [x] `S2-UI-05` Step2 の `やりなおし` を各候補行から撤去し、`候補を提案` 左に単一配置する。文言は `やり直し` へ統一する。
- [x] `LEX-RPT-01` `id_slot` の実測一覧（CSV）と役割説明（コード根拠）を監査レポートとして明示する。
  - 成果物: [lexicon-idslot-audit-ja.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/lexicon-idslot-audit-ja.md)
- [x] `LEX-API-09` メタDB未設定時でも `value-dictionary` 一覧が空停止しないよう、Lexicon実データ由来のフォールバック辞書を返す。

## 59. 語彙編集フォローアップ（可読性・辞書編集・説明補強）
- [x] `LEX-UI-19` 語彙項目一覧の行内 `編集` ボタンが白地白文字にならないよう、他ボタンと同系統の可読配色へ統一する。
- [x] `LEX-RPT-02` `id_slot` 値（`0,24` / `2,22` / `2,24` / `2,27,target`）が実際にどのマージ処理で読まれるかを、コード参照付きで追記する。
- [x] `LEX-UI-20` バリュー辞書で既存項目選択時に `値` 入力へ自動反映し、そのまま `更新` できるUXへ修正する（`metadata(JSON)` 入力は撤去）。
- [x] `LEX-API-10` `使用語彙を表示` の結果を `lexicon_id / entry` を含む明示的な一覧に変更し、メタDB未設定時のフォールバック経路でも返却する。

## 60. 語彙編集追加調整（配色統一・重複制御・中間値所在）
- [x] `LEX-UI-21` 行内 `編集` ボタンを緑背景・白文字（既存緑ボタン系）へ統一する。
- [x] `LEX-UI-22` バリュー辞書の `新規追加` は同値が既存にある場合は無効化し、同値がない場合のみ有効化する。
- [x] `LEX-UI-23` バリュー辞書の `更新` は「同一IDで値が変化したときのみ」有効化する（未変更値では無効）。
- [x] `LEX-RPT-03` `0,24 / 2,22 / 2,24 / 2,27,target` の所在（`lexicon-all.csv` のどの項目に現れるか）をレポートへ明示する。
- [x] `LEX-DATA-01` 指示訂正により、`lexicon-all.csv` の `id_slot` 値（`0,24 / 2,22 / 2,24 / 2,27,target`）は削除せず維持する（バックアップから復元済み）。

## 61. 語彙編集タブ表示固定 + 文言調整（CSV/YAML管理）
- [x] `LEX-UI-24` 語彙編集ページで `語彙項目一覧 / 語彙項目編集 / バリュー辞書 / CSV/YAML管理` をタブ切替表示に固定し、同時縦表示を回帰テストで禁止する。
- [x] `LEX-UI-25` タブ名および見出しの `CSV/YAML` 表記を `CSV/YAML管理` に統一する。

## 63. semantics候補源の辞書固定
- [x] `LEX-UI-26` 語彙項目編集 `semantics` は `kind=semantic` の辞書値を候補源として表示し、語彙一覧ページ由来の候補混入を廃止する（編集中の既存値は保持のため併記）。
- [x] `LEX-REG-04` Webテストで `kind=semantic` 辞書取得が実行されることを固定し、候補源の退行を防止する。

## 64. Step1/Step2 候補ID常時表示 + 語彙編集遷移
- [x] `S1S2-UI-01` Step1「numerationの語彙情報参照」とStep2「適用対象」の候補UIで、候補1件でも `候補(1)` と選択中IDを表示する。
- [x] `S1S2-UI-02` Step1/Step2 の候補一覧各行に `語彙項目を編集` ボタンを追加し、語彙編集画面へ遷移して対象IDを自動読込する。
- [x] `S1S2-REG-01` Web回帰で、Step1/Step2とも単一候補の候補パネル表示・ID表示・Step2候補から語彙編集遷移（ID読込）を固定する。

## 65. Step1 パートナー要求充足（候補自動選択 + 警告）
- [x] `S1-PART-01` `Lexiconから組み立てる` の候補初期選択で、`25/33` 要求を満たす相方がある組み合わせを優先する（なるべく満たす）。
- [x] `S1-PART-02` Step1 `numerationの語彙情報参照` に、相方不在で充足不能な要求を赤字警告（理由つき）で表示する。
- [x] `S1-PART-03` 現在の選択では条件を満たす語がないが、候補差し替えで満たせる要求を橙色注意で表示する。
- [x] `S1-REG-23` API回帰で、`ジョンが本を読む` の `226(読む)` に対して単体系 `ga/wo` 候補が優先選択されることを固定する。
- [x] `S1-REG-24` Web回帰で、`25(ga/wo)` が満たせない構成時に赤警告が表示されることを固定する。

## 66. fixed-action A/B（global deficit ordering + 再訪計測）
- [x] `S2-HDA-52` Reachability探索に `global_deficit_ordering_enabled` を追加し、`33/25` の不足量（multiplicity）を使った order-only 優先順位を導入する（候補集合は不変）。
- [x] `S2-PROF-08` `cache_stats` に `all_current_state_visits / unique_current_struct_states / revisit_ratio / unique_child_struct_states / cross_parent_duplicate_child_ratio` を追加し、再訪率と cross-parent 重複率を直接観測できるようにする。
- [x] `S2-AUD-06` fixed-action 予算（`25k/50k/100k`）で ordering `OFF/ON` を比較する監査スクリプトを追加し、JSONレポートを生成する。
- [x] `S2-REG-31` `global_deficit_ordering_enabled` の有無で `action_key` 集合が一致することをテストで固定する。
- [x] `DOC-RCH-05` fixed-action A/B の結果（速度・質・再訪率）をMarkdownレポートに整理し、次判断（ordering継続かPareto先行か）の根拠を文書化する。
  - 成果物: [reachability-fixed-action-audit-20260301.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-fixed-action-audit-20260301.md)

## 67. imi01 min-streak dominance（安全側圧縮）
- [x] `S2-HDA-53` imi01 で `min_zero_delta_streak_by_struct_sig` を child評価段へ導入し、dominated child を `partner/unique` 判定前に除外する。
- [x] `S2-PROF-09` `cache_stats` に `dominated_child_count / dominated_child_ratio / dominance_improvement_count / post_filter_skipped_by_dominance / unique_structural_states_per_100k_actions` を追加する。
- [x] `S2-AUD-07` fixed-action 予算（`25k/50k/100k`）を再実行し、dominance 導入後の `revisit_ratio` と `cross_parent_duplicate_child_ratio` の変化を記録する。
- [x] `DOC-RCH-06` fixed-action A/B レポートを更新し、dominance導入後の結果と次判断を追記する。
  - 成果物: [reachability-fixed-action-audit-20260301.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-fixed-action-audit-20260301.md)

## 68. residual 診断（persistent residual の証拠化）
- [x] `S2-DIAG-01` `leaf_stats.best_samples` を `top_k=50` まで保持し、`residual_family_counts` を含む診断向けサンプルへ拡張する。
- [x] `S2-DIAG-02` `basenum=2/3` の良好状態サンプル（`best_mid_state_samples`）を追加し、`min_delta_unresolved` と `materialized_action_count` を記録する。
- [x] `S2-DIAG-03` residual 診断スクリプトを追加し、`best leaf`/`best mid-state` の残差族集計と局所死活率（non-improving ratio）をJSON出力する。
- [x] `S2-DIAG-04` residual 診断JSONに `initial_slots` と `residual_family_sources` 集計（best leaf / best mid）を追加し、残差導入元 lexical item を追跡可能にする。
- [x] `DOC-RCH-07` residual 診断結果をMarkdownレポート化し、persistent residual（`se:33/sy:11/sy:17`）と次アクションを明記する。
- [x] `DOC-RCH-08` residual 診断レポートに導入元 source 集計（item/phono/raw）を追記し、grammar/lexicon 側で確認すべき対象を明示する。
  - 成果物: [reachability-residual-diagnose-20260301.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-residual-diagnose-20260301.md)

## 62. 自動分割の語彙既知形再構成（ふわふわした/食べている/話している）
- [x] `S1-MOR-03` Sudachi自動分割後に `X + する + た => Xした` と `動詞 + て + いる => 〜ている` を再構成し、語彙引き当て可能なトークン列へ正規化する。
- [x] `S1-REG-20` `numeration/tokenize` 回帰で `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる` が `ふわふわした / わたあめ / を / 食べている / ひつじ / と / 話している / うさぎ / が / いる / る` に分割されることを固定する。
- [x] `S1-REG-21` `init/from-sentence` 回帰で同文の初期化が `Unknown token` で失敗せず、語彙ID列を生成できることを固定する。

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

## 66. Step2 `候補を提案` が `reachable` にならない原因特定（調査）
- [x] `S2-RCH-19` `ジョンがメアリをスケートボードで追いかけた` は現行UI/APIで `reachable` になることを再確認する（UI実操作・API直叩き）。
- [x] `S2-RCH-20` `ジョンが本を読む` について、削減あり探索（現行）と削減なし全探索（候補全展開）を比較し、探索打ち切り起因ではないことを確認する。
- [x] `S2-RCH-21` `ジョンが本を読む` の最小未解釈残差（`Agent:2,25,ga / 2,3L,V / 2,1,Num / 1,5,J-Merge`）を抽出し、到達不能の直接原因を特定する。
- [x] `S2-RCH-22` `japanese2` で `ジョン+が` と `本+を` を先に `J-Merge` した状態から探索しても `unreachable` であることを確認する（総当たりでなく局所先行での切り分け）。
- [x] `S2-RCH-23` 上記局所先行状態の最小未解釈残差を抽出し、`2,1,Num` と `2,1L,T`（`本=227` では `2,1L,T` のみ）が詰まり点であることを特定する。

## 67. Step1差し替えがStep2で戻る不具合の修正
- [x] `S1S2-BUG-03` Step1 `Lexiconから組み立てる` で候補差し替え後に `Numerationを形成` しても、再Generateで初期候補へ戻さず差し替え値を保持する。
- [x] `S1S2-REG-02` Web回帰で `本(227)` へ差し替え -> `Numerationを形成` -> Step2遷移後も `227` が保持されることを固定する。
- [x] `S2-REG-19` API回帰で `japanese2 / ジョンが本を読む` は `ジョン+が` と `本+を` を先行 `J-Merge` しても `unreachable` のままであることを固定する。

## 68. japanese2 「ジョンが本を読む」の自動Numeration改善
- [x] `S1-MOR-03` 自動モード（Sudachi）の時制補完は `いる`（動詞終止形）に限定し、`読む` など他動詞終止形へ `る` を自動補完しない。
- [x] `S1-PART-02` `japanese2` の `本` 候補は既定選択を `227` に固定し、`100`（`2,1,Num` 要求）を既定から外す。
- [x] `S1-REG-23` API回帰で `japanese2 / ジョンが本を読む` は `tokenize=ジョン,が,本,を,読む`（`る` 非補完）かつ `generate` が `本=227` を既定選択することを固定する。

## 69. Reachable確認セット固定 + 探索器改善回帰
- [x] `S2-HDA-34` Reachability探索の優先順を「強制枝刈り」から「優先度付き探索順」へ変更し、`case-local` / `vt-local` 経路を潰さずに探索できるようにする。
- [x] `S2-HDA-35` Reachability探索に深さ情報付き再訪制御（remaining-depthベース）を追加し、同一状態の浅い再探索を抑制しつつ深い再探索は許可する。
- [x] `S2-REG-20` 既知reachableセット（12件）を parameterized API回帰に固定し、探索器改修後も全件 `reachable` を維持できることを確認する。
- [x] `DOC-RCH-01` 既知reachableセットを `reachability-confirmed-sets-ja.md` に固定し、文・語彙ID列・対応テストIDを明記する。

## 70. timeout / node_limit 後の追加探索（continue）
- [x] `S2-HDA-36` `POST /v1/derivation/reachability/jobs/{job_id}/continue` を追加し、`completed=false` ジョブを同一 `job_id` で予算拡張して再探索できるようにする。
- [x] `S2-HDA-37` continue 実行時は prior evidences を tree署名で統合し、`max_evidences` の拡張分も同一ジョブで取得できるようにする。
- [x] `S2-REG-21` `max_nodes=1` で `unknown(node_limit)` を作ったジョブを continue で `reachable` へ遷移できることをAPI回帰で固定する。
- [x] `S2-REG-22` `completed=true` ジョブへの continue 要求を `409` で拒否する回帰テストを追加する。
- [x] `S2-UI-06` Step2に `探索を続ける` ボタンを追加し、`completed=false` のときのみ有効化して continue API を呼べるようにする。

## 71. Step0連動の語彙互換警告（Step1・赤警告のみ）
- [x] `S1-COMP-01` Step1 `Lexiconから組み立てる` の自動候補選択で、Step0文法に互換な候補がある場合は互換候補のみを初期選択対象にする（候補一覧から非互換候補は除外しない）。
- [x] `S1-COMP-02` 互換判定は語彙項目の素性と文法ルールカタログから自動推定し、手動管理テーブルは導入しない（推定根拠: `1L/2L/3L` と `J-Merge` 等の参照ルール名）。
- [x] `S1-COMP-03` 非互換候補を手動で差し替えた場合は許可しつつ、Step1 `numerationの語彙情報参照` に赤警告を表示する（warn-only）。
- [x] `S1-COMP-04` Step1 候補一覧に非互換候補の視認表示（`文法非互換` バッジ + 理由）を追加し、候補比較時に判断できるようにする。
- [x] `S1-REG-25` API回帰で `imi01 / ジョンが本を読む` の自動候補選択が `が=19 / を=23` を選び、`183` の互換判定が `missing_required_rule(J-Merge)` になることを固定する。
- [x] `S1-REG-26` Web回帰で Step1 で非互換候補へ手動差し替えした際に赤警告が表示されることを固定する。
- [x] `S1-REG-27` API回帰で `imi01 / ジョンが本を読んだ`（自動分割）でも `が=19` が選ばれ、`183` が非互換（`J-Merge` 欠落）であることを固定する。

## 72. 候補パネルを閉じた状態の警告サマリ表示（Step1/Step2）
- [x] `S1S2-UI-03` Step1 `numerationの語彙情報参照` と Step2 `適用対象` の両方で、候補一覧を閉じた状態でも選択中候補の警告サマリ（文法非互換・相方条件不一致）を行内表示する。

## 73. 警告文言の平易化（「未充足」廃止）
- [x] `S1S2-TXT-01` Step1/Step2 の警告文から「未充足」を廃止し、`2,25,wo を満たす語が見つかりません` 系の表現へ統一する。

## 74. Step1冒頭警告の廃止（行内警告へ集約）
- [x] `S1-UI-10` Step1 `numerationの語彙情報参照` 冒頭の警告一覧（文法互換・相方条件）を廃止し、各slot行内の警告サマリ表示に集約する。

## 75. Step2 ルール一覧の常時表示（可否と理由）
- [x] `S2-UI-07` Step2 `Grammarの適用` で、left/right の選択前後を問わず全ルールを一覧表示し、適用可能ルールを上位に並べる。
- [x] `S2-UI-08` Step2 ルール一覧は3行分を目安にスクロール表示とし、適用不可ルールの `実行` ボタンを無効化（薄色）する。
- [x] `S2-UI-09` 適用不可ルールには、`left/right 未選択` / `同一選択` / `このleft/rightでは適用不可` などの理由を表示する。
- [x] `S1S2-REG-03` Web回帰で、Step1/Step2 の候補一覧を開かずに警告サマリが表示されること、および候補一覧を開いたときに詳細理由が引き続き確認できることを固定する。

## 76. Step1 φ(309) 自動補完 + Numeration編集画面改修
- [x] `S1-AUTO-309-01` `Lexiconから組み立てる` の生成経路で、`2,33,ga` 要求数が `4,11,ga` 供給数を超える場合に限り `309(φ)` を不足数ぶん自動追加する（`auto_add_ga_phi=true` 時のみ）。
- [x] `S1-AUTO-309-02` 自動追加時に注釈情報（追加件数・理由・根拠 `.num` パス/メモ）を返し、Step1で表示する。
- [x] `S1-AUTO-309-03` 注釈リンクから `Numeration編集` へ遷移し、根拠 `.num` を読込表示できるようにする。
- [x] `S1-NUM-EDIT-01` `Numeration編集` 画面を改修し、`numファイルアップロード` + `ファイルパス表示` + `タブ区切りグリッド編集` + `下部の語彙情報参照` の構成へ整理する。
- [x] `S1-REG-28` API回帰で `imi01` 長文に対して `auto_add_ga_phi=true` なら `309` が2件追加され、根拠 `.num` が返ることを固定する。
- [x] `S1-REG-29` API回帰で `auto_add_ga_phi` 未指定時は従来どおり `309` を追加しないことを固定する。
- [x] `S1-REG-30` Web回帰で自動補完注釈の表示と、根拠リンクから `Numeration編集` へ遷移できることを固定する。

## 77. Step1 309表示の実行環境取り違え再発防止
- [x] `S1-OPS-01` `309` 自動補完がUIに出ない報告を受けた際、API実装差分ではなく「旧プロセス残留（再起動漏れ）」を原因として切り分ける手順を追記する。
- [x] `S1-OPS-02` `restart-playwright-env --force` 実行後に `POST /v1/derivation/numeration/generate(auto_add_ga_phi=true)` を直叩きし、`lexicon_ids` に `309,309` が含まれることを確認する運用を固定する。

## 78. Reachability探索（長文ケース改善）
- [x] `S2-HDA-38` Reachability探索に「一意供給ラベル（33/25）の早期消失を抑止する制約」を追加し、唯一の相方供給を無駄消費する遷移を除外する。
- [x] `S2-HDA-39` Reachability探索の遷移順序に `partner deficit` 指標を追加し、相方要求（25/33）を満たしやすい経路を優先する。
- [x] `S2-HDA-40` imi系の探索で `case-local` / `vt-local` 優先を「並び替え」から「絞り込み優先」に引き上げ、局所規則の先行適用を徹底する。
- [ ] `S2-RCH-24` `ふわふわしたわたあめを食べているひつじと話しているうさぎがいる` を `reachable` へ到達させる（imi01/imi03を含む実測確認）。

## 79. Reachability探索（単項規則経路と相方優先の再調整）
- [x] `S2-HDA-41` 遷移列挙で `basenum==1` の単項規則（single）を探索対象に含め、終端での単項操作経路を失わないようにする。
- [x] `S2-HDA-42` imi系の長文局面（`basenum>=10`）に限り、`33/25` 要求と `11/12` 供給が直接噛み合う遷移を優先する順序キーを追加する。
- [x] `S2-REG-23` 既知reachableセット（`known_reachable_sets`）と `skateboard/usagi` 回帰を再実行し、既存 reachable の手戻りがないことを確認する。
- [ ] `S2-RCH-25` 上記調整後も `ふわふわした...うさぎがいる` は `unknown(timeout)` のため、追加の探索戦略改善が必要であることを記録する。

## 80. 外部相談用ブリーフ作成（自然さ優先の段階拡張）
- [x] `DOC-BRF-01` 事前知識ゼロの言語学/CS専門家向けに、問題設定・制約・再現手順・評価指標・受け入れ基準を1本で説明する文書を作成する。

## 81. 外部相談用ブリーフの自己完結化（追記）
- [x] `DOC-BRF-02` 外部相談用ブリーフに用語集・非目標・再現手順・採択条件を追記し、当該文書のみで相談が成立するように改訂する。

## 82. 外部相談用ブリーフに語彙・規則・解析手順を追加
- [x] `DOC-BRF-03` 今回前提語彙項目の詳細（ID/素性）と `imi01` マージルール詳細（RH/LH）および解析フローを追記し、専門家が文書だけで議論開始できる状態にする。

## 83. 外部相談用ブリーフの不足補完（探索仕様・自然さ・停滞ログ）
- [x] `DOC-BRF-04` 外部レビュー指摘に基づき、reachable可否の現状根拠、現行探索器仕様、自然さ評価定義抜粋、深さ12停滞ログを本文内へ追記する。

## 84. 外部相談用ブリーフの機構重視全面改稿
- [x] `DOC-BRF-05` 文書全体を4分類（確認済み事実/現行仕様/作業仮説/未確認）で再構成し、探索器パイプライン・RH/LH擬似コード・刈り込み安全性・数値整合・未確定事項を機構中心に明記する。

## 85. 外部相談用ブリーフの機構定義追補（深さ12解釈・定義表・契約表）
- [x] `DOC-BRF-06` 深さ12の意味を「終端深さ到達済み」と明示し、探索器の主因を深さ不足から幅/重複/順序へ補正する。
- [x] `DOC-BRF-07` `unresolved / delta_unresolved / state_signature(packed,structural) / partner_deficit / case-local / vt-local / max_frontier` を本文内で定義し、入力・出力・用途・安全性を表で明示する。
- [x] `DOC-BRF-08` RH/LH補助関数（`_process_*`）の入出力契約・副作用・不変量を本文へ追補し、安全な同値化議論に必要な情報を追加する。

## 86. 外部レビュー追補（数値段階整合・self-loop説明分離・局所定義精密化）
- [x] `DOC-BRF-09` `3.5` の `134` を「nohead通過候補（実行前候補）」へ改名し、`max_frontier=79` との差が測定段階差であることを本文で明示する。
- [x] `DOC-BRF-10` self-loop 判定が structural 固定である点と、packed/structural差が効く対象（再訪抑制キー）を分離して記述する。
- [x] `DOC-BRF-11` `zero_delta_streak=12` の題材依存の実効性（imi01 double-only では枝刈り強度が高くない可能性）を注記する。
- [x] `DOC-BRF-12` `partner_deficit` の式（全ラベル合計）と `case-local/vt-local` の参照領域（現在のbase配列隣接）を定義表へ明記する。
- [x] `DOC-BRF-13` 4.5 擬似コードの変数宣言を補い、`append_merge_relation_semantic` が before-state の `hb[4]/nb[4]` を参照する点を明示する。

## 87. Reachability計測強化と安全圧縮（A/B前提整備）
- [x] `S2-PROF-01` Reachabilityレスポンス `metrics` に `timing_ms`（enumerate/sort/unresolved/partner/sibling_dedup）を追加し、time支配箇所を可視化する。
- [x] `S2-PROF-02` `metrics.layer_stats` を追加し、`basenum` 層ごとに候補数・刈り込み数・重複圧縮数（sibling dedup）を記録する。
- [x] `S2-PROF-03` `metrics.leaf_stats` を追加し、`basenum=1` 終端の `unresolved` 分布（min/max/histogram）を返す。
- [x] `S2-HDA-43` 同一親から生成される兄弟遷移を `next structural signature` で1件へ圧縮し、到達性を落とさず重複展開を削減する。
- [x] `S2-HDA-44` 再訪抑制を `(signature,streak)` 個別判定から「小さい `zero_delta_streak` が大きい streak を支配する」判定に強化する。
- [x] `S2-REG-24` `apps/api/tests/test_derivation.py` 全件通過で回帰がないことを確認する。
- [x] `S2-RCH-26` 長文 `imi01`（ふわふわ…）で `structural/packed` A/B を実測し、`max_depth=12到達済み・timeout継続・leaf unresolved最小=9` を確認する。

## 88. Reachability候補列挙の二層化（descriptor / materialize）
- [x] `S2-HDA-45` 候補列挙を `enumerate_action_descriptors` と `materialize_action_descriptor` に分離し、cheap情報と実行後情報の境界を明確化する。
- [x] `S2-PROF-04` `timing_ms` を `pairs_scan/rule_expand/cheap_feature_extract/execute_double_merge/next_signature/post_filter/descriptor_sort` に細分化する。
- [x] `DOC-RCH-02` A/B計測結果を `reachability-ab-profile-20260301.md` に更新し、分離後の支配時間を記録する。

## 89. Lazy descriptor generator と dedup順序の再構成
- [x] `S2-HDA-46` `iter_action_descriptors` を導入し、pair schedule 順に descriptor を逐次生成する（descriptor一括生成を廃止）。
- [x] `S2-HDA-47` sibling dedup を `execute -> signature -> dedup -> unresolved/partner` の順へ前倒しし、代表childのみ exact 計算を払う。
- [x] `S2-HDA-48` lazy path の dominance 署名を structural 固定にし、packed は比較用メトリクスに限定する。
- [x] `S2-PROF-05` leaf best-sample（残差サマリ）を `metrics.leaf_stats.best_samples` として返し、残差要因の切り分け材料を追加する。
- [x] `S2-REG-25` `apps/api/tests/test_derivation.py` 全件通過を再確認する。

## 90. Reachability DFSホットパスのdescriptorストリーム化（list除去）
- [x] `S2-HDA-49` `_search_reachability` 内の `descriptors = list(_iter_action_descriptors(...))` を撤去し、iterator 直処理に変更して descriptor 一括構築コストを除去する。
- [x] `S2-REG-26` 上記変更後に `apps/api/tests/test_derivation.py` 全件通過を再確認する。

## 91. Reachability lazy境界の可視化 + IMI fast path
- [x] `S2-MET-01` `layer_stats` に `descriptors_emitted / descriptors_exhausted / descriptors_partial` を追加し、lazy列挙が exact か lower-bound かを状態単位で識別できるようにする。
- [x] `S2-HDA-50` `_iter_action_descriptors` に IMI double-only fast path（RH/LH直接emit）を追加し、generic `list_merge_candidates` 呼び出しを回避する。
- [x] `S2-PROF-06` `timing_ms.rule_expand_fast_path` を追加し、fast path 適用回数を観測できるようにする。
- [x] `S2-REG-27` 上記変更後に `apps/api/tests/test_derivation.py` 全件通過を再確認する。

## 92. Reachability監査（A/A + Structural A/B + best-leaf + sanity）
- [x] `S2-AUD-01` A/A 意味同値監査として `generic/fast` の `action_key` 集合一致テストを追加する（13/12/11 + short/medium）。
- [x] `S2-AUD-02` Structural 主系列で long imi01 を `fast OFF/ON` で同条件実測し、`rule_expand/post_filter/execute` の総量と正規化値を比較する。
- [x] `S2-AUD-03` `best leaf` 比較を `unresolved_min` のみで終わらせず、残差サマリ（33/25 系）を含めて評価する。
- [x] `S2-AUD-04` short/medium の既知 reachable ケースで性能 sanity を取得し、回帰がないことを確認する。
- [x] `DOC-RCH-03` 監査結果を `reachability-ab-audit-20260301.md` と `reachability-ab-audit-20260301.json` に保存する。

## 93. Reachability post_filter 高速化（exact incremental summary）
- [x] `S2-HDA-51` `post_filter` の full recompute を削減するため、`_StateSummary`（unresolved / 33・25 demand-provider 集計）を導入し、double merge 時は `current - left - right + mother` の局所差分で次状態 summary を更新する。
- [x] `S2-BUG-04` summary キャッシュを `id()` キーから内容キー（`state: structural signature`, `node: JSON signature`）へ変更し、オブジェクトID再利用による `reachable` 誤判定を防止する。
- [x] `S2-REG-28` differential audit テスト `test_derivation_incremental_state_summary_matches_full_recompute_for_double_merge` を追加し、incremental更新と full recompute が一致することを回帰固定する。
- [x] `S2-REG-29` `apps/api/tests/test_derivation.py` 全件実行で手戻りがないことを再確認する。

## 94. 正しさ修正後の再ベースライン（cache統計つき）
- [x] `S2-PROF-07` Reachability `metrics` に `cache_stats`（state/node hit/miss、avg key build ms）を追加し、content-key 化後のコストと有効性を可視化する。
- [x] `S2-REG-30` same-content / different-content の summary cache key 回帰テストを追加し、内容同値・内容差分の挙動を固定する。
- [x] `S2-AUD-05` `6cdb979` 基準で long structural A/B（fast OFF/ON）と sanity を再計測し、旧ベースラインを置換する。
- [x] `DOC-RCH-04` 再ベースライン結果を `reachability-ab-audit-20260301-postfix.md/.json` に保存する。

## 95. candidate Grammar別 discharge 監査（4文 × φなし/あり）
- [x] `S2-DIAG-05` 4文（`うさぎがいる` / `わたあめを食べているひつじがいる` / `ひつじと話しているうさぎがいる` / `ふわふわした...うさぎがいる`）を対象に、`imi01/imi02/imi03` × `φなし/φ+2` の reachability 実測を同一条件で実行する。
- [x] `S2-DIAG-06` 各ケースで `initial_family_counts`・`best_leaf_residual_family_avg`・`residual source top` を集計し、`se:33/sy:11/sy:17` の discharge 観測表を作成する。
- [x] `DOC-RCH-09` discharge 監査結果を JSON/Markdown で保存し、`φ追加はcount補完だが質改善に直結しない` こと（S2/S3/S4で `unknown` 継続）を明記する。
  - 成果物: [reachability-discharge-matrix-20260302.md](/Users/tomonaga/Documents/syncsemphoneIMI/syncsemphone-next/docs/specs/reachability-discharge-matrix-20260302.md)
