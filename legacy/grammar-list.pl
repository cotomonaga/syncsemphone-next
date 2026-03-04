	$lgnum=39;

	($japanese1, 
	$japanese2, 
	$japanese3, 
	$imi01,
	$imi02,
	$imi03,
	$jpf202001,
	$jpf202002,
	$jpf201801,
	$jpf201802,
	$jpf201803,
	$jpf201804,
	$jpf0, 
	$jpf0e, 
	$otago0, 
	$otago1, 
	$jpf1a, 
	$jpf1b, 
	$jpf1c, 
	$jpf1d, 
	$jpf1d2, 
	$jpf1e, 
	$jpf1f, 
	$jpf1g, 
	$jpf1, 
	$jpf2, 
	$jpf3, 
	$jpf3minus, 
	$jpf3few, 
	$jpf3more, 
	$jpf4, 
	$jpf5, 
	$jpf6, 
	$ex1,
	$ex2,
	$chinese1, 
	$chinese2, 
	$chinese3, 
	$english) = (0..$lgnum-1);

# $mergefile = "./".$folder[$lg]."/".$folder[$lg]."R.pl";	#	Merge rules
# $lexiconfile = "./".$folder[$lg]."/".$folder[$lg].".csv";	# Lexicon
# $featurefile = "./".$folder[$lg]."/f-".$folder[$lg].".pl";	# Feature specifications
# $instructionfile = $instruction[$lg];


##@ $japanese1///
$folder[$japanese1] = 'japanese1';
$grammar[$japanese1] = '日本語（簡易版）';
$grammarmemo[$japanese1] = "（『統語意味論』の１章および２章の途中まで用いられているバージョン。格助詞の分布および Predication について考慮していない文法です。参考までに、３章以降の話題についても、ある程度、対応できるものについては Numeration が登録されています。）";
$instruction[$japanese1] = 'japaneseM.pl';

##@ $japanese2///
$folder[$japanese2] = 'japanese2';
$grammar[$japanese2] = '日本語（『統語意味論』版）';
$grammarmemo[$japanese2] = "（『統語意味論』の２章以降で提案されたバージョン。参考までに、簡易版で説明されていた例文についても Numeration が登録されています。）";
$instruction[$japanese2] = 'japaneseM.pl';


##@ $imi01///
# 中身としては、もともと jpf201801 と同じ
$folder[$imi01] = 'imi01';
$lexicon[$imi01] = 'all';
$grammar[$imi01] = 'IMI 共同研究用・日本語文法片 01';
$grammarmemo[$imi01] = "（IMI 共同研究用・日本語文法片 01: RH-Merge/LH-Merge）";
$instruction[$imi01] = 'japaneseM.pl';

##@ $imi02///
# 中身としては、もともと jpf202001 と同じ
$folder[$imi02] = 'imi02';
$lexicon[$imi02] = 'all';
$grammar[$imi02] = 'IMI 共同研究用・日本語文法片 02';
$grammarmemo[$imi02] = "（IMI 共同研究用・日本語文法片 02: RH-Merge/LH-Merge/zero-Merge）";
$instruction[$imi02] = 'japaneseM.pl';

##@ $imi03///
# 中身としては、もともと jpf202002 と同じ
$folder[$imi03] = 'imi03';
$lexicon[$imi03] = 'all';
$grammar[$imi03] = 'IMI 共同研究用・日本語文法片 03';
$grammarmemo[$imi03] = "（IMI 共同研究用・日本語文法片 03: target 素性）";
$instruction[$imi03] = 'japaneseM.pl';

##@ $jpf202001///
$folder[$jpf202001] = 'jpf202001';
$grammar[$jpf202001] = '日本語文法片 1 : 2020';
$grammarmemo[$jpf202001] = "（ミニミニ日本語 01）";
$instruction[$jpf202001] = 'japaneseM.pl';

##@ $jpf202002///
$folder[$jpf202002] = 'jpf202002';
$grammar[$jpf202002] = '日本語文法片 2 : 2020';
$grammarmemo[$jpf202002] = "（ミニミニ日本語 02）";
$instruction[$jpf202002] = 'japaneseM.pl';

##@ $jpf201801///
$folder[$jpf201801] = 'jpf201801';
$grammar[$jpf201801] = '日本語文法片 1 : 2018';
$grammarmemo[$jpf201801] = "（ミニミニ日本語 01: RH-Merge と LH-Merge）";
$instruction[$jpf201801] = 'japaneseM.pl';

##@ $jpf201802///
$folder[$jpf201802] = 'jpf201802';
$grammar[$jpf201802] = '日本語文法片 2 : 2018';
$grammarmemo[$jpf201802] = "（ミニミニ日本語 02: 非隣接関係）";
$instruction[$jpf201802] = 'japaneseM.pl';

##@ $jpf201803///
$folder[$jpf201803] = 'jpf201803';
$grammar[$jpf201803] = '日本語文法片 3 : 2018';
$grammarmemo[$jpf201803] = "（ミニミニ日本語 03: Predication）";
$instruction[$jpf201803] = 'japaneseM.pl';

##@ $jpf201804///
$folder[$jpf201804] = 'jpf201804';
$grammar[$jpf201804] = '日本語文法片 4 : 2018';
$grammarmemo[$jpf201804] = "（ミニミニ日本語 04: Partitioning）";
$instruction[$jpf201804] = 'japaneseM.pl';


##@ $jpf0///
$folder[$jpf0] = 'jpf0';
$grammar[$jpf0] = '日本語文法片 0';
$grammarmemo[$jpf0] = "（システムに慣れるためのミニミニ日本語 0: RH-Merge と LH-Merge）";
$instruction[$jpf0] = 'japaneseM.pl';

##@ $otago0///
$folder[$otago0] = 'otago0';
$grammar[$otago0] = 'Fragment of Japanese Grammar 0';
$grammarmemo[$otago0] = "(RH-Merge & LH-Merge)";
$instruction[$otago0] = 'englishM.pl';

##@ $jpf0e///
$folder[$jpf0e] = 'jpf0e';
$grammar[$jpf0e] = 'Fragment of Japanese Grammar 0';
$grammarmemo[$jpf0e] = "(RH-Merge & LH-Merge)";
$instruction[$jpf0e] = 'englishM.pl';

##@ $jpf1a///
$folder[$jpf1a] = 'jpf1a';
$grammar[$jpf1a] = '日本語文法片 1';
$grammarmemo[$jpf1a] = "（システムに慣れるためのミニミニ日本語 1: 他動詞の項の区別）";
$instruction[$jpf1a] = 'japaneseM.pl';

##@ $otago1///
$folder[$otago1] = 'otago1';
$grammar[$otago1] = 'Fragment of Japanese Grammar 1';
$grammarmemo[$otago1] = "(GA/WO distinction)";
$instruction[$otago1] = 'englishM.pl';

##@ $jpf1b///
$folder[$jpf1b] = 'jpf1b';
$grammar[$jpf1b] = '日本語文法片 2';
$grammarmemo[$jpf1b] = "（システムに慣れるためのミニミニ日本語 2: zero-Merge）";
$instruction[$jpf1b] = 'japaneseM.pl';

##@ $jpf1c///
$folder[$jpf1c] = 'jpf1c';
$grammar[$jpf1c] = '日本語文法片 3';
$grammarmemo[$jpf1c] = "（システムに慣れるためのミニミニ日本語 3: 格助詞ヲとガ）";
$instruction[$jpf1c] = 'japaneseM.pl';

##@ $jpf1d///
$folder[$jpf1d] = 'jpf1d';
$grammar[$jpf1d] = '日本語文法片 4';
$grammarmemo[$jpf1d] = "（システムに慣れるためのミニミニ日本語 4: 使役と受身）";
$instruction[$jpf1d] = 'japaneseM.pl';

##@ $jpf1d2///
# rare1 と rare2 の違いを Lex ではなく、rule のみにしてしまったもの
$folder[$jpf1d2] = 'jpf1d2';
$grammar[$jpf1d2] = '日本語文法片 4';
$grammarmemo[$jpf1d2] = "（システムに慣れるためのミニミニ日本語 4: 使役と受身）";
$instruction[$jpf1d2] = 'japaneseM.pl';

##@ $jpf1e///
$folder[$jpf1e] = 'jpf1e';
$grammar[$jpf1e] = '日本語文法片 5';
$grammarmemo[$jpf1e] = "（システムに慣れるためのミニミニ日本語 5: 移動）";
$instruction[$jpf1e] = 'japaneseM.pl';

##@ $jpf1f///
$folder[$jpf1f] = 'jpf1f';
$grammar[$jpf1f] = '日本語文法片 6';
$grammarmemo[$jpf1f] = "（システムに慣れるためのミニミニ日本語 6: wh疑問文）";
$instruction[$jpf1f] = 'japaneseM.pl';

##@ $jpf1g///
$folder[$jpf1g] = 'jpf1g';
$grammar[$jpf1g] = '日本語文法片 7';
$grammarmemo[$jpf1g] = "（システムに慣れるためのミニミニ日本語 7: 分配読み）";
$instruction[$jpf1g] = 'japaneseM.pl';

##@ $jpf1///
$folder[$jpf1] = 'jpf1';
$grammar[$jpf1] = '日本語文法片 1 (2016)';
$grammarmemo[$jpf1] = "（システムに慣れるためのミニミニ日本語 1: RH-Merge と J-Merge）";
$instruction[$jpf1] = 'japaneseM.pl';

##@ $jpf2///
$folder[$jpf2] = 'jpf2';
$grammar[$jpf2] = '日本語文法片 2 (2016)';
$grammarmemo[$jpf2] = "（システムに慣れるためのミニミニ日本語 2: RH-Merge, J-Merge, zero-Merge）";
$instruction[$jpf2] = 'japaneseM.pl';

##@ $jpf3///
$folder[$jpf3] = 'jpf3';
$grammar[$jpf3] = '日本語文法片 3 (2016)';
$grammarmemo[$jpf3] = "（システムに慣れるためのミニミニ日本語 3: sase / rare）";
$instruction[$jpf3] = 'japaneseM.pl';

##@ $jpf3minus///
$folder[$jpf3minus] = 'jpf3minus';
$grammar[$jpf3minus] = '日本語文法片 3 with no features';
$grammarmemo[$jpf3minus] = "（文法片 3 の解釈不可能統語素性をすべて削除したバージョン）";
$instruction[$jpf3minus] = 'japaneseM.pl';

##@ $jpf3few///
$folder[$jpf3few] = 'jpf3few';
$grammar[$jpf3few] = '日本語文法片 3 with few features';
$grammarmemo[$jpf3few] = "（文法片 3 の解釈不可能統語素性 wo と +J-Merge を削除したバージョン）";
$instruction[$jpf3few] = 'japaneseM.pl';

##@ $jpf3more///
$folder[$jpf3more] = 'jpf3more';
$grammar[$jpf3more] = '日本語文法片 3 with more features';
$grammarmemo[$jpf3more] = "（文法片 3 から解釈不可能統語素性 wo を削除したバージョン）";
$instruction[$jpf3more] = 'japaneseM.pl';

##@ $jpf4///
$folder[$jpf4] = 'jpf4';
$grammar[$jpf4] = '日本語文法片 4 (2016)';
$grammarmemo[$jpf4] = "（システムに慣れるためのミニミニ日本語 4: no / da）";
$instruction[$jpf4] = 'japaneseM.pl';

##@ $jpf5///
$folder[$jpf5] = 'jpf5';
$grammar[$jpf5] = '日本語文法片 5 (2016)';
$grammarmemo[$jpf5] = "（システムに慣れるためのミニミニ日本語 5: ga / movement）";
$instruction[$jpf5] = 'japaneseM.pl';

##@ $jpf6///
$folder[$jpf6] = 'jpf6';
$grammar[$jpf6] = '日本語文法片 6 (2016)';
$grammarmemo[$jpf6] = "（システムに慣れるためのミニミニ日本語 6: wh）";
$instruction[$jpf6] = 'japaneseM.pl';

##@ $japanese3///
$folder[$japanese3] = 'japanese3';
$grammar[$japanese3] = '日本語（開発途中版）';
$grammarmemo[$japanese3] = "（『統語意味論』後の発展を含むバージョン。）";
$instruction[$japanese3] = 'japaneseM.pl';

##@ $ex1///
$folder[$ex1] = 'ex1';
$grammar[$ex1] = '統語規則練習用 1';
$grammarmemo[$ex1] = "（意味素性なし、right/left）";
$instruction[$ex1] = 'japaneseM.pl';

##@ $ex2///
$folder[$ex2] = 'ex2';
$grammar[$ex2] = '統語規則練習用 2';
$grammarmemo[$ex2] = "（意味素性なし、right/left, head/nonhead）";
$instruction[$ex2] = 'japaneseM.pl';

##@ $chinese1///
$folder[$chinese1] = 'chinese1';
$grammar[$chinese1] = '中文1';
$grammarmemo[$chinese1] = "（作成中の中国語文法 1 張晨迪）";
$instruction[$chinese1] = 'japaneseM.pl';

##@ $chinese2///
$folder[$chinese2] = 'chinese2';
$grammar[$chinese2] = '中文2';
$grammarmemo[$chinese2] = "（作成中の中国語文法 2 陳陸琴）";
$instruction[$chinese2] = 'japaneseM.pl';

##@ $chinese3///
$folder[$chinese3] = 'chinese3';
$grammar[$chinese3] = '中文3';
$grammarmemo[$chinese3] = "（作成中の中国語文法 3 郭楊）";
$instruction[$chinese3] = 'japaneseM.pl';


