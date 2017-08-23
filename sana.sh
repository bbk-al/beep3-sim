#!/bin/bash
# scenario analysis
log=${PJT:-/d/mw6/u/la002/pjt}/results/$1/phase1.log
inits=$(grep -c DEBUG:init $log)
nzero=$(grep -c '[(,]-0[,)]' $log)
mtz=$(grep -c DEBUG:Insert $log)
occupy=$(grep -c DEBUG:occupy $log)
rejects=$(grep -c 'INFO:Move rejected' $log)
accepts=$(grep -c 'INFO:Move accepted' $log)
subjects=$(grep -c 'insertMesh' $log)
echo "Spheres in arena: $((inits-nzero))"
echo "Subjects: $subjects"
echo "Crowders: $((mtz-subjects))"
echo "Iterations: $((rejects+accepts))"
echo "Accepted: $accepts"
echo "Subject spheres: $((occupy-rejects-rejects-accepts-mtz+subjects))"

