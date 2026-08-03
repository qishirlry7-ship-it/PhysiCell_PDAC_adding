# -*- coding: utf-8 -*-
"""
Seeds an initial Bifidobacterium_longum population near the vessels
(representing "just arrived via blood, at the entry points"), since
this simplified version does not model continuous blood influx --
documented simplification, a single colonization event rather than
ongoing translocation.
"""
import csv, math, random

random.seed(3)

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
N_BACTERIA = 40

with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

vessel_positions = [(float(r[0]), float(r[1])) for r in rows if r[3] in ("fixed_vessel_source", "fixed_vessel_source_compressed")]

new_rows = []
for _ in range(N_BACTERIA):
    vx, vy = random.choice(vessel_positions)
    # scatter within ~40um of a randomly chosen vessel
    r = random.uniform(0, 40)
    theta = random.uniform(0, 2 * math.pi)
    x, y = vx + r * math.cos(theta), vy + r * math.sin(theta)
    new_rows.append([f"{x:.6f}", f"{y:.6f}", "0.0", "Bifidobacterium_longum"])

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    writer.writerows(new_rows)

print(f"seeded {len(new_rows)} Bifidobacterium_longum near vessels, total rows now {len(rows) + len(new_rows)}")
