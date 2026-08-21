#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

if ! cmp -s main.cpp tests/bacterial_uptake_simulation/main.cpp; then
  echo "test main.cpp is stale; review and copy the production main.cpp" >&2
  exit 1
fi

name="petrinet_uptake_test"
python3 scripts/generate_petrinet_cpp.py --check
python3 scripts/make_minimal_petrinet_config.py \
  --output-name "$name" --duration-min 30 --bacteria 0 --cells 25 \
  --extracellular-bacteria 50 --input-mode agent

make petrinet-uptake-test-build -j4
rm -f "outputs/$name/bacterial_uptake.csv" \
      "outputs/$name/xenophagy_metrics.csv" "outputs/$name/run.log"
./project_petrinet_uptake_test "outputs/$name/PhysiCell_settings.xml" \
  >"outputs/$name/run.log" 2>&1

uptake="outputs/$name/bacterial_uptake.csv"
metrics="outputs/$name/xenophagy_metrics.csv"
test -s "$uptake"
test -s "$metrics"
head -n 1 "$uptake" | grep -q '^time_min,bacteria_id,tumor_id,tokens,entry_place,result$'
head -n 1 "$metrics" | grep -q 'intracellular_bacteria,sal_ruffle_tokens,uptaken_bacteria'

accepted="$(awk -F, 'NR > 1 && $6 == "accepted" {count++} END {print count+0}' "$uptake")"
unique="$(awk -F, 'NR > 1 && $6 == "accepted" {seen[$2]=1} END {for (id in seen) count++; print count+0}' "$uptake")"
if [[ "$accepted" -le 0 || "$accepted" -ne "$unique" ]]; then
  echo "uptake invariant failed: accepted=$accepted unique_bacteria=$unique" >&2
  exit 1
fi

echo "bacterial uptake simulation: PASS"
echo "  production main copy: current"
echo "  initial agents: 25 tumor + 50 bacteria"
echo "  unique accepted bacteria: $accepted"
echo "  audit: $uptake"
echo "  metrics: $metrics"
