use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.03 ... Partitioning とか、いろいろ手当をする前のバージョン。T を head としない分析に合わせたもの

##@ rule 適用可否チェック
sub relMerge_c {
	$b=0;
  if (($base[$right][$ca] eq "N") && ($base[$left][$ca] ne "N")) {
		if ($base[$left][$sl] =~ m/,[0-9]/) { 
					$b=$b+1;
		}
		for($z=1; $z<=$semnum[$left]; $z++){
				if ($base[$left][$se] =~ m/,[0-9]/) { 
					$b=$b+1;
				}
		}
		for($z=1; $z<=$prednum[$left]; $z++){
			for($sp=0; $sp<=2; $sp++){
				if ($base[$left][$pr][$z][$sp] =~ m/,[0-9]/) { 
					$b=$b+1;
				}
			}
		}
		if ($b < 1){
		  $rule_c[$relMerge][0] = $left;
		  $rule_c[$relMerge][1] = $right;
		}
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

