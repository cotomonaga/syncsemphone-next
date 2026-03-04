use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.02 ... Theme の場合に加えて、Affectee にも適用する。
## ver.03 ... 格助詞のfeatureが、日本語独自のものから No.11, No.12 に変わったので、それに対応するため。Theme の場合に加えて、Affectee にも適用する。

##@ rule 適用可否チェック
sub sase2_c {
	if (($base[$left][$ca] eq "V") && ($base[$right][$ph] eq "-sase-")) {## Themeであるものが ga の場合
    for($z=1; $z<=$semnum[$left]; $z++){
      if (($base[$left][$se][$z] =~ m/Theme/) && ($base[$left][$se][$z] =~ m/ga/)) {
        $rule_c[$sase2][0] = $left;
        $rule_c[$sase2][1] = $right;
	    }
      if (($base[$left][$se][$z] =~ m/Affectee/) && ($base[$left][$se][$z] =~ m/ga/)) {
        $rule_c[$sase2][0] = $left;
        $rule_c[$sase2][1] = $right;
	    }
		}
	}
}

sub sase2_r {
## left-headed
	$head=$left;
	$nonhead=$right;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	  &id;
	  &ca;
		&pr;

		$mo[$sy] = $hb[$sy];
		$ha[$sy] = "";
		$na[$sy] = "";

		$mo[$sl] = $hb[$sl];
		$ha[$sl] = "zero";
		$na[$sl] = "zero";

		@{$mo[$se]}=@{$hb[$se]};      ## [mo]ther 
		$ha[$se]="zero";               ## [h]ead [a]fter Merge
		$na[$se]="zero";               ## [h]ead [a]fter Merge

	for($z=1; $z<=$semnum[$head]; $z++){
		if ($hb[$se][$z] =~ /Theme:2,33,ga/) {
			$mo[$se][$z]="Theme:2,33,wo";
		}
		if ($hb[$se][$z] =~ /Affectee:2,33,ga/) {
			$mo[$se][$z]="Affectee:2,33,wo";
		}
	}
	push(@{$mo[$se]}, "Causer:2,33,ga");

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

