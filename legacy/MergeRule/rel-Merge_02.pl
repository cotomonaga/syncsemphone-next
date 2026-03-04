use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... Partitioning とか、いろいろ手当をする前のバージョン

##@ rule 適用可否チェック
sub relMerge_c {
  if (($base[$left][$ca] eq "T") && ($base[$right][$ca] eq "N")) {
	  $rule_c[$relMerge][0] = $left;
	  $rule_c[$relMerge][1] = $right;
	}
}

sub relMerge_r {
## right-headed
	@hb = @{$base[$right]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$left]}; ## [n]on-head [b]efore Merge
	$head=$right;
	$nonhead=$left;
	  &id;
	  &ca;
		&pr;
			$reltemp[0] = "x".$newnum."-1";  ## 新番号
			$reltemp[1] = $hb[$id];  ## Subject
			$reltemp[2] = $nb[$id];  ## Predicate
			$monum0 = @{$mo[$pr]};
			if ($monum0 < 1) {
				@{$mo[$pr][1]} = @reltemp;
			} else {
				@{$mo[$pr]} = (@{$mo[$pr]}, \@reltemp);
			}
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
	$newnum++;
}


1;

