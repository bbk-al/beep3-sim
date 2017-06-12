#!/bin/bash
# Expect to find configs and some binaries in the same directory as we started
here=`dirname $0`
cd $here${here:+/}

# Set up environment
PJT=${PJT:-/d/mw6/u/la002/pjt}
. $PJT/profile
TOOLS=$PJT/build/tools
RESULTS=$PJT/results/${2:-phase1test}
if [ ! -d $RESULTS ]
then
	echo "Oops - no such test $RESULTS"
	exit 1
fi

# Informal script to run phase1.py to drop out kinemage or plot files
if [ "x$1" == x ]
then
	echo Usage: $0 bsc-file [testname]
	exit 1
fi
if [ -f "$1" ]
then
	BSC=$1
elif [ -f "$1.bsc" ]
then
	BSC=$1.bsc
else
	echo "Oops - no such file $1"
	exit 1
fi
if [ $(basename $0) == "phase1kin.sh" ]
then
	out="-k"
	OUT=$RESULTS/${2:-phase1}kin.out
elif [ $(basename $0) == "phase1plot.sh" ]
then
	out="-r"
	OUT=$RESULTS/${2:-phase1}plot.out
else
	echo "Oops, didn't recognise the command name"
	exit 1
fi
PCT=

# Install py files - this should normally be via build.sh or check.sh
cp -p pipeline.cfg *.py *.sh $TOOLS

echo "Running phase1.py..."
$TOOLS/phase1.py -p $TOOLS/pipeline.cfg -s $BSC $out --nosolve -w $RESULTS --loglevel DEBUG >>$OUT
echo "zipping kins..."
ls $RESULTS/*.kin 2>/dev/null | grep '\.kin$' >/dev/null && gzip $RESULTS/*.kin
echo "Done.  Output is in $OUT"

