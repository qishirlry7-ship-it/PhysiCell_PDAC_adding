#!/usr/bin/env python3
"""Visualise the MHC-II -> CD4 activation loop over a run.

Reads, from an output directory:
  - xenophagy_metrics.csv   (per-cell PetriNet + MHC state, written by the
                             adapter every petrinet_metrics_interval)
  - <tag>_cells.mat         (cell type composition at initial/final)

Produces a multi-panel figure:
  1. surface pMHC-II over time (per infected cell), with the
     mhcii_cd4_half_max line for reference
  2. mhcii_cd4_recognition over time, with the activation threshold line
  3. tumour / immune cell counts from the saved cell snapshots
  4. bacterial burden over time

Usage:
    python scripts/plot_cd4_loop.py <output_dir> [--out PNG]
"""
import argparse
import csv
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent.parent


def read_metrics(out_dir):
    f = out_dir / "xenophagy_metrics.csv"
    if not f.exists():
        return None
    with f.open() as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return None
    cols = ["time_min", "surface_pMHC_II", "surface_pMHC_I",
            "mhcii_cd4_recognition", "intracellular_bacteria",
            "xenophagy_activity", "uptake"]
    data = {c: [] for c in cols if c != "uptake"}
    for r in rows:
        for c in data:
            try:
                data[c].append(float(r[c]))
            except (KeyError, ValueError):
                data[c].append(np.nan)
    return {k: np.asarray(v) for k, v in data.items()}


def cell_type_names():
    t = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    return {int(i): n for n, i in
            re.findall(r'<cell_definition name="([^"]+)" ID="(\d+)"', t)}


def read_snapshot_counts(out_dir):
    """[(tag, {type_name: count})] for every saved *_cells.mat we can read."""
    names = cell_type_names()
    out = []
    for f in sorted(out_dir.glob("*_cells.mat")):
        try:
            m = loadmat(str(f))
        except Exception:
            continue
        keys = [k for k in m if not k.startswith("__")]
        if not keys:
            continue
        arr = np.asarray(m[keys[0]], dtype=float)
        if arr.shape[0] < 6:
            continue
        types = arr[5, :].astype(int)
        counts = {}
        for t_, c in zip(*np.unique(types, return_counts=True)):
            counts[names.get(int(t_), "ID%d" % t_)] = int(c)
        out.append((f.name.replace("_cells.mat", ""), counts))
    return out


def cfg_number(text, tag, default=None):
    m = re.search(r'<%s[^>]*>([^<]*)</%s>' % (tag, tag), text)
    if not m:
        return default
    try:
        return float(m.group(1))
    except ValueError:
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    d = Path(args.out_dir)
    if not d.is_absolute():
        d = ROOT / d
    if not d.is_dir():
        raise SystemExit("no such directory: %s" % d)

    m = read_metrics(d)
    snaps = read_snapshot_counts(d)
    if m is None and not snaps:
        raise SystemExit("nothing to plot in %s (no metrics and no cell snapshots)" % d)

    cfg = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
    half_max = cfg_number(cfg, "mhcii_cd4_half_max", None)
    if half_max is None:
        pm = ROOT / "config" / "petrinet" / "parameters.xml"
        if pm.exists():
            half_max = cfg_number(pm.read_text(encoding="utf-8"), "mhcii_cd4_half_max", 30.0)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("MHC-II -> CD4 activation loop   (%s)" % d.name, fontsize=13)

    # 1. pMHC-II over time
    ax = axes[0][0]
    if m is not None:
        order = np.argsort(m["time_min"])
        ax.plot(m["time_min"][order], m["surface_pMHC_II"][order], "o-",
                ms=3, lw=0.8, color="tab:red", label="surface pMHC-II")
        if half_max:
            ax.axhline(half_max, color="gray", ls="--", lw=1,
                       label="mhcii_cd4_half_max = %g" % half_max)
        ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("molecules / cell")
    ax.set_title("1. MHC-II presentation on infected tumours")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # 2. recognition + threshold
    ax = axes[0][1]
    if m is not None:
        order = np.argsort(m["time_min"])
        ax.plot(m["time_min"][order], m["mhcii_cd4_recognition"][order], "o-",
                ms=3, lw=0.8, color="tab:purple", label="mhcii_cd4_recognition")
        thr = cfg_number(cfg, "cd4_activation_threshold", 0.5)
        ax.axhline(thr, color="green", ls="--", lw=1.2,
                   label="activation threshold = %g" % thr)
        ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("recognition (0..1)")
    ax.set_title("2. CD4 recognition (does it cross the threshold?)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # 3. cell counts
    ax = axes[1][0]
    if snaps:
        groups = {}
        for tag, counts in snaps:
            for k, v in counts.items():
                groups.setdefault(k, []).append(v)
        # keep only types that ever appear, sorted by final count desc
        items = sorted(groups.items(), key=lambda kv: -max(kv[1]))
        labels = [k for k, _ in items]
        x = np.arange(len(labels))
        vals = [max(v) for _, v in items]
        colors = ["tab:red" if "tumor" in k else
                  "tab:green" if "CD4" in k else
                  "tab:blue" if "CD8" in k else
                  "tab:orange" if "Bifido" in k else "lightgray" for k in labels]
        ax.bar(x, vals, color=colors)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_yscale("log")
        ax.set_ylabel("cells (max over snapshots)")
    ax.set_title("3. Cell composition (CD4 subtypes: did any activate?)")
    ax.grid(alpha=0.3, axis="y")

    # 4. bacterial burden
    ax = axes[1][1]
    if m is not None:
        order = np.argsort(m["time_min"])
        ax.plot(m["time_min"][order], m["intracellular_bacteria"][order], "o-",
                ms=3, lw=0.8, color="tab:orange", label="intracellular bacteria")
        ax.plot(m["time_min"][order], m["xenophagy_activity"][order], "s-",
                ms=3, lw=0.8, color="tab:brown", label="xenophagy activity")
    ax.set_xlabel("time (min)")
    ax.set_title("4. Bacterial burden / xenophagy")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = Path(args.out) if args.out else (d / "cd4_loop.png")
    if not out.is_absolute():
        out = ROOT / out
    fig.savefig(out, dpi=140)
    print("wrote %s" % out)

    # console summary
    if m is not None:
        print("\nmetrics rows: %d" % len(m["time_min"]))
        print("pMHC-II    : min=%.4g  max=%.4g" % (np.nanmin(m["surface_pMHC_II"]), np.nanmax(m["surface_pMHC_II"])))
        print("recognition: min=%.4g  max=%.4g" % (np.nanmin(m["mhcii_cd4_recognition"]), np.nanmax(m["mhcii_cd4_recognition"])))
    if snaps:
        print("\nCD4 composition per snapshot:")
        for tag, counts in snaps:
            cd4 = {k: v for k, v in counts.items() if "CD4" in k}
            print("   %-12s %s" % (tag, cd4 if cd4 else "(none)"))


if __name__ == "__main__":
    main()
