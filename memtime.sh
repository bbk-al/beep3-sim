#!/bin/sh
# Collect memory usage and timing data from log files
if [ x$1 = x ]
then
	echo "Usage: $0 testname"
	exit 1
fi
n=1
outdir=../../results/$1
echo "time memory" >${outdir}/memtime.dat
grep 'Process size' ${outdir}/phase1.log | cut -d' ' -f1,2,6 | while read d t m
do
	echo $n $(date -d "$d $t" +%s) $(echo $m | sed 's/,//')
	n=$((n+1))
done >>${outdir}/memtime.dat

# R
# df <- read.table("memtime")
# df$time <- df$time - min(df$time)
# df$time <- df$time - c(0,df$time)[1:length(df$time)]
# plot(df$time, xlab="Iteration", ylab="Time (s)")
# plot(df$memory, xlab="Iteration", ylab="Memory (MB)")
# Curious! :
# plot(x=df$time, y=df$memory, xlab="Time (s)", ylab="Memory (MB)")
