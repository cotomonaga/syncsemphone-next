use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## 日本語版

## 新しく rule を作った場合：（language ごとの *r.pl）
##		$mergenum を増やす
##		rule名で rule-numberを登録
##		@rulename に登録
##		@ruletype に登録
##		@ rule適用可否チェック
##		@ rule適用
##		rule の説明の html ファイル
## 新しく素性を作った場合：（synsem.cgi）
##		howto-lexicon.doc への記載
##		@ 素性処理のところへ適宜加える
##		@ 共通サブルーチン
##		sub show_feature
##		feature の説明の html ファイル
##	plus の場合：（language ごとの *r.pl）
##		plus_feature1
##		plus_feature2
##		plus_to_numeration
##		plus の説明の html ファイル

##  @rulename ... [0] は画面上に表示される rule名、[1] は version数を含むファイル名、[2] は single Merge か double Merge かの区別。

	@rulename = (['','',0],
		['RH-Merge', 'RH-Merge_03', 2],
		['LH-Merge', 'LH-Merge_03', 2],
		['zero-Merge', 'zero-Merge_02', 1]
	);

  $mergenum=@rulename-1;  ## Merge 規則の数

  ($RHMerge, $LHMerge, $zeroMerge)=(1..$mergenum); 

	@plusf = ();
#	$plusfnum = @plusf;

sub plus_feature1 {  ## ← lexicon_select
}

sub plus_feature2 {  ## ← numeration_arrange
}

sub plus_to_numeration {
}

sub double_Merge_check {  ## この順番は表示とは無関係。表示は @rulename 順。
	&RHMerge_c;
	&LHMerge_c;
}

sub single_Merge_check {  ## 順番は表示とは無関係。表示は @rulename 順。
	&zeroMerge_c;
}

sub rule_execution {
  if ($r eq "$RHMerge") {
    &RHMerge_r;
  } elsif ($r eq "$zeroMerge") {
	  &zeroMerge_r;
  } elsif ($r eq "$LHMerge") {
	  &LHMerge_r;
	}
}

sub sl_head_lg {
}

sub sl_nonhead_lg {
}

sub sy_head_lg {
		##2  2  ga
			if (($www[1] eq "1L") && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
			} elsif (($www[1] eq "1L") && ($rulename[$r][0] eq "J-Merge")) {	
			## J-Mergeの場合には、ga-movement ではなく継承させる
				$ha[$sy][$z]="";
		##2  3  no
			} elsif (($www[1] eq "2L") && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  4  wo
			} elsif (($www[1] eq "3L") && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
			}
}

sub sy_both_lg {
			##2  2  ga
				if (($www[1] eq "1L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
				} elsif (($www[1] eq "1L") && ($rulename[$r][0] eq "J-Merge")) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
			##2  3  no
				} elsif (($www[1] eq "2L") && (($rulename[$r][0] eq "J-Merge") || ($rulename[$r][0] eq "property-no"))) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
				} elsif (($www[1] eq "2L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  4  wo
				} elsif (($www[1] eq "3L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
				} elsif (($www[1] eq "3L") && ($rulename[$r][0] eq "J-Merge")) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
				}
}

sub sy_nonhead_lg {
			##2  2  ga
				if (($www[1] eq "1L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  3  no
				} elsif (($www[1] eq "2L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  4  wo
				} elsif (($www[1] eq "3L") && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
				}
}

sub pr_head_i_lg {
}

sub pr_head_s_lg {
}

sub pr_nonhead_i_lg {
}

sub pr_nonhead_s_lg {
}

sub se_head_lg {
}

sub se_nonhead_lg {
}

sub show_feature_lg {
## 各言語用に設定された feature の扱いは、こちらで。

		if ($www[1] eq "1L"){
			$ww = "ga";
			$wfile = "ga";
		} elsif ($www[1] eq "2L"){
			$ww = "no";
			$wfile = "no";
		} elsif ($www[1] eq "3L"){
			$ww = "wo";
			$wfile = "wo";
		}
}


##@
1;
