# -*- coding: utf-8 -*-
"""Reverts the two TEST-ONLY changes (seed_infected_for_test.py,
toggle_rapamycin_test.py) back to the real default (no-drug) state
before committing."""
import csv

IC = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"
with open(IC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

reverted = 0
for r in rows:
    if r[3] == "PD-L1lo_tumor_infected":
        r[3] = "PD-L1lo_tumor"
        reverted += 1

with open(IC, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
print(f"reverted {reverted} test-seeded _infected rows back to PD-L1lo_tumor")

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()
old = '<initial_condition units="dimensionless">5</initial_condition>'
new = '<initial_condition units="dimensionless">0</initial_condition>'
n = xml.count(old)
assert n == 1, n
xml = xml.replace(old, new)
with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print("reverted rapamycin initial_condition 5 -> 0 (default no-drug state)")
