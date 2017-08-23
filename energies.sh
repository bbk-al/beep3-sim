#!/bin/bash
# Extract energies breakdown from .out file into R data file format.
PJT=/d/mw6/u/la002/pjt
(echo it mi he lj e t
n=0
pmi=0
it=0
HE=0
LJ=0
total=0
varname=""
regname="[a-zA-Z]+"
# Following to cope with old format .out
grep electrostatic= $PJT/results/$1/${1}.out >/dev/null 2>&1
if [ $? -ne 0 ]
then
	varname="electrostatic"
	regname=""
fi
grep 'Energy for mesh ' $PJT/results/$1/${1}.out | cut -c16- | sed -e 's/= /=/g' | while read l
do
	eval ${varname}$(echo $l | grep -Po "${regname}"'= ?-?[0-9\.][0-9\.]*(e-?[0-9]*)?([^)]|$)')
	n=$((n+1))
	mi=$(echo $l | cut -d' ' -f1)
	it=$((it+($mi<$pmi)))
	pmi=$mi
	echo $n $it $mi $HE $LJ $electrostatic $total
done) >$PJT/results/$1/energies.dat
#Energy for mesh 0 (lib_id=0) electrostatic=-4840.395879 HE=0.4921671103 LJ=0 total=-4839.903712
