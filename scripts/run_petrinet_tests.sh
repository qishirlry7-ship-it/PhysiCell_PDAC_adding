#!/usr/bin/env bash
# PetriNet runtime unit / parity tests.
#
# The runtime loads its model from JSON at run time
# (config/petrinet/xenophagy_model.json), so the four runtime translation
# units must be linked alongside petrinet_engine.cpp -- there is no longer a
# generated C++ translation unit to compile in.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

runtime_inc="-Icustom_modules/petrinet/runtime/include"
runtime_src=(
  custom_modules/petrinet/runtime/src/json.cpp
  custom_modules/petrinet/runtime/src/model.cpp
  custom_modules/petrinet/runtime/src/expression.cpp
  custom_modules/petrinet/runtime/src/ssa.cpp
)

g++ -std=c++11 -O2 $runtime_inc \
  tests/petrinet_engine_test.cpp \
  custom_modules/petrinet/petrinet_engine.cpp \
  "${runtime_src[@]}" \
  -o /tmp/petrinet_engine_test
/tmp/petrinet_engine_test

g++ -std=c++11 -O2 $runtime_inc \
  tests/petrinet_parity_driver.cpp \
  custom_modules/petrinet/petrinet_engine.cpp \
  "${runtime_src[@]}" \
  -o /tmp/petrinet_parity_driver
echo "parity driver: /tmp/petrinet_parity_driver"
