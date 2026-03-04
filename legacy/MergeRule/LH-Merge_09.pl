use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.09 ... 無標の状態＋ deObjectize/PredicationMerge/property-Merge のときには適用しない。

##@ rule 適用可否チェック
sub LHMerge_c {
	$a = 0;
	$b = 0;
	#PredicationMerge の適用条件
  if (($base[$left][$ca] eq "N") && ($base[$right][$ca] ne "J") && ($base[$right][$ca] ne "N") && ($base[$right][$ca] ne "Z")) {
		if ($base[$right][$sl] =~ m/,[0-9]/) { 
			$b=$b+1;
		}
		if ($base[$left][$sl] =~ m/,[0-9]/) { 
			$b=$b+1;
		}
		for($z=1; $z<=$semnum[$right]; $z++){
				if ($base[$right][$se] =~ m/,[0-9]/) { 
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
			$a = $a+1;
		}
	}

	#deObjectize の適用条件
	for($z=0; $z<=$syncnum[$right]; $z++){
		if ($base[$right][$sy][$z] eq "deObjectize") {
			$a=$a+1;
		}
	}

	#property-Merge の適用条件
	if (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {  ## 両方が property記述ならば
			$a=$a+1;
	}

#	if ($a < 1) {
	  $rule_c[$LHMerge][0] = $left;
	  $rule_c[$LHMerge][1] = $right;
#	}
}

sub LHMerge_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;
		&sl;
		&se;  ## この中で消える sy があるので、こちらが先。

		## α追加
		if ($mo[$sl] ne $na[$sl]) {
			$mosenum=@{$mo[$se]};
			if ($mosenum > 0) {
				$mosenum = $mosenum-1;
			} else {
				$mosenum = 0;
			}
			$temp=0;
			for($s=1; $s<=$mosenum; $s++){
				if ($mo[$se][$s] =~ /$nb[$id]/){   ##  含む
					$temp=1;
				}
			}
			for($z=1; $z<=$prednum[$head]; $z++){
				for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
					if ($mo[$pr][$z][$sp] =~ /$nb[$id]/){   ##  含む
						$temp=1;
					}
				}
			}
			if (($temp < 1) && ($na[$sl] eq $nb[$id])) { ## nonhead が object指示表現の場合のみ
				$mosenum++;
				$mo[$se][$mosenum]="α<sub>$newnum</sub>:$nb[$id]";   ##  以前の「Relate」
				$newnum++;
			}
		}

		&sy;  ## 継承は head 中心
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

