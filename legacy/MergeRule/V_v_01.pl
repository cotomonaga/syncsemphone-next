use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック

sub V_v_c {
  if (($base[$left][$ca] eq "V") && ($base[$right][$ca] eq "v")) {
	  $rule_c[$V_v][0] = $left;
	  $rule_c[$V_v][1] = $right;
	}
}

sub V_v_r {
## right-headed
	$head=$right;
	$nonhead=$left;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;

	  $ha[$sl] = "zero";
	  $na[$sl] = "zero";
	  $mo[$sl] = $nb[$sl];

	  $ha[$se] = "zero";
	  $na[$se] = "zero";
	  $mo[$se] = $nb[$se];

		&sy;  ## 継承は head 中心
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

