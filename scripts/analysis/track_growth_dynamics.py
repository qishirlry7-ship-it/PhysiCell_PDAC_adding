# -*- coding: utf-8 -*-
"""
Tracks cancer-cell (all tumor-lineage types: PD-L1lo/hi_tumor and their
_infected/_xenophagy variants) population over time by cross-referencing
persistent cell IDs across consecutive full-data checkpoints:
  - a tumor-lineage ID appearing that wasn't live in the previous
    checkpoint = a division event (the only way a brand-new tumor-
    lineage ID can appear; transformations between tumor-lineage types
    keep the same ID so they don't get double-counted here)
  - a tumor-lineage ID that was live last checkpoint but is now dead or
    gone = a death event (apoptosis, necrosis, or CD4/CD8 killing --
    not distinguished here, just "left the live population")
Writes a CSV: time_min,live_count,divisions_this_interval,deaths_this_interval,net_this_interval
"""
import struct, glob, csv

def read_matlab4(path):
    with open(path, "rb") as f:
        data = f.read()
    typ, rows, cols, imag, namelen = struct.unpack_from("<5i", data, 0)
    offset = 20 + namelen
    prec = "d" if (typ % 100) // 10 == 0 else "f"
    count = rows * cols
    vals = struct.unpack_from(f"<{count}{prec}", data, offset)
    mat = [[vals[r + c * rows] for c in range(cols)] for r in range(rows)]
    return rows, cols, mat

TUMOR_LINEAGE = {0, 1, 20, 21, 22, 23}
INTERVAL_MIN = 60  # matches full_data save interval

mats = sorted(glob.glob("outputs/pdac_therapy/output*_cells.mat"))
prev_live_ids = None
out_rows = []

for idx, path in enumerate(mats):
    rows, cols, mat = read_matlab4(path)
    id_row, type_row, dead_row = mat[0], mat[5], mat[26]
    live_ids = set()
    for c in range(cols):
        t = int(round(type_row[c]))
        if t in TUMOR_LINEAGE and dead_row[c] < 0.5:
            live_ids.add(int(round(id_row[c])))

    if prev_live_ids is None:
        divisions = 0
        deaths = 0
    else:
        divisions = len(live_ids - prev_live_ids)
        deaths = len(prev_live_ids - live_ids)

    out_rows.append((idx * INTERVAL_MIN, len(live_ids), divisions, deaths, divisions - deaths))
    prev_live_ids = live_ids

with open("scripts/analysis/growth_dynamics.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_min", "live_count", "divisions_this_interval", "deaths_this_interval", "net_this_interval"])
    w.writerows(out_rows)

print(f"wrote scripts/analysis/growth_dynamics.csv, {len(out_rows)} checkpoints")
for r in out_rows[:5] + out_rows[-5:]:
    print(r)
