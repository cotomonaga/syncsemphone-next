use utf8;  ## ←*.pl であっても、これがないと文字化けする。

# ver.01 ... da の場合の対処あり

##@ rule 適用可否チェック

sub propertyMerge_c {
    if (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {
	    $rule_c[$propertyMerge][0] = $left;
	    $rule_c[$propertyMerge][1] = $right;
    }
}

sub propertyMerge_r {
## right-headed
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
		$mo[$sl]=$hb[$sl];  ## とりあえず、★か☆かは、head に合わせることにする

		$mo[$pr]="";  ## da が property-Merge したときには Predication素性は無効になるように

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

