# -*- coding: utf-8 -*-
"""TEST ONLY -- seeds 15 PD-L1lo_tumor_infected cells directly (converting
existing tumor cell rows), to isolate-test the infected->xenophagy->CD4-
attack chain without waiting on slow stochastic colonization. Reverted
before final commit."""
import csv

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

converted = 0
for r in rows:
    if r[3] == "PD-L1lo_tumor" and converted < 15:
        r[3] = "PD-L1lo_tumor_infected"
        converted += 1

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)

print(f"converted {converted} PD-L1lo_tumor rows to PD-L1lo_tumor_infected for isolated testing")
