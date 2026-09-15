# -*- coding: utf-8 -*-
"""
Domain-mean concentration of the 7 tracked substrates (oxygen, glucose,
lactate, ECM, TGF_beta, IFN_gamma, Gal8_ext) at every full_data checkpoint.
Pure stdlib (no numpy/scipy in this environment) -- reads the same MATLAB
level-4 .mat format as track_growth_dynamics.py / make_field_heatmaps.py.
Writes scripts/analysis/substrate_means.csv.
"""
import struct, glob, csv, xml.etree.ElementTree as ET

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

SUBSTRATES = ["oxygen", "glucose", "lactate", "ECM", "TGF_beta", "IFN_gamma", "Gal8_ext"]
INTERVAL_MIN = 60

mats = sorted(glob.glob("outputs/pdac_therapy/output*_microenvironment0.mat"))
assert mats, "no microenvironment checkpoints found"

xml0 = mats[0].replace("_microenvironment0.mat", ".xml")
tree = ET.parse(xml0)
ids = {v.get("name"): int(v.get("ID")) for v in tree.iter("variable")}

out_rows = []
for idx, path in enumerate(mats):
    rows, cols, mat = read_matlab4(path)
    means = []
    for sub in SUBSTRATES:
        val_row = mat[4 + ids[sub]]
        means.append(sum(val_row) / len(val_row))
    out_rows.append([idx * INTERVAL_MIN] + means)

with open("scripts/analysis/substrate_means.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_min"] + SUBSTRATES)
    w.writerows(out_rows)

print(f"wrote scripts/analysis/substrate_means.csv, {len(out_rows)} checkpoints")
for r in out_rows[:3] + out_rows[-3:]:
    print(r)
