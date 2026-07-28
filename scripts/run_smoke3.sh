#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid
make clean > /dev/null 2>&1
make -j"$(nproc)" 2>&1 | tail -10
echo "=== build done, running ==="
rm -rf outputs output
mkdir -p output
touch output/empty.txt
./project > smoke_test3.log 2>&1 &
PID=$!
sleep 90
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "=== stopped after ~90s wall time ==="
grep -E "current simulated time|total agents|Warning|error|Error" smoke_test3.log | tail -30
echo "=== cell type list ==="
grep "Pre-processing type" smoke_test3.log
