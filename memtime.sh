#!/bin/sh
# Collect memory usage and timing data from log files
if [ x$1 = x ]
then
	echo "Usage: $0 testname"
	exit 1
fi
grep 'Process size' ../../results/$1/phase1.log | cut -d: -f4 | cut -d' ' -f3,6 | sed 's/,//' >mem.txt
grep 'Process size' ../../results/$1/phase1.log | cut -d' ' -f2 | sed -e 's/[:,]/ /g' >time.txt

