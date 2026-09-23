#!/usr/bin/env python3
"""Track bacteria across SVG snapshots and measure their motion.

Answers two questions directly:
  1. Are the bacteria actually MOVING TOWARD the tumour, and how fast?
  2. How long do individual bacteria survive?

For each bacterium we record its position per snapshot, match it to the
nearest track from the previous snapshot (simple greedy nearest-neighbour
matching; adequate here because bacteria are few and far apart), and report
per-track displacement, speed, and the change in distance-to-nearest-tumour.

Usage:
    python scripts/track_bacteria.py <svg_dir> [--tumour-colour grey] [--csv OUT]
"""
import argparse
import re
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent

DEFAULT = {0: "grey", 1: "red", 2: "yellow", 3: "green", 4: "blue",
           5: "magenta", 6: "orange", 7: "lime", 8: "cyan",
           9: "hotpink", 10: "peachpuff", 11: "darkseagreen", 12: "lightskyblue"}
EXTRA = {13: "brown", 14: "purple", 15: "gold", 16: "teal",
         17: "black", 18: "crimson", 19: "lawngreen",
         20: "white", 21: "white"}

FILL_RE = re.compile(r'(?:fill\s*[:=]\s*["\']?)([#\w(),. ]+)', re.I)
TUMOUR_COLOURS = {"grey"}
BACTERIA_COLOUR = "lawngreen"
VESSEL_COLOURS = {"black", "crimson"}


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
    ap.add_argument("svg_dir")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    d = Path(args.svg_dir)
    if not d.is_absolute():
        d = ROOT / d
    files = sorted(d.glob("snapshot*.svg"))
    if not files:
        raise SystemExit("no SVGs in %s" % d)

    # SVGs are saved every SVG_save_interval; infer dt from the interval in config
    cfg = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    m = re.search(r"<SVG_save_interval[^>]*>([^<]+)</SVG_save_interval>", cfg)
    dt_min = float(m.group(1)) if m else 6.0

    tracks = []          # list of dicts: {"pts": [(t, x, y), ...]}
    prev_bac = None
    prev_tum = None

    for idx, f in enumerate(files):
        cells = parse(f)
        bac = np.array([(x, y) for x, y, r, c in cells if c == BACTERIA_COLOUR])
        tum = np.array([(x, y) for x, y, r, c in cells if c in TUMOUR_COLOURS])
        ves = np.array([(x, y) for x, y, r, c in cells if c in VESSEL_COLOURS])
        t = idx * dt_min

        if len(bac) == 0:
            prev_bac = None
            continue

        if prev_bac is None or len(prev_bac) == 0:
            for p in bac:
                tracks.append({"pts": [(t, p[0], p[1])]})
        else:
            tt = cKDTree(prev_bac)
            used = set()
            for p in bac:
                dist, j = tt.query(p)
                if dist < 40.0 and j not in used:
                    used.add(j)
                    tracks[j]["pts"].append((t, p[0], p[1]))
                else:
                    tracks.append({"pts": [(t, p[0], p[1])]})
        prev_bac = bac

    print("bacteria tracks found: %d   (svg dt = %g min)" % (len(tracks), dt_min))

    # tumour centroid over time (for a directional reference)
    cells = parse(files[-1])
    tum_last = np.array([(x, y) for x, y, r, c in cells if c in TUMOUR_COLOURS])
    tum_centroid = tum_last.mean(axis=0) if len(tum_last) else np.array([0.0, 0.0])
    print("final tumour centroid: (%.0f, %.0f)" % tuple(tum_centroid))

    print("\n%-6s %6s %8s %10s %12s %14s" %
          ("track", "steps", "dur(min)", "net_move", "speed", "d_to_tum_chg"))
    rows = []
    for i, tr in enumerate(tracks):
        pts = tr["pts"]
        if len(pts) < 2:
            continue
        t0, x0, y0 = pts[0]
        t1, x1, y1 = pts[-1]
        dur = t1 - t0
        net = np.hypot(x1 - x0, y1 - y0)
        speed = net / dur if dur > 0 else 0.0
        d0 = np.hypot(x0 - tum_centroid[0], y0 - tum_centroid[1])
        d1 = np.hypot(x1 - tum_centroid[0], y1 - tum_centroid[1])
        rows.append((i, len(pts), dur, net, speed, d1 - d0))
        print("%-6d %6d %8.0f %10.1f %12.3f %14.1f" %
              (i, len(pts), dur, net, speed, d1 - d0))

    if rows:
        arr = np.array([(r[4], r[5]) for r in rows])
        print("\nsummary over %d track(s) with >=2 points:" % len(rows))
        print("   speed (micron/min): median=%.3f  mean=%.3f  max=%.3f" %
              (np.median(arr[:, 0]), arr[:, 0].mean(), arr[:, 0].max()))
        print("   change in distance-to-tumour-centroid: median=%+.1f  mean=%+.1f" %
              (np.median(arr[:, 1]), arr[:, 1].mean()))
        print("   tracks that got CLOSER to the tumour: %d / %d" %
              ((arr[:, 1] < 0).sum(), len(arr)))
        print("\n   configured speed = 0.3 micron/min (from <motility><speed>)")

    if args.csv:
        out = Path(args.csv)
        if not out.is_absolute():
            out = ROOT / out
        with out.open("w") as fh:
            fh.write("track,steps,duration_min,net_move_micron,speed_micron_per_min,d_to_tumour_change\n")
            for r in rows:
                fh.write(",".join(str(x) for x in r) + "\n")
        print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
