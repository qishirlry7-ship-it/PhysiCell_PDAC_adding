#!/usr/bin/env bash
# Short PetriNet SSA benchmark (1/10/100 cells, 1 hour, 1 and 4 threads).
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
output="benchmark-results/petrinet_cpp_quick.csv"
echo "cells,hours,threads,seconds,reactions,reactions_per_second,checksum" > "$output"
for cells in 1 10 100; do
  for threads in 1 4; do
    /tmp/petrinet_benchmark "$cells" 1 "$threads" | tail -1 >> "$output"
  done
done
echo "$output"
