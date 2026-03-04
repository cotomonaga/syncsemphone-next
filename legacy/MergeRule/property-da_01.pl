use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## 0=da=0 は使ってる？

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
	$head=$right;
	$nonhead=$left;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;
		$mo[$pr]="";  ## Predication素性は無効
		&sy;
#	for($z=0; $z<=$syncnum[$head]; $z++){
#	  if ($ha[$sy][$z] eq "da") {
#     	$ha[$sy][$z]="";
#	  }
#	}
		
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

