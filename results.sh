#!/bin/bash
if [ "x$1" == x ]
then
	echo "Usage $0 testname [options] [(results|_simple_)]"
	exit 1
fi
test=$1
dat=${!#:-simple}

# Get results data from sparrow
cd $(dirname $0)
scp la002@ssh.cryst.bbk.ac.uk:/d/mw6/u/la002/pjt/results/${1:-blip}/$dat.dat .
shift

# Analyse results - note time for output checks later
now=$(date -j -f "%b %d %T" "$(date '+%b %e %H:%M:00')" "+%s")
./results.py $@

# Move png files to local store
lspng=$(ls -ltr *.png 2>/dev/null)
if [ "x$lspng" != x ]
then
	latest=$(ls -ltr *.png | tail -1 | sed 's/  */ /g' | cut -d' ' -f6-8)
	files=$(ls -l *.png | sed 's/  */ /g' | grep "$latest" | sed 's/  */ /g' | cut -d' ' -f9-)
	ts=$(date -j -f "%b %d %T" "${latest}:00" "+%s")
	if [ "x$files" != x ]
	then
		if [ $now -le $ts ]
		then
			# Move pngs to store
			echo test=$test files=$files
			mkdir -p results/$test
			mv $files results/$test
		else
			echo "Not moving any old files"
			echo "now=$now ts=$ts"
		fi
	fi
fi
ls -l *.png 2>/dev/null

