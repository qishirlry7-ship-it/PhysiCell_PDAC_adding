#!/usr/bin/env python3
"""Zoom in on where the bacteria actually are, relative to vessels and tumour.

Answers "why are the bacteria so far from the tumour?" by drawing, for one
SVG snapshot:
  - all tumour cells (light grey background scatter)
  - all vessels (black / crimson)
  - every bacterium, with a line to its nearest vessel and nearest tumour cell,
    annotated with both distances

Usage:
    python scripts/bacteria_context.py <snapshot.svg> [--radius 200] [--out PNG]
"""
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parent.parent

# verbatim from modules/PhysiCell_pathology.cpp:1702 (type 0..12)
DEFAULT = {0: "grey", 1: "red", 2: "yellow", 3: "green", 4: "blue",
           5: "magenta", 6: "orange", 7: "lime", 8: "cyan",
           9: "hotpink", 10: "peachpuff", 11: "darkseagreen", 12: "lightskyblue"}
EXTRA = {13: "brown", 14: "purple", 15: "gold", 16: "teal",
         17: "black", 18: "crimson", 19: "lawngreen",
         20: "white", 21: "white"}

FILL_RE = re.compile(r'(?:fill\s*[:=]\s*["\']?)([#\w(),. ]+)', re.I)


def type_names():
    t = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    return {int(i): n for n, i in
            re.findall(r'<cell_definition name="([^"]+)" ID="(\d+)"', t)}


def parse(path):
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in re.finditer(r"<circle\b([^>]*)>", txt, re.I):
        a = m.group(1)
        def num(k):
            mm = re.search(r'\b%s="([-\d.eE+]+)"' % k, a)
            return float(mm.group(1)) if mm else None
        cx, cy, r = num("cx"), num("cy"), num("r")
        if None in (cx, cy, r):
            continue
        f = FILL_RE.search(a)
        out.append((cx, cy, r, f.group(1).strip().lower() if f else "black"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--radius", type=float, default=200.0,
                    help="half-width of the zoom window centred on bacteria")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    p = Path(args.svg)
    if not p.is_absolute():
        p = ROOT / p
    cells = parse(p)
    names = type_names()
    col2name = {}
    for tid, nm in names.items():
        col2name[EXTRA.get(tid) or DEFAULT.get(tid, "black")] = nm

    tum_c, ves_c, bac_c = "grey", {"black", "crimson"}, "lawngreen"
    tum = np.array([(x, y) for x, y, r, c in cells if c == tum_c])
    ves = np.array([(x, y) for x, y, r, c in cells if c in ves_c])
    bac = np.array([(x, y) for x, y, r, c in cells if c == bac_c])

    print("tumour=%d  vessels=%d  bacteria=%d" % (len(tum), len(ves), len(bac)))
    if len(bac) == 0:
        raise SystemExit("no bacteria in this snapshot")

    from scipy.spatial import cKDTree
    tt = cKDTree(tum) if len(tum) else None
    tv = cKDTree(ves) if len(ves) else None

    print("\nper-bacterium distances (micron):")
    print("%8s %14s %14s" % ("id", "to_vessel", "to_tumour"))
    for i, (x, y) in enumerate(bac):
        dv = tv.query([x, y])[0] if tv else float("nan")
        dt = tt.query([x, y])[0] if tt else float("nan")
        print("%8d %14.1f %14.1f" % (i, dv, dt))

    cx, cy = bac.mean(axis=0)
    fig, ax = plt.subplots(figsize=(10, 10))
    for x, y, r, c in cells:
        if abs(x - cx) > args.radius * 1.6 or abs(y - cy) > args.radius * 1.6:
            continue
        ax.add_patch(Circle((x, y), r, facecolor=c, edgecolor="none", alpha=0.85))

    for i, (x, y) in enumerate(bac):
        if tv:
            dv, jv = tv.query([x, y])
            ax.plot([x, ves[jv, 0]], [y, ves[jv, 1]], "-", color="blue", lw=1.0, alpha=0.8)
        if tt:
            dt, jt = tt.query([x, y])
            ax.plot([x, tum[jt, 0]], [y, tum[jt, 1]], "--", color="red", lw=1.0, alpha=0.8)
        ax.annotate("b%d\nv=%.0f\nt=%.0f" % (i, dv, dt), (x, y),
                    textcoords="offset points", xytext=(8, 8), fontsize=8, color="darkgreen")

    ax.set_xlim(cx - args.radius, cx + args.radius)
    ax.set_ylim(cy - args.radius, cy + args.radius)
    ax.set_aspect("equal")
    ax.set_title("%s  (green=bacteria, black/crimson=vessel, grey=tumour)\n"
                 "solid blue = to nearest vessel, dashed red = to nearest tumour" % p.name,
                 fontsize=10)
    out = Path(args.out) if args.out else p.with_name(p.stem + "_bacteria.png")
    if not out.is_absolute():
        out = ROOT / out
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
