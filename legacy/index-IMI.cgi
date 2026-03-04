#!/usr/bin/perl
#use utf8;
#use FindBin;
#use lib "$FindBin::RealBin/My";
#use JSON;
#use Encode;
#use CGI;
#use HTML::Entities;
#require '../../cgi-bin/lib/jcode.pl';
#require '../../cgi-bin/lib/color-project.pl';
#use Encode qw(decode);
#use strict;
#use warnings;
require 'grammar-list.pl'; # 最初のページの選択肢は、このファイルに書き込んでおいて、そのどれをどの順番で提示するかは、あとの &grammar_choose で指定する

##@ 変数のわりあて///
  $self = "syncsemphone.cgi";

  #  $cwinback = '#CCFFCC';
  #  $cwinback = '#DDFFDD';
  #  $cret = '#FFBBBB';
  #  $ctitlemain = '#99CC99';
  #  $ctitleback = '#447744';
  #  $cletter = '#FFFFFF';
  #  $cwinframe = '#BBBBFF';
  #  $cwinframe = '#CCCCFF';
  #  $cwintext = '#EEEEFF';
  #  $cbbsmain = '#447744';
  #  $cbbsback = '#FFDDBB';
  
  $cwinback = '#EEFFEE';
  #$cret = '#FFCCEE';
  $ctitlemain = '#AAAACC';
  $ctitleback = '#BBCCDD';
  $cbbsmain = '#BBDDFF';
  $cbbsback = '#CCEEFF';
  $cwintext = '#FFFFFF';
  $green = '#CCFF99'; # green
  $ctablebox = '#FFFFBB';  # yellow
  $csummary = '#FFDDFF';  # pink

  &show_header;
  &grammar_choose;

  exit;

##@ メイン処理///

sub grammar_choose {# 0. スタート画面
#	Encode::from_to($grammar[$l], 'utf-8', 'sjis' );
#	Encode::from_to($grammarmemo[$l], 'utf-8', 'sjis' );

	

print <<"END";
<FORM method="post" action=$self>
	<div>
	<table width='100%'>
		<tr>
			<td width='100' valign="center" align="center">
				<INPUT type="hidden" name="mode" value="numeration_select">
				<INPUT type="submit" value=" start "></p>
			</td>
			<td bgcolor=$cwintext>
				<p>lexicon/grammar を選んで、start　ボタンをクリックしてください。<br>
				(Choose the lexicon/grammar that you would like to test, and click the 'start' button.)</p>
			</td>
		</tr>
	</table>
	</div>

	<br>
	<TABLE width='100%' border cellpadding=5 bgcolor=$cwintext>
		<TR><TD><p><INPUT type="radio" name="grammar" value=$imi01><strong>$grammar[$imi01]</strong> <span class="memo">$grammarmemo[$imi01]</span></p></TD></TR>
		<TR><TD><p><INPUT type="radio" name="grammar" value=$imi02><strong>$grammar[$imi02]</strong> <span class="memo">$grammarmemo[$imi02]</span></p></TD></TR>
		<TR><TD><p><INPUT type="radio" name="grammar" value=$imi03><strong>$grammar[$imi03]</strong> <span class="memo">$grammarmemo[$imi03]</span></p></TD></TR>
	</TABLE>
</FORM>
END
}

sub show_header {
	$maintitle = "統語意味論デモプログラム（IMI-人文 言語学共同研究用）";
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
    </TD>
  </TABLE>
</TD>
</TABLE>
END
}

