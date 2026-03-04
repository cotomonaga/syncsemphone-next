use utf8;  ## ←*.pl であっても、これがないと文字化けする。

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

##  @rulename ... [0] は画面上に表示される rule名、[1] は version数を含むファイル名、[2] は single Merge か double Merge かの区別。この[0]は、fragmentによって違っていてもよい。ただし、rule名を明記した feature での rule名は、これと同一でなければならない。

	@rulename = (['','',0],
		['NumCl', 'NumCl_01', 2], ## chinese1
		['V_v', 'V_v_01', 2], ## chinese1
		['sase1', 'sase1_01', 2], ## japanese1 japanese2 japanese3 jpf3 jpf4 jpf5 jpf6
		['sase2', 'sase2_01', 2], ## japanese1 jpf3 jpf4 jpf5 jpf6
		['sase2', 'sase2_02', 2], ## japanese2 japanese3
		['rare2', 'rare2_01', 2], ## japanese1 japanese2 japanese3 jpf3 jpf4 jpf5 jpf6
		['rare1', 'rare1_01', 2], ## japanese1 japanese2 japanese3 jpf3 jpf4 jpf5 jpf6
		['property-no', 'property-no_01', 2], ## japanese1 japanese2 japanese3 jpf4 jpf5 jpf6
		['property-da', 'property-da_01', 2], ## japanese2 japanese3 jpf4 jpf5 jpf6
		['property-da', 'property-da_02', 2], ## japanese1
		['J-Merge', 'J-Merge_01', 2], ## japanese2 japanese3 jpf1 jpf2 jpf3 jpf4 jpf5 jpf6
		['P-Merge', 'P-Merge_01', 2], ## japanese1 japanese2 japanese3
		['property-Merge', 'property-Merge_01', 2], ## japanese1 japanese2 japanese3 jpf1 jpf2 jpf3 jpf4 jpf5 jpf6
		['propertyLH', 'property-LH_02', 2], ## chinese1
		['propertyRH', 'property-RH_02', 2], ## chinese1
		['rel-Merge', 'rel-Merge_01', 2], ## japanese2 japanese3
		['rel-Merge', 'rel-Merge_02', 2], ## japanese1
		['RH-Merge', 'RH-Merge_01', 2], ## japanese2 japanese3 jpf1
		['RH-Merge', 'RH-Merge_02', 2], ## japanese1
		['RH-Merge', 'RH-Merge_03', 2], ## jpf0 jpf2 jpf3 jpf5 jpf6
		['RH-Merge', 'RH-Merge_04', 2],
		['RH', 'RH-Merge_05', 2], ## chinese1
		['LH-Merge', 'LH-Merge_02', 2], ## japanese1
		['LH-Merge', 'LH-Merge_03', 2], ## jpf0
		['LH-Merge', 'LH-Merge_04', 2], ## jpf5 jpf6
		['LH-Merge', 'LH-Merge_07', 2], ## japanese3
		['LH', 'LH-Merge_05', 2], ## chinese1
		['Predication-adjuntion', 'Predication-adjunction_01', 1], ## japanese1
		['Pickup', 'Pickup_01', 1], ## japanese1 japanese2 japanese3 jpf5 jpf6
		['Landing', 'Landing_01',1],  ## japanese1 jpf5 jpf6
		['Landing', 'Landing_02',1],  ## japanese2 japanese3
		['zero-Merge', 'zero-Merge_01', 1], ## japanese1, chinese1 japanese2 japanese3 jpf2 jpf3 jpf4 jpf5 jpf6
		['Partitioning', 'Partitioning_01', 1] ## japanese1 japanese2 japanese3
	);

  $mergenum=@rulename-1;  ## Merge 規則の数

## 以下の変数名は、全 fragment を通じて共通にしておくべし。上の@rulenameと順番が一致していること。
  (
		$NumCl, 
		$V_v, 
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
		$PredicationAdjunction, 
		$pickup, 
		$landing, 
		$zeroMerge, 
		$Partitioning
  )
  =(1..$mergenum); 

	@plusf = ('', 'partitioning', 'Subject+partitioning', 'Bind+partitioning', 'Bind', 'target', 'wo', 'ga'); ## [0] が "" なので選択式とか？　でも結局は、$lg ごとに別のサブルーチン
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

sub double_Merge_check {  ## この順番は表示とは無関係。表示は @rulename 順になる。
	&NumCl_c; 
	&V_v_c; 
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
	&PredicationAdjunction_c; 
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
  } elsif ($r eq "$PMerge") {
	  &PMerge_r;
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
  } elsif ($r eq "$propertyMerge") {
	  &propertyMerge_r;
  } elsif ($r eq "$Partitioning") {
	  &Partitioning_r;
  } elsif ($r eq "$NumCl") {
	  &NumCl_r;
  } elsif ($r eq "$V_v") {
	  &V_v_r;
##  } elsif ($r eq "$PredicationAdjunction") {
##		&PredicationAdjunction_r;
##  } elsif ($r eq "$propertyLH") {
##	  &propertyLH_r;
##  } elsif ($r eq "$propertyRH") {
##	  &propertyRH_r;
	}
}

sub sl_head_lg {
}

sub sl_nonhead_lg {
}

sub sy_head_lg {
}

sub sy_both_lg {
}

sub sy_nonhead_lg {
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

}


1;

