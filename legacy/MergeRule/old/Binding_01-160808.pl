use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub Binding_c {
	  $a=0;
	  $b=0;
    for($z=0; $z<=$syncnum[$left]; $z++){
      if ($base[$left][$sy][$z] =~ m/H=Bind=0/) {
	      $a=1;
	    }
		}
    for($z=0; $z<=$syncnum[$right]; $z++){
      if ($base[$right][$sy][$z] =~ m/A=beta/) {
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

      for($z=1; $z<=$semnum[$head]; $z++){
        if ($hb[$se][$z] =~ m/black/) {
	        @headse1 = (split(/:/, $hb[$se][$z]));  ## attribute と value に分ける
  	      if ($hb[$se][$z] =~ m/H=black=0/) {
						$derived_a=$headse1[0];
  	      } else {
	      	  if ($headse1[1] =~ m/=/) {
	      		  @headse2 = (split(/=/, $headse1[1])); ## value のほうに feature が含まれていたら分ける
	  	        $cond = $headse2[2];
	  	        for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
	  	          if ($nb[$sy][$zz] =~ m/$cond/) {
									$derived_a=$headse1[0];
	  	    	    }
	  	        }
     	      }
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
			if ($nb[$sy][$zz] eq "H=Bind=0") {
				$nb[$sy][$zz] = "";
			}
		}
    for($z=0; $z<=$syncnum[$head]; $z++){
			if ($hb[$sy][$z] =~ /A=beta/) {
				$a = (split(/=/, $hb[$sy][$z]))[1];
				$a = substr($a,4);  ## "beta"の次
##				$hb[$sy][$z] = "β".$a."＝".$derived_a."(".$hb[$id].")";
				$hb[$sy][$z] = "beta#".$a."#".$derived_a."(".$hb[$id].")";
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

