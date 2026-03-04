use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.03 ... まったく無標の状態。jpf0 用。

##@ rule 適用可否チェック
sub RHMerge_c {
	  $rule_c[$RHMerge][0] = $left;
	  $rule_c[$RHMerge][1] = $right;
}

sub RHMerge_r {
## right-headed
	$head=$right;
	$nonhead=$left;
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
			if ($nb[$sl] eq "rel") { ## 関係節用
					$temp=1;
			}
			if ($hb[$sl] eq "rel") { ## 関係節用
					$temp=1;
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

	$mo[$wo][0] = \@na;   ## left = non-head
	$mo[$wo][1] = \@ha;   ## right = head

	$base[$right] = \@mo;
	splice(@base, $left, 1);

	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

