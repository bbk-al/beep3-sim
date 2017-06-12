#!/bin/bash
# Kill a dunk run
kill $(ps -fwwu la002 | grep -E '(\./dunk.sh|end-to-end run_pairs|timings --append|python3 \./run_pair)' | grep -v grep | cut -c10-15)
sleep 2
ps -fwwu la002
