# -*- coding: utf-8 -*-
"""
Renders substrate concentration fields (oxygen + a representative set of
cytokines) as heatmaps, one PPM/PNG per checkpoint, for later ffmpeg
animation. Pure stdlib (no numpy/matplotlib available in this
environment) -- writes raw PPM (P6) images directly.
"""
import struct, glob, os, xml.etree.ElementTree as ET

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

def colormap(v, vmin, vmax):
    # simple blue -> cyan -> green -> yellow -> red perceptual-ish ramp
    if vmax <= vmin:
        t = 0.0
    else:
        t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
    stops = [
        (0.00, (13, 8, 135)),
        (0.25, (84, 2, 163)),
        (0.50, (204, 71, 120)),
        (0.75, (248, 149, 64)),
        (1.00, (240, 249, 33)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(int(c0[k] + f * (c1[k] - c0[k])) for k in range(3))
    return stops[-1][1]

def write_ppm(path, grid, n, vmin, vmax):
    with open(path, "wb") as f:
        f.write(f"P6\n{n} {n}\n255\n".encode())
        for row in range(n - 1, -1, -1):  # flip y so north is up
            for col in range(n):
                r, g, b = colormap(grid[row][col], vmin, vmax)
                f.write(bytes([r, g, b]))

SUBSTRATES = ["oxygen", "glucose", "lactate", "ECM", "TGF_beta", "IFN_gamma", "Gal8_ext"]
RANGES = {  # fixed color-scale range per substrate so frames are comparable across time
    "oxygen": (0, 25),
    "glucose": (0, 1.0),
    "lactate": (0, 8),
    "ECM": (0, 10),
    "TGF_beta": (0, 5),
    "IFN_gamma": (0, 5),
    "Gal8_ext": (0, 15),  # spans both biphasic thresholds (half_max=1 costim, half_max=10 apoptosis)
}

mats = sorted(glob.glob("outputs/pdac_therapy/output*_microenvironment0.mat"))
out_dir = "scripts/analysis/field_frames"
os.makedirs(out_dir, exist_ok=True)

# get substrate IDs once
xml0 = mats[0].replace("_microenvironment0.mat", ".xml")
tree = ET.parse(xml0)
ids = {v.get("name"): int(v.get("ID")) for v in tree.iter("variable")}

N = 100  # 2000um / 20um

for sub in SUBSTRATES:
    os.makedirs(os.path.join(out_dir, sub), exist_ok=True)

for frame_idx, path in enumerate(mats):
    rows, cols, mat = read_matlab4(path)
    x_row, y_row = mat[0], mat[1]
    for sub in SUBSTRATES:
        val_row = mat[4 + ids[sub]]
        grid = [[0.0] * N for _ in range(N)]
        for c in range(cols):
            col = int(round((x_row[c] + 1000) / 20 - 0.5))
            row = int(round((y_row[c] + 1000) / 20 - 0.5))
            if 0 <= row < N and 0 <= col < N:
                grid[row][col] = val_row[c]
        vmin, vmax = RANGES[sub]
        write_ppm(os.path.join(out_dir, sub, f"frame_{frame_idx:04d}.ppm"), grid, N, vmin, vmax)

print(f"wrote {len(mats)} frames x {len(SUBSTRATES)} substrates to {out_dir}/<substrate>/frame_XXXX.ppm")
