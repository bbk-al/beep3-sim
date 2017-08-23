#!/bin/bash
# Tabulate number of faces and vertices in each gts file
cd ${PJT:-/d/mw6/u/la002/pjt}/results/hydro
alt=0
# Plain text
#endl=("" "")
#sep="\t"
# TeX tabu in two columns
endl=("&	" "\\\\\\\\")
sep="\t& "
ls -1 *.gts | while read g
do
	pdb=$(echo $g | cut -d- -f1 | cut -d. -f1)
	pct=$(echo $g | cut -d- -f2 | cut -d. -f1)
	if [ x$pct = x$pdb ]
	then
		pct="-"
	fi
	if [ x$pct = x1 -o x$pct = x2 -o x$pct = x3 -o x$pct = xref ]
	then
		continue
	fi
	fac=$(head -1 $g | cut -d' ' -f3)
	ver=$(head -1 $g | cut -d' ' -f1)
	echo -e "$pdb$sep$pct$sep$fac$sep$ver"
done | sort -k 1,1 -k 3,3n | while read l
do
	echo -e "$l\t${endl[$alt]}"
	alt=$((1-$alt))
done
