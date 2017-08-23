#!/bin/bash
# Informal script to run phase1.py during development
PCT=

source $(dirname $0)/setupResults.sh

echo "Running phase1.py..."
OUT=$RESULTS/${1:-phase1}.out
# phase1.py:  -f forces a refresh from PDB files;  gdb is if libBEEP coredumps
$TOOLS/phase1.py -p $TOOLS/pipeline.cfg -s ${BSC:-test.bsc} -o $RESULTS/results.dat -w $RESULTS --loglevel DEBUG >>$OUT
#gdb -ex r --args python3 $TOOLS/phase1.py -s test.bsc -o results.dat -w $RESULTS --loglevel INFO
echo "zipping kins..."
ls $RESULTS/*.kin 2>/dev/null | grep '\.kin$' >/dev/null && gzip $RESULTS/*.kin
echo "Done.  Output is in $OUT"

