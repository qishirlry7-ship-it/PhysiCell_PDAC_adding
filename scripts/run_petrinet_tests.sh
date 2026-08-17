#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
python3 scripts/generate_petrinet_cpp.py --check
g++ -std=c++11 -O2 \
  tests/petrinet_engine_test.cpp \
  custom_modules/petrinet/petrinet_engine.cpp \
  custom_modules/generated/xenophagy_model_generated.cpp \
  -o /tmp/petrinet_engine_test
/tmp/petrinet_engine_test
g++ -std=c++11 -O2 \
  tests/petrinet_parity_driver.cpp \
  custom_modules/petrinet/petrinet_engine.cpp \
  custom_modules/generated/xenophagy_model_generated.cpp \
  -o /tmp/petrinet_parity_driver
echo "parity driver: /tmp/petrinet_parity_driver"
