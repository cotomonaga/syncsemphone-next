use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##ver.01 ... deObjectize が right 要素

##@ rule 適用可否チェック
sub deObjectize_c {
	if ($base[$left][$sl] !~ m/,[0-9]/) { ##left 要素が id
    for($z=0; $z<=$syncnum[$right]; $z++){
      if ($base[$right][$sy][$z] eq "deObjectize") { 
	      $rule_c[$deObjectize][0] = $left;
	      $rule_c[$deObjectize][1] = $right;
	    }
		}
	}
}


sub deObjectize_r {

## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;
		&sy;  ## どちらからも継承したいかもしれないので、要確認!!!

		$ha[$sl]="zero";
		$na[$sl]="zero";
		$mo[$sl]=$nb[$sl];  ## nonhead(deObjectizer) の指定通り

		$ha[$se]="zero";
		$na[$se]="zero";
		@temp = @{$nb[$se]};
		$temp[0] = "zero";
		splice(@temp, 0, 1); ## 0 の位置に null をとるため。
		@{$mo[$se]}=(@{$hb[$se]},@temp);

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

