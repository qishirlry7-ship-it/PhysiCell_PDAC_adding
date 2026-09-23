#!/usr/bin/env python3
"""Compare two runs of the same model configuration.

Reports, side by side:
  - bacterial uptake events (count, first time, per-day rate)
  - infection onset and the number of distinct infected tumour cells
  - mhcii_cd4_recognition trajectory (max, and how early it crosses threshold)
  - per-cell-type counts from the SVG snapshots (RELIABLE source; the .mat row
    layout is not trustworthy -- see the project notes)

Usage:
    python scripts/compare_runs.py <runA_dir> <runB_dir> [--labels A,B]
"""
import argparse
import csv
import glob
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# verbatim from modules/PhysiCell_pathology.cpp:1702
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


def svg_counts(svg_path):
    txt = Path(svg_path).read_text(encoding="utf-8", errors="ignore")
    c = Counter()
    for m in re.finditer(r"<circle\b([^>]*)>", txt, re.I):
        f = FILL_RE.search(m.group(1))
        if f:
            c[f.group(1).strip().lower()] += 1
    return c


def summarise(d):
    out = {}
    # uptake
    u = d / "bacterial_uptake.csv"
    if u.exists():
        rows = list(csv.DictReader(u.open()))
        acc = [r for r in rows if r.get("result") == "accepted"]
        out["uptake_total"] = len(acc)
        if acc:
            ts = sorted(float(r["time_min"]) for r in acc)
            out["uptake_first"] = ts[0]
            out["uptake_last"] = ts[-1]
            out["infected_tumours"] = len(set(r["tumor_id"] for r in acc))
    # metrics
    f = d / "xenophagy_metrics.csv"
    if f.exists():
        rows = list(csv.DictReader(f.open()))
        if rows:
            t = np.array([float(r["time_min"]) for r in rows])
            rec = np.array([float(r["mhcii_cd4_recognition"]) for r in rows])
            out["metrics_rows"] = len(rows)
            out["sim_time"] = float(t.max())
            out["recog_max"] = float(rec.max())
            over = t[rec > 0.5]
            out["recog_first_over_0.5"] = float(over.min()) if over.size else None
            out["recog_frac_over_0.5"] = float((rec > 0.5).mean())
            out["infected_cells_metrics"] = len(set(r["cell_id"] for r in rows))
    # svg-based composition (reliable)
    svgs = sorted(d.glob("snapshot*.svg"))
    if svgs:
        names = type_names()
        col2name = {EXTRA.get(k) or DEFAULT.get(k, "black"): v for k, v in names.items()}
        last = svg_counts(svgs[-1])
        comp = defaultdict(int)
        for col, n in last.items():
            if col in col2name:
                comp[col2name[col]] += n
        out["svg_last"] = dict(comp)
        out["svg_count"] = len(svgs)
        # bacteria over time
        bac_series = []
        for s in svgs:
            c = svg_counts(s)
            bac_series.append(sum(v for k, v in c.items() if col2name.get(k, "").startswith("Bifido")))
        out["bacteria_max"] = max(bac_series) if bac_series else 0
        out["bacteria_mean"] = float(np.mean(bac_series)) if bac_series else 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--labels", default=None)
    args = ap.parse_args()

    a = Path(args.run_a)
    b = Path(args.run_b)
    if not a.is_absolute():
        a = ROOT / a
    if not b.is_absolute():
        b = ROOT / b
    labels = args.labels.split(",") if args.labels else [a.name, b.name]

    sa, sb = summarise(a), summarise(b)
    keys = ["sim_time", "uptake_total", "uptake_first", "uptake_last",
            "infected_tumours", "infected_cells_metrics", "metrics_rows",
            "recog_max", "recog_first_over_0.5", "recog_frac_over_0.5",
            "bacteria_max", "bacteria_mean", "svg_count"]

    print("=" * 78)
    print("%-28s %18s %18s" % ("metric", labels[0][:18], labels[1][:18]))
    print("=" * 78)
    for k in keys:
        va, vb = sa.get(k), sb.get(k)
        fa = ("%.4g" % va) if isinstance(va, (int, float)) else str(va)
        fb = ("%.4g" % vb) if isinstance(vb, (int, float)) else str(vb)
        print("%-28s %18s %18s" % (k, fa, fb))

    print("\n" + "=" * 78)
    print("CD4 composition at the LAST SVG of each run")
    print("=" * 78)
    allk = set()
    for s in (sa, sb):
        for k in s.get("svg_last", {}):
            if "CD4" in k:
                allk.add(k)
    for k in sorted(allk):
        print("   %-26s %-18s %s" % (k, sa.get("svg_last", {}).get(k, 0),
                                     sb.get("svg_last", {}).get(k, 0)))


if __name__ == "__main__":
    main()
