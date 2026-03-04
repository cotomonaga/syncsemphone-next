#!/usr/bin/perl
use utf8;

##@ Merge の際の素性処理///
##!!! 変数を受け渡して、共通のサブルーチンにするべき？　それとも、かえって面倒？

sub id {
	$mo[$id]=$hb[$id];
	$na[$id]=$nb[$id];
	$ha[$id]=$hb[$id];
}

sub ca {
	$mo[$ca]=$hb[$ca];
	$na[$ca]=$nb[$ca];
	$ha[$ca]=$hb[$ca];
}

sub sl {
## id-slot については、""ではなく、"zero" にしておく。そうすると、意味素性がない、という印になる。

##1 $hb[$sl] (head 側)

	## 解釈不可能素性が含まれている場合
	if ($hb[$sl] =~ m/,[0-9]/) { 
		@www = split(/,/, $hb[$sl]);
		if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
			&sl_head_lg;

	##2 21  ○
		} elsif ($www[1] eq 21) {
			$mo[$sl] = "2,22";  ## →●
			$ha[$sl] = "zero";
			for ($x=0;$x<=$syncnum[$head];$x++) {
				@wwww = split(/,/, $hb[$sy][$x]);
				if ($wwww[1] eq 60){
				$hb[$sy][$x] = "3,61,$wwww[2],22,$wwww[4]";
				}
			}
	##2 23  ☆
		} elsif ($www[1] eq 23) {
			$mo[$sl] = "0,24";  ## →★
			$ha[$sl] = "zero";
			for ($x=0;$x<=$syncnum[$head];$x++) {
				@wwww = split(/,/, $hb[$sy][$x]);
				if ($wwww[1] eq 62){
				$hb[$sy][$x] = "3,63,$wwww[2],24,$wwww[4]";
				}
			}
	##2 24  ★ (相手がheadのときのみ成功)
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
#		} elsif ($www[1] eq 24) {  
#			$mo[$sl] = $hb[$sl];
#			$na[$sl] = "zero";
#			for ($x=0;$x<=$syncnum[$head];$x++) {
#				@wwww = split(/,/, $hb[$sy][$x]);
#				if ($wwww[1] eq 63){
#				$hb[$sy][$x] = "3,59,$wwww[2],$nb[$sl],$wwww[4]";
#				}
#			}
	##2 32  ▲ (自分がheadのときのみ成功)
		} elsif ($www[1] eq 32) { 
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
			$mo[$sl] = $nb[$sl];
			$ha[$sl] = "zero";
			for ($x=0;$x<=$syncnum[$head];$x++) {
				@wwww = split(/,/, $hb[$sy][$x]);
				if ($wwww[1] eq 63){
				$hb[$sy][$x] = "3,59,$wwww[2],$nb[$sl],$wwww[4]";
				}
			}
	##2 26  ★[α]
		} elsif ($www[1] eq 26) {
			if ($rulename[$r][0] eq $www[2]) {
				$mo[$sl]=$nb[$id];
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 27  ★<α>
		} elsif ($www[1] eq 27) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($nb[$sy][$zz] =~ m/,[0-9]/) {
					@nbsy = (split(/,/, $nb[$sy][$zz]));
					if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
						$pos=$zz;
					}
				}
			}
			if ($pos > -1) {
				@nbsy1 = (split(/,/, $nb[$sy][$pos]));
				$nb[$sy][$pos]="";
				$na[$sy][$pos]="";
				$mo[$sy][$pos]="";
				$mo[$sl]=$nbsy1[3];
				$ha[$sl]=$nbsy1[3];  
#				$ha[$sl]="zero";##!!!←なぜにこれではなく？　でも、あえてそうしているみたいなので。。。
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 28  ●<<α>>
		} elsif ($www[1] eq 28) {
			$pos=-1;
			for($yy=0; $yy<=$semnum[$head]; $yy++){
				@headse1 = (split(/:/, $hb[$se][$yy]));  ## attribute と value に分ける
				if ($headse1[0] eq "__") {
					$value=$headse1[1];
					$pos=$yy;
				}
			}
			if ($pos > -1) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 59) && ($nbsy[2] eq $www[2])) {  ## <α, <xn, {<  >}>>
							$nb[$sy][$zz]="";
							$na[$sy][$zz]="";
							$ha[$sl]=$nbsy[3];  
							$newsem = $nbsy[4].":".$value;
							$hb[$se][$pos]=$newsem;
						} else {
							$mo[$sl]=$hb[$sl];
							$ha[$sl]="zero";
						}
					} else {
						$mo[$sl]=$hb[$sl];
						$ha[$sl]="zero";
					}
				}
			} else {
				$mo[$sl]=$hb[$sl];
				$ha[$sl]="zero";
			}
	##2 上にリストしていない解釈不可能素性の対処
		} else {
				  ## ここはheadなので
			if (($www[0] eq 3) || ($www[0] eq 2)) {
				$mo[$sl] = $hb[$sl];
				$ha[$sl] = "zero";
 			## slでこれが適用してしまうと困るけど、一応規則として
 			} else {
				$mo[$sl] = "zero";
				$ha[$sl] = $hb[$sl];
			}
		}
  ##2 解釈不可能素性が含まれていない場合
 	} else {
		$mo[$sl] = $hb[$sl];
		$ha[$sl] = "zero";
	}

##1 $nb[$sl] (non-head 側)
	## 解釈不可能素性が含まれている場合
	if ($nb[$sl] =~ m/,[0-9]/) {
		@www = split(/,/, $nb[$sl]);

		if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
			&sl_nonhead_lg;

	##2 21  ○
		} elsif ($www[1] eq 21) {
			$na[$sl] = "2,22";  ## →●
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 60){
				$nb[$sy][$x] = "3,61,$wwww[2],22,$wwww[4]";
				}
			}
	##2 22  ●	
		} elsif ($www[1] eq 22) {
			$na[$sl] = $hb[$id];
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 61){
					$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
				}
			}
	##2 23  ☆
		} elsif ($www[1] eq 26) {
			$na[$sl] = "0,24";  ## →★
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 62){
					$nb[$sy][$x] = "3,63,$wwww[2],24,$wwww[4]";
				}
			}
	##2 24  ★ （相手がheadのときのみ成功）
		} elsif ($www[1] eq 24) {
			$na[$sl] = $hb[$id];
			for ($x=0;$x<=$syncnum[$nonhead];$x++) {
				@wwww = split(/,/, $nb[$sy][$x]);
				if ($wwww[1] eq 63){
				$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
				}
			}
	##2 32  ▲ （自分がheadのときのみ成功）
	##2 25  ★α
		} elsif ($www[1] eq 25) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($hb[$sy][$zz] eq $www[2]) {
					$pos=1;
					$na[$sl] = $hb[$id];
					for ($x=0;$x<=$syncnum[$nonhead];$x++) {
						@wwww = split(/,/, $nb[$sy][$x]);
						if ($wwww[1] eq 64){
						$nb[$sy][$x] = "3,59,$wwww[2],$hb[$id],$wwww[4]";
						}
					}
				}
			}
			if ($pos eq -1) {  ##!!! こういう処置がほかの場所でも必要かもしれないのでチェックするべし
				$na[$sl]=$nb[$sl];
			}
	##2 26  ★[α]
		} elsif ($www[1] eq 26) {
			if ($rulename[$r][0] eq $www[2]) {
				$na[$sl]=$nb[$id];
			} else {
				$na[$sl]=$nb[$sl];
			}
	##2 27  ★<α>
		} elsif ($www[1] eq 27) {
			$pos=-1;
			for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($hb[$sy][$zz] =~ m/,[0-9]/) {
					@hbsy = (split(/,/, $hb[$sy][$zz]));
					if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
						$pos=$zz;
					}
				}
			}
			if ($pos > -1) {
				@hbsy1 = (split(/,/, $hb[$sy][$pos]));
				$hb[$sy][$pos]="";
				$ha[$sy][$pos]="";
				$mo[$sy][$pos]="";
				$na[$sl]=$hbsy1[3];  
			} else {
				$na[$sl]=$nb[$sl];
			}
	##2 28  ●<<α>>
		} elsif ($www[1] eq 28) {
			$pos=-1;
			for($yy=0; $yy<=$semnum[$nonhead]; $yy++){
				@nonheadse1 = (split(/:/, $nb[$se][$yy]));  ## attribute と value に分ける
				if ($nonheadse1[0] eq "__") {  ## 新たに組み合わせるべき value を得る
					$value=$nonheadse1[1];
					$pos=$yy;
				}
			}
			if ($pos > -1) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 59) && ($hbsy[2] eq $www[2])) {  ## <α, <xn, {<  >}>>
							$hb[$sy][$zz]="";
							$ha[$sy][$zz]="";
							$mo[$sy][$zz]="";
							$na[$sl]=$hbsy[3];  
							$newsem = $hbsy[4].":".$value;
							$nb[$se][$pos]=$newsem;
						} else {
							$na[$sl]=$nb[$sl];
						}
					} else {
						$na[$sl]=$nb[$sl];
					}
				}
			} else {
				$na[$sl]=$nb[$sl];
			}
		}

	##2 解釈不可能素性が含まれていない場合
	} else {
		$na[$sl]=$nb[$sl];
	}
}

sub sy {	
## やっぱり for-to の中で splice するのは具合が悪いので、最初にmotherに上げておいて消していったほうが楽。
## non-head からのfeatureは push する。push すると、[0] のところに入ってしまうことに注意。

##1 $hb[$sy] （head 側)
	@{$mo[$sy]}=@{$hb[$sy]};## [mo]ther 
	@{$ha[$sy]}=@{$hb[$sy]};## [h]ead [a]fter Merge

	for($z=0; $z<=$syncnum[$head]; $z++){
		if ($hb[$sy][$z] =~ m/,[0-9]/) {   ## commaの後ろに数字が来ていたら解釈不可能素性
			@www = split(/,/, $hb[$sy][$z]);

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
									## ↑なるべくなくしていく方向
				&sy_head_lg;

		##2  1  +V, +A, etc
			} elsif (($www[1] eq 1) && ($nb[$ca] eq $www[2])) {
			 	$ha[$sy][$z]="";
			 	$mo[$sy][$z]="";
		##2  3  ++Pred, etc
			} elsif (($www[1] eq 3) && ($nb[$ca] eq $www[2])) {
			 	$ha[$sy][$z]="";
			 	$mo[$sy][$z]="";
		##2  5  rule1
			} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  6  rule2
			} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  7  -rule(n)
			} elsif (($www[1] eq 7) && ($rulename[$r][0] eq $www[2])) {
				$www[3]=$www[3]-1;
				$ha[$sy][$z]="";
				$mo[$sy][$z]=$www[0].",".$www[1].",".$www[2].",".$www[3];
		##2  11  ga(★), etc.  これは必ず nonhead 側のときしか消えない
		##2  12  ga(+T), etc.
			} elsif (($www[1] eq 12) && ($nb[$ca] eq $www[3])) {
					$ha[$sy][$z]="";
					$mo[$sy][$z]="";
		##2  14  SUFFIX
			} elsif (($www[1] eq 14) && ($rulename[$r][0] eq "RH-Merge")) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  16  PREFIX
			} elsif (($www[1] eq 16) && ($rulename[$r][0] eq "LH-Merge")) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  51  <α, ☆>
			} elsif ($www[1] eq 51) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3,52,".$www[2];  ## <α, ★>
		##2  52  <α, ★>
			} elsif ($www[1] eq 52) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3,53,".$www[2].",".$nb[$id];  ## <α, xn>
		##2  54 <★[Predication], partitioning>
			} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
				$mo[$sy][$z]="3,56,".$nb[$pr][1][0];  ## <xn partitioning>
				$ha[$sy][$z]="";
		##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
			} elsif (($www[1] eq 56) && ($www[2] eq $ha[$pr][1][0])) {
				$mo[$sy][$z]="";
		##2  103  β
			## もともと、Binding という Merge rule だったが、feature の作業なので、こちらへ移動した
			} elsif ($www[1] eq 103) {
				$a = -1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/2,102/) {  ## Bind
						$a=$zz;
					}
				}
				if ($a>0) {
					## binder の意味役割（$derived_a）を得る
					for($zz=1; $zz<=$semnum[$head]; $zz++){
						@headse1 = (split(/:/, $hb[$se][$zz]));  ## attribute と value に分ける
						@vvv = (split(/,/, $headse1[1]));  ## valueのほう
						if ($vvv[1] eq 24) {  ## ★
							$derived_a=$headse1[0];
						} elsif ($vvv[1] eq 25) {  ## ★α
							for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
								if ($nb[$sy][$zzz] eq $vvv[2]) {
									$derived_a=$headse1[0];
								}
							}
						} elsif ($vvv[1] eq 26) {  ## ★[α]
							if ($rulename[$r][0] eq $vvv[2]) {
								$derived_a=$headse1[0];
							}
						}
					}
					$mo[$sy][$z] = "3,103,$www[2],$derived_a,$hb[$id]";  ## βn＝Agent(x1-1)
					$ha[$sy][$z]="";
					for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
						if ($nb[$sy][$zz] =~ /2,102/) {  ## Bind
							$nb[$sy][$zz] = "";
						}
					}
				} else {   ## Merge相手に「Bind」がなければ継承
					$ha[$sy][$z] = "";
				}

		##2 上にリストしていない解釈不可能素性の対処
			} else {
				  ## ここはheadなので
				if ($www[0] >= 2) { 
					$ha[$sy][$z] = "";
	 			} else {
					$mo[$sy][$z] = "";
				}
			}
		##2 解釈不可能素性でない場合
		} else {
			$ha[$sy][$z] = "";
		}
	}

##1 $nb[$sy]（non-head からも mother に行く場合）... japanese2 の場合、J-Merge と property-no
	if ($symode eq 2) {
		@{$mo2[$sy]}=@{$nb[$sy]};
		@{$na[$sy]}=@{$nb[$sy]};
		for($z=0; $z<=$syncnum[$nonhead]; $z++){

	## 解釈不可能素性が含まれている場合
			if ($nb[$sy][$z] =~ m/,[0-9]/) {
				@www = split(/,/, $nb[$sy][$z]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&sy_both_lg;

			##2  1  +V, +A, etc.
				} elsif (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  3  ++Pred, etc.
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  5  rule1
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  6  rule2
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3,52,".$www[2];  ## <α, ★>
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3,53,".$www[2].",".$nb[$id];  ## <α, xn>
			##2  54 <★[Predication], partitioning>
				} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
					$mo2[$sy][$z]="3,56,".$hb[$pr][1][0];  ## <xn partitioning>
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
					$mo2[$sy][$z]="";
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$mo2[$sy][$z] = "3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					$na[$sy][$z] = "";

			##2 上にリストしていない解釈不可能素性の対処
				} else {
					  ## ここはnon-headなので
					if ($www[0] eq 3) {
						$na[$sy][$z] = "";
		 			} else {
						$mo2[$sy][$z] = "";
					}
				}
			##2 解釈不可能素性でない場合
			} else {
				$na[$sy][$z] = "";
			}
		}
		@{$mo[$sy]}=(@{$mo[$sy]}, @{$mo2[$sy]});

##1 $nb[$sy] （non-head 側)
	} else {
		@{$na[$sy]}=@{$nb[$sy]};## [n]on-head [a]fter Merge
		@mosy=();	## $mo[$sy] に追加する素性の受け皿

		for($z=0; $z<=$syncnum[$nonhead]; $z++){

	## 解釈不可能素性が含まれている場合
			if ($nb[$sy][$z] =~ m/,[0-9]/) {
				@www = split(/,/, $nb[$sy][$z]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&sy_nonhead_lg;

			##2  1  +V, +A, etc.
				} elsif (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  3  ++Pred, etc.
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  5  rule1
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
			##2  6  rule2
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
			##2  11  ga(★), etc.  これは、$se の ★αのところで削除しておく
				} elsif ($www[1] eq 11) {
					if ($www[0] eq 4){
						$na[$sy][$z]= "2,".$www[1].",".$www[2];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					}
			##2  12  ga(+T), etc.
				} elsif ($www[1] eq 12) {
					if ($www[0] eq 5){
						$na[$sy][$z]= "4,".$www[1].",".$www[2].",".$www[3];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					} elsif ($hb[$ca] eq $www[3]) {
					 	$na[$sy][$z]="";
					} elsif ($www[0] eq 4){
						$na[$sy][$z]= "2,".$www[1].",".$www[2].",".$www[3];
						push(@mosy, $na[$sy][$z]);
					 	$na[$sy][$z]="";
					} else {
					 	$na[$sy][$z]="$nb[$sy][$z]";
#					 	$na[$sy][$z]="";
					}
			##2  13  suffix
				} elsif (($www[1] eq 13) && ($rulename[$r][0] eq "LH-Merge")) {
				 	$na[$sy][$z]="";
			##2  15  prefix
				} elsif (($www[1] eq 15) && ($rulename[$r][0] eq "RH-Merge")) {
				 	$na[$sy][$z]="";
			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="3,52,".$www[2];  ## <α, ★>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  54 <★[Predication], partitioning>
				} elsif ($www[1] eq 54) {
					if ($prednum[$head] > 0){
						$na[$sy][$z]="3,56,".$hb[$pr][1][0];  ## <xn partitioning>
					}
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$na[$sy][$z] = "3,53,".$www[2].",".$hb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z] = "";
			##2  101  Kind
				## もともと、Kind-addition という Merge rule だったが、feature の作業なので、こちらへ移動した → se で処理？
				} elsif ($www[1] eq 101) {
					## 意味役割（$derived_a）を得る
					$derived_a="--";
					for($zz=1; $zz<=$semnum[$head]; $zz++){
						@headse1 = (split(/:/, $mo[$se][$zz]));  ## attribute と value に分ける
						@vvv = (split(/,/, $headse1[1]));  ## valueのほう
						if ($headse1[1] eq $na[$id]) {
							$derived_a=$headse1[0];
						}
					}
					if ($derived_a ne "--") {
						$semnum[$nonhead]++;
						$na[$se][$semnum[$nonhead]]="Kind:$derived_a($hb[$id])";
						$na[$sy][$z]="";
					} else {
						push(@mosy, $na[$sy][$z]);
						$na[$sy][$z]="";
					}
			##2 上にリストしていない解釈不可能素性の対処
				} else {
					  ## ここはnon-headなので
					if ($www[0] eq 3) {
						push(@mosy, $na[$sy][$z]);
						$na[$sy][$z] = "";
		 			} else {
					}
				}
			##2 解釈不可能素性でない場合
			} else {
			}
		}
		@{$mo[$sy]}=(@{$mo[$sy]}, @mosy);
 	}
}

sub pr {
	## １つの Pred素性は、3つの指標のリストになっている。
	## $hb[$pr][$z][0] = id
	## $hb[$pr][$z][1] = Subject
	## $hb[$pr][$z][2] = Predicate
	##
	## head側からは一律にmotherへ、non-head側からは daughter のまま。

##1 $mo[$pr]  head 
	@{$mo[$pr]}=@{$hb[$pr]};
	$ha[$pr]="";
	for($z=1; $z<=$prednum[$head]; $z++){

	##2 $mo[$pr][$z][0]  pred-id
		## 解釈不可能素性が含まれている場合
		if ($hb[$pr][$z][0] =~ m/,[0-9]/) { 
			@www = split(/,/, $hb[$pr][$z][0]);

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_head_i_lg;

		##3 21  ○
			} elsif ($www[1] eq 21) {
				$mo[$pr][$z][0] = "2,22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$pr][$z][0] = "0,24";  ## →★
		##3 24  ★
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
			} elsif ($www[1] eq 24) {
				$mo[$pr][$z][0] = $nb[$id];
		##3 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] eq $www[2]) {
						$mo[$pr][$z][0]=$nb[$id];
					}
				}
		##3 26  ★[α]
			} elsif ($www[1] eq 26) {
				if ($rulename[$r][0] eq $www[2]) {
					$mo[$pr][$z][0]=$nb[$id];
				} else {
					$mo[$pr][$z][0]=$hb[$pr][$z][0];
					$ha[$pr][$z][0]="zero";
				}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$pr][$z][0]=$nbsy1[3];  
				} else {
					$mo[$pr][$z][0]=$hb[$pr][$z][0];  
					$ha[$pr][$z][0]="zero";
				}

		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $mo[$pr][$z][$sp]  Subj, Pred
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($hb[$pr][$z][$sp] =~ m/,[0-9]/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				@www = (split(/,/, $hb[$pr][$z][$sp]));

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_head_s_lg;

		##3 21  ○
				} elsif ($www[1] eq 21) {
					$mo[$pr][$z][$sp]="2,22";  ## →●
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$mo[$pr][$z][$sp] = "0,24";  ## →★
		##3 24  ★
				} elsif ($www[1] eq 24) {
					$mo[$pr][$z][$sp]=$nb[$id];
		##3 25  ★α
				} elsif ($www[1] eq 25) {
					for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
						if ($nb[$sy][$zzz] eq $www[2]) {
							$mo[$pr][$z][$sp]=$nb[$id];
						}
					}
		##3 26  ★[α]
				} elsif ($www[1] eq 26) {
					if ($rulename[$r][0] eq $www[2]) {
						$mo[$pr][$z][$sp]=$nb[$id];
					} else {
						$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];
						$ha[$pr][$z][$sp]="zero";
					}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$pr][$z][$sp]=$nbsy1[3];  
				} else {
					$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
					$ha[$pr][$z][$sp]="zero";
				}
		##3 29  ★α,[β]
				} elsif ($www[1] eq 29) {
					if ($rulename[$r][0] eq $www[3]) {
						if ($nb[$ca] eq $www[2]){
							$mo[$pr][$z][$sp]=$nb[$id];
						} else {
							for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
								@nbsy = (split(/,/, $nb[$sy][$zzz]));
								if (($nb[$sy][$zzz] eq $www[2]) || ($nbsy[2] eq $www[2])) {
									$mo[$pr][$z][$sp]=$nb[$id];
									$nb[$sy][$zzz]="";
								} else {
									$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
									$ha[$pr][$z][$sp]="zero";
								}
							}
						}
					} else {
						$mo[$pr][$z][$sp]=$hb[$pr][$z][$sp];  
						$ha[$pr][$z][$sp]="zero";
					}
		##3 上にリストしていない解釈不可能素性の対処
				}
		##3 解釈不可能素性が含まれていない場合
			}
		}			## Subject が済んだら Predicate へ
	}		## 次の predication素性へ

##1 $na[$pr]  non-head 
	@{$na[$pr]}=@{$nb[$pr]};
	@on=();	## mo にあげる場合には 1 になる。
	for($z=1; $z<=$prednum[$nonhead]; $z++){

	##2 $na[$pr][$z][0]  pred-id
		## 解釈不可能素性が含まれている場合
		if ($nb[$pr][$z][0] =~ m/,[0-9]/) { 
			@www = split(/,/, $nb[$pr][$z][0]);

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&pr_nonhead_i_lg;

		##3 21  ○
			} elsif ($www[1] eq 21) {
				$na[$pr][$z][0] = "2,22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$na[$pr][$z][0] = "0,24";  ## →★
		##3 24  ★
			} elsif ($www[1] eq 24) {
				$na[$pr][$z][0] = $hb[$id];
		##3 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($hb[$sy][$zz] eq $www[2]) {
						$na[$pr][$z][0]=$hb[$id];
					}
				}
		##3 26  ★[α]
			} elsif ($www[1] eq 26) {
				if ($rulename[$r][0] eq $www[2]) {
					$na[$pr][$z][0]=$hb[$id];
				}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@hbsy1 = (split(/,/, $hb[$sy][$pos]));
					$hb[$sy][$pos]="";
					$na[$pr][$z][0]=$hbsy1[3];  
				} else {
					$na[$pr][$z][0]=$nb[$pr][$z][0];  
				}

		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $na[$pr][$z][$sp] Subject/Predicate
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($nb[$pr][$z][$sp] =~ m/,[0-9]/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				$on[$z]=1;
				@www = (split(/,/, $nb[$pr][$z][$sp]));

				if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
					&pr_nonhead_s_lg;

		##3 21  ○
				} elsif ($www[1] eq 21) {
					$na[$pr][$z][$sp]="2,22";  ## →●
		##3 22  ●
				} elsif ($www[1] eq 22) {
					$na[$pr][$z][$sp]=$hb[$id];
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$na[$pr][$z][$sp] = "0,24";  ## →★
		##3 24  ★
				} elsif ($www[1] eq 24) {
					$na[$pr][$z][$sp]=$hb[$id];
		##3 25  ★α
				} elsif ($www[1] eq 25) {
					for($zzz=0; $zzz<=$syncnum[$head]; $zzz++){
						if ($hb[$sy][$zzz] eq $www[2]) {
							$na[$pr][$z][$sp]=$hb[$id];
						}
					}
		##3 26  ★[α]
				} elsif ($www[1] eq 26) {
					if ($rulename[$r][0] eq $www[2]) {
						$na[$pr][$z][$sp]=$hb[$id];
					}
		##3 27  ★<α>
				} elsif ($www[1] eq 27) {
					$pos=-1;
					for($zz=0; $zz<=$syncnum[$head]; $zz++){
						if ($hb[$sy][$zz] =~ m/,[0-9]/) {
							@hbsy = (split(/,/, $hb[$sy][$zz]));
							if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
								$pos=$zz;
							}
						}
					}
					if ($pos > -1) {
						@hbsy1 = (split(/,/, $hb[$sy][$pos]));
						$hb[$sy][$pos]="";
						$na[$pr][$z][$sp]=$hbsy1[3];  
					} else {
						$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
					}
		##3 上にリストしていない解釈不可能素性の対処
				}
		##3 解釈不可能素性が含まれていない場合
			}
		}			## Subject が済んだら Predicate へ
	}		## 次の predication素性へ

	##2 non-head から mother への継承
	for($z=1; $z<=$prednum[$nonhead]; $z++){
		if ($on[$z] > 0) {
			$tempnum = @{$mo[$pr]};
			if ($tempnum < 1) {
				$tempnum = 1;
			}
			$mo[$pr][$tempnum] = $na[$pr][$z];
			$na[$pr][$z]="zero";
		}
	}
}

sub se {
##		$semnum_n = @{$nb[$se]};
##			if ($semnum_n > 0) {
##				$semnum_n = $semnum_n-1;
##			} else {
##				$semnum_n = 0;
##			}
##		$semnum_h = @{$hb[$se]};
##			if ($semnum_h > 0) {
##				$semnum_h = $semnum_h-1;
##			} else {
##				$semnum_h = 0;
##			}

##1 $mo[$se]
	@{$mo[$se]}=@{$hb[$se]};			## [mo]ther 
	$ha[$se]="zero";							 ## [h]ead [a]fter Merge
	for($z=1; $z<=$semnum[$head]; $z++){
		@hbse1 = (split(/:/, $hb[$se][$z]));	## attribute と value に分ける

		## 今のところ、attribute のほうは feature 処理をしていない

		if ($hbse1[1] =~ m/,[0-9]/) {		 ## value のほうに feature が含まれていたら分ける
			@www = (split(/,/, $hbse1[1]));

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&se_head_lg;

		##2 21  ○
			} elsif ($www[1] eq 21) {
				$mo[$se][$z]=$hbse1[0].":2,22";  ## →●
		##2 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$se][$z]=$hbse1[0].":2,24";  ## →★
		##2 24  ★
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
			} elsif ($www[1] eq 24) {
				$mo[$se][$z]=$hbse1[0].":".$nb[$id];
		##2 25  ★α
			} elsif ($www[1] eq 25) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] eq $www[2]) {
						$mo[$se][$z]=$hbse1[0].":".$nb[$id];
					}
				}
		##2 33  ★α
			} elsif ($www[1] eq 33) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 11) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nb[$id];
						}
						if (($nbsy[1] eq 12) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
#							## sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nb[$id];
						}
					}
				}
#				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
#					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
#						@nbsy = (split(/,/, $nb[$sy][$zz]));
#						if ($nbsy[1] eq 101) {  ## Kind
##							## sy の処理は、このあとでなければならない。
#							for($zz2=1; $zz2<=$semnum[$head]; $zz2++){
#								@headse1 = (split(/:/, $hb[$se][$zz2]));  ## attribute と value に分ける
#								if ($headse1[1] eq $nb[$id]) {
#									$derived_a=$headse1[0];
#								} else {
#									$derived_a="--";
#								}
#							}
#							if ($derived_a ne "--") {
#								$semnum[$nonhead]++;
#								$na[$se][$semnum[$nonhead]]="Kind:$derived_a($hb[$sl])";
#								$nb[$sy][$zz]="";
#							} else {
#								push(@mosy, $na[$sy][$z]);
#								$na[$sy][$z]="";
#							}
#						}
#					}
#				}


		##2 26  ★[α]
			} elsif ($www[1] eq 26) {
				if (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq 'zero-Merge')) {
					$mo[$se][$z]=$hbse1[0].":".$nb[$id];
				} else {
					$mo[$se][$z]=$hb[$se][$z];
				}
		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nbsy[3];
						}
					}
				}
		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@nbsy1 = (split(/,/, $nb[$sy][$pos]));
					$nb[$sy][$pos]="";
					$mo[$se][$z]=$hbse1[0].":".$nbsy1[3];
				} else {
					$mo[$se][$z]=$hb[$se][$z];  
				}
		##2 29  ★α,[β]
			} elsif ($www[1] eq 29) {
				if (($rulename[$r][0] eq $www[3]) || ($rulename[$r][0] eq 'zero-Merge')) {
					if ($nb[$ca] eq $www[2]){
						$mo[$se][$z]=$hbse1[0].":".$nb[$id];
					} else {
						for($zzz=0; $zzz<=$syncnum[$nonhead]; $zzz++){
							@nbsy = (split(/,/, $nb[$sy][$zzz]));
							if (($nb[$sy][$zzz] eq $www[2]) || ($nbsy[2] eq $www[2])) {
								$mo[$se][$z]=$hbse1[0].":".$nb[$id];
							} else {
								$mo[$se][$z]=$hb[$se][$z];  
							}
						}
					}
				} else {
					$mo[$se][$z]=$hb[$se][$z];
				}
		##2 30  α（★<α>）
			} elsif ($www[1] eq 30) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){
					if ($nb[$sy][$zz] =~ m/,[0-9]/) {
						@nbsy = (split(/,/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$se][$z]="$hbse1[0]:α($nbsy[3])";
						} else {
							$mo[$se][$z]=$hb[$se][$z];  
						}
					} else {
						$mo[$se][$z]=$hb[$se][$z];  
					}
				}
		##2 上にリストしていない解釈不可能素性の対処
			}
	  ##2 解釈不可能素性が含まれていない場合
		}
	}

##1 $na[$se]
	@{$na[$se]}=@{$nb[$se]};
	for($z=1; $z<=$semnum[$nonhead]; $z++){
		@nbse1 = (split(/:/, $nb[$se][$z]));	## attribute と value に分ける

		## 今のところ、attribute のほうは feature 処理をしていない

		if ($nbse1[1] =~ m/,[0-9]/) {		 ## value のほうに feature が含まれていたら分ける
			@www = (split(/,/, $nbse1[1]));

			if ($www[1] =~ /L$/) { ## feature番号の末尾が「L」の場合には、個別lg のファイルで指定されている。
				&se_nonhead_lg;

		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				$pos=-1;
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$pos=$zz;
						}
					}
				}
				if ($pos > -1) {
					@hbsy1 = (split(/,/, $hb[$sy][$pos]));
					$hb[$sy][$pos]="";
					$na[$pr][$z][$sp]=$hbsy1[3];  
				} else {
					$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
				}
		##2 30  α（★<α>）
			} elsif ($www[1] eq 30) {
				for($zz=0; $zz<=$syncnum[$head]; $zz++){
					if ($hb[$sy][$zz] =~ m/,[0-9]/) {
						@hbsy = (split(/,/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$hb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$na[$se][$z]="$hbse1[0]:α($nbsy[3])";
						} else {
							$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
						}
					} else {
						$na[$pr][$z][$sp]=$nb[$pr][$z][$sp];  
					}
				}
			}
		}
	}
} 

sub ph {
		$ha[$ph]=$hb[$ph];
		$na[$ph]=$nb[$ph];
}

sub wo {
	if ("ARRAY" eq ref $hb[$wo]) {
		@{$ha[$wo]}=@{$hb[$wo]};
	} else {
		$ha[$wo]=$hb[$wo];
	}
	if ("ARRAY" eq ref $nb[$wo]) {
		@{$na[$wo]}=@{$nb[$wo]};
	} else {
		$na[$wo]=$nb[$wo];
	}
}


1;

