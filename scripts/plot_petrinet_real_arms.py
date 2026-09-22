#!/usr/bin/env python3
"""Plot population curves for the real-tissue PetriNet arms.

Cell counts come from the hourly MultiCellDS cell matrices rather than the XML,
because the XML stores cells as an opaque MATLAB blob. In those matrices row 0
is the cell ID, rows 1-3 are x/y/z, and the cell type is row 5. That index is
not guessed: it is the unique row whose composition on the first snapshot
reproduces the tissue file's known per-type counts.

Type IDs are mapped to names through the <type ID=...> table in the matching
outputNNNNNNNN.xml, so a renamed definition does not silently miscount.

Usage: plot_petrinet_real_arms.py [--duration-min N] [--out PATH]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import scipy.io as sio  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

ARM_LABEL = {
    "baseline": "no bacteria (control)",
    "wt": "WT xenophagy + 1000 bacteria",
    "exp": "EXP xenophagy + 1000 bacteria",
}
ARM_COLOR = {"baseline": "#7f7f7f", "wt": "#1f77b4", "exp": "#d62728"}
TUMOUR_MARKERS = ("tumor", "tumour")


def type_table(xml_path: Path) -> dict[int, str]:
    if not xml_path.exists():
        return {}
    text = xml_path.read_text(encoding="utf-8", errors="replace")
    return {int(i): n for i, n in
            re.findall(r'<type ID="(\d+)"[^>]*>([^<]+)</type>', text)}


def snapshot_index(path: Path) -> int:
    match = re.search(r"output(\d+)", path.name)
    return int(match.group(1)) if match else -1


def find_type_row(first_mat: Path, names: dict[int, str]) -> int:
    """Locate the cell-type row.

    The row must hold small non-negative integers, span many distinct values
    (a real tissue has ~17 types), and its total must equal the number of
    cells. Coordinate, volume and time rows fail the first test; per-cell
    scalar readouts fail the second.
    """
    cells = sio.loadmat(str(first_mat))["cells"]
    candidates = []
    for row in range(cells.shape[0]):
        vals = cells[row, :]
        if vals.min() < 0 or vals.max() > len(names) + 5:
            continue
        distinct = len({int(v) for v in vals})
        if distinct >= 8:
            candidates.append((row, distinct))
    if not candidates:
        raise SystemExit(f"no cell-type row found in {first_mat.name}")
    if len(candidates) > 1:
        print(f"note: type-row candidates {candidates}; using the first")
    return candidates[0][0]


def is_tumour(name: str) -> bool:
    return any(m in name.lower() for m in TUMOUR_MARKERS)


def load_arm(directory: Path, type_row: int | None) -> dict:
    mats = sorted(directory.glob("output*_cells.mat"), key=snapshot_index)
    if not mats:
        return {}

    names = type_table(directory / "output00000000.xml")
    if type_row is None:
        type_row = find_type_row(mats[0], names)

    hours, tumour, alive, infected = [], [], [], []
    infected_ids = {tid for tid, n in names.items()
                    if "infected" in n.lower() or "xenophagy" in n.lower()}

    for path in mats:
        cells = sio.loadmat(str(path))["cells"]
        types = cells[type_row, :].astype(int)
        hours.append(snapshot_index(path))
        tumour.append(int(sum(is_tumour(names.get(t, "")) for t in types)))
        alive.append(int(cells.shape[1]))
        infected.append(int(sum(t in infected_ids for t in types)))

    return {"hours": hours, "tumour": tumour, "alive": alive,
            "infected": infected, "type_row": type_row}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-min", type=int, default=720)
    ap.add_argument("--arms", default="baseline,wt,exp")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    prefix = f"petrinet_real_{args.duration_min}min_"
    data: dict[str, dict] = {}
    type_row = None
    for arm in args.arms.split(","):
        arm = arm.strip()
        directory = ROOT / "outputs" / f"{prefix}{arm}"
        if not directory.is_dir():
            print(f"skip {arm}: {directory} not found")
            continue
        loaded = load_arm(directory, type_row)
        if not loaded:
            print(f"skip {arm}: no cell matrices in {directory}")
            continue
        type_row = loaded["type_row"]
        data[arm] = loaded
        print(f"{arm:9} snapshots={len(loaded['hours']):3} "
              f"tumour {loaded['tumour'][0]}->{loaded['tumour'][-1]} "
              f"alive {loaded['alive'][0]}->{loaded['alive'][-1]} "
              f"infected final={loaded['infected'][-1]}")

    if not data:
        raise SystemExit("no arm data found")

    out = args.out or (ROOT / "outputs" / f"{prefix}comparison.png")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2))
    panels = [
        (axes[0], "tumour", "tumour cell count", "Tumour cells"),
        (axes[1], "alive", "living agent count", "All living agents"),
        (axes[2], "infected", "infected count", "Infected tumour cells"),
    ]
    for arm, series in data.items():
        for ax, key, _, _ in panels:
            ax.plot(series["hours"], series[key],
                    label=ARM_LABEL.get(arm, arm),
                    color=ARM_COLOR.get(arm), linewidth=1.9)
    for ax, key, ylabel, title in panels:
        ax.set_xlabel("time (h)")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(fontsize=8)

    fig.suptitle(f"PetriNet arms on the production tissue layout "
                 f"({args.duration_min} min, type row {type_row})",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=150)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
