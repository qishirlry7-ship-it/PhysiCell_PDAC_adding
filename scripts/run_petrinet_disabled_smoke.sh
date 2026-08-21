#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

name="petrinet_disabled_smoke"
metrics="outputs/$name/xenophagy_metrics.csv"
log="outputs/$name/run.log"

if [[ ! -x ./project ]]; then
  echo "missing ./project; run make first" >&2
  exit 1
fi

python3 scripts/make_minimal_petrinet_config.py \
  --output-name "$name" --duration-min 1 --bacteria 150 --cells 2 \
  --disable-petrinet
rm -f "$metrics" "$log"
./project "outputs/$name/PhysiCell_settings.xml" >"$log" 2>&1

if [[ -e "$metrics" ]]; then
  echo "disabled PetriNet unexpectedly wrote metrics: $metrics" >&2
  exit 1
fi
if grep -q '\[PetriNet demo\]' "$log"; then
  echo "disabled PetriNet unexpectedly injected demo bacteria" >&2
  exit 1
fi
if ! grep -q 'Total simulation runtime' "$log"; then
  echo "PhysiCell disabled-mode smoke run did not finish normally" >&2
  exit 1
fi

echo "disabled PetriNet smoke test passed"
