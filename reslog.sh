#!/bin/bash
# Recovery of results from log file
if [ x$1 = x ]
then
	echo "Usage: $0 runX"
	exit 1
fi
loc=$(grep ' Propose move ' ../../results/$1/phase1.log | sed -e 's/^.* Propose move //' -e 's/ *to .*//' -e 's/ /_/g')
loca=($(for z in $loc; do echo $z; done))
e=$(grep 'INFO:New energy' ../../results/$1/phase1.log | sed -e 's/^.*INFO:New energy //' -e 's/, current.*$//')
ea=($(for z in $e; do echo $z; done))
stat=$(egrep 'INFO:Move (reject|accept)ed' ../../results/$1/phase1.log | sed -e 's/^.*INFO:Move //')
stata=($(for z in $stat; do echo $z; done))
n=${#ea[@]}
((n--))
for i in `seq 0 $n`
do
	echo ${ea[$i]} ${loca[$i]//_/ } ${stata[$i]}
done

#2017-03-21 17:32:31,286 phase1 INFO:[40] Propose move 175.421 -86.8454 163.757  to -175.561 303.959 -81.8786 , rotating by -0.105568,0.633731,0.745955,0.175475
#2017-03-21 17:32:31,286 phase1 DEBUG:Move mesh instance 2
#2017-03-21 17:32:31,434 phase1 INFO:BEEP solve... 
#2017-03-21 17:36:13,169 phase1 INFO:New energy -57634.2458678392, current energy -57635.58627572718
#2017-03-21 17:36:13,170 phase1 DEBUG:Move mesh instance 2 back
#2017-03-21 17:36:13,327 phase1 INFO:Move rejected
#2017-03-21 17:36:13,334 phase1 INFO:[41] Propose move 175.421 -86.8454 163.757  to 125.28 -173.691 163.757 , rotating by 0.0321572,-0.740583,-0.671148,-0.0079014
#2017-03-21 17:36:13,334 phase1 DEBUG:Move mesh instance 2
#2017-03-21 17:36:13,498 phase1 INFO:BEEP solve... 
#2017-03-21 17:40:19,649 phase1 INFO:New energy -57635.46005028515, current energy -57635.58627572718
#2017-03-21 17:40:19,649 phase1 INFO:Move accepted
