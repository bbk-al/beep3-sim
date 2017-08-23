# Anticipated usages:  <including-script> [phase1] [bsc-file] folder [new]
# literal phase1 indicates not to use hydro i.e electrostatics only
# bsc-file defaults to test.bsc
# folder is also defaulted to phase1test
# new means start from PDB files not prepared MTZs

# Expect to find configs and some binaries in the same directory as we started
here=`dirname $0`
cd $here${here:+/}

# Set up environment
PJT=${PJT:-/d/mw6/u/la002/pjt}
. $PJT/profile
TOOLS=$PJT/build/tools

# Install py files - this should normally be via build.sh or check.sh
cp -p pipeline.cfg beep.ah *.py *.sh $TOOLS

# Get details of the test
PDB=$PJT/pdb
BSC=test.bsc
nohydro=0
if [ "x$1" == xphase1 ]
then
	nohydro=1
	shift
fi
if [ $# -gt 1 ]
then
	BSC=$1
	shift
fi
RESULTS=$PJT/results/${1:-phase1test}
PDBLIST=$(grep -v '^#' $BSC | grep -v '^\s*$' | cut -d' ' -f1 | grep -v = | sort | uniq)

# Work out which pdb and pct files will be needed
files=$(for pdb in $PDBLIST
do
	echo ${pdb}.mtz		# Used to signal pipeline processing is done
	pdbonly=$(echo $pdb | cut -d- -f1)
	echo ${pdbonly}H.pdb	# Needed for mass calculation
	if [ "x$pdbonly" == "x$pdb" ]
	then
		for d in $PCT
		do
			echo ${pdb}-${d}.mtz
		done
	fi
done | sort | uniq)

# Determine where to find input files for BEEP
srcdir=""
first=$(for f in $files
do
	echo $f
	break
done
)
if [ $nohydro -eq 0 -a -f $PJT/results/hydro/$first ]
then
	srcdir=hydro
elif [ -f $PJT/results/phase1/$first ]
then
	srcdir=phase1
	echo "NOTICE:  using $srcdir files"
fi

# Create the results directory
if [ ! -d $RESULTS ]
then
	# If "new" is not specified as second argument, set up inputs from srcdir
	if [ "x$srcdir" != x -a "x$2" == x ]
	then
		mkdir -p $RESULTS
		echo mtz $RESULTS
		if [ "x$srcdir" != x ]
		then
			echo "Linking all files from $srcdir..."
			# Not *.kin, *.dat, *.log or *.out
			cd $PJT/results/$srcdir
			#files=$(ls -1 | egrep -v '\.(kin|kin.gz|dat|log|out)$')
			#cp -pr $files $RESULTS || exit 1
			ln $files $RESULTS || exit 1
			cd - >/dev/null
		fi
	elif [ "x$srcdir" == x -o "x$2" == xnew ]
	then
		mkdir -p $RESULTS
		echo pdb $RESULTS
		cd $PDB
		for pdb in $PDBLIST
		do
			cp -pr ${pdb}.pdb $RESULTS || exit 1
		done
		cd - >/dev/null
	else
		echo "Usage: $0 [rundir] ['new']"
		echo "'new' initiates a fresh build from PDB files, else $srcdir is linked"
	fi
	# Now the directory exists, pretty-copy the bsc as history (and for rerun)
	if [ $(dirname $BSC) != $RESULTS ]
	then
		>$RESULTS/$BSC
		written=0
		cat $BSC | while read line
		do
			if [ "x$line" == x ]
			then
				if [ $written -ne 0 ]
				then
					break
				else
					>$RESULTS/$BSC
					continue
				fi
			elif [ "x$(echo $line | cut -c1)" != "x#" ]
			then
				written=1
			fi
			echo $line >>$RESULTS/$BSC
		done
	fi
else
	echo "Run already exists, overwriting..."
	sleep 15  # You have 15 seconds to wake up!
	rm -f $RESULTS/*.kin $RESULTS/*.kin.gz
	for f in $RESULTS/{phase1.log,results.dat}; do test -f "$f" && >$f; done
	for f in $files
	do
		if [ ! -f $RESULTS/$f ]
		then
			restart=$(echo ${f/*-/} | cut -d. -f1)
			first=${f/-[^.]*\.mtz/}.mtz
			if [ -f $RESULTS/$first ]
			then
				mv $RESULTS/$first $RESULTS/$f || exit 1
			else
				echo "Confused!  Manual check required"
				exit 1
			fi
		fi
	done
	for f in $RESULTS/*-default.mtz
	do
		if [ -f $f ]
		then
			mv $f ${f/-default.mtz/}.mtz
		fi
	done
	# Got this far, so switch to the pre-existing bsc if there is just one file
	bsc=$(ls -1 $RESULTS/*.bsc 2>/dev/null)
	if [ -f "$bsc" ]
	then
		BSC=$bsc
	fi
fi

