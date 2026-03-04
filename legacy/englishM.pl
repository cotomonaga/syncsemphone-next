use utf8;  ## ←*.pl にもこれがないと文字化けする。

##@ lexicon.cgi 用
$lexicon_list = "Lexicon List";
$entry_title = "見出し語";
$legend2[$ca] = "<span class=f1>範疇素性</span>";
$legend2[$pr] = "<span class=fi2>Predication素性指標</span> 
  <span class=fs2>Subject: 指標</span> 
  <span class=fp2>Predicate: 指標</span>";
$legend2[$sy] = "<span class=f3>統語素性</span>/<span class='feature'>解釈不可能素性</span>";
$legend2[$sl] = "<span class=f4>id-slot</span>";
$legend2[$se] = "<span class=f5>意味素性（attribute: value)</span>";
$legend2[$wo] = "<span class=f6>音韻形式</span>";
$legend2[$nb] = "備考";


##@ numeration_select {## 1.1. 登録してある Numeration から選ぶ
$numeration_select_instruction="(i) <span class='orangeback'>新たに Numeration を定義する</span>か、<br>(ii) 保存してあった Numeration を BOX に貼り付けて<span class='greenback'>操作を始める</span>か素性や指標を<span class='plus'>再調整</span>するか、<br>(iii) 下にあらかじめて準備されている Numeration に対して<span class='greenback'>操作を始める</span>か素性や指標を<span class='plus'>再調整</span>するか<br><br>いずれかを選んで、左の　<strong>numeration</strong>　ボタンをクリックしてください。";
$numeration_select_choice1="新たに Numeration を定義する";
$numeration_upload="保存してあった Numeration をこの BOX に貼り付けて用いる";
$start_sign = "開始";
$rearrange_sign = "Extra operations at numeration";
$numeration_reset="　（間違った列に印を入れてしまった場合には、こちら→　　";
$reset_sign=" やり直し ";
$resume_target1="もしくは、保存してある派生状態から操作を再開する場合には、<a href='#resume'>画面の一番下のピンク色の BOX </a>に貼りこんで、「resume」ボタンを押してください。";
$resume_target2="保存してあった 派生状態をこの BOX に貼り付けて、「resume」ボタンを押してください。";

##@ lexicon_specify {## 1.2. 新しい Numeration を作成するために見出し語を記入する
$lexicon_specify_instruction1="新たに Numeration を作ります。<br>以下の box に１つずつ単語を入力して、「lexicon search」ボタンを押してください。<br>（余った欄は空欄のままでかまいません。）";
$lexicon_specify_instruction2[$japanese1]="動詞は、活用形もしくは辞書見出し形を入れてください。<br>格助詞（が／を／に／の）は、ここでは入力せず、次の画面で指定してもらいます。";
$lexicon_specify_instruction2[$japanese2]="動詞は、国語辞典の見出し語形を入れてください。";

##@ lexicon_select {## 1.3. 正しい lexical item を選んで Numeration を登録する
$numeration_arrange_instruction1="Numeration を調整します。<br>必要に応じて、<span class='greenback'>指標番号を変更する</span>か、<span class='plus'>追加の素性を指定する</span>かをし、メモに追記をして「start」ボタンを押してください。";
$lexicon_select_instruction1[$japanese1]="新たに、Numeration を登録します。<br>メモを入力し、右側の列で正しい lexical item が選択されていることを確認してください。<br>格助詞が必要な場合には、<span class='plus'>追加の素性</span>に書き込んで、「save」ボタンを押してください。<br>（動詞に選択されている格助詞は、ga, wo, ni のようにローマ字で書いてください。それ以外の格助詞は、ひらがなでかまいません。）";
$lexicon_select_instruction1[$japanese2]="新たに、Numeration を登録します。<br>メモを入力し、右側の列で正しい lexical item が選択されていることを確認してください。<br>必要に応じて、<span class='plus'>追加の素性</span>を指定してから、「start」ボタンを押してください。";
$lexicon_select_instruction2="この numeration からできる文＋特徴のメモ（他の numeration と十分区別できるように。。。）→";
$lexicon_select_info="（未登録）";

##@ numeration_check {## 1.5. Numeration の内容を見せて Merge へ
$numeration_check_instruction="We now start applying Merge rules to this Numeration";
$save_numeration="自分で設定した Numeration で、また使う可能性がある場合は、一番下のBOX↓内にあるものを「すべて選択」して、自分のファイルに保存しておいてください。";

##@ target {## 2.1. Merge するものを選ぶ
$leftsign="Left";
$rightsign="Right";
$target_instruction1=
	"２つの要素を Merge するのならば、「左」に来るものと「右」に来るものを１つずつ選んでください。<br>
	１つの要素に対して操作を行なうのならば、どちらか１つだけでもかまいません。<br>
	下の「rule」を押すと、選んだ節点に対して適用可能な規則の一覧が示されます。<br>
	<span class='feature'>解釈不可能素性</span>をクリックすると、下の BOX に特徴が表示されます。<br>
	<a href='#resume'>一番下のピンクの BOX</a> の中を「すべて選択」して自分のファイルに保存しておくと、この派生状態から操作を再開することができます。";
$target_instruction3=
	"<span class='feature'>Uninterpretable features</span> still remain.  This is not grammatical.";
$legend = 
	"<span class=f0>Index</span> 
	<span class=f1>Categorial features</span> 
	<span class=f3>Syntactic features</span>/<span class='feature'>Uninterpretable features</span> 
	<span class=f4>id-slot</span> 
	<span class=f5>Semantic features（attribute: value)</span> 
	<span class=f6>Phonological features</span>";
## 	"<span class=f0>Index</span> 
##	<span class=f1>Categorial features</span> 
##	<span class=fi2>Predication素性指標</span> 
##  <span class=fs2>Subject: 指標</span> 
##  <span class=fp2>Predicate: 指標</span> 
##	<span class=f3>Syntactic features</span>/<span class='feature'>Uninterpretable features</span> 
##	<span class=f4>id-slot</span> 
##	<span class=f5>Semantic features（attribute: value)</span> 
##	<span class=f6>Phonological features</span>";

$target_instruction4="All the uniterpretable features have been erased.  This is grammatical.";
$target_instruction5="<span class='f6'>word</span>を上から読んだものが PF です。";
$target_instruction2="　Available Merge rules　　（間違った列に印を入れてしまった場合には、こちら→　　";
$target_instruction2sign=" やり直し ";
$to_target=" 再び統語操作を適用する ";

##@ PF へ ... 単に上から読んだらいいから、要らないか。
$PFsign=" PF表示 ";

##@ Merge_select { ## 2.2. 適用する rule を選ぶ
$merge_select_instruction1=
	"The names of applicable Merge rules are listed here. Choose one and click 「Apply」. <br>	If you like to see the definition of any Merge rule, click the name of the Merge rule.";
$merge_select_instruction2="適用できる rule がありませんでした。<br>前の画面に戻って、指定をやりなおしてください。";

##@ tree {  ##    2.4. TreeDrawer用 の csv ファイル書き出し
$tree_sign="TreeDrawer 用の csv データ作成（指標番号）";
$tree_sign_cat="TreeDrawer 用の csv データ作成（範疇素性）";
$tree_instruction1="（全節点を含む樹形図用のデータが作成されるので、節点を選ぶ必要はありません）";
$tree_instruction2="以下を copy して、テキストファイルに保存し、それを TreeDrawer で load すると、樹形図が表示されます。";

##@ lf { ##     3.1 LF意味素性
$lfsign="List of semantic features";
$lf_instruction0="（全節点の意味素性が表示されるので、節点を選ぶ必要はありません）";
$lf_instruction1="List of semantic features"; ##（Predication素性は表示されていない）
$lf_instruction2="意味表示の中に解釈不可能素性が残っているので、意味表示は出せません。";

##@ sr { ## 3.2   意味表示
$sr_sign=" Semantic representation ";
$numeration_sign=" あらためて Numeration を選択する ";

##@ show_header
#$maintitle = "Demo program ($grammar[$lg])"; ##統語意味論デモプログラム
$maintitle1 = "Demo program"; ##統語意味論デモプログラム
$to_start = "Numeration選択に戻る";
