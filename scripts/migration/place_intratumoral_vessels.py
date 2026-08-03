# -*- coding: utf-8 -*-
"""
Places 5 fixed_vessel_source_compressed cells scattered within the
tumor core (radius 0-250um, well inside the existing 0-320um tumor+
stroma zone), fewer than the 18 peripheral vessels, per the approved
"few, compressed" design.
"""
import csv, math, random

random.seed(2)

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
N_VESSELS = 5
R_MAX = 250

with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

new_rows = []
for k in range(N_VESSELS):
    theta = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, R_MAX)
    x, y = r * math.cos(theta), r * math.sin(theta)
    new_rows.append([f"{x:.6f}", f"{y:.6f}", "0.0", "fixed_vessel_source_compressed"])

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    writer.writerows(new_rows)

print(f"appended {len(new_rows)} fixed_vessel_source_compressed cells, total rows now {len(rows) + len(new_rows)}")
