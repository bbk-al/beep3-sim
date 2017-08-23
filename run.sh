#!/bin/bash
# Run a script in the background protected from logout
if [ -f $1.pid ]
then
	ps -p $(cat $1.pid) >/dev/null 2>&1
	if [ $? -ne 0 ]
	then
		rm $1.pid
	else
		ps -p $(cat $1.pid)
		exit 3
	fi
fi
(nohup $@ >$1.out 2>&1 &
echo $! >$1.pid
sleep 5
cat $1.out)
exit 0
