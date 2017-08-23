#!/bin/sh
#!/bin/bash
PROJECT=${PJT:-/d/mw6/u/la002/pjt}
. $PROJECT/profile
cd $PROJECT/src/tools
if [ -d $PROJECT/results/old -o -f wastest.bsc ]
then
	echo old exists - bailing
	exit 2
fi
mv test.bsc wastest.bsc
model=""
if [ "x$1" = xphase1 ]
then
	model=phase1
	shift
elif [ "x$1" = xsimpli1 ]
then
	model=simpli1
	shift
fi
for t in $@
do
	if [ -d $PROJECT/results/$t ]
	then
		echo $t:
		cp $PROJECT/results/$t/test.bsc .
		mv $PROJECT/results/$t $PROJECT/results/old
	else
		echo $t: New
	fi
	if [ x$model = xsimpli1 ]
	then
		./simpli.sh phase1 $t
	else
		./phase1.sh $model $t
	fi
	if [ $? -ne 0 ]
	then
		echo error with $t - check for old and wastest!
		exit 2
	fi
	if [ x$model != xsimpli1 ]
	then
		./energies.sh $t
	fi
	if [ -d $PROJECT/results/old ]
	then
		mv $PROJECT/results/old $PROJECT/results/$t
	fi
done
mv wastest.bsc test.bsc
echo All done, I hope!
	
