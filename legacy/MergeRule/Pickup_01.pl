use utf8;  ## ←*.pl であっても、これがないと文字化けする。

## ver.01 : Pickup できる要素は１つのみ

##@ rule 適用可否チェック
sub pickup_c {
	my $temp1 = \@{$base[$check][$wo][$ch][$sy]};
	my $temp2 = JSON->new->encode($temp1);
	my $temp3 = \@{$base[$check][$sy]};
	my $temp4 = JSON->new->encode($temp3);
  if (($temp2 =~ m/,[0-9]/) && ($temp4 !~ /3,106/)) {  
  ## daughter の中に素性が残っていること
  ## すでにpickupしていないこと
	  $rule_c[$pickup][$ch] = $check;
	}
}


sub pickup_r {
## single
	@mob = @{$base[$check]};
	@nb = @{$mob[$wo][0]};
	@hb = @{$mob[$wo][1]};
	@moa = @mob;

	my $temp1 = \@nb;
	my $temp2 = JSON->new->encode($temp1);
	my $temp3 = "3,106,".$temp2; ## pickup

	push(@{$moa[$sy]},$temp3);
	$moa[$wo][0] = "zero";

	$base[$check] = \@moa;
	$basenum = @base;
	$basenum = $basenum-1;  ## 配列の要素の数
}


1;

