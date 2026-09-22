#!/usr/bin/env bash
# Run one arm of the 5-day PetriNet comparison.
#
# Invoked as: bash scripts/run_petrinet_5day_arm.sh <baseline|wt|exp>
# Reads outputs/petrinet_real_7200min_<arm>/PhysiCell_settings.xml, writes
# run.log beside it, and reports timing plus the population endpoints.
set -uo pipefail

arm="${1:?usage: run_petrinet_5day_arm.sh <baseline|wt|exp>}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

dir="outputs/petrinet_real_7200min_${arm}"
if [[ ! -f "$dir/PhysiCell_settings.xml" ]]; then
  echo "missing config: $dir" >&2
  exit 2
fi

start=$(date +%s)
./project "$dir/PhysiCell_settings.xml" > "$dir/run.log" 2>&1
rc=$?
wall=$(( $(date +%s) - start ))

echo "arm=$arm rc=$rc wall=${wall}s"
echo "skipped_type_warnings=$(grep -c "don't recognize" "$dir/run.log" || true)"
echo "initial_agents=$(grep 'total agents' "$dir/run.log" | head -1 | awk '{print $NF}')"
echo "final_agents=$(grep 'total agents' "$dir/run.log" | tail -1 | awk '{print $NF}')"
echo "snapshots=$(ls "$dir"/output*_cells.mat 2>/dev/null | wc -l)"
