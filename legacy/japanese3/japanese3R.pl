use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## 日本語版

##  @rulename ... [0] は画面上に表示される rule名、[1] は version数を含むファイル名、[2] は single Merge か double Merge かの区別。

	@rulename = (['','',0],
		['sase1', 'sase1_01', 2],
		['sase2', 'sase2_02', 2],
		['rare2', 'rare2_01', 2],
		['rare1', 'rare1_01', 2],
		['property-no', 'property-no_01', 2],
		['property-da', 'property-da_01', 2],
		['J-Merge', 'J-Merge_01', 2],
		['P-Merge', 'P-Merge_01', 2],
		['property-Merge', 'property-Merge_01', 2],
		['rel-Merge', 'rel-Merge_01', 2],
		['RH-Merge', 'RH-Merge_01', 2],
		['LH-Merge', 'LH-Merge_07', 2], ## japanese3
		['Pickup', 'Pickup_01', 1],
		['Landing', 'Landing_02',1], 
		['zero-Merge', 'zero-Merge_01', 1],
		['Partitioning', 'Partitioning_01', 1]
	);

  $mergenum=@rulename-1;  ## Merge 規則の数

  (
  	$sase1, 
  	$sase2, 
  	$rare2, 
  	$rare1, 
  	$propertyNo, 
  	$propertyDa, 
  	$JMerge, 
  	$PMerge, 
  	$propertyMerge, 
  	$relMerge, 
  	$RHMerge, 
  	$LHMerge, 
  	$pickup, 
  	$landing, 
  	$zeroMerge, 
  	$Partitioning
  )=(1..$mergenum); 

	@plusf = ('', 'target', 'basis', 'partitioning', 'rel-partitioning', 'Bind+partitioning', 'Bind', 'wo', 'ga'); ## [0] が "" なので選択式とか？　でも結局は、$lg ごとに別のサブルーチン
	$plusfnum = @plusf;

sub plus_feature1 {  ## ← lexicon_select
	if ($idslot[$no[$x]] eq "id") { ## OBJECT指示表現の場合、target を持ちうる
print <<"END";
		<span class="plus">
		<SELECT NAME="plus$i">
END
		for($ff=0; $ff<$plusfnum; $ff++){
print <<"END";
		<option VALUE=$plusf[$ff]>$plusf[$ff]
END
		}
print <<"END";
		</SELECT></span>
END
	}
##  	if ($prednum[$no[$x]] > 0) {
##  print <<"END";
##  		<span class="plus">
##  		<SELECT NAME="plus$i">
##  		<option VALUE="">
##  		</SELECT></span>
##  END
##  	}
}

sub plus_feature2 {  ## ← numeration_arrange
	if ($idslot[$no[$i]] eq "id") { ## OBJECT指示表現の場合、target を持ちうる
print <<"END";
		<span class="plus"> 
		<SELECT NAME="plus$i">
END
		for($ff=0; $ff<$plusfnum; $ff++){
			if ($plus[$i] eq $plusf[$ff]) {
				$checked[$ff] = "SELECTED";
			} else {
				$checked[$ff] = "";
			}
print <<"END";
		<option $checked[$ff] VALUE=$plusf[$ff]>$plusf[$ff]
END
		}
print <<"END";
		</SELECT></span>
END
	}
##  	if ($prednum[$no[$i]] > 0) {
##  print <<"END";
##  		<span class="plus">$plus[$i] 
##  		<SELECT NAME="plus$i">
##  		<option VALUE="">
##  		</SELECT></span>
##  END
##  	}
}

sub plus_to_numeration {
##1 target
	if ($plus[$j] eq "target") {
		$a="3,53,target,x$j-1";   ## <target, x$j-1>
		push(@{$base[$j][$sy]}, $a);
		&show_feature($sy, "", $a);
##1 basis
	} elsif ($plus[$j] eq "basis") {
		$a="3,53,basis,x$j-1";   ## <basis, x$j-1>
		push(@{$base[$j][$sy]}, $a);
		&show_feature($sy, "", $a);
##1 partitioning
	} elsif ($plus[$j] eq "partitioning") {  ## wide scope になるやつ
		$a="3,54,";   ## <★[Predication], partitioning>
		push(@{$base[$j][$sy]}, $a);
		&show_feature($sy, "", "3,54,");
##1 rel-partitioning
	} elsif ($plus[$j] eq "rel-partitioning") {  ## rel clause 内部の partitioning
		push(@{$base[$j][$sy]}, "2,54"); ## <★[Rel], partitioning>
		&show_feature($sy, "", "2,54");
##1 Bind+partitioning
	} elsif ($plus[$j] eq "Bind+partitioning") {
		push(@{$base[$j][$sy]}, "3,54");  ## <★[Predication], partitioning>
		&show_feature($sy, "", "3,54");
		push(@{$base[$j][$sy]}, "2,102");  ## Bind
		&show_feature($sy, "", "2,102");
##1 Bind
	} elsif ($plus[$j] eq "Bind") {
		push(@{$base[$j][$sy]}, "2,102");
		&show_feature($sy, "", "2,102");
	} else {
##1 その他 そのまま、単に加えればいいもの
		push(@{$base[$j][$sy]}, $plus[$j]);
		&show_feature($sy, "", $plus[$j]);
	}
}

sub double_Merge_check {  ## この順番は表示とは無関係。表示は @rulename 順。
	&sase1_c;
	&sase2_c;
	&rare2_c;
	&rare1_c;
	&propertyNo_c;
	&propertyDa_c;
	&JMerge_c;
	&PMerge_c;
	&propertyMerge_c;
	&relMerge_c;
	&RHMerge_c;
	&LHMerge_c;
}

sub single_Merge_check {  ## 順番は表示とは無関係。表示は @rulename 順。
	&pickup_c;
	&landing_c;
	&zeroMerge_c;
	&Partitioning_c;
}

sub rule_execution {
  if ($r eq "$RHMerge") {
    &RHMerge_r;
  } elsif ($r eq "$LHMerge") {
	  &LHMerge_r;
  } elsif ($r eq "$JMerge") {
	  &JMerge_r;
  } elsif ($r eq "$propertyNo") {
	  &propertyNo_r;
  } elsif ($r eq "$propertyDa") {
	  &propertyDa_r;
  } elsif ($r eq "$relMerge") {
	  &relMerge_r;
  } elsif ($r eq "$zeroMerge") {
	  &zeroMerge_r;
  } elsif ($r eq "$pickup") {
	  &pickup_r;
  } elsif ($r eq "$landing") {
	  &landing_r;
  } elsif ($r eq "$sase1") {
	  &sase1_r;
  } elsif ($r eq "$sase2") {
	  &sase2_r;
  } elsif ($r eq "$rare2") {
	  &rare2_r;
  } elsif ($r eq "$rare1") {
	  &rare1_r;
  } elsif ($r eq "$PMerge") {
	  &PMerge_r;
  } elsif ($r eq "$propertyMerge") {
	  &propertyMerge_r;
  } elsif ($r eq "$Partitioning") {
	  &Partitioning_r;
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

1;

