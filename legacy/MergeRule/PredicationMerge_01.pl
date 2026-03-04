use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub PredicationMerge_c {
	$b=0;
  if (($base[$left][$ca] eq "N") && ($base[$right][$ca] ne "J") && ($base[$right][$ca] ne "Z")) {
		if ($base[$right][$sl] =~ m/,[0-9]/) { 
			$b=$b+1;
		}
		if ($base[$left][$sl] =~ m/,[0-9]/) { 
			$b=$b+1;
		}
		for($z=1; $z<=$semnum[$right]; $z++){
				if ($base[$right][$se][$z] =~ m/,[0-9]/) { 
					$b=$b+1;
				}
		}
		for($z=1; $z<=$prednum[$right]; $z++){
			for($sp=0; $sp<=2; $sp++){
				if ($base[$right][$pr][$z][$sp] =~ m/,[0-9]/) { 
					$b=$b+1;
				}
			}
		}
		if ($b < 1){
		  $rule_c[$PredicationMerge][0] = $left;
		  $rule_c[$PredicationMerge][1] = $right;
		}
	}
}

sub PredicationMerge_r {
## right-headed
	@hb = @{$base[$right]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$left]}; ## [n]on-head [b]efore Merge
	$head=$right;
	$nonhead=$left;
	  &id;
	  &ca;
		&pr;
			$reltemp[0] = "x".$newnum."-1";  ## 新番号
			$reltemp[1] = $nb[$id];  ## Subject
			$reltemp[2] = $hb[$id];  ## Predicate
			$monum0 = @{$mo[$pr]};
			if ($monum0 < 1) {
				@{$mo[$pr][1]} = @reltemp;
			} else {
				@{$mo[$pr]} = (@{$mo[$pr]}, \@reltemp);
			}
		$mo[$id] = $reltemp[0];

		## ga(★) が Subject になったときには、消していいことにする。
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 11) && ($nbsy[2] eq "ga")) {
							$nb[$sy][$zz]=""; ## $nb側の feature を消す。sy の処理は、このあとでなければならない。
						}
					}
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

