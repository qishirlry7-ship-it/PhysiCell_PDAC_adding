#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2
make -j"$(nproc)" 2>&1 | tail -5
rm -rf outputs output
mkdir -p output
touch output/empty.txt
./project > smoke_viz.log 2>&1 &
PID=$!
sleep 240
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "=== progress ==="
grep -E "current simulated time|total agents" smoke_viz.log | tail -10
echo "=== snapshot count ==="
ls outputs/pdac_therapy/output*_cells.mat | wc -l
