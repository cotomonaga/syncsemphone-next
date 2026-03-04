use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.06 ... 中国語用。property同士の場合には適用しない。vが左要素だと適用しない。-rule(n) に対応。

##@ rule 適用可否チェック
sub LHMerge_c {
	## -rule(n)については、headになる要素の統語素性のみを確認すればよい。
	$noapply=0;
	for($z=0; $z<=$syncnum[$left]; $z++){
		if ($base[$left][$sy][$z] =~ m/,[0-9]/) {
			@www = split(/,/, $base[$left][$sy][$z]);
			if (($www[1] eq 7) && ($www[2] eq $rulename[$LHMerge][0]) && ($www[3] < 1)){
				$noapply=1;
			}
		}
	}

	if ($noapply eq 1) { ## noapply が 0 でなければ×
	} elsif (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {  ## 両方が property記述ならば×
	} elsif ($base[$left][$ca] eq "v") {  ## v が左要素の場合、LH になれない
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
		if ($mo[$sl] ne $na[$sl] ) {
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
			if ($temp < 1) {
				$mosenum++;
				$mo[$se][$mosenum]="α$newnum:$nb[$id]";   ##  以前の「Relate」
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

