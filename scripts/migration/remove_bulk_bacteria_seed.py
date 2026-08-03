# -*- coding: utf-8 -*-
"""
Removes the bulk 40-bacteria initial seed (place_bifidobacterium.py),
per the user's correction: bacteria should enter the tumor
probabilistically over time via recruit_bacteria() in custom.cpp, not
as a one-time bolus at t=0. Simulation now starts with zero bacteria.
"""
import csv

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

kept = [r for r in rows if r[3] != "Bifidobacterium_longum"]
removed = len(rows) - len(kept)

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(kept)

print(f"removed {removed} bulk-seeded Bifidobacterium_longum rows, {len(kept)} rows remain")
