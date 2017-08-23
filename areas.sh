#!/bin/bash
echo "mi area" >../../results/$1/areas.dat
# For R data file
grep 'hydrophobic area' ../../results/$1/*.out | cut -d' ' -f8,10 | grep -n '[0-9]' | sed 's/:/ /g' >>../../results/$1/areas.dat
# df <- read.table("results/lnc3c/areas.dat")
# plot(df$area, col=hsv(df$mi/max(df$mi),1,1), ylab="Area")
# plot(density(df$area[df$mi>1]),xlab="Area",main="Density of crowder HE contact area")
# density(df$area[df$mi>1])$x[which.max(density(df$area[df$mi>1])$y)]

# For TeX table
grep 'hydrophobic area' ../../results/$1/*.out | cut -d' ' -f8,10 |
while read mi a
do
	echo -n "$a "
	if [ $mi -eq 1 ]
	then
		echo
	fi
done >>../../results/$1/areas.dat




