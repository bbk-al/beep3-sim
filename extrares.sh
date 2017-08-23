#!/bin/bash
if [ "x$1" == x ]
then
	echo "Usage $0 testname [options]"
	exit 1
fi
test=$1
shift

# Get results data from sparrow
cd $(dirname $0)
mkdir -p results/$test
#ssh la002@ssh.cryst.bbk.ac.uk /d/mw6/u/la002/pjt/src/tools/energies.sh $test
scp la002@ssh.cryst.bbk.ac.uk:/d/mw6/u/la002/pjt/results/${test}/energies.dat results/$test
sleep 2

# Analyse results (will create png's in target directory)
./energies.r --file results/$test/energies.dat $(eval echo \"\ \${1..9}\ \")

