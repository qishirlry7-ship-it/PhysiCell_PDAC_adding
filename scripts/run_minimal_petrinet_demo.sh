#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python3 scripts/generate_petrinet_cpp.py --check
bash scripts/run_petrinet_tests.sh
python3 scripts/make_minimal_petrinet_config.py
make -j4
./project outputs/petrinet_minimal/PhysiCell_settings.xml \
  > outputs/petrinet_minimal/run.log 2>&1
python3 scripts/plot_xenophagy_metrics.py

test -s outputs/petrinet_minimal/xenophagy_metrics.csv
test -s outputs/petrinet_minimal/xenophagy_metrics.svg
grep -q "\[PetriNet demo\] injected 50" outputs/petrinet_minimal/run.log
echo "minimal PetriNet+PhysiCell demo: PASS"
echo "  metrics: outputs/petrinet_minimal/xenophagy_metrics.csv"
echo "  figure:  outputs/petrinet_minimal/xenophagy_metrics.svg"
