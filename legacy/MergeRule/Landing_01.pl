use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.1 : 適用条件 ga が T と Mergeするときのみ

##@ rule 適用可否チェック
sub landing_c {
	my $temp1 = \@{$base[$check][$sy]};
	my $temp2 = JSON->new->encode($temp1);
  if (($temp2 =~ m/3,106/) && ($temp2 =~ m/2,2,T/) && ($base[$check][$ca] eq "T")) { ## pickup, ga
	  $rule_c[$landing][$ch] = $check;
	}
}

sub landing_r {
## single, right-headed
	@hb = @{$base[$check]};
	$head=$check;

##	my $syncnum = @{$hb[$sy]};
##      if ($syncnum > 0) {
##        $syncnum = $syncnum-1;
##      } else {
##        $syncnum = 0;
##      }
	for($zz=0; $zz<=$syncnum[$head]; $zz++){
		if ($hb[$sy][$zz] =~ m/3,106/) {  ## pickup
			my $temp1=substr($hb[$sy][$zz], 6);## 「3,106,」のあとの部分
			my $temp2 = JSON->new->decode($temp1);
			@nb = @$temp2;
			splice(@{$hb[$sy]}, $zz, 1);
		}
	}

	$nonhead=$basenum+1;
    $prednum[$nonhead] = @{$nb[$pr]};
      if ($prednum[$nonhead] > 0) {
        $prednum[$nonhead] = $prednum[$nonhead]-1;
      } else {
        $prednum[$nonhead] = 0;
      }
    $syncnum[$nonhead] = @{$nb[$sy]};
      if ($syncnum[$nonhead] > 0) {
        $syncnum[$nonhead] = $syncnum[$nonhead]-1;
      } else {
        $syncnum[$nonhead] = 0;
      }
    $semnum[$nonhead] = @{$nb[$se]};
      if ($semnum[$nonhead] > 0) {
        $semnum[$nonhead] = $semnum[$nonhead]-1;
      } else {
        $semnum[$nonhead] = 0;
      }

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
	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

