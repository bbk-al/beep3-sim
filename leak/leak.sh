#!/bin/bash
# Informal script to run leak.py during development
PCT=

source $(dirname $0)/setupResults.sh

echo "Running leak.py..."
OUT=$RESULTS/${1:-leak}.out
# leak.py:  -f forces a refresh from PDB files;  gdb is if libBEEP coredumps
$TOOLS/leak.py -p $TOOLS/pipeline.cfg -s test.bsc -o $RESULTS/results.dat -w $RESULTS --loglevel DEBUG >>$OUT
#gdb -ex r --args python3 $TOOLS/leak.py -s test.bsc -o results.dat -w $RESULTS --loglevel INFO
echo "zipping kins..."
ls $RESULTS/*.kin 2>/dev/null | grep '\.kin$' >/dev/null && gzip $RESULTS/*.kin
echo "Done.  Output is in $OUT"

