#!/usr/bin/perl
use utf8;

##@ 変数のわりあて

($id, $ca, $pr, $sy, $sl, $se, $ph, $wo, $nb)=(0..8); ## lexical item/phrase の素性構造

	#	$cwinback = '#CCFFCC';
	#	$cwinback = '#DDFFDD';
	#	$cret = '#FFBBBB';
	#	$ctitlemain = '#99CC99';
	#	$ctitleback = '#447744';
	#	$cletter = '#FFFFFF';
	#	$cwinframe = '#BBBBFF';
	#	$cwinframe = '#CCCCFF';
	#	$cwintext = '#EEEEFF';
	#	$cbbsmain = '#447744';
	#	$cbbsback = '#FFDDBB';
	
  $cwinback = '#EEFFEE';
  ##$cret = '#FFCCEE';
  $ctitlemain = '#AAAACC';
  $ctitleback = '#BBCCDD';
  $cbbsmain = '#BBDDFF';
  $cbbsback = '#CCEEFF';
  $cwintext = '#FFFFFF';
  $green = '#CCFF99'; ## green
  $ctablebox = '#FFFFBB';  ## yellow
  $csummary = '#FFDDFF';  ## pink

sub show_header {
print <<"END";
Content-Type: text/html

<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="robots" content="index,nofollow">
<LINK rel="stylesheet" href="./syncsem.css" type="text/css" title="syncsem">
<title>$maintitle</title>
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

sub read_lexicon {## Lexicon を読み込む
	open(IN,"$lexiconfile");
		@data = <IN>;
	close(IN);

		$i=1;
		foreach $m (@data) {
			$no[$i] = (split(/\t/, $m))[0];
			$entry[$no[$i]] = (split(/\t/, $m))[1];
###			$word[$no[$i]] = (split(/\t/, $m))[2];
###				if ($word[$no[$i]] eq "") {
###					$word[$no[$i]]=$entry[$no[$i]];
###				}
			$phono[$no[$i]] = (split(/\t/, $m))[2];
				if ($phono[$no[$i]] eq "") {
					$phono[$no[$i]]=$entry[$no[$i]];
				}
			$category[$no[$i]] = (split(/\t/, $m))[3];
			$y=4;
			$prednum[$no[$i]] = (split(/\t/, $m))[$y];
#			@x=();
			for($z=1; $z<=$prednum[$no[$i]]; $z++){
				for($zz=0; $zz<=2; $zz++){
					$y=$y+1;
					$pred[$no[$i]][$z][$zz] = (split(/\t/, $m))[$y];
				}
			}
			$y=8;
			($syncnum[$no[$i]]) = (split(/\t/, $m))[$y];
			for($z=1; $z<=$syncnum[$no[$i]]; $z++){
				$y=$y+1;
				$sync[$no[$i]][$z] = (split(/\t/, $m))[$y];
			}
			$y=14;
			($idslot[$no[$i]]) = (split(/\t/, $m))[$y];
			$y=15;
			@x=();
			($semnum[$no[$i]]) = (split(/\t/, $m))[$y];
			for($z=1; $z<=$semnum[$no[$i]]; $z++){
				for($zz=1; $zz<=2; $zz++){
					$y=$y+1;
					$x[$zz] = (split(/\t/, $m))[$y];
				}
				if ($x[2] eq "") {
					$sem[$no[$i]][$z] = "$x[1]:＿";
				} else {
					$sem[$no[$i]][$z] = "$x[1]:$x[2]";
				}
			}
			$y=28;
			($note[$no[$i]]) = (split(/\t/, $m))[$y]; ## Lexicon における備考事項。Numeration 選定以降は無関係
			if ($note[$no[$i]] ne "") {
				$note[$no[$i]] = "[".$note[$no[$i]]."]";
			}
			$i=$i+1;
		}
		$lexnum=$i-1;
}

sub hidden {	## Numeration 決定後（＝1.5 以降）、常に hidden で送る変数
print <<"END";
	<INPUT type="hidden" name="grammar" value=$lg>
	<INPUT type="hidden" name="memo" value="$memo">
	<INPUT type="hidden" name="newnum" value=$newnum>
	<INPUT type="hidden" name="basenum" value=$basenum>
	<INPUT type="hidden" name="history" value="$history">
	<INPUT type="hidden" name="base" value="$json">
END
}

sub show_feature { ## 各 feature をそれぞれの方法で表示する
	($b, $bb, $ww) = @_;

##1-1 pr
	if ($b eq $pr) {
		$fclass = "f".$bb.$b;
	} else {
		$fclass = "f".$b;
	}

##1-2 sl
	if ($b eq $sl) {
		if ($ww eq "zero"){
			$ww="";
		}
		if ($ww eq "rel"){
			$ww="";
		}
	}

##1-3 se
	if ($b eq $se) {
		$attribute = (split(/:/, $ww))[0];	## se の場合、attribute と value に分ける
		utf8::decode($attribute);	## これをしないと文字化けする
		$ww = (split(/:/, $ww))[1];
		utf8::decode($ww);	## これをしないと文字化けする
	}

##1-4 features
	if ($ww =~ m/,[0-9]/) { ## 解釈不可能素性を目立たせる
		@www = split(/,/, $ww);
		if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
			&show_feature_lg;

		} elsif ($www[1] eq 1){
			$ww = "+".$www[2];
			$wfile = "plusCategory";
		} elsif ($www[1] eq 2){
			$ww = $www[2];
			$wfile = "AllwayUp";  
		} elsif ($www[1] eq 3){
			$ww = "++".$www[2];
			$wfile = "plusplusCategory";
		} elsif ($www[1] eq 5){
			$ww = "+".$www[2];
			$wfile = "rule1";  
		} elsif ($www[1] eq 6){
			$ww = "+".$www[2]."/".$www[3];
			$wfile = "rule2";  
		} elsif ($www[1] eq 7){
			$ww = "-".$www[2]."($www[3])";
			$wfile = "noapply";  
		} elsif ($www[1] eq 8){
			$ww = "+".$www[2]."[$www[3]]";
			$wfile = "plusCategoryRule";  
		} elsif ($www[1] eq 9){
			$ww = "+".$www[2]."[$www[3]]"."<sub>$www[4]</sub>";
			$wfile = "plusCategoryRuleHead";  
		} elsif ($www[1] eq 10){
			$ww = "+".$www[2]."<sub>$www[3]</sub>";
			$wfile = "plusCategoryHead";  
		} elsif ($www[1] eq 11){
			$ww = $www[2]."(★)";
			$wfile = "suffixalFunction";
		} elsif ($www[1] eq 12){
			$ww2 = $www[0]-3; #non-head から継承される残り回数
				if ($ww2<0) {
					$ww2=0;
				}
##			$ww = $www[2]."(+".$www[3].")...$ww2";
			$ww = $www[2]."(+".$www[3].")";
			$wfile = "suffixalFunction2";
		} elsif ($www[1] eq 13){
			$ww = "suffix";
			$wfile = "suffixN";
		} elsif ($www[1] eq 14){
			$ww = "SUFFIX";
			$wfile = "suffixH";
		} elsif ($www[1] eq 15){
			$ww = "prefix";
			$wfile = "prefixN";
		} elsif ($www[1] eq 16){
			$ww = "PREFIX";
			$wfile = "prefixH";

	##2 17  ＋α類
		} elsif ($www[1] eq 17){
				#   ＋α類	
				#   #,X,17,α,β,γ,δ	
				#   α:相手の範疇素性,β:相手の統語素性,γ:Merge-rule,δ:自分が右/左
			$ww = "+".$www[2].$www[3]."";
			if ($www[4] ne "") {
				$ww = $ww."<span class='orange'>[".$www[4]."]</span>";
			}
			if ($www[5] ne "") {
				$ww = $ww."<span class='orange'>(".$www[5].")</span>";
			}
			if ($www[6] ne "") {
				$ww = $ww."<span class='orange'>(".$www[6].")</span>";
			}
			$wfile = "17";

		} elsif ($www[1] eq 21){
			$ww = "○";
			$wfile = "whitecircle"; 
		} elsif ($www[1] eq 22){
			$ww = "●";
			$wfile = "blackcircle";
		} elsif ($www[1] eq 23){
			$ww = "☆";
			$wfile = "whitestar";
		} elsif ($www[1] eq 24){
			$ww = "★";
			$wfile = "blackstar";
		} elsif ($www[1] eq 25){
			$ww = "★<sub>$www[2]</sub>";
			$wfile = "blackstara";
		} elsif ($www[1] eq 70){
			$ww = "●<sub>$www[2]</sub>";
			$wfile = "blackstara";
		} elsif ($www[1] eq 26){
			$ww = "★<sub>[$www[2]]</sub>";
			$wfile = "blackrule_a";
		} elsif ($www[1] eq 27){
			$ww = "★<sub>&lt;$www[2]&gt;</sub>";
			$wfile = "blackstar_a";
		} elsif ($www[1] eq 71){
			$ww = "●<sub>&lt;$www[2]&gt;</sub>";
			$wfile = "blackstar_a";
		} elsif ($www[1] eq 28){
			$ww = "●<sub>&lt;&lt;$www[2]&gt;&gt;</sub>";
			$wfile = "target_sl";
		} elsif ($www[1] eq 29){
			$ww = "★<sub>$www[2],[$www[3]]</sub>";
			$wfile = "target";
		} elsif ($www[1] eq 30){
			$ww = "α(★<sub>&lt;$www[2]&gt</sub>);";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 31){
			$ww = "★<sub>&lt;$www[2]&gt;,[$www[3]]</sub>";
			$wfile = "targetRule";
		} elsif ($www[1] eq 32){
			$ww = "▲";
			$wfile = "blacktriangle";
		} elsif ($www[1] eq 33){
			$ww = "★<sub>$www[2]</sub>";
			$wfile = "blackstara";

	##2 34  ★類
		} elsif ($www[1] eq 34){
				#   ★類	
				#   #,head,34,α,β,γ,δ	
				#   Mergeしたときに相手の指標になる。α:相手の統語素性,β:素性No.11,12 の第4要素,γ:Merge-rule,δ:自分が右/左。ただし、id-slotならば、相手がhead、意味素性ならば自分がheadのときのみ。
			$ww = "★<span class='orange'><sub>$www[2]$www[3]</sub></span>";
			if ($www[4] ne "") {
				$ww = $ww."<span class='orange'>[".$www[4]."]</span>";
			}
			if ($www[5] ne "") {
				$ww = $ww."<span class='orange'>(".$www[5].")</span>";
			}
			$wfile = "34";

		} elsif ($www[1] eq 51){
			$ww = "&lt;$www[2], ☆&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 52){
			$ww = "&lt;$www[2], ★&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 53){
			$ww = "&lt;$www[2], $www[3]&gt;";	## <	> はタグだと思われてしまって表示されないので実体参照にする
			$wfile = "ind_xn";
		} elsif (($www[1] eq 54) && ($www[0] eq 3)){
			$ww = "&lt;★<sub>[Predication]</sub>, partitioning&gt;";
			$wfile = "blackstar_predication";
		} elsif (($www[1] eq 54) && ($www[0] eq 2)){
			$ww = "&lt;★<sub>[Rel]</sub>, partitioning&gt;";
			$wfile = "blackstar_rel_predication";
		} elsif ($www[1] eq 56){
			$ww = "&lt;$www[2], partitioning&gt;";	## <	> はタグだと思われてしまって表示されないので実体参照にするべし
			$wfile = "partitioning";
		} elsif ($www[1] eq 58){
			$ww = "&lt;$www[2], ●&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 59){
			$ww = "&lt;$www[2],&lt;$www[3],{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 60){
			$ww = "&lt;$www[2],&lt;○,{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 61){
			$ww = "&lt;$www[2],&lt;●,{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 62){
			$ww = "&lt;$www[2],&lt;☆,{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 63){
			$ww = "&lt;$www[2],&lt;★,{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 64){
			$ww = "&lt;$www[2],&lt;★$www[5],{&lt;$www[4], __&gt;}&gt;&gt;";
			$wfile = "target";
		} elsif ($www[1] eq 101){
			$ww = "Kind";
			$wfile = "Kind";
		} elsif ($www[1] eq 102){
			$ww = "Bind";
			$wfile = "Bind";
		} elsif (($www[1] eq 103) && ($www[3] eq "")) {
			$ww = "β".$www[2]."＝■";
			$wfile = "be-ta";
		} elsif ($www[1] eq 106){
			$ww = "pickup";
			$wfile = "pickup";
		} elsif ($www[1] eq 107){
			$ww = "move";
			$wfile = "107-move";
		} elsif ($ww eq "0=R=0"){	 ## 17  !!! 再考するべし
			$ww = "+R";
			$wfile = "plusR";
		} elsif ($ww eq "0=da=0"){	 ## 18  ←!!! 使ってる？
			$ww = "da";
			$wfile = "da";
		}
		if ($www[1] eq 7){ ## 7 だけは、継承されてほしいが爆弾素性ではないので。
			$ww = "<a href='./features/$wfile.html' target='feature_description'>$ww</a>";
		} else {
			$ww = "<span class='feature'><a href='./features/$wfile.html' class='red' target='feature_description'>$ww</a></span>";
		}
	}
	if (($www[1] eq 103) && ($www[3] ne "")) {	 ## 解釈後のbeta
		$ww = "β".$www[2]."＝$www[3]($www[4])";
	}
	if ($fclass eq "fs$pr") {
		$ww = "Subject: $ww";
	} elsif ($fclass eq "fp$pr") {
		$ww = "Predicate: $ww";
	} elsif ($fclass eq "f$se") {
		$ww = "$attribute: $ww";
	}
print <<"END";
	<span class=$fclass>$ww</span>
END
}



sub get_params {  ## ←CGI.pm を使ったほうがいいのかもしれない
  local($alldata) = @_;
##	%param = ();
  local($data, $key, $val);
  foreach $data (split(/&/, $alldata)) {	#個々のパラメータに分割して
    ($key, $val) = split(/=/, $data);		#さらにパラメータ名と値に分割
    $val =~ tr/+/ /;				#URLエンコードの復元
    $val =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack('C',hex($1))/eg;
    $val =~ s/\t//g;				#タブコードを削除
##    &jcode'convert(*val, 'sjis');		#漢字を統一(jcode.plが必要)
    $param{$key} = $val;
  }
}

sub timeshow {
  local($now, $style) = @_;
  ($sec, $min, $hour, $day, $mon, $year, $wday) = localtime($now);
  if ($style eq 'with_yoobi') {
    local(@wdays) = ('Sun','Mon','Tue','Wed','Thu','Fri','Sat');
    $when = sprintf("%s\/%02d\/%d (%s) %02d:%02d", (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)[$mon], $day, $year+1900, $wdays[$wday], $hour, $min);
  } elsif ($style eq 'year_date_time') {
    $when = sprintf("%s/%02d/%d (%02d:%02d)", (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)[$mon], $day, $year+1900, $hour, $min);
  } elsif ($style eq 'year_only') {
    $when = sprintf("%d", $year+1900);
  } elsif ($style eq 'for_compare') {
    $when = sprintf("%d%02d%02d", $year+1900, $mon+1, $day);
  } elsif ($style eq 'all_number') {
    $when = sprintf("%d.%02d.%02d (%02d:%02d)",$year+1900,$mon+1,$day,$hour,$min);
  } elsif ($style eq 'no_year') {
    $when = sprintf("%s-%02d (%02d:%02d)", (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)[$mon], $day, $hour, $min);
  } elsif ($style eq 'no_date') {
    $when = sprintf("%02d:%02d", $hour, $min); 
  } elsif ($style eq 'no_time') {
    $when = sprintf("%d\/%02d\/%02d", $year+1900, $mon+1, $day);
  } elsif ($style eq 'no_timeUS') {
    $when = sprintf("%s\/%02d\/%d", (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)[$mon], $day, $year+1900);
  } else {
    $when = sprintf("%d.%02d.", $year+1900, $mon+1); 
  }
$when;
}

sub get_logdate {
local($b_update) = @_;
  if ($b_update eq ""){
    $lasttime = "";
  } else {
    $lasttime = (stat($b_update))[9];
  }
$lasttime;
}

