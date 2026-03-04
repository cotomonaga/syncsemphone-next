use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... property-Merge が適用する場合には、適用しない。T のときには RH-Merge は適用しない。japanese1 用。

##@ rule 適用可否チェック
sub RHMerge_c {
	if (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {  ##  propertyMerge のときにも Mergeはできない
	} elsif ($base[$right][$ca] ne "T") {  ##  T のときは左が head
	  $rule_c[$RHMerge][0] = $left;
	  $rule_c[$RHMerge][1] = $right;
	}
}

sub RHMerge_r {
## right-headed
	@hb = @{$base[$right]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$left]}; ## [n]on-head [b]efore Merge
	$head=$right;
	$nonhead=$left;

	  &id;
	  &ca;
		&pr;
		&sy;  ## 継承は head 中心
		&sl;
		&se;
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

