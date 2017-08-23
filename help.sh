#!/bin/bash
. ../../profile
while read p
do
	echo "\\subsubsection\{$p\}"
	echo
	echo "\\begin\{lstlisting\}"
	./$p --help
	echo "\\end\{lstlisting\}"
	echo
	echo
done <<-_PROGRAMS
area.r
areas.r
centre.py
energies.r
expand.py
hydro.py
iter.r
memtime.r
phase1.py
pipeline.py
ply2gts.py
results.py
rotate.py
salt.r
sepden.r
shift.py
simpli.py
_PROGRAMS
