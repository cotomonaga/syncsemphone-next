use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.01 ... J-Merge や property-Merge が適用する場合には、適用しないようにする

##@ rule 適用可否チェック
sub RHMerge_c {
	if (($base[$left][$ca] eq "N") && ($base[$right][$ca] eq "J")) {  ## JMerge が可能な場合には、Merge はできない

	} elsif (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {  ##  propertyMerge のときにも Mergeはできない
  } else {
	  $rule_c[$RHMerge][0] = $left;
	  $rule_c[$RHMerge][1] = $right;
	}
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

  ## 以前の「Relate」のαを置く
		if ($mo[$sl] ne $na[$sl]) {  ## 条件1：motherの id-slot≠nonhead の id-slot
			$mosenum=@{$mo[$se]};
			if ($mosenum > 0) {
				$mosenum = $mosenum-1;
			} else {
				$mosenum = 0;
			}
			$temp=0; ##                  条件2：mother の意味素性の中に nonhead の $id が含まれていない
			for($s=1; $s<=$mosenum; $s++){
				if ($mo[$se][$s] =~ /$nb[$id]/){   ##  含む
					$temp=1;
				}
			}
			if (($hb[$sl] =~ m/,[0-9]/) || ($nb[$sl] =~ m/,[0-9]/)) {
				$temp=1; ##                条件3：もともと、どちらの id-slot も値が定まっている
			}
			if ($temp < 1){
				$mosenum++;
				$mo[$se][$mosenum]="α<sub>$newnum</sub>:$nb[$id]";
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

