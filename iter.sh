#!/bin/bash
# Collect iterations data from .out files
if [ x$1 = x ]
then
	echo "Usage: $0 testname"
	exit 1
fi
n=1
outdir=../../results/$1
echo "count convergence" >${outdir}/iter.dat
pcregrep -Mo 'gmres\([0-9]+\)(.*)\nGMRES reached convergence' $outdir/${1}.out | grep -v GMRES | cut -d'	' -f3-5 | sed -e 's/\(\.[0-9][0-9]*\)	/\1e00	/g' | sed -e 's/[eE]/ /g' | paste -s - iter.end | bc iter.bc >>$outdir/iter.dat 
