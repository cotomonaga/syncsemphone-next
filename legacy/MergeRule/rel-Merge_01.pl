use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub relMerge_c {
  if (($base[$left][$ca] eq "T") && ($base[$right][$ca] eq "N")) {
	  $rule_c[$relMerge][0] = $left;
	  $rule_c[$relMerge][1] = $right;
	}
}

sub relMerge_r {
## right-headed
	$head=$right;
	$nonhead=$left;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge
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
			$newnum++;
		&sl;
		&se;
			$mosenum=@{$mo[$se]};
			if ($mosenum > 0) {
				$mosenum = $mosenum-1;
			} else {
				$mosenum = 0;
			}
			$mosenum++;
			$mo[$se][$mosenum]="α<sub>$newnum</sub>:$nb[$sl]";   ##  以前の「Relate」
			$newnum++;
		for($z=0; $z<=$syncnum[$head]; $z++){
			if ($hb[$sy][$z] =~ /2,54/) {  ## ★[Rel]
				$hb[$sy][$z]="2,56,$reltemp[0]";
				$ha[$sy][$z]="";
			}
		}
		&sy;  ## 継承は head 中心

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

