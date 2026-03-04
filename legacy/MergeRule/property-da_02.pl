use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... チェックのほうは同じ。

##@ rule 適用可否チェック
sub propertyDa_c {
	if (($base[$left][$ca] eq "N") && ($base[$right][$ca] eq "T") && ($base[$left][$sl] !~ m/,[0-9]/)){   ##含んでいなければ
		for($z=0; $z<=$syncnum[$right]; $z++){
      if ($base[$right][$sy][$z] eq "da") {
					$rule_c[$propertyDa][0] = $left;
					$rule_c[$propertyDa][1] = $right;
	    }
		}
	}
}


sub propertyDa_r {
## right-headed
	@hb = @{$base[$right]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$left]}; ## [n]on-head [b]efore Merge
	$head=$right;
	$nonhead=$left;

	  &id;
	  &ca;
		&pr;
		&sy;
## この for文↓が ver.01 ではコメントアウトされていた。
	for($z=0; $z<=$syncnum[$head]; $z++){
	  if ($ha[$sy][$z] eq "1,105,da") {
     	$ha[$sy][$z]="";
	  }
	}
		
		$ha[$sl]="zero";
		$na[$sl]="zero";
		$mo[$sl]="0,24";

		$ha[$se]="zero";
		$na[$se]="zero";
		@temp = @{$hb[$se]};
		$temp[0] = "zero";
		splice(@temp, 0, 1); ## 0 の位置に null をとるため。
		@{$mo[$se]}=(@{$nb[$se]},@temp);

		&ph;
		&wo;

	$mo[$wo][0] = \@na;
	$mo[$wo][1] = \@ha;

	$base[$right] = \@mo;
	splice(@base, $left, 1);
	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

