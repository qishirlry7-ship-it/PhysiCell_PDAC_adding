#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid
rm -rf outputs output
mkdir -p output
touch output/empty.txt
echo "=== start: $(date) ==="
./project > smoke_test.log 2>&1 &
PID=$!
sleep 90
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "=== stopped after ~90s wall time ==="
tail -15 smoke_test.log
echo "=== output files ==="
ls outputs/pdac_therapy | wc -l
ls outputs/pdac_therapy | grep '^snapshot' | wc -l
du -sh outputs/pdac_therapy
