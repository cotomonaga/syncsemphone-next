use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub zeroMerge_c {
	for($zs=1; $zs<=$semnum[$check]; $zs++){
		@www = split(/,/, $base[$check][$se][$zs]);
		if (($www[1] eq 24) || ($www[1] eq 25) || ($www[1] eq 26) || ($www[1] eq 29)) {
			$rule_c[$zeroMerge][$ch] = $check;
		}
	}
	for($zp=1; $zp<=$prednum[$check]; $zp++){
		@www1 = split(/,/, $base[$check][$pr][$zp][1]);
		@www2 = split(/,/, $base[$check][$pr][$zp][2]);
		if (($www1[1] eq 24) || ($www1[1] eq 25) || ($www1[1] eq 26) || ($www1[1] eq 29) || ($www2[1] eq 24) || ($www2[1] eq 25) || ($www2[1] eq 26) || ($www2[1] eq 29)) {
			$rule_c[$zeroMerge][$ch] = $check;
		}
	}
}

##@ rule 適用

sub zeroMerge_r {
## right-headed

	$cond_s = "";
	for($zs=1; $zs<=$semnum[$check]; $zs++){
		@www = split(/,/, $base[$check][$se][$zs]);
		if (($www[1] eq 25) || ($www[1] eq 29)) {
			$cond_s = $www[2];
			last;
		}
	}
	$cond_p = "";
	for($zp=1; $zp<=$prednum[$check]; $zp++){
		@www1 = split(/,/, $base[$check][$pr][$zp][1]);
		@www2 = split(/,/, $base[$check][$pr][$zp][2]);
		if (($www1[1] eq 25) || ($www1[1] eq 29)) {
			$cond_p = $www1[2];
			last;
		} elsif (($www2[1] eq 25) || ($www2[1] eq 29)) {
			$cond_p = $www2[2];
			last;
		}
	}

	@hb = @{$base[$check]}; ## [h]ead [b]efore Merge

	$nb[$id]="x".$newnum."-1";
	if ($www[1] eq 29) {
		$nb[$ca] = $www[2];
	} else {
		$nb[$ca]="NP";
	}
	$nb[$pr]="";
#	if ($cond_s ne ""){
		$nb[$sy][1]="$cond_s";
#	}
#	if ($cond_p ne ""){
		$nb[$sy][2]="$cond_p";
#	}
	$nb[$sl]="x".$newnum."-1";
	$nb[$se]=();
#	$nb[$wo]="";
	$nb[$ph]="φ";

	$head=$check;
	$nonhead=$basenum+1;

	@{$base[$nonhead]}=@nb;
	$prednum[$nonhead]=0;
	$syncnum[$nonhead]=2;
	$semnum[$nonhead]=0;

	  &id;
	  &ca;
		&pr;
		&sy;  ## 継承は head 中心
		&sl;
		&se;
		&ph;
		&wo;

	$mo[$wo][0] = \@na;   ## left = non-head
	$mo[$wo][1] = \@ha;   ## right = head

	$base[$check] = \@mo;
#	$basenum = @base;
#	$basenum = $basenum-1;  ## 配列の要素の数
	$newnum++;
	splice(@base, $basenum+1, 1);
}

1;

