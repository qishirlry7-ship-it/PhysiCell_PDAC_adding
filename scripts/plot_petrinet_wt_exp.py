#!/usr/bin/env python3
"""Plot WT vs EXP antigen-presentation time series from the PetriNet engine.

Reads the long-format CSV emitted by tests/petrinet_wt_exp.cpp:
    model,t_hours,mhc1_surface,pmhc2_surface,xenosig,intracellular

Produces a four-panel figure: MHC-I, MHC-II, XenoSig signal and intracellular
burden, so the experimental branch's effect on presentation can be read off
directly rather than inferred.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LABELS = {"WT": "WT (V2_merged_bridge_enter_V3)", "EXP": "EXP (+EXP1/EXP2)"}
COLORS = {"WT": "#1f77b4", "EXP": "#d62728"}


def load(path: Path) -> dict[str, dict[str, list[float]]]:
    series: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            model = (row.get("model") or "").strip()
            # The writer emits the header once per model block, so the reader
            # sees it again mid-file; skip anything that is not a data row.
            if not model or model == "model":
                continue
            try:
                values = {col: float(row[col]) for col in
                          ("t_hours", "mhc1_surface", "pmhc2_surface",
                           "xenosig", "intracellular")}
            except (TypeError, ValueError):
                continue
            for key, col in (
                ("t", "t_hours"),
                ("mhc1", "mhc1_surface"),
                ("mhc2", "pmhc2_surface"),
                ("xenosig", "xenosig"),
                ("burden", "intracellular"),
            ):
                series[model][key].append(values[col])
    return series


def simple_axis(ax, xlabel, ylabel, title):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle=":")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="long-format CSV from petrinet_wt_exp")
    ap.add_argument("-o", "--out", type=Path, default=None, help="output PNG path")
    args = ap.parse_args()

    series = load(args.csv)
    if not series:
        raise SystemExit(f"no data in {args.csv}")

    out = args.out or args.csv.with_name("petrinet_wt_vs_exp_mhc.png")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    panels = [
        (axes[0][0], "mhc1", "MHC-I surface (pMHC-I)", "MHC-I cross-presentation"),
        (axes[0][1], "mhc2", "MHC-II surface (pMHC-II)", "MHC-II presentation"),
        (axes[1][0], "xenosig", "XenoSig (token count)", "Xenophagy signal accumulation"),
        (axes[1][1], "burden", "Intracellular bacteria", "Intracellular burden"),
    ]

    for model in sorted(series):
        label = LABELS.get(model, model)
        color = COLORS.get(model)
        for ax, key, ylabel, title in panels:
            ax.plot(series[model]["t"], series[model][key],
                    label=label, color=color, linewidth=1.7)

    for ax, key, ylabel, title in panels:
        simple_axis(ax, "time (h)", ylabel, title)
        ax.legend(loc="best", fontsize=8)

    # Overlay the WT/EXP ratio for the two presentation readouts. Their
    # absolute magnitudes differ by ~800x, so a shared axis would hide the
    # question that actually matters here: does the EXP1/EXP2 branch shift
    # presentation, and by how much over time?
    ax_ratio = axes[0][1].inset_axes([0.58, 0.12, 0.40, 0.34])
    if "WT" in series and "EXP" in series:
        t = series["WT"]["t"]
        w2 = series["WT"]["mhc2"]
        e2 = series["EXP"]["mhc2"]
        ratio = [e / w if w > 1e-9 else float("nan") for e, w in zip(e2, w2)]
        ax_ratio.plot(t, ratio, color="#2ca02c", linewidth=1.4)
        ax_ratio.axhline(1.0, color="gray", linewidth=0.8, linestyle="--")
        ax_ratio.set_ylim(0.98, 1.08)
        ax_ratio.set_title("EXP / WT (pMHC-II)", fontsize=7)
        ax_ratio.tick_params(labelsize=6)
        ax_ratio.grid(True, alpha=0.25, linestyle=":")

    fig.suptitle("Xenophagy PetriNet: WT vs EXP antigen presentation",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out, dpi=150)
    print(out)

    for model in sorted(series):
        print(f"{model}:  final mhc1={series[model]['mhc1'][-1]:.3f}"
              f"  final mhc2={series[model]['mhc2'][-1]:.1f}"
              f"  peak mhc2={max(series[model]['mhc2']):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
