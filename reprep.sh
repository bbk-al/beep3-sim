#!/bin/bash
PROJECT=${PJT:-/d/mw6/u/la002/pjt}
. $PROJECT/profile
cd $PROJECT/results/hydro
for m in *.mtz
do
	echo $m:
	$PROJECT/build/tools/prepare.py $(tar tf $m | egrep '\.(gts|xyzqr)$' | sort -t . -k 2) $m
	if [ ! -f $m ]
	then
		echo Prep of $m failed >&2
	fi
done >reprep.out
echo "Details in reprep.out"

