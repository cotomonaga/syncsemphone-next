use utf8;  ## ←*.pl であっても、これがないと文字化けする。

sub Partitioning_c {
		for($z=0; $z<=$syncnum[$check]; $z++){
			@www = split(/,/, $base[$check][$sy][$z]);
			if ($www[1] eq 56) {   ## partitioning
				$rule_c[$Partitioning][$ch] = $check;
			}
		}
}

sub Partitioning_r {
	@hb = @{$base[$check]};
	$head=$check;
	$found=0;

##1-1 domain を見つける ($tgp → $tgpp → $tgd)
	for($zz=0; $zz<=$syncnum[$head]; $zz++){
		@www = split(/,/, $hb[$sy][$zz]);
		if ($www[1] eq 56) {  ## partitioning
			$tgp = $www[2];	##	Predication素性の指標
			$hb[$sy][$zz]="";
		}
	}

	for($zz=0; $zz<=$prednum[$head]; $zz++){
		if ($hb[$pr][$zz][0] eq $tgp) {
			$tgpp = $hb[$pr][$zz][2];	##	Predicate
			if ($tgpp ne $hb[$id]) {	## mo のように、それ自体が Predicate の場合には、ここは skip
				@temp = (split(/-/, $hb[$pr][$zz][2]));	##	Predication 素性の LAYER を増やしておく
				$temp[1]++;
				$hb[$pr][$zz][2]=$temp[0]."-".$temp[1];
##				$found=1;
			}
			if ($tgpp eq $hb[$id]) {	## mo のように、それ自体が Predicate の場合、Subject のLAYER を下げたくないので、１つ上げておく
				@temp = (split(/-/, $hb[$pr][$zz][1]));	
				$temp[1] = $temp[1]-1;
				$hb[$pr][$zz][1]=$temp[0]."-".$temp[1];
				@temp = (split(/-/, $hb[$pr][$zz][0]));	
				$temp[1] = $temp[1]-1;
				$hb[$pr][$zz][0]=$temp[0]."-".$temp[1];
##				$found=1;
			}
		}
	}
##	if ($found < 1) {		## rel の場合
##		$relprednum = @{$hb[$wo][0][$pr]};
##			for($zz=1; $zz<$relprednum; $zz++){
##				if ($hb[$wo][0][$pr][$zz][0] eq $tgp) {
##					$tgpp = $hb[$wo][0][$pr][$zz][2];	##	Predicate
##					@temp = (split(/-/, $hb[$wo][0][$pr][$zz][2]));	##	Predication 素性の LAYER を増やしておく
##					$temp[1]++;
##					$hb[$wo][0][$pr][$zz][2]=$temp[0]."-".$temp[1];
##					$found=1;
##				}
##			}
##	}

	&search_predicate(\@hb);	##	@tgd(=partitioning domain) を見つける

##1-2 配列をほどいて LAYER 番号を増やす
	$tgd1 = \@tgd;
	$tgd2 = JSON->new->encode($tgd1);
	$tgd0 = $tgd2;
	$tgd2 =~ s/"/'/g; ## 引用符「"」を「'」に置き換える
	$tlength=length($tgd2);
	for ($z=0; $z<=$tlength;$z++) {
		$temp3=index($tgd2,"x", $z);
		if ($temp3 > -1){
			$temp4=index($tgd2,"-", $temp3);
			$temp4=$temp4+1;	 ## LAYER番号の始まり位置
			$temp51=index($tgd2,"'", $temp4);
			$temp52=index($tgd2,")", $temp4);
			if (($temp52>0) && ($temp52<$temp51)) {
				$temp5=$temp52;
			} elsif ($temp51 < 0) {	## 解釈後の beta の場合、おそらく、' がない
				$temp5=$temp52;
			} else {
				$temp5=$temp51;
			}
			$temp5=$temp5-$temp4;	## LAYER番号の桁数
			$l=substr($tgd2,$temp4,$temp5);
			$l++;
			$tgd2=substr($tgd2,0,$temp4).$l.substr($tgd2,$temp4+$temp5);
			$z=$temp4;
		}
	}
	$tgd2 =~ s/'/"/g; ## 「'」を引用符「"」に置き換える

##1-3 配列形式に戻す
	$whole1 = \@hb;
	$whole2 = JSON->new->encode($whole1);
	$wlength=length($whole2);
	$temp6=index($whole2,$tgd0);
	$whole2=substr($whole2,0,$temp6).$tgd2.substr($whole2,$temp6+$tlength);

	$partitioned = JSON->new->decode($whole2);
	@{$base[$check]} = @{$partitioned};
#	$basenum = @base;
#	$basenum = $basenum-1;	## 配列の要素の数

}

sub search_predicate {
	my $x = shift;
	@w = @$x;
	if ($w[$id] eq $tgpp){
		@tgd = @w;
		return;
	}
	if ("ARRAY" eq ref $w[$wo]) {  ## non-terminal の場合
		for my $ww (@{$w[$wo]}) { # bodyの中身を一つ一つ処理
			&search_predicate($ww);
		}
	}
}

1;

