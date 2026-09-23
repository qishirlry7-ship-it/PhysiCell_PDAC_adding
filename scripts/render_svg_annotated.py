#!/usr/bin/env python3
"""Render a PhysiCell SVG snapshot with an annotated colour legend.

PhysiCell colours cells via my_coloring_function(). We map the colours that
appear back to the cell types this model uses, so bacteria / vessels / resting
vs activated CD4 can be told apart at a glance.

The colour->type mapping is read from custom_modules/custom.cpp's
extra_colors table for types >= 13, and PhysiCell's built-in
paint_by_number_cell_coloring() palette for types 0..12.

Usage:
    python scripts/render_svg_annotated.py <snapshot.svg> [--out PNG]
"""
import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent

# extra_colors from custom.cpp (index = type - 13)
EXTRA = {
    13: "brown", 14: "purple", 15: "gold", 16: "teal",
    17: "black", 18: "crimson", 19: "lawngreen",
    20: "white", 21: "white",
}
# PhysiCell's paint_by_number_cell_coloring() palette, taken verbatim from
# modules/PhysiCell_pathology.cpp:1702 -- order matters, colors[type].
DEFAULT = {
    0: "grey", 1: "red", 2: "yellow", 3: "green", 4: "blue",
    5: "magenta", 6: "orange", 7: "lime", 8: "cyan",
    9: "hotpink", 10: "peachpuff", 11: "darkseagreen", 12: "lightskyblue",
}


def type_names():
    t = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    return {int(i): n for n, i in
            re.findall(r'<cell_definition name="([^"]+)" ID="(\d+)"', t)}


def colour_of(type_id):
    return EXTRA.get(type_id) or DEFAULT.get(type_id, "black")


FILL_RE = re.compile(r'(?:fill\s*[:=]\s*["\']?)([#\w(),. ]+)', re.I)


def parse_svg(path):
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in re.finditer(r"<circle\b([^>]*)>", txt, re.I):
        attrs = m.group(1)
        def num(name):
            mm = re.search(r'\b%s="([-\d.eE+]+)"' % name, attrs)
            return float(mm.group(1)) if mm else None
        cx, cy, r = num("cx"), num("cy"), num("r")
        if cx is None or cy is None or r is None:
            continue
        f = FILL_RE.search(attrs)
        out.append((cx, cy, r, (f.group(1).strip().lower() if f else "black")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    p = Path(args.svg)
    if not p.is_absolute():
        p = ROOT / p
    cells = parse_svg(p)
    if not cells:
        raise SystemExit("no circles in %s" % p)

    names = type_names()
    colour2type = defaultdict(list)
    for tid, nm in names.items():
        colour2type[colour_of(tid)].append(nm)

    present = Counter(c[3] for c in cells)

    print("colour -> type mapping used by this model:")
    for col, tids in sorted(colour2type.items()):
        n = present.get(col, 0)
        print("   %-16s %-40s in svg: %d" % (col, ", ".join(tids), n))
    unmatched = {c: n for c, n in present.items() if c not in colour2type}
    if unmatched:
        print("\ncolours in the SVG with no model type (background/legend/etc):")
        for c, n in sorted(unmatched.items(), key=lambda kv: -kv[1])[:10]:
            print("   %-16s %d" % (c, n))

    fig, ax = plt.subplots(figsize=(10, 10))
    for cx, cy, r, fill in cells:
        ax.add_patch(Circle((cx, cy), r, facecolor=fill, edgecolor="none"))
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.set_title(p.name, fontsize=11)

    handles = []
    for tid in sorted(names):
        col = colour_of(tid)
        if present.get(col, 0) > 0:
            handles.append(Line2D([], [], marker="o", ls="", ms=7,
                                  markerfacecolor=col, markeredgecolor="gray",
                                  label="%s (ID %d, n=%d)" % (names[tid], tid, present[col])))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)

    out = Path(args.out) if args.out else p.with_name(p.stem + "_annotated.png")
    if not out.is_absolute():
        out = ROOT / out
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
