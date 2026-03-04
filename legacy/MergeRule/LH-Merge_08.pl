use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.08 ... 無標の状態＋ property-Merge のときには適用しない。

##@ rule 適用可否チェック
sub LHMerge_c {
	if (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {  ## 両方が property記述ならば×
	} else {
	  $rule_c[$LHMerge][0] = $left;
	  $rule_c[$LHMerge][1] = $right;
	}
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

