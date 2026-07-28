# -*- coding: utf-8 -*-
"""
Adds the 8 new cell types to PDAC_TISSUE_1.csv (the untreated baseline
sample that config/PhysiCell_settings.xml currently points to), via
rejection sampling in the radial zones agreed with the user:
  - myCAF / iCAF: 0-320 um (within + tight around the existing tumor mass)
  - M-MDSC / PMN-MDSC: 200-320 um (juxtatumoral transition band)
  - Treg / cDC1 / B_cell / NK_cell: 300-500 um (existing T-cell band)
Original 1237 rows (9 pdac_therapy cell types) are left completely
untouched -- this only appends new rows.
"""
import csv, math, random

random.seed(0)

SRC = "config/ic_cells/PDAC_TISSUE_1.csv"
OUT = "config/ic_cells/PDAC_TISSUE_1_hybrid.csv"

VOLUME = 2494.0  # matches this project's uniform default cell volume
RADIUS = (3.0 * VOLUME / (4.0 * math.pi)) ** (1.0 / 3.0)  # ~8.4 um
MIN_SPACING = 1.10 * (2 * RADIUS)  # ~18.5 um between any two cell centers

NEW_CELLS = [
    # name, count, r_min, r_max
    ("myCAF", 250, 0, 320),
    ("iCAF", 100, 0, 320),
    ("M_MDSC", 30, 200, 320),
    ("PMN_MDSC", 40, 200, 320),
    ("Treg", 18, 300, 500),
    ("cDC1", 8, 300, 500),
    ("B_cell", 10, 300, 500),
    ("NK_cell", 8, 300, 500),
]

with open(SRC, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

existing_points = [(float(r[0]), float(r[1])) for r in rows]

def place_one(r_min, r_max, existing, max_tries=300):
    for _ in range(max_tries):
        r = math.sqrt(random.uniform(r_min**2, r_max**2))
        theta = random.uniform(0, 2 * math.pi)
        x, y = r * math.cos(theta), r * math.sin(theta)
        ok = True
        for (ex, ey) in existing[-400:]:  # local check window for speed
            if (ex - x) ** 2 + (ey - y) ** 2 < MIN_SPACING ** 2:
                ok = False
                break
        if ok:
            return x, y
    return None

new_rows = []
placed_summary = []
for name, count, r_min, r_max in NEW_CELLS:
    placed = 0
    local_points = list(existing_points)
    for _ in range(count):
        pt = place_one(r_min, r_max, local_points)
        if pt is None:
            continue
        x, y = pt
        new_rows.append([f"{x:.6f}", f"{y:.6f}", "0.0", name])
        local_points.append(pt)
        existing_points.append(pt)
        placed += 1
    placed_summary.append((name, placed, count))

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    writer.writerows(new_rows)

print(f"wrote {OUT}: {len(rows)} original + {len(new_rows)} new = {len(rows) + len(new_rows)} total rows")
for name, placed, requested in placed_summary:
    flag = "" if placed == requested else "  <-- UNDERPLACED"
    print(f"  {name}: placed {placed}/{requested}{flag}")
