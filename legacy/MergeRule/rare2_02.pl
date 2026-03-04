use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... 格助詞のfeatureが、日本語独自のものから No.11, No.12 に変わったので、それに対応するため。

##@ rule 適用可否チェック
sub rare2_c {
	if (($base[$left][$ca] eq "V") && ($base[$right][$ph] eq "-rare-") && ($base[$right][$sl] eq "zero")) {
	  $a=0;
	  $b=0;
    for($z=1; $z<=$semnum[$left]; $z++){
      if ($base[$left][$se][$z] =~ /Agent:2,33,ga/) {
	      $a=1;
	    }
      if ($base[$left][$se][$z] =~ m/wo/) {
	      $b=1;
	    }
		}
	  if ($a+$b > 1) {
        $rule_c[$rare2][0] = $left;
        $rule_c[$rare2][1] = $right;
	  }
	}
}


sub rare2_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;

		$mo[$sy] = $hb[$sy];
		$ha[$sy] = "";
		$na[$sy] = "";

		$mo[$sl] = $hb[$sl];
		$ha[$sl] = "zero";
		$na[$sl] = "zero";

		@{$mo[$se]}=@{$hb[$se]};      ## [mo]ther 
		$ha[$se]="zero";               ## [h]ead [a]fter Merge
		$na[$se]="zero";               ## [h]ead [a]fter Merge

	for($z=1; $z<=$semnum[$head]; $z++){
	  @hbse1 = (split(/:/, $hb[$se][$z]));  ## attribute と value に分ける
		if ($hbse1[1] =~ /2,33,wo/) {
			$hbse1[1]="2,33,ga";
			$mo[$se][$z]=$hbse1[0].":".$hbse1[1];
		}
		if ($hb[$se][$z] =~ /Agent:2,33,ga/) {
			$mo[$se][$z]="";
		}
##  		if ($hb[$se][$z] =~ m/Agent/) {   ## 「させられ」のときなどは、Agent が ni になってしまうので
##  			$mo[$se][$z]="";
##  		}
	}

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

