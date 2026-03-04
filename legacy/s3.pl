#!/usr/bin/perl
use utf8;

##@ 共通サブルーチン///

sub target_resume {

	$mm = $param{"resume"};
		$m[0] = (split(/\n/, $mm))[0];
##				if ($m[0] ne $folder[$lg]) {
##					&numeration_select;	 ##	別の文法の派生状態の場合には無効。何かメッセージを出すべき？
##				}
	$memo = (split(/\n/, $mm))[1];
	utf8::decode($memo);	## こうしないと文字化けする
	$newnum = (split(/\n/, $mm))[2];
	$basenum = (split(/\n/, $mm))[3];
	$history = (split(/\n/, $mm))[4];
	$json = (split(/\n/, $mm))[5];
	my $aref = JSON->new->utf8(1)->decode($json);
	##my $aref = JSON->new->utf8(1)->decode(decode_entities($json));
	@base = @$aref;
	for ($j=1; $j<=$basenum; $j++){
		$prednum[$j] = @{$base[$j][$pr]};
			if ($prednum[$j] > 0) {
				$prednum[$j] = $prednum[$j]-1;
			} else {
				$prednum[$j] = 0;
			}
		$syncnum[$j] = @{$base[$j][$sy]};
			if ($syncnum[$j] > 0) {
				$syncnum[$j] = $syncnum[$j]-1;
			} else {
				$syncnum[$j] = 0;
			}
		$semnum[$j] = @{$base[$j][$se]};
			if ($semnum[$j] > 0) {
				$semnum[$j] = $semnum[$j]-1;
			} else {
				$semnum[$j] = 0;
			}
	}
}

sub mergebase_read {
	##		my $q = CGI->new;
	##		my $json = $q->param('base');
	$memo=$param{"memo"};
	$newnum=$param{"newnum"};
	utf8::decode($memo);	## こうしないと文字化けする
	$json=$param{"base"};
	my $aref = JSON->new->utf8(1)->decode($json);
	##my $aref = JSON->new->utf8(1)->decode(decode_entities($json));
	@base = @$aref;
	$history = $param{"history"};
	$basenum = $param{"basenum"};
	for ($j=1; $j<=$basenum; $j++){
		$prednum[$j] = @{$base[$j][$pr]};
			if ($prednum[$j] > 0) {
				$prednum[$j] = $prednum[$j]-1;
			} else {
				$prednum[$j] = 0;
			}
		$syncnum[$j] = @{$base[$j][$sy]};
			if ($syncnum[$j] > 0) {
				$syncnum[$j] = $syncnum[$j]-1;
			} else {
				$syncnum[$j] = 0;
			}
		$semnum[$j] = @{$base[$j][$se]};
			if ($semnum[$j] > 0) {
				$semnum[$j] = $semnum[$j]-1;
			} else {
				$semnum[$j] = 0;
			}
	}
}

sub sr_read {
	$json2=$param{"sr"};
	my $aref2 = JSON->new->utf8(1)->decode($json2);
	##my $aref = JSON->new->utf8(1)->decode(decode_entities($json));
	@sr = @$aref2;
}

sub show_base {	## 配列に読み込まれている中身を見やすく表示する
	my $x = shift;
	@w = @$x;

##1-1 id, ca
print <<"END";
		<p class="base$u">
END
		&show_feature($id, "", $w[$id]);
		&show_feature($ca, "", $w[$ca]);

##1-2 pr
	if (($w[$pr] eq "")){
		 $prednum = 0;
	} else {
		$prednum = @{$w[$pr]};
			if ($prednum > 0) {
				$prednum = $prednum-1;
			} else {
				$prednum = 0;
			}
	}
	for($zz=1; $zz<=$prednum; $zz++){
		if ($w[$pr][$zz] ne "zero") {
			&show_feature($pr, "i", $w[$pr][$zz][0]);
			&show_feature($pr, "s", $w[$pr][$zz][1]);
			&show_feature($pr, "p", $w[$pr][$zz][2]);
		}
	}

##1-3 sy
	$syncnum = @{$w[$sy]};
			if ($syncnum > 0) {
				$syncnum = $syncnum-1;
			} else {
				$syncnum = 0;
			}
	for($zz=0; $zz<=$syncnum; $zz++){
		&show_feature($sy, "", $w[$sy][$zz]);
	}

##1-4 sl
		&show_feature($sl, "", $w[$sl]);

##1-5 se
	$semnum = @{$w[$se]};
			if ($semnum > 0) {
				$semnum = $semnum-1;
			} else {
				$semnum = 0;
			}
	for($zz=1; $zz<=$semnum; $zz++){
		&show_feature($se, "", $w[$se][$zz]);
	}

##1-6 wo
		if ("ARRAY" eq ref $w[$wo]) {  ## non-terminal の場合
print <<"END";
			</p>
END
			$u=$u+1;
			for my $ww (@{$w[$wo]}) { # bodyの中身を一つ一つ処理
				if ($ww eq "zero") { ##	←movement の trace
print <<"END";
			<p class="base$u">[ ]</p>
END
				} else {
			&show_base($ww);
				}
			}
			$u=$u-1;
		} else {
###			&show_feature($wo, "", $w[$wo]);
			&show_feature($ph, "", $w[$ph]);
print <<"END";
			</p>
END
		}
}

sub show_tree {	## TreeDrawer 用の csvデータの書き出し
	my $x = shift;
	@w = @$x;
	$tree[$t][0] = $t;
	$tree[$t][3] = $w[$id];
	$tree[$t][4] = $u;
	push (@{$treerel[$u]}, $t);
		if ("ARRAY" eq ref $w[$wo]) {
			$u=$u+1;
			for my $ww (@{$w[$wo]}) { # bodyの中身を一つ一つ処理
				$t++;
				if ($ww eq "zero") { ##	←movement の trace
					$tree[$t][0] = $t;
					$tree[$t][1] = "";
					$tree[$t][2] = 0;
					$tree[$t][3] = "[	]";
					$tree[$t][4] = $u;
					push (@{$treerel[$u]}, $t);
				} else {
##					$tree[$m][1]=$tree[$m][1]." ".$t;
					&show_tree($ww);
				}
			}
			$u=$u-1;
		} else {
###			utf8::decode($w[$wo]);
###			$tree[$t][3] = $w[$id]."&lt;br&gt;".$w[$wo];
			utf8::decode($w[$ph]);
			$tree[$t][3] = $w[$id]."&lt;br&gt;".$w[$ph];
		}
}

sub show_tree_cat {	## TreeDrawer 用の csvデータの書き出し
	my $x = shift;
	@w = @$x;
	$tree[$t][0] = $t;
	$tree[$t][5] = $w[$ca];
	$tree[$t][3] = $w[$id];
	$tree[$t][4] = $u;
	push (@{$treerel[$u]}, $t);
		if ("ARRAY" eq ref $w[$wo]) {
			$u=$u+1;
			for my $ww (@{$w[$wo]}) { # bodyの中身を一つ一つ処理
				$t++;
				if ($ww eq "zero") { ##	←movement の trace
					$tree[$t][0] = $t;
					$tree[$t][1] = "";
					$tree[$t][2] = 0;
					$tree[$t][5] = "trace";
					$tree[$t][4] = $u;
					push (@{$treerel[$u]}, $t);
				} else {
##					$tree[$m][1]=$tree[$m][1]." ".$t;
					&show_tree_cat($ww);
				}
			}
			$u=$u-1;
		} else {
#			utf8::decode($w[$wo]);
###			$tree[$t][5] = $w[$ca]."&lt;br&gt;".$w[$wo];
#?			utf8::decode($w[$ph]);
			$tree[$t][5] = $w[$ca]."&lt;br&gt;".$w[$ph];
		}
}

sub show_lf {	## 意味素性の表示と @sr への登録
	my $x = shift;
	@w = @$x;

##1-1 β＝...	## この時点では、property の中身のβは置き換えてしまって、idslot のβだけ「意味表示」で整理する
	$syncnum = @{$w[$sy]};
			if ($syncnum > 0) {
				$syncnum = $syncnum-1;
			} else {
				$syncnum = 0;
			}
	for($zz=0; $zz<=$syncnum; $zz++){
		if ($w[$sy][$zz] =~ /beta#/) {		## Binding 適用後の βがあれば
			$a1 = (split(/#/, $w[$sy][$zz]))[1];	 ## βに付された数字
			$a2 = (split(/#/, $w[$sy][$zz]))[2];	 ## derived complex
			$a3 = "β".$a1;
		}
	}

##1-2 意味素性
	$semnum = @{$w[$se]};
			if ($semnum > 0) {
				$semnum = $semnum-1;
			} else {
				$semnum = 0;
			}
	if (($w[$sl] ne "zero") && ($w[$se] ne "zero")) {
		$hostnum=0;
print <<"END";
			<p>
END
		&show_feature($sl, "", $w[$sl]);
		$l=index($w[$sl], "-");
		if ($l < 1) {	 ## idslot がβの場合、いったん記録しておいて「意味表示」のところで目的のところに入れる
			$sr[0][0][0]=1; ## βがあるということのしるし
			push(@{$sr[0][0]}, $a1);	## 何番のβがあるかをここに記録しておく
			$obj=$a1;
			$sr[$obj][0]=$a2;	## ここにderived complex を記録して覚えておく
			$layer=1;	## property は layer 1 に記録しておく
		} else {
			$obj=substr($w[$sl],1,$l-1);	## $obj = 「x」の次の文字から「-」の前の文字まで
			$layer=substr($w[$sl],$l+1);	## $layer = 「-」の次の文字から残り
		}

		if ($semnum < 1) {		## 意味素性のないφも、一応、見出しだけは出すために。
			push(@{$sr[$obj][$layer]}, "");
		}

		for($z=1; $z<=$semnum; $z++){
			$w[$se][$z] =~ s/$a3/$a2/g;			## $a3 (β###) を $a2 (derived complex) で置き換える
			push(@{$sr[$obj][$layer]}, $w[$se][$z]);
			&show_feature($se, "", $w[$se][$z]);

##1-3 Host addition
			@temp1 = (split(/:/, $w[$se][$z]));	## attribute と value に分ける
			if ($temp1[0] eq "Host") {
				$hostl=index($temp1[1], "-");
				$hostobj=substr($temp1[1],1,$hostl-1);
				$hostlayer=substr($temp1[1],$hostl+1);
				$hostnum++;
			}
			if ($temp1[0] eq "Kind") {
				$hostattr=$temp1[1];
				$hostnum++;
			}
		}
		if ($hostnum > 1) {
			push(@{$sr[$hostobj][$hostlayer]}, $hostattr.":x".$obj."-".$layer);
		}

##1-4 Predication 素性（ LF意味素性のところでは表示されないが、最終的な意味表示には出てくる。この時点では、いったん、Subject property や Predicate property を登録しておき、&sr のところで、それが Predication 素性だったら、登録を取り消す。）

		$prednum = @{$w[$pr]};
			if ($prednum > 0) {
				$prednum = $prednum-1;
			} else {
				$prednum = 0;
			}
		for($z=1; $z<=$prednum; $z++){
			$lpred=index($w[$pr][$z][0], "-");	## Predication-id
			if ($lpred > 0) {
				$objpred=substr($w[$pr][$z][0],1,$lpred-1);
				$layerpred=substr($w[$pr][$z][0],$lpred+1);
				$sr[$objpred][0]="Predication";		## OBJECT と区別するため
				$sr[$objpred][$layerpred][0]="Subject: $w[$pr][$z][1]";
				$sr[$objpred][$layerpred][1]="Predicate: $w[$pr][$z][2]";

##  やっぱり、Subject property と Predicate property はバラで登録しないことにしよう。(2016.09.12.)
#				$l1=index($w[$pr][$z][1], "-");	## Subject
#				$p1_obj=substr($w[$pr][$z][1],1,$l1-1);
#				$p1_layer=substr($w[$pr][$z][1],$l1+1);
#				push(@{$sr[$p1_obj][$p1_layer]}, "Predicate: $w[$pr][$z][2]");

#				$l2=index($w[$pr][$z][2], "-");	## Predicate
#				$p2_obj=substr($w[$pr][$z][2],1,$l2-1);
#				$p2_layer=substr($w[$pr][$z][2],$l2+1);
#				push(@{$sr[$p2_obj][$p2_layer]}, "Subject: $w[$pr][$z][1]");

			}
		}
print <<"END";
			</p>
END
	}
		if ("ARRAY" eq ref $w[$wo]) {
			for my $ww (@{$w[$wo]}) { # bodyの中身を一つ一つ処理
				if ($ww ne "zero") { ##	←注意：movement のときの書き方によっては変える！
					&show_lf($ww);
				}
			}
		}
}

sub make_tree {  ## ←もう使っていなさそう
	($d0, $m0, @ww) = @_;
		$tree[$d0][0]=$d0;
		$tree[$m0][1]=$tree[$m0][1]." ".$d0;
		if ($ww[0] eq "zero") { ##	←movement の trace
			$tree[$d0][1]="";
			$tree[$d0][2]="0";
			$tree[$d0][3]="[　]";
		} else {
##			@ww = @$x;
			$tree[$d0][3]=$ww[$id];
			if ($tree[$d0][3] eq $tree[$m0][3]) {
				$tree[$d0][2]="1";
			} else {
				$tree[$d0][2]="0";
			}
		}
}

1;

