#!/bin/bash
# Kill a phase1 run
kill $(ps -fwwu $(whoami) | grep -E '(\./simpli.sh |python3 )' | grep -v grep | cut -c10-15)
sleep 2
ps -fwwu $(whoami)
echo "Best to delete the run results..."
