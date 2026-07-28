#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid
rm -rf outputs output
mkdir -p output
touch output/empty.txt
./project > smoke_test5.log 2>&1 &
PID=$!
sleep 90
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "=== progress ==="
grep -E "current simulated time|total agents|Warning|error" smoke_test5.log | tail -20
