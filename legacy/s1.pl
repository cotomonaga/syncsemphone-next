#!/usr/bin/perl
use utf8;

##@ メイン処理///

sub to_index {
	utf8::decode($grammar[$lg]);	## こうしないと文字化けする
	if (defined $param{'grammar'}){
		$maintitle = "統語意味論デモプログラム（$grammar[$lg]）";
	} else {
		$maintitle = "統語意味論デモプログラム";
	}
	&show_header;
print <<"END";
<div>
<p><a href="http://www.gges.xyz/syncsem/index.cgi">http://www.gges.xyz/syncsem/index.cgi</a></p>
</div>
END
	exit;
}

sub numeration_select {# 1. 登録してある Numeration から選ぶ
	my @numfile1 = glob "$folder[$lg]/set-numeration/*.num";
	my @numfile2 = glob "$folder[$lg]/numeration/*.num";
	$numfilenum1 = @numfile1;
	$numfilenum2 = @numfile2;

print <<"END";
<p align="right"><a href="lexicon.cgi?grammar=$lg" target="_blank">$lexicon_list</a></p>
	<center><TABLE border width='80%' cellpadding=5 bgcolor=$cwintext>
		<TR><TD width="25%">$grammarlist</TD>
				<TD>
END
	for($r=1; $r<=$mergenum; $r++){
		print "$r) $rulename[$r][0], "; 
	}
print <<"END";
		</TD></TR>
	</TABLE></center>
<FORM method="post" action=$self>
	<div>
	<table width='100%'>
		<tr>
			<td width='100' valign="center" align="center">
				<INPUT type="hidden" name="mode" value="numeration_check">
				<INPUT type="hidden" name="grammar" value=$lg>
				<INPUT type="submit" value=" numeration ">
			</td>
			<td bgcolor=$cwintext>
				<p>$numeration_select_instruction</p>
				<p>$numeration_reset <INPUT type="reset" value=$reset_sign>)</p>
			</td>
		</tr>
	</table>
	</div>
	<p>$resume_target1</p>
	<TABLE width='100%' border cellpadding=5 bgcolor=$cwintext>
END

##1-1 new
print <<"END";
		<TR><TD>
			<p><span class='orangeback'><INPUT type="radio" name="numeration" value="new">$numeration_select_choice1</span></p>
			</TD></TR>
END

##1-2 upload
print <<"END";
		<TR><TD valign="top">
			<p><span class="greenback"> <INPUT type="radio" name="numeration" value="upload"> </span>$numeration_upload<br>
		<textarea name="upload" rows="4" cols="100" wrap="off" style="overflow:hidden;"></textarea>
		<span class="plus">$rearrange_sign <INPUT type="radio" name="arrange" value="upload"></span></p>
		</TD></TR>
END

##1-3 set-numeration
print <<"END";
		<TR><TD>
END
	for($f=0; $f<$numfilenum1; $f++){
		$numfile1S[$f] = (split(/\//, $numfile1[$f]))[2];
		open(NUM,"$numfile1[$f]");
			$m = <NUM>;
		close(NUM);
		$memo[$f] = (split(/\t/, $m))[0];
		utf8::decode($memo[$f]);	# こうしないと文字化けする
print <<"END";
			<p><span class="greenback"> <INPUT type="radio" name="numeration" value=$numfile1[$f]> </span>
			<span class="memo">[$memo[$f]]</span> 
			<span class="plus">$rearrange_sign <INPUT type="radio" name="arrange" value=$numfile1[$f]></span> 
			<span class="hide">$numfile1S[$f]</span></p>
END

#	print <<"END";
#				<p><span class="greenback"> <INPUT type="radio" name="numeration" value=$numfile1[$f]> </span><span class="memo">[$memo[$f]]</span> (
#	END
#			for($i=1; $i<=30; $i++){
#				$lex[$f][$i] = (split(/\t/, $m))[$i];
#				if ($lex[$f][$i] ne "") {
#	print <<"END";
#	$lex[$f][$i], 
#	END
#				}
#			}
#	print <<"END";
#	) <span class="plus">$rearrange_sign <INPUT type="radio" name="arrange" value=$numfile1[$f]></span> <span class="hide">$numfile1S[$f]</span></p>
#	END
	}
print <<"END";
		</TD></TR>
</FORM>
END

##1-4 resume_target
print <<"END";
<FORM method="post" action=$self>
		<TR><TD valign="top">
			<a name="resume"></a>
			<p>$resume_target2<br>
		<textarea name="resume" rows="7" cols="100" wrap="off" style="overflow:hidden;background-color:#FFEEFF"></textarea>
				<INPUT type="hidden" name="mode" value="resume">
				<INPUT type="hidden" name="grammar" value=$lg>
				<INPUT type="submit" value=" resume ">
</p>
		</TD></TR>
</FORM>
END

##1-5 footer
print <<"END";
	</TABLE>
END
}

sub lexicon_specify {# 1.A.1 新しい Numeration を作成するために見出し語を記入する

print <<"END";
<p align="right"><a href="lexicon.cgi?grammar=$lg" target="_blank">$lexicon_list</a></p>
<p>$lexicon_specify_instruction1</p>
<p>$lexicon_specify_instruction2[$lg]</p>
<FORM method="post" action=$self>
	<p><INPUT type="submit" value=" lexicon search "></p>
	<INPUT type="hidden" name="grammar" value=$lg>
	<INPUT type="hidden" name="mode" value="lexicon_select">
	<TABLE width='100%' border cellpadding=10 bgcolor=$cwintext>
END
	for($i=1; $i<=30; $i++){
print <<"END";
		<TR>
			<TD bgcolor="$ctablebox" width="3%" nowrap align="center"><p>$i</p></TD>
			<TD><INPUT type="text" name="lex$i" value="$lex[$i]" size="10"></td>
		</TR>
END
	}
print <<"END";
	</TABLE>
</FORM>
END
}

sub lexicon_select {# 1.A.2. 正しい lexical item を選ぶ
										#	※lg別 perl スクリプト（plus_feature1）
	$numfilememo="";
	for($i=1; $i<=30; $i++){
		$a[$i] = $param{"lex$i"};	# 入力語
		utf8::decode($a[$i]);	# こうしないと文字化けする
		$numfilememo=$numfilememo.$a[$i];	# 文字化け

	}
print <<"END";
<p>$lexicon_select_instruction1[$lg]</p>
<FORM method="post" action=$self>
			<p><INPUT type="submit" value=" start "></p>
			<INPUT type="hidden" name="grammar" value=$lg>
			<INPUT type="hidden" name="mode" value="numeration_save">
			<p>$lexicon_select_instruction2<INPUT type="text" name="numfilememo" value="$numfilememo" size="50"></p>
	<br>
	<TABLE width='100%' border cellpadding=0 bgcolor=$cwintext>
END
	for($i=1; $i<=30; $i++){
		$lex[$i] = $param{"lex$i"};	# 入力語
		if ($lex[$i] ne "") {	 # 入力語がなくなったら、表にしない
print <<"END";
		<TR>
			<TD width="2%" align="center" bgcolor="$ctablebox" nowrap>$i</TD>
			<TD width="3%" align="center" bgcolor="$ctablebox" nowrap>x<INPUT type="text" name="idx$i" value="$i" size="1">-1</TD>
			<TD width="3%" align="center" bgcolor="$ctablebox" nowrap>$lex[$i]</td>
			<TD width="95%">
END
				$j=0;
				for($x=1; $x<=$lexnum; $x++){		# lexicon を調べる
					if (($entry[$no[$x]] ne "") && ($entry[$no[$x]] eq $lex[$i])) {
						$j=$j+1;
						if ($j eq "1") {
							$ch="checked";
						} else {
							$ch="";
						}
print <<"END";
						<p><INPUT type="radio" name="lexicon$i" $ch value=$no[$x]>
END
						&show_feature($ca, "", $category[$no[$x]]);
						for($z=1; $z<=$prednum[$no[$x]]; $z++){
							&show_feature($pr, "i", $pred[$no[$x]][$z][0]);
							&show_feature($pr, "s", $pred[$no[$x]][$z][1]);
							&show_feature($pr, "p", $pred[$no[$x]][$z][2]);
						}
						for($z=1; $z<=$syncnum[$no[$x]]; $z++){
							&show_feature($sy, "", $sync[$no[$x]][$z]);
						}
						&show_feature($sl, "", $idslot[$no[$x]]);
						for($z=1; $z<=$semnum[$no[$x]]; $z++){
							&show_feature($se, "", $sem[$no[$x]][$z]);
						}
						&plus_feature1;	# 各 $lg によって中身が異なる
###						&show_feature($wo, "", $word[$no[$x]]);
						&show_feature($ph, "", $phono[$no[$x]]);
						&show_feature($nb, "", $note[$no[$x]]);
print <<"END";
						</p>
END
					}
				}
				if ($j eq "0") {	 # lexicon になかった場合
print <<"END";
						<p>$lexicon_select_info</p>
END
				}
		}
print <<"END";
		</TD></TR>
END
	}
print <<"END";
			</TABLE>
		</TD></TR>
	</TABLE>
</FORM>
END
}

sub numeration_arrange {# 1.B.
										#	※lg別 perl スクリプト（plus_feature2）
	$memo = (split(/\t/, $m[0]))[0];
	utf8::decode($memo);	# こうしないと文字化けする
print <<"END";
<div>
<p>$numeration_arrange_instruction1</p>
<FORM method="post" action=$self>
			<p><INPUT type="submit" value=" start "></p>
			<INPUT type="hidden" name="grammar" value=$lg>
			<INPUT type="hidden" name="mode" value="numeration_save">
			<p>$lexicon_select_instruction2<INPUT type="text" name="numfilememo" value="$memo" size="50"></p>
	</div>
	<TABLE width='100%' border cellpadding=0 bgcolor=$cwintext>
END
	for($i=1; $i<=30; $i++){
		$no[$i] = (split(/\t/, $m[0]))[$i];
		$plus[$i] = (split(/\t/, $m[1]))[$i];
		$idx[$i] = (split(/\t/, $m[2]))[$i];
			if ($idx[$i] < 1) {
				$idx[$i]=$i;
			}
		if ($no[$i] ne "") {
print <<"END";
		<TR>
			<TD width="3%" align="center" bgcolor="$ctablebox" nowrap>$i</TD>
			<TD valign="center"><span class="greenback"><span class="f$id">x<INPUT type="text" name="idx$i" value="$idx[$i]" size="1">-1</span></span><INPUT type="hidden" name="lexicon$i" value="$no[$i]">
END
#			&show_feature($id, "", "x$i-1");
			&show_feature($ca, "", $category[$no[$i]]);
			for($z=1; $z<=$prednum[$no[$i]]; $z++){
				$pred[$no[$i]][$z][0] =~ s/id/x$i-1/g;		#「id」を指標で置き換える
				$pred[$no[$i]][$z][1] =~ s/id/x$i-1/g;		#「id」を指標で置き換える
				$pred[$no[$i]][$z][2] =~ s/id/x$i-1/g;		#「id」を指標で置き換える
				&show_feature($pr, "i", $pred[$no[$i]][$z][0]);
				&show_feature($pr, "s", $pred[$no[$i]][$z][1]);
				&show_feature($pr, "p", $pred[$no[$i]][$z][2]);
			}
			for($z=1; $z<=$syncnum[$no[$i]]; $z++){
				$sync[$no[$i]][$z] =~ s/id/x$i-1/g;			#「id」を指標で置き換える
				&show_feature($sy, "", $sync[$no[$i]][$z]);
			}
###			&show_feature($wo, "", $word[$no[$i]]);
			&show_feature($ph, "", $phono[$no[$i]]);

			&plus_feature2;	 #	※lg別 perl スクリプト

			$idslot[$no[$i]] =~ s/id/x$i-1/g;				 #「id」を指標で置き換える
			&show_feature($sl, "", $idslot[$no[$i]]);
			for($z=1; $z<=$semnum[$no[$i]]; $z++){
				$sem[$no[$i]][$z] =~ s/id/x$i-1/g;		#「id」を指標で置き換える
				utf8::decode($sem[$no[$i]][$z]);		#
				&show_feature($se, "", $sem[$no[$i]][$z]);
			}
			&show_feature($nb, "", $note[$no[$i]]);
print <<"END";
			</p>
		</TD></TR>
END
		}
	}
print <<"END";
	</TABLE>
	</FORM>
END
}

sub numeration_save {# 1.2. Numeration を登録する
	$filememo = $param{"numfilememo"};
	$filename = time;
#	$filename = "$folder[$lg]/numeration/".$filename.".num";
	$filename = "$folder[$lg]/set-numeration/".$filename.".num";   ## 今は、こっちに!!!
	open(NUM,"> $filename");

	print NUM "$filememo\t";
	for($i=1; $i<=30; $i++){
		$lexicon[$i] = $param{"lexicon$i"};
		print NUM "$lexicon[$i]\t";
	}
	print NUM "\n";
	print NUM "\t";
	for($i=1; $i<=30; $i++){
		if (defined $param{"plus$i"}) {
			$plus[$i] = $param{"plus$i"};
			print NUM "$plus[$i]\t";
		} else {
			print NUM "\t";
		}
	}
	print NUM "\n";
	print NUM "\t";
	for($i=1; $i<=30; $i++){
		if (defined $param{"idx$i"}) {
			$idx[$i] = $param{"idx$i"};
			print NUM "$idx[$i]\t";
		} else {
			print NUM "\t";
		}
	}
	print NUM "\n";
	close(NUM);
}

sub numeration_check {# 2. Numeration の内容を見せて Merge へ
	$memo = (split(/\t/, $m[0]))[0];
	$history = "";
	utf8::decode($memo);	# こうしないと文字化けする
print <<"END";
<p><span class="memo">[$memo]</span></p>
<p>$numeration_check_instruction</p>
<p>$save_numeration</p>
<br>
<FORM method="post" action=$self>
	<p><INPUT type="submit" value=" ok "></p>
	<INPUT type="hidden" name="mode" value="target">
	<br>
	<TABLE width='100%' border cellpadding=5 bgcolor=$cwintext>
END
	$j=1;
	for($i=1; $i<=30; $i++){
		$no[$j] = (split(/\t/, $m[0]))[$i];
		if ($no[$j] ne "") {
#			$newnum=$j+1; # plus されたものやβに新しい指標番号を付けるときのために
			$newnum=$j; # この時点で要るのは、βに新しい指標番号を付けるときしかないので、これでいい
print <<"END";
		<TR><TD width="3%" align="center" bgcolor="$ctablebox">$j</TD>
		<TD valign="center">
			<p>
END
##1-1 id
			$idx[$j] = (split(/\t/, $m[2]))[$i];
				if ($idx[$j] < 1) {	# 指定が書き込まれていない場合には順番に
					$idx[$j]=$j;
				}
			$beta=0;
			for($z=1; $z<=$syncnum[$no[$j]]; $z++){
				if ($sync[$no[$j]][$z] eq "3,103") {
					$sync[$no[$j]][$z]="3,103,$newnum";
					$beta=1;
				}
			}
			if ($beta>0) {
				$base[$j][$id]="β$newnum";
#				$newnum++;
			} else {
				$base[$j][$id]="x".$idx[$j]."-1";
			}
			&show_feature($id, "", $base[$j][$id]);
##1-2 ca
			$base[$j][$ca]=$category[$no[$j]];
			&show_feature($ca, "", $base[$j][$ca]);
##1-3 sync
			$plus[$j] = (split(/\t/, $m[1]))[$i];
			for($z=1; $z<=$syncnum[$no[$j]]; $z++){
				$base[$j][$sy][$z]=$sync[$no[$j]][$z];
				$base[$j][$sy][$z] =~ s/id/$base[$j][$id]/g;			#「id」を指標で置き換える
				&show_feature($sy, "", $sync[$no[$j]][$z]);
			}
##1-4 plus
			&plus_to_numeration;	 ## Grammar 別ファイルでの指定
##1-5 pred
			for($z=1; $z<=$prednum[$no[$j]]; $z++){
				@{$base[$j][$pr][$z]}=@{$pred[$no[$j]][$z]};
				$base[$j][$pr][$z][0] =~ s/id/$base[$j][$id]/g;		#「id」を指標で置き換える
				$base[$j][$pr][$z][1] =~ s/id/$base[$j][$id]/g;		#「id」を指標で置き換える
				$base[$j][$pr][$z][2] =~ s/id/$base[$j][$id]/g;		#「id」を指標で置き換える
				&show_feature($pr, "i", $base[$j][$pr][$z][0]);
				&show_feature($pr, "s", $base[$j][$pr][$z][1]);
				&show_feature($pr, "p", $base[$j][$pr][$z][2]);
			}
##1-6 idslot
			$base[$j][$sl]=$idslot[$no[$j]];
			$base[$j][$sl] =~ s/id/$base[$j][$id]/g;				 #「id」を指標で置き換える
			&show_feature($sl, "", $base[$j][$sl]);
##1-7 sem
			for($z=1; $z<=$semnum[$no[$j]]; $z++){
				utf8::decode($sem[$no[$j]][$z]);
				$base[$j][$se][$z]=$sem[$no[$j]][$z];
				$base[$j][$se][$z] =~ s/id/$base[$j][$id]/g;		#「id」を指標で置き換える
				&show_feature($se, "", $base[$j][$se][$z]);
			}
##1-8 ph
###			$base[$j][$wo]=$word[$no[$j]];
			$base[$j][$ph]=$phono[$no[$j]];
###			utf8::decode($base[$j][$wo]);	# これをしないと文字化けする?
			utf8::decode($base[$j][$ph]);	# これをしないと文字化けする?
###			&show_feature($wo, "", $base[$j][$wo]);
			&show_feature($ph, "", $base[$j][$ph]);
##1-9 wo
##1-10 nb
			&show_feature($nb, "", $note[$no[$j]]);
print <<"END";
			</p>
		</TD></TR>
END
		$j=$j+1;
#		$j=$newnum;
		$newnum=$j;
		}
	}
	$basenum = $j-1;
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
	#$json = encode_entities(JSON->new->utf8(0)->encode($aref));

	$m[0] =~ s/\t/\\t/g; #	&#x0009
	$m[1] =~ s/\t/\\t/g; #	&#x0009
	$m[2] =~ s/\t/\\t/g; #	&#x0009
print <<"END";
	</TABLE>
<br>
<p><TEXTAREA rows=4 cols=90 wrap="off" NAME="numfile" readonly	style="overflow:hidden;">
@m
</TEXTAREA></p>
END
	&hidden;
print <<"END";
	</FORM>
END
}

sub target {# 3.1. Merge するものを選ぶ
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
		if ($json =~ /,[0-9]/) {
			$status= "ungrammatical";
		} else {
			$status= "grammatical";
		}
	if ($status eq "ungrammatical") {
		$status_sign = $target_instruction3;
	} else {
		$status_sign = $target_instruction4. $target_instruction5;
	}
##1-1 recursive application
print <<"END";
<FORM method="post" action=$self>
			<p><span class="memo">[$memo]</span></p>
			<p>$target_instruction1</p>
	<TABLE border width="100%" cellpadding=5 bgcolor=$cwintext>
		<TR>
			<TD colspan=3>$history<br><div>$status_sign</div></TD>
		</TR>
		<TR>
			<TH width="2%" bgcolor=$csummary nowrap>$leftsign</TH>
			<TH width="2%" bgcolor=$csummary nowrap>$rightsign</TH>
			<TD>$legend</TD>
		</TR>
END
	for($j=1; $j<=$basenum; $j++){
print <<"END";
		<TR>
			<TD nowrap><INPUT type="radio" name="left" value=$j></TD>
			<TD nowrap><INPUT type="radio" name="right" value=$j></TD>
			<TD>
END
		$u=0;
			&show_base($base[$j]);
print <<"END";
			</TD></TR>
END
	}
print <<"END";
		</TABLE>
END
	&hidden;

##1-2 素性説明
print <<"END";
<p><iframe src="vacant.html" width="100%" height="80" name="feature_description"></iframe></p>

			<div>
			<p><INPUT type="submit" value=" rule ">
			$target_instruction2<INPUT type="reset" value=$reset_sign>）</p>
			<INPUT type="hidden" name="mode" value="rule_select">
			</div>
		</FORM>
END

##1-3 意味表示 へ
print <<"END";
	<FORM method="post" action=$self>
		<div class="orangeback">
		<p><INPUT type="submit" value="$lfsign">$lf_instruction0</p>
		<INPUT type="hidden" name="mode" value="lf">
END
	&hidden;
print <<"END";
		</div>
	</FORM>
END

##1-4 tree へ
print <<"END";
	<div class="greenback">
	<FORM method="post" action=$self>
		<p><INPUT type="submit" value="$tree_sign">$tree_instruction1</p>
		<INPUT type="hidden" name="mode" value="tree">
END
	&hidden;
print <<"END";
	</FORM>
END
print <<"END";
	<FORM method="post" action=$self>
		<p><INPUT type="submit" value="$tree_sign_cat">$tree_instruction1</p>
		<INPUT type="hidden" name="mode" value="tree_cat">
END
	&hidden;
print <<"END";
	</FORM>
	</div>
END

##1-5 footer
print <<"END";
<a name="resume"></a>
<p><TEXTAREA rows=7 cols=90 wrap="off" NAME="process" readonly	style="overflow:hidden;background-color:#FFEEFF">
$folder[$lg]
$memo
$newnum
$basenum
$history
$json
</TEXTAREA></p>
END
}

sub Merge_select { # 3.2. 適用する rule を選ぶ
##1-1 base 表示
print <<"END";
<br>
<FORM method="post" action=$self>
			<p><span class="memo">[$memo]</span></p>
	<TABLE width='100%' border cellpadding=5 bgcolor=$cwintext>
END
	for ($j=1; $j<=$basenum; $j++){
		if ($j eq $left) {
			$tg = "<strong>$leftsign</strong>";
		} elsif ($j eq $right) {
			$tg = "<strong>$rightsign</strong>";
		} else {
			$tg = "";
		}
print <<"END";
		<TR>
			<TD align="center" bgcolor="$ctablebox">$j $tg</TD>
			<TD>
END
		$u=0;
			&show_base($base[$j]);
print <<"END";
			</TD></TR>
END
	}
print <<"END";
		</TABLE>
END
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
	#	$json = encode_entities(JSON->new->utf8(0)->encode($aref));
print <<"END";
	<br>
	<p>$merge_select_instruction1</p>
	<br>
	<p><INPUT type="submit" value=" Apply "></p>
		<INPUT type="hidden" name="mode" value="execute">
END
	&hidden;

##1-2 rule 検索
# 適用可能な rule だけ、base の番号が define される
# $rule_c[$rule_number][0] = 左要素
# $rule_c[$rule_number][1] = 右要素
	@rule_c = ();

	if (($left ne $right) && ($left ne "") && ($right ne "")) {
		&double_Merge_check;		# 個別言語ファイル
	}
	if ($left ne "") {
		$check=$left;
		$ch=0;
		&single_Merge_check;		# 個別言語ファイル
	}
	if ($right ne "") {
		$check=$right;
		$ch=1;
		&single_Merge_check;		# 個別言語ファイル
	}

##1-3 rule 表示
	$a=0;
	$ch[0]="checked";
	for($r=1; $r<=$mergenum; $r++){
		if ((defined $rule_c[$r][0]) || (defined $rule_c[$r][1])) {
			if (($rulename[$r][2] eq 1) && (defined $rule_c[$r][0])) {	# single Merge が 左要素に適用可能なら。こうやって、その都度１行ずつ書かないと、たとえば左要素と右要素それぞれに同じ rule が適用可能な場合、正しい表示にならない。
###				<a href="$folder[$lg]/rules/$rulename[$r].html" target='rule_description'>$rulename[$r]</a>	
print <<"END";
				<p><INPUT type="radio" name="choice" value=$a $ch[$a]> 
				<a href="MergeRule/$rulename[$r][1].html" target='rule_description'>$rulename[$r][0]</a>	
				($rule_c[$r][0])
				<INPUT type="hidden" name="rule$a" value=$r>
				<INPUT type="hidden" name="check$a" value="$rule_c[$r][0]"></p>
END
				$a=$a+1;
			}
			if (($rulename[$r][2] eq 1) && (defined $rule_c[$r][1])) {	# single Merge が 右要素に適用可能なら
###				<a href="$folder[$lg]/rules/$rulename[$r].html" target='rule_description'>$rulename[$r]</a>	
print <<"END";
				<p><INPUT type="radio" name="choice" value=$a $ch[$a]> 
				<a href="MergeRule/$rulename[$r][1].html" target='rule_description'>$rulename[$r][0]</a>	
				($rule_c[$r][1])
				<INPUT type="hidden" name="rule$a" value=$r>
				<INPUT type="hidden" name="check$a" value="$rule_c[$r][1]"></p>
END
				$a=$a+1;
			}
			if (($rulename[$r][2] eq 2) && (defined $rule_c[$r])) {	# double Merge が適用可能なら
###				<a href="$folder[$lg]/rules/$rulename[$r].html" target='rule_description'>$rulename[$r]</a>	
print <<"END";
				<p><INPUT type="radio" name="choice" value=$a $ch[$a]> 
				<a href="MergeRule/$rulename[$r][1].html" target='rule_description'>$rulename[$r][0]</a>	
				(@{$rule_c[$r]})
				<INPUT type="hidden" name="rule$a" value=$r>
				<INPUT type="hidden" name="left$a" value="$rule_c[$r][0]">
				<INPUT type="hidden" name="right$a" value="$rule_c[$r][1]"></p>
END
				$a=$a+1;
			}
		}
	}
	if ($a eq "0") {	 # 「適用できる rule がありませんでした。」
print <<"END";
		<p>$merge_select_instruction2</p>
END
	}
print <<"END";
		<p><iframe src="vacant.html" width="100%" height="250" name="rule_description"></iframe></p>
END
print <<"END";
		</FORM>
END
}

sub execute { ## 3.3. 操作を実行して 3.1 target へ戻る
	$a = $param{"choice"};
	$r = $param{"rule$a"};
	if (defined $param{"left$a"}){
		$left = $param{"left$a"};
	} else {
		$left = "";
	}
	if (defined $param{"right$a"}){
		$right = $param{"right$a"};
	} else {
		$right = "";
	}
	if (defined $param{"check$a"}){
		$check = $param{"check$a"};
	} else {
		$check = "";
	}
	if ($check ne "") {
		$history=$history."([".$base[$check][$id]."] ".$rulename[$r][0].") ";
		$history =~ s/β/beta/g; # 「β」を「beta」に置き換える
	} else {
		$history=$history."([".$base[$left][$id]." ".$base[$right][$id]."] ".$rulename[$r][0].") ";
		$history =~ s/β/beta/g; # 「β」を「beta」に置き換える
	}
	&rule_execution;	# 個別言語ファイル
}

sub tree {	#		4. TreeDrawer用 の csv ファイル書き出し
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
print <<"END";
	<br>
	<FORM method="post" action=$self>
		<p><span class="memo">[$memo]</span></p>
		<p><INPUT type="submit" value="$to_target"></p>
		<INPUT type="hidden" name="mode" value="target">
END
	&hidden;
print <<"END";
	</FORM>
	<div>
	<p>$tree_sign</p>
	<p>$tree_instruction2</p>
	<br>
END
	@tree = ();
	$t=0;	# node number
	$u=0;
	for ($j=1; $j<=$basenum; $j++){
		$tree[$t][0] = $t;
		$tree[$t][3] = $w[$id];
		$tree[$t][2]="R";
		&show_tree($base[$j]);
		$t++;
	}
	for ($tt=0; $tt<$t; $tt++){
		$y0=$tree[$tt][4];
		$y1=$tree[$tt+1][4];
		if ($y1 eq $y0+1) {
			$d1 = shift(@{$treerel[$y0+1]});
			$d2 = shift(@{$treerel[$y0+1]});
			$tree[$tt][1]=$d1." ".$d2;
			if ($tree[$d1][3] =~ /$tree[$tt][3]/){
				$tree[$d1][2]="1";
				$tree[$d2][2]="0";
			}
			if ($tree[$d2][3] =~ /$tree[$tt][3]/){
				$tree[$d2][2]="1";
				$tree[$d1][2]="0";
			}
		}
	}
	for ($tt=0; $tt<$t; $tt++){
print <<"END";
		$tree[$tt][0],$tree[$tt][1],$tree[$tt][2],$tree[$tt][3]<br>
END
	}
print <<"END";
	</div>
END
}

sub tree_cat {	#		4.B. TreeDrawer用 の csv ファイル書き出し
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
print <<"END";
	<br>
	<FORM method="post" action=$self>
		<p><span class="memo">[$memo]</span></p>
		<p><INPUT type="submit" value="$to_target"></p>
		<INPUT type="hidden" name="mode" value="target">
END
	&hidden;
print <<"END";
	</FORM>
	<div>
	<p>$tree_sign</p>
	<p>$tree_instruction2</p>
	<br>
END
	@tree = ();
	$t=0;	# node number
	$u=0;
	for ($j=1; $j<=$basenum; $j++){
		$tree[$t][0] = $t;
		$tree[$t][3] = $w[$id];
		$tree[$t][5] = $w[$ca];
		$tree[$t][2]="R";
		&show_tree_cat($base[$j]);
		$t++;
	}
	for ($tt=0; $tt<$t; $tt++){
		$y0=$tree[$tt][4];
		$y1=$tree[$tt+1][4];
		if ($y1 eq $y0+1) {
			$d1 = shift(@{$treerel[$y0+1]});
			$d2 = shift(@{$treerel[$y0+1]});
			$tree[$tt][1]=$d1." ".$d2;
			if ($tree[$d1][3] =~ /$tree[$tt][3]/){
				$tree[$d1][2]="1";
				$tree[$d2][2]="0";
			}
			if ($tree[$d2][3] =~ /$tree[$tt][3]/){
				$tree[$d2][2]="1";
				$tree[$d1][2]="0";
			}
		}
	}
	for ($tt=0; $tt<$t; $tt++){
print <<"END";
		$tree[$tt][0],$tree[$tt][1],$tree[$tt][2],$tree[$tt][5]<br>
END
	}
print <<"END";
	</div>
END
}

sub lf { #		 5.1 LF意味素性
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
print <<"END";
	<br>
	<FORM method="post" action=$self>
		<p><span class="memo">[$memo]</span></p>
		<p><INPUT type="submit" value="$to_target"></p>
		<INPUT type="hidden" name="mode" value="target">
END
	&hidden;
print <<"END";
	</FORM>
	<div>
	<p>$lf_instruction1</p>
	<br>
END
	@sr = ();
	for ($j=1; $j<=$basenum; $j++){
		&show_lf($base[$j]);	# LF意味素性の表示と @sr の登録
	}
print <<"END";
	</div>
END
		$aref2 = \@sr;
		$json2 = JSON->new->utf8(0)->encode($aref2);
		$json2 =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える
		$signal = index($json2, "=");	# feature が残っていれば、その位置の数字。なければ -1
	if ($signal < 0) { 
print <<"END";
		<br>
		<FORM method="post" action=$self>
		<p><INPUT type="submit" value="$sr_sign"></p>
		<INPUT type="hidden" name="mode" value="sr">
		<INPUT type="hidden" name="sr" value="$json2">
END
	&hidden;	# $json と $basenum は不要だけれど
print <<"END";
		</FORM>
END
	} else {
print <<"END";
		<br>
		<p>$lf_instruction2</p>
END
	}
}

sub sr { # 5.2	 意味表示
#	$sr[X][Y][Z]
#		X ... OBJECT指標番号
#		Y ... LAYER 番号
#		Z ... property
#  $betanum=@{$sr[0][0]};
#  $sr[$o][0] eq "Predication"
#	$sr[0][0][0]=1; # βがあるということのしるし
#	push(@{$sr[0][0]}, $a1);	# 何番のβがあるかをここに記録しておく
#	$sr[$obj][0]=$a2;	# ここにderived complex を記録して覚えておく
#	$layer=1;	# property は layer 1 に記録しておく


	$memo=$param{"memo"};
	utf8::decode($memo);	# こうしないと文字化けする
print <<"END";
	<br>
	<p><span class="memo">[$memo]</span></p>
	<div>
	<p><strong>$sr_sign</strong> (<span class="object">OBJECT</span>	<span class="Predication">Predication</span>)</p>
	<br>
END

	$objnum = @sr;
			if ($objnum > 0) {
				$objnum = $objnum-1;
			} else {
				$objnum = 0;
			}

	if (defined $sr[0][0][0]) {	# βがある場合
		$betanum=@{$sr[0][0]};
		for($b=1; $b<$betanum; $b++){
			$a1=$sr[0][0][$b];
			$a2=$sr[$a1][0];
			$ll=index($a2, "(");
			$derived_a=substr($a2, 0, $ll);
			$ll++; 
			$lll=index($a2, ")");
			$lll=$lll-$ll; #	host-id の文字数
			$host_id=substr($a2, $ll, $lll);
			$l=index($host_id, "-");
			$l=$l-1;
			$host_obj=substr($host_id, 1, $l);
			$l=$l+2;
			$host_layer=substr($host_id, $l);
			$targetnum=@{$sr[$host_obj][$host_layer]};
			for($t=0; $t<$targetnum; $t++){
				$ta = (split(/:/, $sr[$host_obj][$host_layer][$t]))[0];
				$tv = (split(/:/, $sr[$host_obj][$host_layer][$t]))[1];
				if ($ta eq $derived_a) {
					$l=index($tv, "-");
					$l=$l-1;
					$target_obj=substr($tv,1, $l);
					$l=$l+2;
					$ll=length($tv);
					$lll=$ll-$l;
					$target_layer=substr($tv,$l,$lll);
				}
			}
			$propertynum=@{$sr[$a1][1]};
			for($p=0; $p<$propertynum; $p++){
				push(@{$sr[$target_obj][$target_layer]},$sr[$a1][1][$p]);
			}
#			splice(@sr, $a1, 1); # ←これをすると、あとの番号が狂ってしまう。
			$sr[$a1]="";
		}
	}

	for($o=1; $o<=$objnum; $o++){
		$layernum = @{$sr[$o]};
			if ($layernum > 0) {
				$layernum = $layernum-1;
			} else {
				$layernum = 0;
			}
		if ($layernum>0) {
			if ($sr[$o][0] eq "Predication") {
				$content = "Predication"
			} else {
				$content = "object"
			}
		
print <<"END";
		<p><span class=$content>x$o</span> [
END
		}
		for($l=1; $l<=$layernum; $l++){
		$semnum = @{$sr[$o][$l]};
			if ($semnum>0) {
print <<"END";
			(<span class="layer">x$o-$l</span> 
END
			}
			for($s=0; $s<$semnum; $s++){
print <<"END";
			<<span class="f$se">$sr[$o][$l][$s]</span>> 
END
			}
			if ($semnum>0) {
print <<"END";
			) 
END
			}
		}
		if ($layernum>0) {
print <<"END";
			]<br>
END
		}
	}
print <<"END";
	</div>
END

}


1;

