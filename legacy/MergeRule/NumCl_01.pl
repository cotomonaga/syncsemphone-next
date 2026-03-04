use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub NumCl_c {
  if (($base[$left][$ca] eq "Num") && ($base[$right][$ca] eq "Cl")) {
	  $rule_c[$NumCl][0] = $left;
	  $rule_c[$NumCl][1] = $right;
	}
}

sub NumCl_r {
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
	for($z=0; $z<=$syncnum[$head]; $z++){
	  if ($hb[$sy][$z] eq "1,5,NumCl") {
			$hb[$sy][$z]="";
		}
	}
	for($z=0; $z<=$syncnum[$nonhead]; $z++){
	  if ($nb[$sy][$z] eq "1,5,NumCl") {
			$nb[$sy][$z]="";
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

