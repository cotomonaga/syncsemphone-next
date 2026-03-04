use utf8;  ## ←*.pl であっても、これがないと文字化けする。

# ver.02 ...da の対処はしていない
#						●と nonhead の ●<<target>> が Merge できるようにする

##@ rule 適用可否チェック

sub propertyLH_c {
	if (($base[$left][$sl] =~ m/,[0-9]/) && ($base[$right][$sl] =~ m/,[0-9]/)) {
		$rule_c[$propertyLH][0] = $left;
		$rule_c[$propertyLH][1] = $right;
	}
}

sub propertyLH_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;

		if (($hb[$sl] =~ /,22/) && ($nb[$sl] =~ /,28/)){ ## ●と●<<α>>の場合
			@www = split(/,/, $nb[$sl]);
			$pos=-1;
			for($yy=0; $yy<=$semnum[$nonhead]; $yy++){
				@nonheadse1 = (split(/:/, $nb[$se][$yy]));  ## attribute と value に分ける
				if ($nonheadse1[0] eq "__") {  ## 新たに組み合わせるべき value を得る
					$value=$nonheadse1[1];
					$pos=$yy;
				}
			}
			if ($pos > -1) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 61) && ($hbsy[2] eq $www[2])) {  ## <α, <xn, {<  >}>>
							$hb[$sy][$zz]="";
							$ha[$sy][$zz]="";
							$mo[$sy][$zz]="";
							$na[$sl]="zero";
							$mo[$sl]="2,22";
							$newsem = $hbsy[4].":".$value;
							$nb[$se][$pos]=$newsem;
						} else {
							$na[$sl]=$nb[$sl];
						}
					} else {
						$na[$sl]=$nb[$sl];
					}
				}
			} else {
				$na[$sl]=$nb[$sl];
			}

		} else {
			$ha[$sl]="zero";
			$na[$sl]="zero";
			$mo[$sl]=$hb[$sl];  ## とりあえず、★か☆かは、head に合わせることにする
		}

		&sy;  ## 継承は head 中心
		$ha[$se]="zero";
		$na[$se]="zero";
		@temp = @{$hb[$se]};
		$temp[0] = "zero";
		splice(@temp, 0, 1); ## 0 の位置に null をとるため。
		@{$mo[$se]}=(@{$nb[$se]},@temp);

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

