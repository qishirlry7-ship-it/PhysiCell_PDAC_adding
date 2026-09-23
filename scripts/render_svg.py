#!/usr/bin/env python3
"""Render a PhysiCell SVG snapshot with matplotlib.

PhysiCell's SVG output is plain geometry: one <circle> per cell with cx/cy/r
and a fill colour. Parsing that directly avoids needing cairosvg/svglib, and
lets us highlight chosen cell types (bacteria, vessels, infected tumours)
which the flat SVG does not distinguish beyond colour.

Usage:
    python scripts/render_svg.py <snapshot.svg> [--out PNG] [--highlight]
"""
import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parent.parent

CIRCLE_RE = re.compile(
    r'<circle[^>]*\bcx="([-\d.eE+]+)"[^>]*\bcy="([-\d.eE+]+)"[^>]*\br="([-\d.eE+]+)"[^>]*'
    r'(?:fill:\s*([^;"\']+))?', re.I)

# PhysiCell writes either style="fill:..." or fill="..."
FILL_RE = re.compile(r'(?:fill\s*[:=]\s*["\']?)([#\w(),. ]+)', re.I)


def parse_svg(path):
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    cells = []
    for m in re.finditer(r"<circle\b([^>]*)>", txt, re.I):
        attrs = m.group(1)
        def num(name):
            mm = re.search(r'\b%s="([-\d.eE+]+)"' % name, attrs)
            return float(mm.group(1)) if mm else None
        cx, cy, r = num("cx"), num("cy"), num("r")
        if cx is None or cy is None or r is None:
            continue
        f = FILL_RE.search(attrs)
        fill = f.group(1).strip() if f else "black"
        cells.append((cx, cy, r, fill))
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--out", default=None)
    ap.add_argument("--radius-scale", type=float, default=1.0)
    args = ap.parse_args()

    p = Path(args.svg)
    if not p.is_absolute():
        p = ROOT / p
    cells = parse_svg(p)
    if not cells:
        raise SystemExit("no <circle> elements parsed from %s" % p)

    print("parsed %d circles" % len(cells))
    from collections import Counter
    col = Counter(c[3].lower() for c in cells)
    print("top colours:")
    for k, v in col.most_common(15):
        print("   %-22s %d" % (k, v))

    fig, ax = plt.subplots(figsize=(9, 9))
    for cx, cy, r, fill in cells:
        try:
            ax.add_patch(Circle((cx, cy), r * args.radius_scale,
                                facecolor=fill, edgecolor="none"))
        except Exception:
            ax.add_patch(Circle((cx, cy), r * args.radius_scale,
                                facecolor="gray", edgecolor="none"))
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.set_title(p.name)
    ax.set_xlabel("x (micron)")
    ax.set_ylabel("y (micron)")

    out = Path(args.out) if args.out else p.with_suffix(".png")
    if not out.is_absolute():
        out = ROOT / out
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
