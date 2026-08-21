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
test -s outputs/petrinet_minimal/death_statistics.csv
head -n 1 outputs/petrinet_minimal/xenophagy_metrics.csv | grep -q "ap_gal8_tokens,ap_ub_tokens"
head -n 1 outputs/petrinet_minimal/xenophagy_metrics.csv | grep -q "intracellular_bacteria,sal_ruffle_tokens,uptaken_bacteria"
head -n 1 outputs/petrinet_minimal/xenophagy_metrics.csv | grep -q "is_dead,petrinet_death_triggered,death_time_min"
grep -q "\[PetriNet demo\] injected 50" outputs/petrinet_minimal/run.log
echo "minimal PetriNet+PhysiCell demo: PASS"
echo "  metrics: outputs/petrinet_minimal/xenophagy_metrics.csv"
echo "  figure:  outputs/petrinet_minimal/xenophagy_metrics.svg"
echo "  deaths:  outputs/petrinet_minimal/death_statistics.csv"
