#!/usr/bin/perl

##@ Merge の際の素性処理///
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
	if ($hb[$sl] =~ m/@/) { 
		@www = split(/@/, $hb[$sl]);
	##2 21  ○
		if ($www[1] eq 21) {
			$mo[$sl] = "2@22";  ## →●
			$ha[$sl] = "zero";
	##2 23  ☆
		} elsif ($www[1] eq 23) {
			$mo[$sl] = "0@24";  ## →★
			$ha[$sl] = "zero";
	##2 24  ★
				##!!! id からとるのか sl からとるのか：OBJECT指示表現のVと Mergeするときにはいいが、property記述表現とMergeするときのTが問題。ただ、それはproperty-Mergeになるとしたら、そっちで指定すればいいことなのかも。
		} elsif ($www[1] eq 24) {
			if ($hb[$ca] eq "T") {  
				$mo[$sl] = $nb[$id];
				$ha[$sl] = "zero";
			} else {
				$mo[$sl] = $hb[$sl];
				$ha[$sl] = "zero";
			}
	##2 25  ★α
		} elsif ($www[1] eq 25) {
			for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($nb[$sy][$zz] eq $www[2]) {
					$mo[$sl]=$nb[$id];
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
			for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($nb[$sy][$zz] =~ m/@/) {
					@nbsy = (split(/@/, $nb[$sy][$zz]));
					if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
						$nb[$sy][$zz]="";
						$na[$sy][$zz]="";
						$mo[$sy][$zz]="";
						$mo[$sl]=$nbsy[3];
						$ha[$sl]=$nbsy[3];  
#						$ha[$sl]="zero";##!!!←なぜにこれではなく？　でも、あえてそうしているみたいなので。。。
					}
				}
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
	if ($nb[$sl] =~ m/@/) {
		@www = split(/@/, $nb[$sl]);
	##2 21  ○
		if ($www[1] eq 21) {
			$na[$sl] = "2@22";  ## →●
	##2 22  ●	
		} elsif ($www[1] eq 22) {
			$na[$sl] = $hb[$id];
	##2 23  ☆
		} elsif ($www[1] eq 26) {
			$na[$sl] = "0@24";  ## →★
	##2 24  ★
		} elsif ($www[1] eq 24) {
			$na[$sl] = $hb[$id];
	##2 25  ★α
		} elsif ($www[1] eq 25) {
			for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
				if ($hb[$sy][$zz] eq $www[2]) {
					$na[$sl] = $hb[$id];
				}
			}
	##2 26  ★[α]
		} elsif ($www[1] eq 26) {
			if ($rulename[$r][0] eq $www[2]) {
				$na[$sl]=$nb[$id];
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
		if ($hb[$sy][$z] =~ m/@/) { 
			@www = split(/@/, $hb[$sy][$z]);
		##2  1  +V, +A, etc
			if (($www[1] eq 1) && ($nb[$ca] eq $www[2])) {
			 	$ha[$sy][$z]="";
			 	$mo[$sy][$z]="";
		##2  2  ga
			} elsif (($www[1] eq 2) && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
			} elsif (($www[1] eq 2) && ($rulename[$r][0] eq "J-Merge")) {	
			## J-Mergeの場合には、ga-movement ではなく継承させる
				$ha[$sy][$z]="";
		##2  3  no
			} elsif (($www[1] eq 3) && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  4  wo
			} elsif (($www[1] eq 4) && ($nb[$ca] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  5  +R
			} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  6  +R
			} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="";
		##2  51  <α, ☆>
			} elsif ($www[1] eq 51) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3@52@".$www[2];  ## <α, ★>
		##2  52  <α, ★>
			} elsif ($www[1] eq 52) {
				$ha[$sy][$z]="";
				$mo[$sy][$z]="3@53@".$www[2]."@".$nb[$id];  ## <α, xn>
		##2  54 <★[Predication], partitioning>
			} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
				$mo[$sy][$z]="3@56@".$nb[$pr][1][0];  ## <xn partitioning>
				$ha[$sy][$z]="";
		##2  56 <xn partitioning>
		## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
			} elsif (($www[1] eq 56) && ($www[2] eq $ha[$pr][1][0])) {
				$mo[$sy][$z]="";

#	これ↓は rel-Merge でやっておく
#			} elsif ($hb[$sy][$z] =~ /A=partitioning=H/) {	## ★[Predication]
#				if ($prednum[$nonhead] > 0){
#					$mo[$sy][$z]="A=partitioning=$nb[$pr][1][0]";
#				}
#			 	$ha[$sy][$z]="";

		##2 上にリストしていない解釈不可能素性の対処
			} else {
				  ## ここはheadなので
				if (($www[0] eq 3) || ($www[0] eq 2)) {
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
			if ($nb[$sy][$z] =~ m/@/) {
				@www = split(/@/, $nb[$sy][$z]);
			##2  1  +V, +A, etc.
				if (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  2  ga
				} elsif (($www[1] eq 2) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
				} elsif (($www[1] eq 2) && ($rulename[$r][0] eq "J-Merge")) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
			##2  3  no
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
				} elsif (($www[1] eq 3) && ($rulename[$r][0] eq "J-Merge")) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
			##2  4  wo
				} elsif (($www[1] eq 4) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
				} elsif (($www[1] eq 4) && ($rulename[$r][0] eq "J-Merge")) {	
				## J-Mergeの場合には、ga-movement ではなく継承させる
					$na[$sy][$z]="";
			##2  5  +R
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  6  +R
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="";
			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3@52@".$www[2];  ## <α, ★>
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="";
					$mo2[$sy][$z]="3@53@".$www[2]."@".$nb[$id];  ## <α, xn>
			##2  54 <★[Predication], partitioning>
				} elsif (($www[1] eq 54) && ($prednum[$head] > 0)) {
					$mo2[$sy][$z]="3@56@".$hb[$pr][1][0];  ## <xn partitioning>
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
					$mo2[$sy][$z]="";
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$mo2[$sy][$z] = "3@53@".$www[2]."@".$hb[$id];  ## <α, xn>
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
			if ($nb[$sy][$z] =~ m/@/) {
				@www = split(/@/, $nb[$sy][$z]);
			##2  1  +V, +A, etc.
				if (($www[1] eq 1) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  2  ga
				} elsif (($www[1] eq 2) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  3  no
				} elsif (($www[1] eq 3) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  4  wo
				} elsif (($www[1] eq 4) && ($hb[$ca] eq $www[2])) {
					$na[$sy][$z]="";
			##2  5  +R
				} elsif (($www[1] eq 5) && ($rulename[$r][0] eq $www[2])) {
					$na[$sy][$z]="";
			##2  6  +R
				} elsif (($www[1] eq 6) && (($rulename[$r][0] eq $www[2]) || ($rulename[$r][0] eq $www[3]))) {
					$na[$sy][$z]="";
			##2  51  <α, ☆>
				} elsif ($www[1] eq 51) {
					$na[$sy][$z]="3@52@".$www[2];  ## <α, ★>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  52  <α, ★>
				} elsif ($www[1] eq 52) {
					$na[$sy][$z]="3@53@".$www[2]."@".$nb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  54 <★[Predication], partitioning>
				} elsif ($www[1] eq 54) {
					if ($prednum[$head] > 0){
						$na[$sy][$z]="3@56@".$hb[$pr][1][0];  ## <xn partitioning>
					}
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z]="";
			##2  56 <xn partitioning>
			## partitioning素性は、そのPred よりも上に上がらないようにしないと、Partitioning 適用可否チェックができないので。
				} elsif (($www[1] eq 56) && ($www[2] eq $na[$pr][1][0])) {
			##2  58 <α, ●>
				} elsif ($www[1] eq 58) {
					$na[$sy][$z] = "3@53@".$www[2]."@".$hb[$id];  ## <α, xn>
					push(@mosy, $na[$sy][$z]);
					$na[$sy][$z] = "";

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
		if ($hb[$pr][$z][0] =~ m/@/) { 
			@www = split(/@/, $hb[$pr][$z][0]);
		##3 21  ○
			if ($www[1] eq 21) {
				$mo[$pr][$z][0] = "2@22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$pr][$z][0] = "0@24";  ## →★
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
				}
		##3 27  ★<α>
			} elsif ($www[1] eq 27) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/@/) {
						@nbsy = (split(/@/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$pr][$z][0]=$nbsy[3];  
						}
					}
				}
		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $mo[$pr][$z][$sp]  Subj, Pred
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($hb[$pr][$z][$sp] =~ m/@/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				@www = (split(/@/, $hb[$pr][$z][$sp]));

		##3 21  ○
				if ($www[1] eq 21) {
					$mo[$pr][$z][$sp]="2@22";  ## →●
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$mo[$pr][$z][$sp] = "0@24";  ## →★
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
					}
		##3 27  ★<α>
				} elsif ($www[1] eq 27) {
					for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
						if ($nb[$sy][$zz] =~ m/@/) {
							@nbsy = (split(/@/, $nb[$sy][$zz]));
							if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
								$nb[$sy][$zz]="";	 ## sy の処理は、このあとでなければならない。
								$mo[$pr][$z][$sp]=$nbsy[3];
							}
						}
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
		if ($nb[$pr][$z][0] =~ m/@/) { 
			@www = split(/@/, $nb[$pr][$z][0]);
		##3 21  ○
			if ($www[1] eq 21) {
				$na[$pr][$z][0] = "2@22";  ## →●
		##3 23  ☆
			} elsif ($www[1] eq 23) {
				$na[$pr][$z][0] = "0@24";  ## →★
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
				for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($hb[$sy][$zz] =~ m/@/) {
						@hbsy = (split(/@/, $hb[$sy][$zz]));
						if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
							$hb[$sy][$zz]="";
							$na[$pr][$z][0]=$nbsy[3];  
						}
					}
				}
		##3 上にリストしていない解釈不可能素性の対処
			}
	  ##3 解釈不可能素性が含まれていない場合
		}

	##2 $na[$pr][$z][$sp] Subject/Predicate
		for($sp=1; $sp<=2; $sp++){	## Subject($sp=1) と Predicate($sp=2) について
			if ($nb[$pr][$z][$sp] =~ m/@/) {		 ## Subject/Predicate に feature が含まれていたら分ける
				$on[$z]=1;
				@www = (split(/@/, $nb[$pr][$z][$sp]));

		##3 21  ○
				if ($www[1] eq 21) {
					$na[$pr][$z][$sp]="2@22";  ## →●
		##3 22  ●
				} elsif ($www[1] eq 22) {
					$na[$pr][$z][$sp]=$hb[$id];
		##3 23  ☆
				} elsif ($www[1] eq 23) {
					$na[$pr][$z][$sp] = "0@24";  ## →★
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
					for($zz=0; $zz<=$syncnum[$head]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
						if ($hb[$sy][$zz] =~ m/@/) {
							@hbsy = (split(/@/, $hb[$sy][$zz]));
							if (($hbsy[1] eq 53) && ($hbsy[2] eq $www[2])) {  ## <α, xn>
								$hb[$sy][$zz]="";	 ## sy の処理は、このあとでなければならない。
								$na[$pr][$z][$sp]=$hbsy[3];
							}
						}
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

		if ($hbse1[1] =~ m/@/) {		 ## value のほうに feature が含まれていたら分ける
			@www = (split(/@/, $hbse1[1]));

		##2 21  ○
			if ($www[1] eq 21) {
				$mo[$se][$z]=$hbse1[0].":2@22";  ## →●
		##2 23  ☆
			} elsif ($www[1] eq 23) {
				$mo[$se][$z]=$hbse1[0].":2@24";  ## →★
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
		##2 26  ★[α]
			} elsif ($www[1] eq 26) {
				if ($rulename[$r][0] eq $www[2]) {
					$mo[$se][$z]=$hbse1[0].":".$nb[$id];
				}
		##2 27  ★<α>
			} elsif ($www[1] eq 27) {
				for($zz=0; $zz<=$syncnum[$nonhead]; $zz++){ ## sy の場合、push されたものが [0] に入ってしまうので
					if ($nb[$sy][$zz] =~ m/@/) {
						@nbsy = (split(/@/, $nb[$sy][$zz]));
						if (($nbsy[1] eq 53) && ($nbsy[2] eq $www[2])) {  ## <α, xn>
							$nb[$sy][$zz]=""; ## sy の処理は、このあとでなければならない。
							$mo[$se][$z]=$hbse1[0].":".$nbsy[3];
						}
					}
				}
		##2 上にリストしていない解釈不可能素性の対処
			}
	  ##2 解釈不可能素性が含まれていない場合
		}
	}

##1 $na[$se]
	@{$na[$se]}=@{$nb[$se]};

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

##@ 共通サブルーチン///
sub show_feature { ## 各 feature をそれぞれの方法で表示する
	($b, $bb, $ww) = @_;

##1-1 pr
	if ($b eq $pr) {
		$fclass = "f".$bb.$b;
	} else {
		$fclass = "f".$b;
	}

##1-2 sl
	if ($b eq $sl) {
		if ($ww eq "zero"){
			$ww="";
		}
	}

##1-3 se
	if ($b eq $se) {
		$attribute = (split(/:/, $ww))[0];	## se の場合、attribute と value に分ける
		utf8::decode($attribute);	## これをしないと文字化けする
		$ww = (split(/:/, $ww))[1];
		utf8::decode($ww);	## これをしないと文字化けする
	}

##1-4 features
	if ($ww =~ m/@/) { ## 解釈不可能素性を目立たせる
		@www = split(/@/, $ww);
		if ($www[1] eq 1){
			$ww = "+".$www[2];
			$wfile = "plusN";  ##!!! 共通ファイルにする
		} elsif ($www[1] eq 2){
			$ww = "ga";
			$wfile = "ga";
		} elsif ($www[1] eq 3){
			$ww = "no";
			$wfile = "no";
		} elsif ($www[1] eq 4){
			$ww = "wo";
			$wfile = "wo";
		} elsif ($www[1] eq 5){
			$ww = "+".$www[2];
			$wfile = "rule1";  ##!!!まだ
		} elsif ($www[1] eq 6){
			$ww = "+".$www[2]."/".$www[3];
			$wfile = "rule2";  ##!!!まだ
		} elsif ($www[1] eq 21){
			$ww = "○";
			$wfile = "whitecircle"; ##!!!これはもう $wwと同名にするとか
		} elsif ($www[1] eq 22){
			$ww = "●";
			$wfile = "blackcircle";
		} elsif ($www[1] eq 23){
			$ww = "☆";
			$wfile = "whitestar";
		} elsif ($www[1] eq 24){
			$ww = "★";
			$wfile = "blackstar";
		} elsif ($www[1] eq 25){
			$ww = "★<sub>$www[2]</sub>";
			$wfile = "blackstara";
		} elsif ($www[1] eq 26){
			$ww = "★[$www[2]]";
			$wfile = "blackrule_a";
		} elsif ($www[1] eq 27){
			$ww = "★<sub>&lt;$www[2]&gt;</sub>";
			$wfile = "blackstar_a";
		} elsif ($www[1] eq 51){
			$ww = "&lt;$www[2], ☆&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 52){
			$ww = "&lt;$www[2], ★&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 53){
			$ww = "&lt;$www[2], $www[3]&gt;";	## <	> はタグだと思われてしまって表示されないので実体参照にする
			$wfile = "ind_xn";
		} elsif ($www[1] eq 54){
			$ww = "&lt;★<sub>[Predication]</sub>, partitioning&gt;";
			$wfile = "blackstar_predication";
		} elsif ($www[1] eq 55){
			$ww = "&lt;★<sub>[Rel]</sub>, partitioning&gt;";
			$wfile = "blackstar_rel_predication";
		} elsif ($www[1] eq 56){
			$ww = "&lt;$www[2], partitioning&gt;";	## <	> はタグだと思われてしまって表示されないので実体参照にするべし
			$wfile = "partitioning";
		} elsif ($www[1] eq 57){
			$ww = "&lt;$www[2], partitioning&gt;";	## <	> はタグだと思われてしまって表示されないので実体参照にするべし
			$wfile = "partitioning";
		} elsif ($www[1] eq 58){
			$ww = "&lt;$www[2], ●&gt;";
			$wfile = "ind_xn";
		} elsif ($www[1] eq 101){
			$ww = "Kind";
			$wfile = "Kind";
		} elsif ($www[1] eq 102){
			$ww = "Bind";
			$wfile = "Bind";
		} elsif (($www[1] eq 103) && ($www[3] eq "")) {
			$ww = "β".$www[2]."＝■";
			$wfile = "be-ta";
		} elsif ($www[1] eq 104){
			$ww = "pickup";
			$wfile = "pickup";
		} elsif ($ww eq "0=R=0"){	 ## 17  !!! 再考するべし
			$ww = "+R";
			$wfile = "plusR";
		} elsif ($ww eq "0=da=0"){	 ## 18  ←!!! 使ってる？
			$ww = "da";
			$wfile = "da";
		}
		$ww = "<span class='feature'><a href='$folder[$lg]/features/$wfile.html' class='red' target='feature_description'>$ww</a></span>";
	}
	if (($www[1] eq 103) && ($www[3] ne "")) {	 ## 解釈後のbeta
		$a1 = (split(/#/, $ww))[1];
		$a2 = (split(/#/, $ww))[2];
		$ww = "β".$www[2]."＝$www[3]";
	}
	if ($fclass eq "fs$pr") {
		$ww = "Subject: $ww";
	} elsif ($fclass eq "fp$pr") {
		$ww = "Predicate: $ww";
	} elsif ($fclass eq "f$se") {
		$ww = "$attribute: $ww";
	}
print <<"END";
	<span class=$fclass>$ww</span>
END
}

1;

