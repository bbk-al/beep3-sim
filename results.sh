#!/bin/bash
dat=${!#:-simple}
scp la002@ssh.cryst.bbk.ac.uk:/d/mw6/u/la002/pjt/results/${1:-blip}/$dat.dat .
shift
$(dirname $0)/results.py $@
