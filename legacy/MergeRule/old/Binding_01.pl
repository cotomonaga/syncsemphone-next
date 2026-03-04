use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub Binding_c {
	  $a=0;
	  $b=0;
    for($z=0; $z<=$syncnum[$left]; $z++){
      if ($base[$left][$sy][$z] =~ m/2,102/) {
	      $a=1;
	    }
		}
    for($z=0; $z<=$syncnum[$right]; $z++){
      if ($base[$right][$sy][$z] =~ m/3,103/) {
	      $b=1;
	    }
		}
		if ($a+$b > 1) {
			$rule_c[$Binding][0] = $left;
			$rule_c[$Binding][1] = $right;
		}
}

sub Binding_r {
## right-headed
	$head=$right;
	$nonhead=$left;
	@hb = @{$base[$head]}; ## [h]ead [b]efore Merge
	@nb = @{$base[$nonhead]}; ## [n]on-head [b]efore Merge

	## binder の意味役割（$derived_a）を得る
	for($z=1; $z<=$semnum[$head]; $z++){
		@headse1 = (split(/:/, $hb[$se][$z]));  ## attribute と value に分ける
		@www = (split(/,/, $headse1[1]));  ## valueのほう
		if ($www[1] eq 24) {  ## ★
			$derived_a=$headse1[0];
		} elsif ($www[1] eq 25) {  ## ★α
			for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
				if ($nb[$sy][$zz] eq $www[2]) {
					$derived_a=$headse1[0];
				}
			}
		} elsif ($www[1] eq 26) {  ## ★[α]
			if ($rulename[$r][0] eq $www[2]) {
				$derived_a=$headse1[0];
			}
		}
	}
	&id;
	&ca;

##  		<xm, [{..., Bind, α}, <xm,{...}>, body1]>
##  		<xn, [{..., β=■}, <xn,{ ..., <Attribute, ★α>,...}>, body2]>
##  ⇒Binding
##  		<xn, [{..., β=Attribute(xn)}, <xn,{ ..., <Attribute, xm>,...}>, < 
##  			<xm, [{..., α}, <xm,{...}>, body1]>
##  			<xn, [{...}, φ, body2]>
##  		>]>

		&pr;
		&sl;
		&se;
    for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
			if ($nb[$sy][$zz] =~ /2,102/) {  ## Bind
				$nb[$sy][$zz] = "";
			}
		}
    for($z=0; $z<=$syncnum[$head]; $z++){
			if ($hb[$sy][$z] =~ /3,103/) {
				@www = (split(/,/, $hb[$sy][$z]));
				$hb[$sy][$z] = "3,103,$www[2],$derived_a,$hb[$id]";  ## βn＝Agent(x1-1)
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

