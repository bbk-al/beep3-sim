#!/bin/bash
# Informal script to test simplification.
# Run simpli.py to generate multiple simplifications and then phase1.py to test.
PCT=$(eval echo {10..100..10})
restart=all

source $(dirname $0)/setupResults.sh
PCT=${PCT/*$restart/ $restart }

# Simplify... a list of pre-specified pdb files
for pdb in $PDBLIST
do
	pdb=${pdb%.pdb}
	echo $pdb

	# Generate the base meshes - if needed
	if [ ! -f $RESULTS/${pdb}.mtz ]
	then
		$TOOLS/pipeline.py -p $TOOLS/pipeline.cfg -w $RESULTS --loglevel DEBUG $pdb
		if [ $? -ne 0 ]
		then
			echo Pipeline error
			exit 1
		fi
	fi

	# Generate the simplified meshes - if needed
	pct=$(
	for d in $PCT
	do
		if [ ! -f $RESULTS/${pdb}-${d}.mtz ]
		then
			echo $d
		fi
	done
	)
	if [ "x$pct" != x ]
	then
		$TOOLS/simpli.py --decimate $pct -i $RESULTS/${pdb}-3.gts -o $RESULTS/${pdb}.gts
		if [ $? -ne 0 ]
		then
			echo Simplify error
			exit 1
		fi
	fi
done

if [ "x$2" = xnew ]
then
	echo "Not running phase1.py, but mtz files created"
	exit 0
fi

# Save the default meshes
for pdb in $PDBLIST
do
	mv -f $RESULTS/${pdb}.mtz $RESULTS/${pdb}-default.mtz
done

# Set up the scenario
#echo "${pdb} location=(0,0,0),(0,0,0),(0,0,0)" >simple.bsc
#echo "MCiter=1" >>simple.bsc

# Truncate the output files
OUT=$RESULTS/${1:-phase1}.out
if [ "x$restart" = x ]
then
	>$OUT
	>$RESULTS/simple.log
	>$RESULTS/simple.dat
fi

# For each simplification, run phase1.py
for d in $PCT
do
	echo $d
	for pdb in $PDBLIST
	do
		# Trick phase1.py to use the required simplification
		mv -f $RESULTS/${pdb}-${d}.mtz $RESULTS/${pdb}.mtz
	done

	# Run phase1.py as normal
	$TOOLS/phase1.py -p $TOOLS/pipeline.cfg -s ${BSC:-test.bsc} -o $RESULTS/results.dat -w $RESULTS --loglevel DEBUG >>$OUT

	for pdb in $PDBLIST
	do
		# Undo the tricks
		mv -f $RESULTS/${pdb}.mtz $RESULTS/${pdb}-${d}.mtz
	done

	# Save the results
	cat $RESULTS/phase1.log >>$RESULTS/simple.log
	cat $RESULTS/results.dat >>$RESULTS/simple.dat
done

# Restore the default meshes
for pdb in $PDBLIST
do
	mv -f $RESULTS/${pdb}-default.mtz $RESULTS/${pdb}.mtz
done

# Tidy up
echo "zipping kins..."
ls $RESULTS/*.kin 2>/dev/null | grep '\.kin$' >/dev/null && gzip $RESULTS/*.kin
echo "Done.  Output is in $OUT"


