use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
##  sub sase1_c {
##  	if (($base[$left][$ca] eq "V") && ($base[$right][$ph] eq "-sase-")) {
##      for($z=1; $z<=$semnum[$left]; $z++){
##        if (($base[$left][$se][$z] =~ m/Agent/) && ($base[$left][$se][$z] =~ m/ga/)) {## Agentであるものが ga の場合
##            $rule_c[$sase1][0] = $left;
##            $rule_c[$sase1][1] = $right;
##  			}
##      }
##  	}
##  }

##  sub sase1_c {
##  	if (($base[$left][$ca] eq "V") && ($base[$right][$ph] eq "-sase-")) {
##      for($z=1; $z<=$semnum[$left]; $z++){
##        if ($base[$left][$se][$z] =~ m/Agent/) {  ## Agent が含まれていて、
##  	      $a=1;
##  	    }
##        if ($base[$left][$se][$z] =~ m/ga/) {  ## かつ ga が含まれていればよい
##  	      $b=1;
##  	    }
##      }
##  	  if ($a+$b > 1) {
##          $rule_c[$sase1][0] = $left;
##          $rule_c[$sase1][1] = $right;
##  		}
##  	}
##  }

sub sase1_c {
	if (($base[$left][$ca] eq "V") && ($base[$right][$ph] eq "-sase-")) {
    for($z=1; $z<=$semnum[$left]; $z++){
      if ($base[$left][$se][$z] =~ m/Agent/) {  ## Agent が含まれていればよい
        $rule_c[$sase1][0] = $left;
        $rule_c[$sase1][1] = $right;
	    }
    }
	}
}

sub sase1_r {
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
##  		if ($hb[$se][$z] =~ /Agent:2,25,ga/) {
##  			$mo[$se][$z]="Agent:2,25,ni";
##  		}
		$mo[$se][$z] =~ s/2,25,ga/2,25,ni/g;  ## "★ga"を"★ni"に置き換える
	}
	push(@{$mo[$se]}, "Causer:2,25,ga");

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

