#!/bin/bash
# Calculate paths for pairs
# By convention, upper case is for the enzyme, lower case for the inhibitor
# Second pdb is the one that "moves"
PJT=${PJT:-/d/mw6/u/la002/pjt}
SRC=$PJT/results/hydro
echo 1MAH
$(dirname $0)/centre.py $SRC/1MAHH.pdb $SRC/1mahH.pdb -n 35 -s 1
echo
echo 2ZA4
$(dirname $0)/centre.py $SRC/2ZA4H.pdb $SRC/2za4H.pdb -n 10 -s " -0.2"
echo
echo 3C7U
$(dirname $0)/centre.py $SRC/3C7UH.pdb $SRC/3c7uH.pdb -n 25 -s 1
echo
echo 3t0c
$(dirname $0)/centre.py $SRC/3t0cH.pdb
