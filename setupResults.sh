
# Expect to find configs and some binaries in the same directory as we started
here=`dirname $0`
cd $here${here:+/}

# Set up environment
PJT=${PJT:-/d/mw6/u/la002/pjt}
. $PJT/profile
TOOLS=$PJT/build/tools

# Install py files - this should normally be via build.sh or check.sh
cp -p pipeline.cfg *.py *.sh $TOOLS

# Get details of the test
PDB=$PJT/pdb
RESULTS=$PJT/results/${1:-phase1test}
PDBLIST=$(grep -v '^#' test.bsc | grep -v '^\s*$' | cut -d' ' -f1 | grep -v = | sort | uniq)

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
done)

# Determine where to find input files for BEEP
srcdir=""
first=$(for f in $files
do
	echo $f
	break
done
)
if [ -f $PJT/results/simpli1/$first ]
then
	srcdir=simpli1
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
else
	echo "Run already exists, overwriting..."
	sleep 5  # You have 5 seconds to wake up!
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
fi

