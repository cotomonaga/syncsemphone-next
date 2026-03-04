#!/usr/bin/perl
use utf8;
##use CGI;
use FindBin;
use lib "$FindBin::RealBin/My";
use JSON;
##use HTML::Entities;
require 'syncsemphone-common.pl';
require "grammar-list.pl";

##@ メインの流れ
  &get_params($ENV{'QUERY_STRING'});
    if (defined $param{'grammar'}) {
      $lg = $param{'grammar'};
			if ($lexicon[$lg] eq "all"){
				$lexiconfile = "lexicon-all.csv";	# Lexicon
			} else {
				$lexiconfile = $folder[$lg]."/".$folder[$lg].".csv";	# Lexicon
			}
			$mergefile = $folder[$lg]."/".$folder[$lg]."R.pl";	#	Merge rules
			require $mergefile;	#	Merge rules の指定
#			for ($r=1;$r<=$mergenum;$r++) {
#				require "MergeRule/$rulename[$r][1].pl";
#			}
			require $instruction[$lg];  ##  画面に表示されるメッセージ
    }

	utf8::decode($grammar[$lg]);	## こうしないと文字化けする
	if (defined $param{'grammar'}){
		$maintitle = "$lexicon_list（$grammar[$lg]）";
	} else {
		$maintitle = "$lexicon_list";
	}
	&show_header;
	&read_lexicon;
	&show_lexicon;
  exit;

sub show_lexicon {
print <<"END";
	$lexiconfile<br>
	<TABLE width='100%' border cellpadding=2 bgcolor=$cwintext>
		<TR>
			<td>No.</td>
			<td>$entry_title</td>
			<td>PF</td>
			<td>$legend2[$ca] $legend2[$pr] <br>$legend2[$sy] $legend2[$sl] $legend2[$se] $legend2[$wo]</td>
			<td align="center">$legend2[$nb]</td>
		</TR>
END
	for($i=1; $i<=$lexnum; $i++){
print <<"END";
		<TR>
			<TD>$no[$i]</TD>
			<TD>$entry[$no[$i]]</TD>
			<TD>$phono[$no[$i]]</TD>
			<TD>
END
		&show_feature($ca, "", $category[$no[$i]]);

#####*1 pr
	for($zz=1; $zz<=$prednum[$no[$i]]; $zz++){
		&show_feature($pr, "i", $pred[$no[$i]][$zz][0]);
		&show_feature($pr, "s", $pred[$no[$i]][$zz][1]);
		&show_feature($pr, "p", $pred[$no[$i]][$zz][2]);
  }

#####*1 sy
	for($zz=0; $zz<=$syncnum[$no[$i]]; $zz++){
		&show_feature($sy, "", $sync[$no[$i]][$zz]);
	}

#####*1 sl
		&show_feature($sl, "", $idslot[$no[$i]]);

#####*1 se
	for($zz=1; $zz<=$semnum[$no[$i]]; $zz++){
		&show_feature($se, "", $sem[$no[$i]][$zz]);
	}

#####*1 wo
	&show_feature($wo, "", $word[$no[$i]]);

print <<"END";
			</TD>
			<TD>
END
#####*1 NB
	&show_feature($nb, "", $note[$no[$i]]);

print <<"END";
			</TD>
		</TR>
END

	}
print <<"END";
	</TABLE>
END
}

