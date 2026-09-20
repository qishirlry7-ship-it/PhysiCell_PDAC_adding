#!/usr/bin/env bash
# Full PetriNet SSA benchmark sweep (1..10000 cells x 1/6/24 h x 1/2/4/8 threads).
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
mkdir -p benchmark-results
g++ -std=c++11 -O3 -march=native -fopenmp \
  -Icustom_modules/petrinet/runtime/include \
  tests/petrinet_benchmark.cpp \
  custom_modules/petrinet/petrinet_engine.cpp \
  custom_modules/petrinet/runtime/src/json.cpp \
  custom_modules/petrinet/runtime/src/model.cpp \
  custom_modules/petrinet/runtime/src/expression.cpp \
  custom_modules/petrinet/runtime/src/ssa.cpp \
  -o /tmp/petrinet_benchmark
output="benchmark-results/petrinet_cpp.csv"
echo "cells,hours,threads,seconds,reactions,reactions_per_second,checksum" > "$output"
for cells in 1 10 100 1000 10000; do
  for hours in 1 6 24; do
    for threads in 1 2 4 8; do
      /tmp/petrinet_benchmark "$cells" "$hours" "$threads" | tail -1 >> "$output"
    done
  done
done
echo "$output"
