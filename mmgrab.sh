#!/bin/bash
#ps -fu mm001 | grep -v grep | grep gmx >/dev/null
ps -fu la002 | grep -v grep | grep simpli.sh >/dev/null
while [ $? -eq 0 ]
do
	#echo -e -n "\r $(ps -fu mm001 | grep -v grep | grep gmx | cut -c40-47)"
	echo -e -n "\r $(ps -fu la002 | grep -v grep | grep python3 | cut -c40-47)"
	sleep 60
	#ps -fu mm001 | grep -v grep | grep gmx > /dev/null
	ps -fu la002 | grep -v grep | grep simpli.sh >/dev/null
done
echo "GPU is free..."
mv test.bsc test-save.bsc
mv test2.bsc test.bsc
./simpli.sh barn2
