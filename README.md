# beep3-sim
Simulator and utilities for beep3
See Thesis for details of the main utilities in this package (python and R scripts).
These are supported by a number of shell scripts which assume a specific layout for directories and files containing results data.
Under pjt top level directory:  results directory contains all results and scenario configurations.
Within results, special directories are:
  phase1 (linked to simpli1) - models prepared for electrostatics interactions only
  hydro - models prepared for electrostatics and short range effects
Remaining directories are the names of specific tests.  Each test directory contains log files, program output files, results data and scenario configurations.

Supporting utilities include:
  phase1.sh - runs the simulator, phase1.py
  simpli.sh - runs multiple simplifications with phase1.py
  phase1kin.sh - runs phase1.py in kinemage-generating mode
  rerun.sh - re-runs existing simulations, preserving the original in an 'old' subdirectory
  run.sh - partially demonises any of the above to survive session disconnects
  kill.sh - safely aborts any currently running simulation
  
  results.sh - extracts results data and runs results.py to run analyses
  areas.sh, energies.sh, memtime.sh, iter.sh - extract supplementary data for respective R script analysis
  reprep.sh - re-prepares all models (in hydro)
  sana.sh - provides some basic crowding information on a previously run scenario
  
