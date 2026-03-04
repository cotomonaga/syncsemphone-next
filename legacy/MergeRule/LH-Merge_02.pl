use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... property-Merge ではなく、T のときにだけ適用する。japanese1 用。

##@ rule 適用可否チェック
sub LHMerge_c {
	if (($base[$left][$sl] =~ m/,/) && ($base[$right][$sl] =~ m/,/)) {  ##  propertyMerge のときにも Mergeはできない
	} elsif ($base[$right][$ca] eq "T") {  ##  T のときは左が head
	  $rule_c[$LHMergeL][0] = $left;
	  $rule_c[$LHMergeL][1] = $right;
	}
}

sub LHMerge_r {
## left-headed
	@hb = @{$base[$left]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$right]}; ## [n]on-head [b]efore Merge
	$head=$left;
	$nonhead=$right;

	  &id;
	  &ca;
		&pr;
		&sy;  ## 継承は head 中心
		&sl;
		&se;
		&ph;
		&wo;

	$mo[$wo][0] = \@ha;   ## right = head
	$mo[$wo][1] = \@na;   ## left = non-head

	$base[$left] = \@mo;
	splice(@base, $right, 1);

	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

