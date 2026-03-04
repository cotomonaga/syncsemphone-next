use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##ver.01 ... deObjective が right 要素

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

## right-headed ... left-headed にするべきかとも思ったが、右の要素がいろいろと身の振り方を決めるだろうので。
	$head=$right;
	$nonhead=$left;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;
		&sy;  ## 継承は head 中心

		$ha[$sl]="zero";
		$na[$sl]="zero";
		$mo[$sl]=$hb[$sl];  ## head の指定通り

		$ha[$se]="zero";
		$na[$se]="zero";
		@temp = @{$hb[$se]};
		$temp[0] = "zero";
		splice(@temp, 0, 1); ## 0 の位置に null をとるため。
		@{$mo[$se]}=(@{$nb[$se]},@temp);

		&ph;
		&wo;

	$mo[$wo][0] = \@na;   ## left = non-head
	$mo[$wo][1] = \@ha;   ## right = head

	$base[$right] = \@mo;
	splice(@base, $left, 1);

	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}

1;

