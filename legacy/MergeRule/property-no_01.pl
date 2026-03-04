use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub propertyNo_c {
	if (($base[$left][$ca] eq "N") && ($base[$left][$sl] !~ m/,[0-9]/)) {
	  $a=0;
	  $b=0;
    for($z=0; $z<=$syncnum[$right]; $z++){
      if ($base[$right][$sy][$z] =~ m/1,1,N/) {  ## +N  名詞用法のノを排除するため
	      $a=1;
	    }
      if ($base[$right][$sy][$z] =~ m/2,3,N/) {  ## no
	      $b=1;
	    }
		}
	  if ($a+$b > 1) {
	      $rule_c[$propertyNo][0] = $left;
	      $rule_c[$propertyNo][1] = $right;
	  }
	}
}


sub propertyNo_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;
	  $symode = 2;
			&sy;
## japanese1 では、次のfor 文が含まれていないバージョンを使っていたが、現時点では区別していない。
			for($z=0; $z<=$syncnum[$nonhead]; $z++){
			  if ($nb[$sy][$z] =~ /1,5,J-Merge/) {
		     	$na[$sy][$z]="";
				}
			}
		$ha[$sl]="zero";
		$na[$sl]="zero";
		$mo[$sl]="0,24";

		&se;
		&ph;
		&wo;

	$mo[$wo][0] = \@ha;   ## left = head
	$mo[$wo][1] = \@na;   ## right = non-head

	$base[$left] = \@mo;
	splice(@base, $right, 1);
	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}

1;

