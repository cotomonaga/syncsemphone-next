use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub PMerge_c {
  if ($base[$right][$ca] eq "P") {
    $rule_c[$PMerge][0] = $left;
    $rule_c[$PMerge][1] = $right;
  }
}

sub PMerge_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge
	  &id;
	  &ca;
		&pr;
		&sl;
		&se;
	  $symode = 2;
			&sy;
			for($z=0; $z<=$syncnum[$nonhead]; $z++){
			  if ($nb[$sy][$z] eq "1,5,P-Merge") {
		     	$na[$sy][$z]="";
				}
			}
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

