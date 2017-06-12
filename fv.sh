#!/bin/bash
# Tabulate number of faces and vertices in each gts file
cd ${PJT:-/d/mw6/u/la002/pjt}/results/simpli1
alt=0
# Plain text
#endl=("" "")
#sep="\t"
# TeX tabu in two columns
endl=("&	" "\\\\\\\\")
sep="\t& "
ls -1 *-[1-9]0*.gts | while read g
do
	pdb=$(echo $g | cut -d- -f1)
	pct=$(echo $g | cut -d- -f2 | cut -d. -f1)
	fac=$(head -1 $g | cut -d' ' -f2)
	ver=$(head -1 $g | cut -d' ' -f3)
	echo -e "$pdb$sep$pct$sep$fac$sep$ver"
done | sort -k 1,1 -k 3,3n | while read l
do
	echo -e "$l\t${endl[$alt]}"
	alt=$((1-$alt))
done
