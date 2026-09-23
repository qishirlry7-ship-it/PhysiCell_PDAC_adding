#!/usr/bin/env python3
"""Count cell types over time from PhysiCell SVG snapshots.

SVG is the reliable source for cell composition: each <circle> carries the
colour produced by my_coloring_function(), and this model's colour table is
1:1 with cell type. The *_cells.mat row layout is NOT reliable for this (it
produced two separate false conclusions in this project).

Usage:
    python scripts/count_from_svg.py <svg_dir_or_glob> [--types A,B] [--csv OUT]
"""
import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXTRA = {13: "brown", 14: "purple", 15: "gold", 16: "teal",
         17: "black", 18: "crimson", 19: "lawngreen",
         20: "white", 21: "white"}
# PhysiCell's paint_by_number_cell_coloring() palette, verbatim from
# modules/PhysiCell_pathology.cpp:1702 -- colors[type] for type 0..12.
DEFAULT = {0: "grey", 1: "red", 2: "yellow", 3: "green", 4: "blue",
           5: "magenta", 6: "orange", 7: "lime", 8: "cyan",
           9: "hotpink", 10: "peachpuff", 11: "darkseagreen", 12: "lightskyblue"}

FILL_RE = re.compile(r'(?:fill\s*[:=]\s*["\']?)([#\w(),. ]+)', re.I)


def type_names():
    t = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    return {int(i): n for n, i in
            re.findall(r'<cell_definition name="([^"]+)" ID="(\d+)"', t)}


def colour_of(tid):
    return EXTRA.get(tid) or DEFAULT.get(tid, "black")


def counts(svg_path):
    txt = Path(svg_path).read_text(encoding="utf-8", errors="ignore")
    c = Counter()
    for m in re.finditer(r"<circle\b([^>]*)>", txt, re.I):
        f = FILL_RE.search(m.group(1))
        if f:
            c[f.group(1).strip().lower()] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="directory or glob of SVGs")
    ap.add_argument("--types", default=None, help="comma-separated type names to show")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    p = Path(args.pattern)
    if p.is_dir():
        files = sorted(p.glob("snapshot*.svg"))
    else:
        files = sorted(Path(ROOT).glob(args.pattern))
    if not files:
        raise SystemExit("no SVGs matched %s" % args.pattern)

    names = type_names()
    col2name = {colour_of(t): n for t, n in names.items()}

    want = None
    if args.types:
        want = set(x.strip() for x in args.types.split(","))

    shown = [n for n in names.values() if (want is None or n in want)]
    shown = sorted(shown)

    print("%-26s %s" % ("snapshot", " ".join("%10s" % n[:10] for n in shown)))
    rows = []
    for f in files:
        c = counts(f)
        byname = defaultdict(int)
        for col, n in c.items():
            nm = col2name.get(col)
            if nm:
                byname[nm] += n
        row = [byname.get(n, 0) for n in shown]
        rows.append((f.name, row))
        print("%-26s %s" % (f.name, " ".join("%10d" % v for v in row)))

    if args.csv:
        out = Path(args.csv)
        if not out.is_absolute():
            out = ROOT / out
        with out.open("w", newline="") as fh:
            fh.write("snapshot," + ",".join(shown) + "\n")
            for nm, row in rows:
                fh.write(nm + "," + ",".join(str(v) for v in row) + "\n")
        print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
