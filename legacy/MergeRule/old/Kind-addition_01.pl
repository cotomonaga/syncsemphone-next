use utf8;  ## ←*.pl であっても、これがないと文字化けする。

##@ rule 適用可否チェック
sub KindAddition_c {
	  $a=0;
    for($z=0; $z<=$syncnum[$left]; $z++){
      if ($base[$left][$sy][$z] =~ m/A=Kind=0/) {
	      $a=1;
	    }
		}
	  if ($a > 0) {
      for($z=1; $z<=$semnum[$right]; $z++){
        if ($base[$right][$se][$z] =~ m/black/) {
  	      if ($base[$right][$se][$z] =~ m/H=black=0/) {
       	    $rule_c[$KindAddition][0] = $left;
       	    $rule_c[$KindAddition][1] = $right;
  	      } else {
	          @rightse1 = (split(/:/, $base[$right][$se][$z]));  ## attribute と value に分ける
	      	  if ($rightse1[1] =~ m/=/) {
	      		  @rightse2 = (split(/=/, $rightse1[1])); ## value のほうに feature が含まれていたら分ける
	  	        $cond = $rightse2[2];
	  	        for($zz=0; $zz<=$syncnum[$left]; $zz++){
	  	          if ($base[$left][$sy][$zz] =~ m/$cond/) {
		        	    $rule_c[$KindAddition][0] = $left;
		        	    $rule_c[$KindAddition][1] = $right;
	  	    	    }
	  	        }
     	      }
    	    }
	  		}
  		}
	  }
}


sub KindAddition_r {
## 追加の property 以外は、普通の Merge
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
		&pr;
		&sl;
		&se;
			$semnum[$nonhead]++;
			$na[$se][$semnum[$nonhead]]="Kind:$derived_a($hb[$sl])";
    for($z=1; $z<=$syncnum[$nonhead]; $z++){
			if ($nb[$sy][$z] eq "A=Kind=0") {
				$nb[$sy][$z] = "";
			}
		}
		&sy;  ## 継承は head 中心
		&wo;

	$mo[$wo][0] = \@na;   ## left = non-head
	$mo[$wo][1] = \@ha;   ## right = head

	$base[$right] = \@mo;
	splice(@base, $left, 1);

	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

