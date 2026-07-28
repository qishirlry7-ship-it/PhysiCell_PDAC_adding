# -*- coding: utf-8 -*-
"""
Appends 18 stationary fixed_vessel_source cells to
config/ic_cells/PDAC_TISSUE_1_hybrid.csv, in a ring around the currently-
populated region (which extends out to ~500 um for the T-cell/NK/B/cDC1
band), reflecting real PDAC's hypovascular tumor core with perfusion
concentrated at the tumor margin/surrounding stroma rather than inside it.
"""
import csv, math, random

random.seed(1)

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
N_VESSELS = 18
R_MIN, R_MAX = 420, 550

with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

new_rows = []
for k in range(N_VESSELS):
    theta = 2 * math.pi * k / N_VESSELS + random.uniform(-0.15, 0.15)
    r = random.uniform(R_MIN, R_MAX)
    x, y = r * math.cos(theta), r * math.sin(theta)
    new_rows.append([f"{x:.6f}", f"{y:.6f}", "0.0", "fixed_vessel_source"])

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    writer.writerows(new_rows)

print(f"appended {len(new_rows)} fixed_vessel_source cells, total rows now {len(rows) + len(new_rows)}")
