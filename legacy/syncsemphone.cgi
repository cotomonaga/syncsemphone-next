#!/usr/bin/perl
use utf8;
use FindBin;
use lib "$FindBin::RealBin/My";
use JSON;
#use Encode;
#use CGI;
#use HTML::Entities;
#require '../../cgi-bin/lib/jcode.pl';
#require '../../cgi-bin/lib/color-project.pl';
#use Encode qw(decode);
#use strict;
#use warnings;
require 'grammar-list.pl';
require 'syncsemphone-common.pl';


#	!!!まだ

#	!!!やっぱり plus は配列にして、説明ファイルも作ること

#	!!!property-no は、$left が OBJECT指示表現の場合のみにすること
#	!!!今のままだと、複数のβが１つの Bind に必ず bind されてしまう。もしかして coindex じゃないと、本当にそれいいんだったりして？？？
# !!!「agentive niyotte は rare2によってしかlicsされない」←未処理

# 新しく rule を作った場合：（文法ごとの $mergefile）
#		$mergenum を増やす
#		rule名で rule-numberを登録
#		@rulename に登録
#		@ruletype に登録
#		@ rule適用可否チェック
#		@ rule適用
#		rule の説明の html ファイル
# 新しく素性を作った場合：（文法ごとの $featurefile）
#		文法ごとの $featurefile の素性処理の方法と show_feature
#		howto-lexicon.doc への記載
#		feature の説明の html ファイル
#	plus の場合：（文法ごとの $mergefile）
#		plus_feature1
#		plus_feature2
#		plus_to_numeration
#		plus の説明の html ファイル

# 余裕があれば、CGI.pm を使う形に修正する。

##@ 変数のわりあて///
	$self = "syncsemphone.cgi";

##@ 処理振り分け///
##1-1 流れ図
#	0. Grammar を選ぶ
#			$mode=""												to_index
#	
#	1. numeration を選ぶ（set numeration 一覧）	
#			$mode="numeration_select"				numeration_select				$mode="numeration_check"
#	
#		1.A. 新規登録
#			$numeration eq "new"						lexicon_specify					$mode="lexicon_select"
#			$mode="lexicon_select"					lexicon_select					$mode="numeration_save"
#			$mode="numeration_save"					numeration_save					$mode="numeration_check"
#	
#		1.B. 変更
#			defined $param{"arrange"}				numeration_arrange			$mode="numeration_save"
#			$mode="numeration_save"					numeration_save					$mode="numeration_check"
#	
#		1.C. upload
#			$numeration eq "upload"																	$mode="numeration_check"
#	
#		1.D. upload & arrange
#			$param{"arrange"} eq "upload"		numeration_arrange			$mode="numeration_save"
#	
#		1.E. 再開
#			
#	
#	2. numeration check
#			$numeration = $numfile
#			$mode="numeration_check"				numeration_check				$mode="target"
#	
#	3. Merge
#		3.1. target
#		3.2. Merge_select
#		3.3. execute
#	4. Tree
#	5. SR
#		5.1. lf
#		5.2. sr

##1-2 変数読み込み
	if ($ENV{'REQUEST_METHOD'} ne 'POST') {		
		&get_params($ENV{'QUERY_STRING'});
	}
	read(STDIN, $all, $ENV{'CONTENT_LENGTH'});	#入力データ全体を読み込む
	&get_params($all);				#パラメータ取得
		if (defined $param{'mode'}) {
			$mode = $param{'mode'};
		}
		if (defined $param{'grammar'}) {
			$lg = $param{'grammar'};
			if ($lexicon[$lg] eq "all"){
				$lexiconfile = "lexicon-all.csv";	# Lexicon
			} else {
				$lexiconfile = $folder[$lg]."/".$folder[$lg].".csv";	# Lexicon
			}
			$mergefile = $folder[$lg]."/".$folder[$lg]."R.pl";	#	Merge rules
			require $mergefile;	#	Merge rules の指定
			for ($r=1;$r<=$mergenum;$r++) {
				require "MergeRule/$rulename[$r][1].pl";
			}
			$instructionfile = $instruction[$lg];
			require $instructionfile;	#	画面に表示されるメッセージ
		} else {
			&to_index;
		}
	utf8::decode($grammar[$lg]);	## こうしないと文字化けする
	if (defined $param{'grammar'}){
		$maintitle = "$maintitle1 ($grammar[$lg])";
	} else {
		$maintitle = "$maintitle1";
	}
	if (($mode eq "tree") || ($mode eq "tree_cat")){ ## tree のときにはヘッダも変わるので
		&show_header_java;
	} else {
		&show_header;
	}

##1-3 Numeration
	if ($mode eq "") {	# 0.	スタート画面
		&to_index;
	} elsif ($mode eq "numeration_select") {	# 1.
		&numeration_select;
	} elsif ($mode eq "lexicon_select") {		 # 1.A.2.
		&read_lexicon;
		&lexicon_select;
	} elsif ($mode eq "numeration_save") {		# 1.A.3.
		&numeration_save;
			&read_lexicon;
			open(NUM2,"$filename");
				@m = <NUM2>;
			close(NUM2);
		&numeration_check;
	} elsif ($mode eq "numeration_check") {
		if ((defined $param{"arrange"}) && (defined $param{"numeration"})) {
				&numeration_select;
		} elsif ($param{"arrange"} eq "upload") {	 # 1.D.
			&read_lexicon;
			$mm = $param{"upload"};
				$mm =~ s/\\t/\t/g;
				$m[0] = (split(/\n/, $mm))[0];
				$m[1] = (split(/\n/, $mm))[1];
				$m[2] = (split(/\n/, $mm))[2];
			&numeration_arrange;
		} elsif (defined $param{"arrange"}) {	 # 1.B.
			$numeration = $param{"arrange"};
			&read_lexicon;
			open(NUM,"$numeration");
				@m = <NUM>;
			close(NUM);
			&numeration_arrange;
		} else {
			$numeration = $param{"numeration"};
			if ($numeration eq "new") {
				&lexicon_specify;									 # 1.A.1
			} elsif ($numeration eq "upload") {	 # 1.C.
				&read_lexicon;
				$mm = $param{"upload"};
					$mm =~ s/\\t/\t/g;
					$m[0] = (split(/\n/, $mm))[0];
					$m[1] = (split(/\n/, $mm))[1];
					$m[2] = (split(/\n/, $mm))[2];
				&numeration_check;
			} elsif ($numeration eq "") {				 # 1.
				&numeration_select;
			} else {															# 2.
				&read_lexicon;
					open(NUM,"$numeration");
						@m = <NUM>;
					close(NUM);
				&numeration_check;
			}
		}

##1-4 Merge
	} elsif ($mode eq "resume") {# 1.E.
		&target_resume;
		&target;
	} elsif ($mode eq "target") {						 # 3.1.
		&mergebase_read;
		&target;
	} elsif ($mode eq "rule_select") {				# 3.2.
		if (defined $param{"left"}){
			$left = $param{"left"};
		} else {
			$left="";
		}
		if (defined $param{"right"}){
			$right = $param{"right"};
		} else {
			$right="";
		}
		if ($left+$right > 0) {
			&mergebase_read;
			&Merge_select;
		} else {
			&mergebase_read;
			&target;
		}
	} elsif ($mode eq "execute") {						# 3.3.
		&mergebase_read;
		&execute;
		&target;
	} elsif (($mode eq "tree") || ($mode eq "tree_cat")) {							 # 4.
		&mergebase_read;
		&tree;
	} elsif ($mode eq "lf") {								 # 5.1
		&mergebase_read;
		&lf;
	} elsif ($mode eq "sr") {								 # 5.2
		&sr_read;
		&sr;
	} else {																	# 0. スタート画面
		&to_index;
	}

	exit;

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
	$filename = "$folder[$lg]/numeration/".$filename.".num";   ## 今は、こっちに!!!
#	$filename = "$folder[$lg]/set-numeration/".$filename.".num";
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
		<p><INPUT type="submit" value="$tree_button_cat">$tree_instruction1</p>
		<INPUT type="hidden" name="mode" value="tree_cat">
END
	&hidden;
print <<"END";
	</FORM>
END
print <<"END";
	<FORM method="post" action=$self>
		<p><INPUT type="submit" value="$tree_button_id">$tree_instruction1</p>
		<INPUT type="hidden" name="mode" value="tree">
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

sub show_header_java {

##	<meta charset="UTF-8">
##	<link type="text/css" rel="stylesheet" href="vis.min.css" />
##	<link type="text/css" rel="stylesheet" href="syncsem.css" />
##	<meta name="robots" content="index,nofollow">
##	<style type="text/css">
##		#inputs { width: 600px; height: 250px; }
##		textarea {  width: 100%; height: 100%; border: 2px solid lightgray; }
##		#btn {  height: 10%; margin: 10%; }
##		#graph { width: 50%; height: 400px; border: 2px solid lightgray; }
##	</style>

print <<"END";
Content-Type: text/html

<html lang="ja">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<LINK rel="stylesheet" href="./syncsem.css" type="text/css" title="syncsem">
	<title>Graph</title>
	<style type="text/css">
		#inputs { width: 100%; height: 250px; }
		textarea {  width: 100%; height: 100%; border: 2px solid lightgray; }
		#btn {  height: 10%; margin: 10%; }
		#graph { width: 90%; height: 500px;  }
	</style>
	<script type="text/javascript" src="vis.min.js"></script>
</head>

<BODY bgcolor="$cwinback" text="#000000" link="blue" vlink="navy" alink="red">
<A name="top"></a>
<TABLE width="100%">
<TR><TD><IMG src="http://www.gges.xyz/logo-65.gif" height="65" width="65"></TD>
<TD width="99%">
  <TABLE width="100%" bgcolor="$ctitleback" cellpadding="5">
  <TR valign="middle">
    <TD align="left" width="20%" nowrap>
    <FONT color="$ctitleback">......</FONT></TD>
    <TD width="50%" align="middle">
    <TABLE border bgcolor="$ctitlemain" width="100%" cellpadding="10">
      <TR>
        <TH><FONT size=+1>$maintitle</FONT></TH>
    </TABLE>
    </TD>
    <TD align="right" valign="middle" width="30%">
END
	if ($maintitle =~ /$lexicon_list/) { ## lexicon.cgi のときには出さない
	} else {
print <<"END";
			<FORM method="post" action=$self>
				<INPUT type="hidden" name="grammar" value=$lg>
				<INPUT type="hidden" name="mode" value="numeration_select">
				<p><INPUT type="submit" value=" $to_start "></p>
			</FORM>
END
	}
print <<"END";
    </TD>
  </TABLE>
</TD>
</TABLE>
END
}


sub tree {	#		4. TreeDrawer用 の csv ファイル書き出し
	$aref = \@base;
	$json = JSON->new->utf8(0)->encode($aref);
	$json =~ s/"/&#34;/g; # 引用符「"」を実体参照に置き換える

print <<"END";
	<FORM method="post" action=$self>
		<p><span class="memo">[$memo]</span></p>
		<p><INPUT type="submit" value="$to_target"></p>
		<INPUT type="hidden" name="mode" value="target">
END
	&hidden;
print <<"END";
	</FORM>
		<p>$tree_instruction2</p>
	<table width="100%"><tbody>
	<tr>
		<td width="20%">
END
	if ($mode eq 'tree') {
print <<"END";
	<p>$tree_sign</p>
END
	} elsif  ($mode eq 'tree_cat') {
print <<"END";
	<p>$tree_sign_cat</p>
END
	}
print <<"END";
		<textarea rows="15" id="source_csv" placeholder="――CSV形式――&NewLine;番号,子並び,フラグ,ラベル">
END

	if ($mode eq 'tree') {
		&treedrawer_index;
	} elsif  ($mode eq 'tree_cat') {
		&treedrawer_cat;
	}

print <<"END";
		</textarea>
		</td>
			<td rowspan=3 valign="top"><div id="graph"></div></td>
		</tr>
		<tr>
			<td><input id="btn" type="button" value="　変換　" onclick="draw()"></td>
		</tr>
		<tr>
		<td><textarea rows="15" id="converted_dot" placeholder="――DOT言語形式――" readonly disabled></textarea></td>
	</tr></tbody></table>
	
<script type="text/javascript">
function draw(){

// parse
	var csv = document.getElementById("source_csv").value.replace(/<br>/g, "\\\\n").split("\\n");
	var edges = new Array(), flags = new Map(), labels = new Map();
	for(const line of csv) {
		let col = line.split(',');
		if (col.length != 4) continue;
		let node = col[0];
		let edge = col[1].split(' ');
		if (edge != "") for(const e of edge) {
			edges.push([node, e]);
		}
		flags.set(node, col[2]);
		labels.set(node, col[3]);
	}

// convert

	var DOTstring = "graph {";
	for(const [node, label] of labels) {
		DOTstring = DOTstring + node + ' [label="' + label + '"];';
	}
	for(const [node, edge] of edges) {
		DOTstring = DOTstring + node + '--' + edge;
		const flag = flags.get(edge);
		if (flag == "1") {
			DOTstring = DOTstring + ' [color=red]';
		}
		DOTstring = DOTstring + ';';
	}
	DOTstring = DOTstring + '}';

// view
	var dot = document.getElementById("converted_dot");
	dot.value = DOTstring.replace(/;/g, ";\\n");

// generate  <http://visjs.org/docs/network/#importDot>

	var parsedData = vis.network.convertDot(DOTstring);
	var data = {
		nodes: parsedData.nodes,
		edges: parsedData.edges
	}
	var options = parsedData.options;
	options.nodes = {
		shape: 'box',
		color: {
			background: 'white'
		}
	};
	options.edges = {
		color: {
			color: 'black'
		}
	};
	options.layout = {
		hierarchical: {
			direction: "UD",
			sortMethod: "directed",
			levelSeparation: 50,
			nodeSpacing: 180
		}
	};
	options.physics = {
		enabled: false
	};
	options.interaction = {
		dragNodes: true,
		multiselect: true
	};
	// create a network
	var container = document.getElementById('graph');
	var network = new vis.Network(container, data, options);
}

// exec on load
draw();

</script>
</body>
</html>
END



}

sub treedrawer_index {
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
$tree[$tt][0],$tree[$tt][1],$tree[$tt][2],$tree[$tt][3]
END
	}
}

sub treedrawer_cat {
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
$tree[$tt][0],$tree[$tt][1],$tree[$tt][2],$tree[$tt][5]
END
	}

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

##@ Merge の際の素性処理///
##!!! 変数を受け渡して、共通のサブルーチンにするべき？　それとも、かえって面倒？

sub id {
	$mo[$id]=$hb[$id];
	$na[$id]=$nb[$id];
	$ha[$id]=$hb[$id];
}

sub ca {
	$mo[$ca]=$hb[$ca];
	$na[$ca]=$nb[$ca];
	$ha[$ca]=$hb[$ca];
}

sub sl {
## id-slot については、""ではなく、"zero" にしておく。そうすると、意味素性がない、という印になる。
## id-slot が "rel" のときに特別扱いをすること

##1 $hb[$sl] (head 側)

	## 解釈不可能素性が含まれている場合
	if ($hb[$sl] =~ m/,[0-9]/) { 
		@www = split(/,/, $hb[$sl]);
		if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
			&sl_head_lg;

	##2 21  ○
		} elsif ($www[1] eq 21) {
			$mo[$sl] = "2,22";  ## →●
			$ha[$sl] = "zero";
			for ($x=0;$x<=$syncnum[$head];$x++) {
				@wwww = split(/,/, $hb[$sy][$x]);
				if ($wwww[1] eq 60){
				$hb[$sy][$x] = "3,61,$wwww[2],22,$wwww[4]";
				}
			}
	##2 23  ☆
		} elsif ($www[1] eq 23) {
			$mo[$sl] = "0,34";  ## →★
			$ha[$sl] = "zero";
#			for ($x=0;$x<=$syncnum[$head];$x++) {
#				@wwww = split(/,/, $hb[$sy][$x]);
#				if ($wwww[1] eq 62){
#				$hb[$sy][$x] = "3,63,$wwww[2],24,$wwww[4]";
#				}
#			}
	##2 24  ★ old (相手がheadのときのみ成功)
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
	##2 24  ★ (自分がheadのときのみ成功)
		} elsif ($www[1] eq 24) {  
			$mo[$sl] = $nb[$sl];
			$ha[$sl] = "zero";
#			for ($x=0;$x<=$syncnum[$head];$x++) {
#				@wwww = split(/,/, $hb[$sy][$x]);
#				if ($wwww[1] eq 63){
#				$hb[$sy][$x] = "3,59,$wwww[2],$nb[$sl],$wwww[4]";
#				}
#			}
	##2 32  ▲ (自分がheadのときのみ成功)
#		} elsif ($www[1] eq 32) { 
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
#			$mo[$sl] = $nb[$sl];
#			$ha[$sl] = "zero";
#			for ($x=0;$x<=$syncnum[$head];$x++) {
#				@wwww = split(/,/, $hb[$sy][$x]);
#				if ($wwww[1] eq 63){
#				$hb[$sy][$x] = "3,59,$wwww[2],$nb[$sl],$wwww[4]";
#				}
#			}
	##2 26  ★[α]
		} elsif ($www[1] eq 26) {
			if ($rulename[$r][0] eq $www[2]) {
				$mo[$sl]=$nb[$id];
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 27  ★<α>
		} elsif ($www[1] eq 27) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($nb[$sy][$zz] =~ m/,[0-9]/) {
					@nbsy = (split(/,/, $nb[$sy][$zz]));
					if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
						$pos=$zz;
					}
				}
			}
			if ($pos > -1) {
				@nbsy1 = (split(/,/, $nb[$sy][$pos]));
				$nb[$sy][$pos]="";
				$na[$sy][$pos]="";
				$mo[$sy][$pos]="";
				$mo[$sl]=$nbsy1[3];
				$ha[$sl]=$nbsy1[3];  
#				$ha[$sl]="zero";##!!!←なぜにこれではなく？　でも、あえてそうしているみたいなので。。。
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 28  ●<<α>>
		} elsif ($www[1] eq 28) {
			$pos=-1;
			for($yy=0; $yy<=$semnum[$head]; $yy++){
				@headse1 = (split(/:/, $hb[$se][$yy]));  ## attribute と value に分ける
				if ($headse1[0] eq "__") {
					$value=$headse1[1];
					$pos=$yy;
				}
			}
			if ($pos > -1) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 59) && ($nbsy[2] eq $www[2])) {  ## <α, <xn, {<  >}>>
							$nb[$sy][$zz]="";
							$na[$sy][$zz]="";
							$ha[$sl]=$nbsy[3];  
							$newsem = $nbsy[4].":".$value;
							$hb[$se][$pos]=$newsem;
						} else {
							$mo[$sl]=$hb[$sl];
							$ha[$sl]="zero";
						}
					} else {
						$mo[$sl]=$hb[$sl];
						$ha[$sl]="zero";
					}
				}
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 上にリストしていない解釈不可能素性の対処
		} else {
				  ## ここはheadなので
			if (($www[0] eq 3) || ($www[0] eq 2)) {
				$mo[$sl] = $hb[$sl];
				$ha[$sl] = "zero";
 			## slでこれが適用してしまうと困るけど、一応規則として
 			} else {
				$mo[$sl] = "zero";
				$ha[$sl] = $hb[$sl];
			}
		}
  ##2 解釈不可能素性が含まれていない場合
 	} else {
		$mo[$sl] = $hb[$sl];
		$ha[$sl] = "zero";
	}

##1 $nb[$sl] (non-head 側)
	## 解釈不可能素性が含まれている場合
	if ($nb[$sl] =~ m/,[0-9]/) {
		@www = split(/,/, $nb[$sl]);

		if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
			&sl_nonhead_lg;

	##2 21  ○
		} elsif ($www[1] eq 21) {
			$na[$sl] = "2,22";  ## →●
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 60){
				$nb[$sy][$x] = "3,61,$wwww[2],22,$wwww[4]";
				}
			}
	##2 22  ●	
		} elsif ($www[1] eq 22) {
			$na[$sl] = $hb[$id];
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 61){
					$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
				}
			}
	##2 23  ☆
		} elsif ($www[1] eq 26) {
			$na[$sl] = "0,24";  ## →★
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 62){
					$nb[$sy][$x] = "3,63,$wwww[2],24,$wwww[4]";
				}
			}
	##2 24  ★ old（相手がheadのときのみ成功）
#		} elsif ($www[1] eq 24) {
#			$na[$sl] = $hb[$id];
#			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
#				@wwww = split(/,/, $nb[$sy][$x]);
#				if ($wwww[1] eq 63){
#				$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
#				}
#			}
	##2 32  ▲ （自分がheadのときのみ成功）
	##2 25  ★α
		} elsif ($www[1] eq 25) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($hb[$sy][$zz] eq $www[2]) {
					$pos=1;
					$na[$sl] = $hb[$id];
					for ($x=0;$x<=$syncnum[$nonhead];$x++) {
						@wwww = split(/,/, $nb[$sy][$x]);
						if ($wwww[1] eq 64){
						$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
						}
					}
				}
			}
			if ($pos eq -1) {  ##!!! こういう処置がほかの場所でも必要かもしれないのでチェックするべし
				$na[$sl]=$nb[$sl];
			}
	##2 26  ★[α]
		} elsif ($www[1] eq 26) {
			if ($rulename[$r][0] eq $www[2]) {
				$na[$sl]=$nb[$id];
			} else {
				$na[$sl]=$nb[$sl];
			}
	##2 27  ★<α>
		} elsif ($www[1] eq 27) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($hb[$sy][$zz] =~ m/,[0-9]/) {
					@hbsy = (split(/,/, $hb[$sy][$zz]));
					if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
						$pos=$zz;
					}
				}
			}
			if ($pos > -1) {
				@hbsy1 = (split(/,/, $hb[$sy][$pos]));
				$hb[$sy][$pos]="";
				$ha[$sy][$pos]="";
				$mo[$sy][$pos]="";
				$na[$sl]=$hbsy1[3];  
			} else {
				$na[$sl]=$nb[$sl];
			}
	##2 28  ●<<α>>
		} elsif ($www[1] eq 28) {
			$pos=-1;
			for($yy=0; $yy<=$semnum[$nonhead]; $yy++){
				@nonheadse1 = (split(/:/, $nb[$se][$yy]));  ## attribute と value に分ける
				if ($nonheadse1[0] eq "__") {  ## 新たに組み合わせるべき value を得る
					$value=$nonheadse1[1];
					$pos=$yy;
				}
			}
			if ($pos > -1) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 59) && ($hbsy[2] eq $www[2])) {  ## <α, <xn, {<  >}>>
							$hb[$sy][$zz]="";
							$ha[$sy][$zz]="";
							$mo[$sy][$zz]="";
							$na[$sl]=$hbsy[3];  
							$newsem = $hbsy[4].":".$value;
							$nb[$se][$pos]=$newsem;
						} else {
							$na[$sl]=$nb[$sl];
						}
					} else {
						$na[$sl]=$nb[$sl];
					}
				}
			} else {
				$na[$sl]=$nb[$sl];
			}
	##2 34  ★類 （相手がheadのときのみ成功）
		} elsif ($www[1] eq 34) {
				#   #,head,34,α,β,γ,δ	
				#   Mergeしたときに相手の指標になる。α:相手の統語素性,β:素性No.11,12 の $www[3],γ:Merge-rule,δ:自分が右/左。ただし、id-slotならば、相手がhead、意味素性ならば自分がheadのときのみ。
			$pos=0;
			if ($www[2] eq ""){  ## 相手の統語素性
				$pos = $pos+1;
				} else {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($hb[$sy][$zz] eq $www[2]) {
						$pos = $pos+1;
					}
				}
			}
			if ($www[3] eq ""){  ## 素性No.11,12 の $www[2]
				$pos = $pos+1;
				} else {
				##!!!とりあえず、該当表現はないだろうので、今は skip
			}
			if ($www[4] eq ""){  ## Merge-rule
				$pos = $pos+1;
				} else {
				if ($rulename[$r][0] eq $www[4]) {
					$pos = $pos+1;
				}
			}
			if ($www[5] eq ""){  ## 自分(nonhead)が右/左
				$pos = $pos+1;
				} else {
				if (($www[5] eq 'right') && ($nonhead eq $right)) {
					$pos = $pos+1;
				}
				if (($www[5] eq 'left') && ($nonhead eq $left)) {
					$pos = $pos+1;
				}
			}

			if ($pos < 4) {  ## 条件をクリアしていなければ、そのまま
				$na[$sl] = $nb[$sl];
			} else {  ## 条件をクリアしていれば、相手の $id になる
				$na[$sl] = $hb[$id];
			}
		}

	##2 解釈不可能素性が含まれていない場合
	} else {
		$na[$sl]=$nb[$sl];
	}
}

sub sy {	
## やっぱり for-to の中で splice するのは具合が悪いので、最初にmotherに上げておいて消していったほうが楽。
## non-head からのfeatureは push する。push すると、[0] のところに入ってしまうことに注意。

##1 $hb[$sy] （head 側)
	@{$mo[$sy]}=@{$hb[$sy]};## [mo]ther 
	@{$ha[$sy]}=@{$hb[$sy]};## [h]ead [a]fter Merge

	for($z=0; $z<=$syncnum[$head]; $z++){
		if ($hb[$sy][$z] =~ m/,[0-9]/) {   ## commaの後ろに数字が来ていたら解釈不可能素性
			@www = split(/,/, $hb[$sy][$z]);

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
									## ↑なるべくなくしていく方向
				&sy_head_lg;

		##2  1  +V, +A, etc
			} elsif (($www[1] eq 1) && ($nb[$ca] eq $www[2])) {
			 	$ha[$sy][$z]="";
			 	$mo[$sy][$z]="";
		##2  3  ++Pred, etc
			} elsif (($www[1] eq 3) && ($nb[$ca] eq $www[2])) {
			 	$ha[$sy][$z]="";
			 	$mo[$sy][$z]="";
		##2  5  rule1
			} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  6  rule2
			} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  7  -rule(n)
			} elsif (($www[1] eq 7) && ($rulename[$r][0] eq $www[2])) {
				$www[3]=$www[3]-1;
				$ha[$sy][$z]="";
				$mo[$sy][$z]=$www[0].",".$www[1].",".$www[2].",".$www[3];
		##2  11  ga(★), etc.  これは必ず nonhead 側のときしか消えない
		##2  12  ga(+T), etc.
			} elsif (($www[1] eq 12) && ($nb[$ca] eq $www[3])) {
					$ha[$sy][$z]="";
					$mo[$sy][$z]="";
		##2  14  SUFFIX
			} elsif (($www[1] eq 14) && ($rulename[$r][0] eq "RH-Merge")) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  16  PREFIX
			} elsif (($www[1] eq 16) && ($rulename[$r][0] eq "LH-Merge")) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";

		##2  17  ＋α類
			} elsif ($www[1] eq 17) {
				#   #,X,17,α,β,γ,δ,ε	
				#   α:相手の範疇素性,β:相手の統語素性,γ:Merge-rule,δ:自分がright/left, ε:自分がhead/nonhead
				$pos=0;
				if ($www[2] eq ""){  ## 相手の範疇素性
					$pos = $pos+1;
					} else {
					if ($nb[$ca] eq $www[2]) {
						$pos = $pos+1;
					}
				}
				if ($www[3] eq ""){  ## 相手の統語素性
					$pos = $pos+1;
					} else {
					for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
						if ($nb[$sy][$zz] eq $www[3]) {
							$pos = $pos+1;
						}
					}
				}
				if ($www[4] eq ""){  ## Merge-rule
					$pos = $pos+1;
					} else {
					if ($rulename[$r][0] eq $www[4]) {
						$pos = $pos+1;
					}
				}
				if ($www[5] eq ""){  ## 自分がright/left
					$pos = $pos+1;
					} else {
					if (($www[5] eq 'right') && ($head eq $right)) {
						$pos = $pos+1;
					}
					if (($www[5] eq 'left') && ($head eq $left)) {
						$pos = $pos+1;
					}
				}
				if ($www[6] eq ""){  ## 自分がhead/nonhead
					$pos = $pos+1;
					} else {
					if ($www[6] eq 'head') {
						$pos = $pos+1;
					}
				}
				if ($pos < 5) {  ## 条件をクリアしていなければ、そのまま
					if ($www[0] eq '0') {  ## こっちは SB ではないので継承係数が古いままであることに注意
						$mo[$sy][$z] = "";
					} else {
						$ha[$sy][$z]="";
					}
				} else {  ## 条件をクリアしていれば消す
					$ha[$sy][$z]="";
					$mo[$sy][$z]="";
				}

		##2  51  <α, ☆>
			} elsif ($www[1] eq 51) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3,52,".$www[2];  ## <α, ★>
		##2  52  <α, ★>
			} elsif ($www[1] eq 52) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3,53,".$www[2].",".$nb[$id];  ## <α, xn>
		##2  54 <★[Predication], partitioning>
			} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
				$mo[$sy][$z]="3,56,".$nb[$pr][1][0];  ## <xn partitioning>
				$ha[$sy][$z]="";
		##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
			} elsif (($www[1] eq 56) && ($www[2] eq $ha[$pr][1][0])) {
				$mo[$sy][$z]="";
		##2  103  β
			## もともと、Binding という Merge rule だったが、feature の作業なので、こちらへ移動した
			} elsif ($www[1] eq 103) {
				$a = -1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/2,102/) {  ## Bind
						$a=$zz;
					}
				}
				if ($a>0) {
					## binder の意味役割（$derived_a）を得る
					for($zz=1; $zz<=$semnum[$head]; $zz++){
						@headse1 = (split(/:/, $hb[$se][$zz]));  ## attribute と value に分ける
						@vvv = (split(/,/, $headse1[1]));  ## valueのほう
						if ($vvv[1] eq 24) {  ## ★
							$derived_a=$headse1[0];
						} elsif ($vvv[1] eq 25) {  ## ★α
							for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
								if ($nb[$sy][$zzz] eq $vvv[2]) {
									$derived_a=$headse1[0];
								}
							}
						} elsif ($vvv[1] eq 26) {  ## ★[α]
							if ($rulename[$r][0] eq $vvv[2]) {
								$derived_a=$headse1[0];
							}
						}
					}
					$mo[$sy][$z] = "3,103,$www[2],$derived_a,$hb[$id]";  ## βn＝Agent(x1-1)
					$ha[$sy][$z]="";
					for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
						if ($nb[$sy][$zz] =~ /2,102/) {  ## Bind
							$nb[$sy][$zz] = "";
						}
					}
				} else {   ## Merge相手に「Bind」がなければ継承
					$ha[$sy][$z] = "";
				}

		##2 上にリストしていない解釈不可能素性の対処
			} else {
				  ## ここはheadなので
				if ($www[0] >= 2) { 
					$ha[$sy][$z] = "";
	 			} else {
					$mo[$sy][$z] = "";
				}
			}
		##2 解釈不可能素性でない場合
		} else {
			$ha[$sy][$z] = "";
		}
	}

##1 $nb[$sy]（non-head からも mother に行く場合）... japanese2 の場合、J-Merge と property-no
	if ($symode eq 2) {
		@{$mo2[$sy]}=@{$nb[$sy]};
		@{$na[$sy]}=@{$nb[$sy]};
		for($z=0; $z<=$syncnum[$nonhead]; $z++){

	## 解釈不可能素性が含まれている場合
			if ($nb[$sy][$z] =~ m/,[0-9]/) {
				@www = split(/,/, $nb[$sy][$z]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&sy_both_lg;

			##2  1  +V, +A, etc.
				} elsif (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  3  ++Pred, etc.
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  5  rule1
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  6  rule2
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";

			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3,52,".$www[2];  ## <α, ★>
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3,53,".$www[2].",".$nb[$id];  ## <α, xn>
			##2  54 <★[Predication], partitioning>
				} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
					$mo2[$sy][$z]="3,56,".$hb[$pr][1][0];  ## <xn partitioning>
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
					$mo2[$sy][$z]="";
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$mo2[$sy][$z] = "3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					$na[$sy][$z] = "";

			##2 上にリストしていない解釈不可能素性の対処
				} else {
					  ## ここはnon-headなので
					if ($www[0] eq 3) {
						$na[$sy][$z] = "";
		 			} else {
						$mo2[$sy][$z] = "";
					}
				}
			##2 解釈不可能素性でない場合
			} else {
				$na[$sy][$z] = "";
			}
		}
		@{$mo[$sy]}=(@{$mo[$sy]}, @{$mo2[$sy]});

##1 $nb[$sy] （non-head 側)
	} else {
##		@{$mo2[$sy]}=@{$nb[$sy]};
		@{$na[$sy]}=@{$nb[$sy]};## [n]on-head [a]fter Merge
		@mosy=();	## $mo[$sy] に追加する素性の受け皿

		for($z=0; $z<=$syncnum[$nonhead]; $z++){

	## 解釈不可能素性が含まれている場合
			if ($nb[$sy][$z] =~ m/,[0-9]/) {
				@www = split(/,/, $nb[$sy][$z]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&sy_nonhead_lg;

			##2  1  +V, +A, etc.
				} elsif (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  3  ++Pred, etc.
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  5  rule1
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
			##2  6  rule2
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
			##2  11  ga(★), etc.  これは、$se の ★αのところ（と$pr の★のところ）で削除しておくので、ここでは上にあげるだけ
				} elsif ($www[1] eq 11) {
					if ($www[0] eq 4){
						$na[$sy][$z]= "2,".$www[1].",".$www[2];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					}
			##2  12  ga(+T), etc.
				} elsif ($www[1] eq 12) {
					if ($www[0] eq 5){
						$na[$sy][$z]= "4,".$www[1].",".$www[2].",".$www[3];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					} elsif ($hb[$ca] eq $www[3]) {
					 	$na[$sy][$z]="";
					} elsif ($www[0] eq 4){
						$na[$sy][$z]= "2,".$www[1].",".$www[2].",".$www[3];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					} else {
					 	$na[$sy][$z]="$nb[$sy][$z]";
#					 	$na[$sy][$z]="";
					}
			##2  13  suffix
				} elsif (($www[1] eq 13) && ($rulename[$r][0] eq "LH-Merge")) {
				 	$na[$sy][$z]="";
			##2  15  prefix
				} elsif (($www[1] eq 15) && ($rulename[$r][0] eq "RH-Merge")) {
				 	$na[$sy][$z]="";

	##2  17  ＋α類
			} elsif ($www[1] eq 17) {
				#   #,X,17,α,β,γ,δ,ε	
				#   α:相手の範疇素性,β:相手の統語素性,γ:Merge-rule,δ:自分がright/left, ε:自分がhead/nonhead
				$pos=0;
				if ($www[2] eq ""){  ## 相手の範疇素性
					$pos = $pos+1;
					} else {
					if ($hb[$ca] eq $www[2]) {
						$pos = $pos+1;
					}
				}
				if ($www[3] eq ""){  ## 相手の統語素性
					$pos = $pos+1;
					} else {
					for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
						if ($hb[$sy][$zz] eq $www[3]) {
							$pos = $pos+1;
						}
					}
				}
				if ($www[4] eq ""){  ## Merge-rule
					$pos = $pos+1;
					} else {
					if ($rulename[$r][0] eq $www[4]) {
						$pos = $pos+1;
					}
				}
				if ($www[5] eq ""){  ## 自分がright/left
					$pos = $pos+1;
					} else {
						if (($www[5] eq 'right') && ($nonhead eq $right)) {
							$pos = $pos+1;
						}
						if (($www[5] eq 'left') && ($nonhead eq $left)) {
							$pos = $pos+1;
						}
				}
				if ($www[6] eq ""){  ## 自分がhead/nonhead
					$pos = $pos+1;
					} else {
					if ($www[6] eq 'nonhead') {
						$pos = $pos+1;
					}
				}
				if ($pos < 5) {  ## 条件をクリアしていなければ、そのまま
					if ($www[0] eq '3') {  ## こっちは SB ではないので継承係数が古いままであることに注意
						push(@mosy, $na[$sy][$z]);
##						$mo2[$sy][$z] = "3,17,".$www[2].",".$www[3].",".$www[4].",".$www[5].",".$www[6];
						$na[$sy][$z] = "";
					} else {
						$mo[$sy][$z] = "";
					}
				} else {  ## 条件をクリアしていれば消す
					$na[$sy][$z]="";
				}

			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="3,52,".$www[2];  ## <α, ★>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  54 <★[Predication], partitioning>
				} elsif ($www[1] eq 54) {
					if ($prednum[$head] > 0){
						$na[$sy][$z]="3,56,".$hb[$pr][1][0];  ## <xn partitioning>
					}
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$na[$sy][$z] = "3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z] = "";
			##2  101  Kind
				## もともと、Kind-addition という Merge rule だったが、feature の作業なので、こちらへ移動した → se で処理？
				} elsif ($www[1] eq 101) {
					## 意味役割（$derived_a）を得る
					$derived_a="--";
					for($zz=1; $zz<=$semnum[$head]; $zz++){
						@headse1 = (split(/:/, $mo[$se][$zz]));  ## attribute と value に分ける
						@vvv = (split(/,/, $headse1[1]));  ## valueのほう
						if ($headse1[1] eq $na[$id]) {
							$derived_a=$headse1[0];
						}
					}
					if ($derived_a ne "--") {
						$semnum[$nonhead]++;
						$na[$se][$semnum[$nonhead]]="Kind:$derived_a($hb[$id])";
						$na[$sy][$z]="";
					} else {
						push(@mosy, $na[$sy][$z]);
						$na[$sy][$z]="";
					}
			##2 上にリストしていない解釈不可能素性の対処
				} else {
					  ## ここはnon-headなので
					if ($www[0] eq 3) {
						push(@mosy, $na[$sy][$z]);
						$na[$sy][$z] = "";
		 			} else {
					}
				}
			##2 解釈不可能素性でない場合
			} else {
			}
		}
		@{$mo[$sy]}=(@{$mo[$sy]}, @mosy);
 	}
}

sub pr {
	## １つの Pred素性は、3つの指標のリストになっている。
	## $hb[$pr][$z][0] = id
	## $hb[$pr][$z][1] = Subject
	## $hb[$pr][$z][2] = Predicate
	##
	## head側からは一律にmotherへ、non-head側からは daughter のまま。

##1 $mo[$pr]  head 
	@{$mo[$pr]}=@{$hb[$pr]};
	$ha[$pr]="";
	for($z=1; $z<=$prednum[$head]; $z++){

	##2 $mo[$pr][$z][0]  pred-id
		## 解釈不可能素性が含まれている場合
		if ($hb[$pr][$z][0] =~ m/,[0-9]/) { 
			@www = split(/,/, $hb[$pr][$z][0]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_head_i_lg;

		##3 21  ○
			} elsif ($www[1] eq 21) {
				$mo[$pr][$z][0] = "2,22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$pr][$z][0] = "0,24";  ## →★
		##3 24  ★
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
			} elsif ($www[1] eq 24) {
				$mo[$pr][$z][0] = $nb[$id];
		##3 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] eq $www[2]) {
						$mo[$pr][$z][0]=$nb[$id];
					}
				}
		##3 26  ★[α]
			} elsif ($www[1] eq 26) {
				if ($rulename[$r][0] eq $www[2]) {
					$mo[$pr][$z][0]=$nb[$id];
				} else {
					$mo[$pr][$z][0]=$hb[$pr][$z][0];
					$ha[$pr][$z][0]="zero";
				}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$pr][$z][0]=$nbsy1[3];  
				} else {
					$mo[$pr][$z][0]=$hb[$pr][$z][0];  
					$ha[$pr][$z][0]="zero";
				}

		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $mo[$pr][$z][$sp]  Subj, Pred
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($hb[$pr][$z][$sp] =~ m/,[0-9]/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				@www = (split(/,/, $hb[$pr][$z][$sp]));

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_head_s_lg;

		##3 21  ○
				} elsif ($www[1] eq 21) {
					$mo[$pr][$z][$sp]="2,22";  ## →●
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$mo[$pr][$z][$sp] = "0,24";  ## →★
		##3 24  ★
				} elsif ($www[1] eq 24) {
					$mo[$pr][$z][$sp]=$nb[$id];
				## ga(★)が Subject に入るときは、削除していいことにする。
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 11) && ($nbsy[2] eq "ga") && ($sp eq 1)) {
							$nb[$sy][$zz]=""; ## $nb側の feature を消す。sy の処理は、このあとでなければならない。
						}
					}
				}


		##3 25  ★α
				} elsif ($www[1] eq 25) {
					for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
						if ($nb[$sy][$zzz] eq $www[2]) {
							$mo[$pr][$z][$sp]=$nb[$id];
						}
					}
		##3 26  ★[α]
				} elsif ($www[1] eq 26) {
					if ($rulename[$r][0] eq $www[2]) {
						$mo[$pr][$z][$sp]=$nb[$id];
					} else {
						$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];
						$ha[$pr][$z][$sp]="zero";
					}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$pr][$z][$sp]=$nbsy1[3];  
				} else {
					$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
					$ha[$pr][$z][$sp]="zero";
				}
		##3 29  ★α,[β]
				} elsif ($www[1] eq 29) {
					if ($rulename[$r][0] eq $www[3]) {
						if ($nb[$ca] eq $www[2]){
							$mo[$pr][$z][$sp]=$nb[$id];
						} else {
							for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
								@nbsy = (split(/,/, $nb[$sy][$zzz]));
								if (($nb[$sy][$zzz] eq $www[2]) || ($nbsy[2] eq $www[2])) {
									$mo[$pr][$z][$sp]=$nb[$id];
									$nb[$sy][$zzz]="";
								} else {
									$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
									$ha[$pr][$z][$sp]="zero";
								}
							}
						}
					} else {
						$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
						$ha[$pr][$z][$sp]="zero";
					}
		##3 34  ★類 （自分がheadのときのみ成功）
				} elsif ($www[1] eq 34) {
				#   #,head,34,α,β,γ,δ	
				#   Mergeしたときに相手の指標になる。α:相手の統語素性,β:素性No.11,12 の $www[3],γ:Merge-rule,δ:自分が右/左。ただし、id-slotならば、相手がhead、意味素性ならば自分がheadのときのみ。
					$pos=0;
					if ($www[2] eq ""){  ## 相手の統語素性
						$pos = $pos+1;
						} else {
						for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
							if ($nb[$sy][$zz] eq $www[2]) {
								$pos = $pos+1;
							}
						}
					}
					if ($www[3] eq ""){  ## 素性No.11,12 の $www[2]
						$pos = $pos+1;
						} else {
						##!!!とりあえず、該当表現はないだろうので、今は skip
					}
					if ($www[4] eq ""){  ## Merge-rule
						$pos = $pos+1;
						} else {
						if ($rulename[$r][0] eq $www[4]) {
							$pos = $pos+1;
						}
					}
					if ($www[5] eq ""){  ## 自分(nonhead)が右/左
						$pos = $pos+1;
						} else {
						if (($www[5] eq 'right') && ($head eq $right)) {
							$pos = $pos+1;
						}
						if (($www[5] eq 'left') && ($head eq $left)) {
							$pos = $pos+1;
						}
					}

					if ($pos < 4) {  ## 条件をクリアしていなければ、そのまま
						$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];
						$ha[$pr][$z][$sp]="zero";
					} else {  ## 条件をクリアしていれば、相手の $id になる
						$mo[$pr][$z][$sp]=$nb[$id];
					}
		##3 上にリストしていない解釈不可能素性の対処
				}
		##3 解釈不可能素性が含まれていない場合
			}
		}			## Subject が済んだら Predicate へ
	}		## 次の predication素性へ

##1 $na[$pr]  non-head 
	@{$na[$pr]}=@{$nb[$pr]};
	@on=();	## mo にあげる場合には 1 になる。
	for($z=1; $z<=$prednum[$nonhead]; $z++){

	##2 $na[$pr][$z][0]  pred-id
		## 解釈不可能素性が含まれている場合
		if ($nb[$pr][$z][0] =~ m/,[0-9]/) { 
			@www = split(/,/, $nb[$pr][$z][0]);

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&pr_nonhead_i_lg;

		##3 21  ○
			} elsif ($www[1] eq 21) {
				$na[$pr][$z][0] = "2,22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$na[$pr][$z][0] = "0,24";  ## →★
		##3 24  ★
			} elsif ($www[1] eq 24) {
				$na[$pr][$z][0] = $hb[$id];
		##3 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($hb[$sy][$zz] eq $www[2]) {
						$na[$pr][$z][0]=$hb[$id];
					}
				}
		##3 26  ★[α]
			} elsif ($www[1] eq 26) {
				if ($rulename[$r][0] eq $www[2]) {
					$na[$pr][$z][0]=$hb[$id];
				}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@hbsy1 = (split(/,/, $hb[$sy][$pos]));
					$hb[$sy][$pos]="";
					$na[$pr][$z][0]=$hbsy1[3];  
				} else {
					$na[$pr][$z][0]=$nb[$pr][$z][0];  
				}

		##3 34  ★類 （相手がheadのときのみ成功）
				} elsif ($www[1] eq 34) {
				#   #,head,34,α,β,γ,δ	
				#   Mergeしたときに相手の指標になる。α:相手の統語素性,β:素性No.11,12 の $www[3],γ:Merge-rule,δ:自分が右/左。ただし、id-slotならば、相手がhead、意味素性ならば自分がheadのときのみ。
					$pos=0;
					if ($www[2] eq ""){  ## 相手の統語素性
						$pos = $pos+1;
						} else {
						for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
							if ($hb[$sy][$zz] eq $www[2]) {
								$pos = $pos+1;
							}
						}
					}
					if ($www[3] eq ""){  ## 素性No.11,12 の $www[2]
						$pos = $pos+1;
						} else {
						##!!!とりあえず、該当表現はないだろうので、今は skip
					}
					if ($www[4] eq ""){  ## Merge-rule
						$pos = $pos+1;
						} else {
						if ($rulename[$r][0] eq $www[4]) {
							$pos = $pos+1;
						}
					}
					if ($www[5] eq ""){  ## 自分(nonhead)が右/左
						$pos = $pos+1;
						} else {
						if (($www[5] eq 'right') && ($nonhead eq $right)) {
							$pos = $pos+1;
						}
						if (($www[5] eq 'left') && ($nonhead eq $left)) {
							$pos = $pos+1;
						}
					}

					if ($pos < 4) {  ## 条件をクリアしていなければ、そのまま
					} else {  ## 条件をクリアしていれば、相手の $id になる
						$na[$pr][$z][0]=$hb[$id];
					}

		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $na[$pr][$z][$sp] Subject/Predicate
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($nb[$pr][$z][$sp] =~ m/,[0-9]/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				$on[$z]=1;
				@www = (split(/,/, $nb[$pr][$z][$sp]));

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_nonhead_s_lg;

		##3 21  ○
				} elsif ($www[1] eq 21) {
					$na[$pr][$z][$sp]="2,22";  ## →●
		##3 22  ●
				} elsif ($www[1] eq 22) {
					$na[$pr][$z][$sp]=$hb[$id];
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$na[$pr][$z][$sp] = "0,24";  ## →★
		##3 24  ★
				} elsif ($www[1] eq 24) {
					$na[$pr][$z][$sp]=$hb[$id];
		##3 25  ★α
				} elsif ($www[1] eq 25) {
					for($zzz=0; $zzz<=$syncnum[$head]; $zzz++){
						if ($hb[$sy][$zzz] eq $www[2]) {
							$na[$pr][$z][$sp]=$hb[$id];
						}
					}
		##3 26  ★[α]
				} elsif ($www[1] eq 26) {
					if ($rulename[$r][0] eq $www[2]) {
						$na[$pr][$z][$sp]=$hb[$id];
					}
		##3 27  ★<α>
				} elsif ($www[1] eq 27) {
					$pos=-1;
					for($zz=0; $zz<=$syncnum[$head]; $zz++){
						if ($hb[$sy][$zz] =~ m/,[0-9]/) {
							@hbsy = (split(/,/, $hb[$sy][$zz]));
							if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
								$pos=$zz;
							}
						}
					}
					if ($pos > -1) {
						@hbsy1 = (split(/,/, $hb[$sy][$pos]));
						$hb[$sy][$pos]="";
						$na[$pr][$z][$sp]=$hbsy1[3];  
					} else {
						$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
					}
		##3 上にリストしていない解釈不可能素性の対処
				}
		##3 解釈不可能素性が含まれていない場合
			}
		}			## Subject が済んだら Predicate へ
	}		## 次の predication素性へ

	##2 non-head から mother への継承
	for($z=1; $z<=$prednum[$nonhead]; $z++){
		if ($on[$z] > 0) {
			$tempnum = @{$mo[$pr]};
			if ($tempnum < 1) {
				$tempnum = 1;
			}
			$mo[$pr][$tempnum] = $na[$pr][$z];
			$na[$pr][$z]="zero";
		}
	}
}

sub se {
##		$semnum_n = @{$nb[$se]};
##			if ($semnum_n > 0) {
##				$semnum_n = $semnum_n-1;
##			} else {
##				$semnum_n = 0;
##			}
##		$semnum_h = @{$hb[$se]};
##			if ($semnum_h > 0) {
##				$semnum_h = $semnum_h-1;
##			} else {
##				$semnum_h = 0;
##			}

##1 $mo[$se]
	@{$mo[$se]}=@{$hb[$se]};			## [mo]ther 
	$ha[$se]="zero";							 ## [h]ead [a]fter Merge
	for($z=1; $z<=$semnum[$head]; $z++){
		@hbse1 = (split(/:/, $hb[$se][$z]));	## attribute と value に分ける

		## 今のところ、attribute のほうは feature 処理をしていない

		if ($hbse1[1] =~ m/,[0-9]/) {		 ## value のほうに feature が含まれていたら分ける
			@www = (split(/,/, $hbse1[1]));

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&se_head_lg;

		##2 21  ○
			} elsif ($www[1] eq 21) {
				$mo[$se][$z]=$hbse1[0].":2,22";  ## →●
		##2 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$se][$z]=$hbse1[0].":2,24";  ## →★
		##2 24  ★
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
			} elsif ($www[1] eq 24) {
				$mo[$se][$z]=$hbse1[0].":".$nb[$id];
		##2 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] eq $www[2]) {
						$mo[$se][$z]=$hbse1[0].":".$nb[$id];
					}
				}
		##2 70  ●α
			} elsif ($www[1] eq 70) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($hb[$sy][$zz] eq $www[2]) {
						$mo[$se][$z]=$nbse1[0].":".$hb[$id];
					}
				}
		##2 33  ★α
			} elsif ($www[1] eq 33) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 11) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## $nb側の feature を消す。sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nb[$id];   ## ★αを$nb[$id]で置き換える
						}
						if (($nbsy[1] eq 12) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
#							## sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nb[$id];   ## ★αを$nb[$id]で置き換える
						}
					}
				}
#				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
#					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
#						@nbsy = (split(/,/, $nb[$sy][$zz]));
#						if ($nbsy[1] eq 101) {  ## Kind
##							## sy の処理は、このあとでなければならない。
#							for($zz2=1; $zz2<=$semnum[$head]; $zz2++){
#								@headse1 = (split(/:/, $hb[$se][$zz2]));  ## attribute と value に分ける
#								if ($headse1[1] eq $nb[$id]) {
#									$derived_a=$headse1[0];
#								} else {
#									$derived_a="--";
#								}
#							}
#							if ($derived_a ne "--") {
#								$semnum[$nonhead]++;
#								$na[$se][$semnum[$nonhead]]="Kind:$derived_a($hb[$sl])";
#								$nb[$sy][$zz]="";
#							} else {
#								push(@mosy, $na[$sy][$z]);
#								$na[$sy][$z]="";
#							}
#						}
#					}
#				}


		##2 26  ★[α]
			} elsif ($www[1] eq 26) {
				if (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq 'zero-Merge')) {
					$mo[$se][$z]=$hbse1[0].":".$nb[$id];
				} else {
					$mo[$se][$z]=$hb[$se][$z];
				}
#		##2 27  ★<α>
#			} elsif ($www[1] eq 27) {
#				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
#					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
#						@nbsy = (split(/,/, $nb[$sy][$zz]));
#						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
#							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
#							$mo[$se][$z]=$hbse1[0].":".$nbsy[3];
#						}
#					}
#				}
		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$se][$z]=$hbse1[0].":".$nbsy1[3];
				} else {
					$mo[$se][$z]=$hb[$se][$z];  
				}
		##2 71  ●<α>
			} elsif ($www[1] eq 71) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@hbsy1 = (split(/,/, $hb[$sy][$pos]));
					$hb[$sy][$pos]="";
					$mo[$se][$z]=$nbse1[0].":".$hbsy1[3];
				} else {
					$mo[$se][$z]=$nb[$se][$z];  
				}
		##2 29  ★α,[β]
			} elsif ($www[1] eq 29) {
				if (($rulename[$r][0] eq $www[3]) || ($rulename[$r][0] eq 'zero-Merge')) {
					if ($nb[$ca] eq $www[2]){
						$mo[$se][$z]=$hbse1[0].":".$nb[$id];
					} else {
						for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
							@nbsy = (split(/,/, $nb[$sy][$zzz]));
							if (($nb[$sy][$zzz] eq $www[2]) || ($nbsy[2] eq $www[2])) {
								$mo[$se][$z]=$hbse1[0].":".$nb[$id];
							} else {
								$mo[$se][$z]=$hb[$se][$z];  
							}
						}
					}
				} else {
					$mo[$se][$z]=$hb[$se][$z];
				}
		##2 30  α（★<α>）
			} elsif ($www[1] eq 30) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$se][$z]="$hbse1[0]:α($nbsy[3])";
						} else {
							$mo[$se][$z]=$hb[$se][$z];  
						}
					} else {
						$mo[$se][$z]=$hb[$se][$z];  
					}
				}

		##2 34  ★類
		} elsif ($www[1] eq 34) {
				#   #,head,34,α,β,γ,δ	
				#   Mergeしたときに相手の指標になる。α:相手の統語素性,β:素性No.11,12 の $www[3],γ:Merge-rule,δ:自分が右/左。ただし、id-slotならば、相手がhead、意味素性ならば自分がheadのときのみ。
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。

			$pos=0;
			if ($www[2] eq ""){  ## 相手の統語素性
				$pos = $pos+1;
				} else {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] eq $www[2]) {
						$pos = $pos+1;
					}
				}
			}
			if ($www[3] eq ""){  ## 素性No.11,12 の $www[2]
				$pos = $pos+1;
				} else {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/\#,/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 11) && ($nbsy[2] eq $www[3])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$pos = $pos+1;
						}
						if (($nbsy[1] eq 12) && ($nbsy[2] eq $www[3])) {  ## <α, xn>
#							## sy の処理は、このあとでなければならない。
							$pos = $pos+1;
						}
					}
				}
			}
			if ($www[4] eq ""){  ## Merge-rule
				$pos = $pos+1;
				} else {
				if (($rulename[$r][0] eq $www[4]) || ($rulename[$r][0] eq 'zero-Merge')) {
					$pos = $pos+1;
				}
			}
			if ($www[5] eq ""){  ## 自分(head)が右/左
				$pos = $pos+1;
				} else {
				if (($www[5] eq 'right') && ($head eq $right)) {
					$pos = $pos+1;
				}
				if (($www[5] eq 'left') && ($head eq $left)) {
					$pos = $pos+1;
				}
			}

			if ($pos < 4) {  ## 条件をクリアしていなければ、そのまま
				$mo[$se][$z]=$hb[$se][$z];
			} else {  ## 条件をクリアしていれば、相手の $id になる →相手の $sl
				$mo[$se][$z]=$hbse1[0].":".$nb[$sl];
			}

		##2 上にリストしていない解釈不可能素性の対処
			}
	  ##2 解釈不可能素性が含まれていない場合
		}
	}

##1 $na[$se]
	@{$na[$se]}=@{$nb[$se]};
	for($z=1; $z<=$semnum[$nonhead]; $z++){
		@nbse1 = (split(/:/, $nb[$se][$z]));	## attribute と value に分ける

		## 今のところ、attribute のほうは feature 処理をしていない

		if ($nbse1[1] =~ m/,[0-9]/) {		 ## value のほうに feature が含まれていたら分ける
			@www = (split(/,/, $nbse1[1]));

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&se_nonhead_lg;

		##2 22  ●
			} elsif ($www[1] eq 22) {
				$na[$se][$z]=$nbse1[0].":".$hb[$id];

		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@hbsy1 = (split(/,/, $hb[$sy][$pos]));
					$hb[$sy][$pos]="";
					$na[$pr][$z][$sp]=$hbsy1[3];  
				} else {
					$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
				}
		##2 30  α（★<α>）
			} elsif ($www[1] eq 30) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$hb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$na[$se][$z]="$hbse1[0]:α($nbsy[3])";
						} else {
							$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
						}
					} else {
						$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
					}
				}
			}
		}
	}
} 

sub ph {
		$ha[$ph]=$hb[$ph];
		$na[$ph]=$nb[$ph];
}

sub wo {
	if ("ARRAY" eq ref $hb[$wo]) {
		@{$ha[$wo]}=@{$hb[$wo]};
	} else {
		$ha[$wo]=$hb[$wo];
	}
	if ("ARRAY" eq ref $nb[$wo]) {
		@{$na[$wo]}=@{$nb[$wo]};
	} else {
		$na[$wo]=$nb[$wo];
	}
}


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
#		if ($hostnum > 1) {
#			push(@{$sr[$hostobj][$hostlayer]}, $hostattr.":x".$obj."-".$layer);
#		}

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



