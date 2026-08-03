# -*- coding: utf-8 -*-
"""
BUG FIX: cloning a cell_definition in XML does NOT carry over
cell_rules.csv entries, since Rules are keyed by exact cell-type name
string. PD-L1lo/hi_tumor_infected and _xenophagy inherited their raw
XML baselines (necrosis rate=0.005 "at O2=0" anchor, cycle entry
floor=3.6e-5 "starved" anchor) with NONE of the oxygen/glucose Rules
that are supposed to pull those back to sane values -- verified this
killed all 15 test-seeded _infected cells within ~2880 simulated
minutes (mean lifetime ~200min at the unmoderated 0.005/min necrosis
rate). Fix: copy every existing PD-L1lo/hi_tumor rule to the
corresponding _infected/_xenophagy variant, substituting only the cell
type name.
"""
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    lines = [l for l in f.read().splitlines() if l.strip()]

base_types = ["PD-L1lo_tumor", "PD-L1hi_tumor"]
variant_suffixes = ["_infected", "_xenophagy"]

new_lines = []
for line in lines:
    parts = line.split(",", 1)
    cell_type = parts[0]
    if cell_type in base_types and "contact with Bifidobacterium" not in line:
        # this is a "normal" tumor biology rule (growth, necrosis,
        # lactate, pressure, damage, debris) -- copy to both variants,
        # but NOT the colonization-trigger rule itself (that only
        # applies to the original, un-infected type)
        for suffix in variant_suffixes:
            new_lines.append(cell_type + suffix + "," + parts[1])

with open(RULES, "a", encoding="utf-8") as f:
    f.write("\n" + "\n".join(new_lines) + "\n")

print(f"copied {len(new_lines)} rules to the 4 tumor variant types (_infected, _xenophagy)")
