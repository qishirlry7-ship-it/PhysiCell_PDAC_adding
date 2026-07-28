#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid
make clean > /dev/null 2>&1
make -j"$(nproc)" 2>&1 | tail -30
echo "=== build done, running ==="
rm -rf outputs output
mkdir -p output
touch output/empty.txt
./project > smoke_test2.log 2>&1 &
PID=$!
sleep 60
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "=== stopped after ~60s wall time ==="
grep -E "current simulated time|total agents|Warning|error|Error" smoke_test2.log | tail -40
echo "=== validate_required substrate/type resolution line (if any) ==="
grep -i "resolved OK\|validate" smoke_test2.log || echo "(no such line in this codebase, expected)"
echo "=== initial cell-type breakdown from log ==="
grep -A20 "Pre-processing type" smoke_test2.log | head -20
