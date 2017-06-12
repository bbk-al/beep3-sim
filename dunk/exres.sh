#!/bin/bash
cd /d/mw6/u/la002/pjt/dunk/${1:-ache_fas4}
for p in `seq 0.01 0.01 0.09` `seq 0.1 0.1 1`
do
	if [ "x$(ls -l results-$p.txt 2>/dev/null | cut -c29-31)" = x639 ]
	then
		tail -n+2 results-$p.txt | cut -d" " -f2 >results-clean-$p.txt
	fi
done
paste results-clean-*.txt >results-all
rm results-clean-*.txt
