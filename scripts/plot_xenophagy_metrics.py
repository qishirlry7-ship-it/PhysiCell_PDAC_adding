#!/usr/bin/env python3
"""Render per-cell xenophagy, bacterial burden, and surface pMHC trajectories."""

import argparse
import csv
from collections import defaultdict
from html import escape
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/petrinet_minimal/xenophagy_metrics.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/petrinet_minimal/xenophagy_metrics.svg"))
    args = parser.parse_args()

    cells = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cells[int(row["cell_id"])].append({
                "time": float(row["time_min"]),
                "type": row["cell_type"],
                "bacteria": float(row["intracellular_bacteria"]),
                "xenophagy": float(row["xenophagy_activity"]),
                "pmhc": float(row["surface_pMHC"]),
            })
    if not cells:
        raise SystemExit("metrics CSV contains no active PetriNet cells")

    width, height = 1100, 900
    left, right, top = 105, 35, 70
    panel_height, gap = 235, 35
    plot_width = width - left - right
    fields = (("bacteria", "Intracellular bacteria"),
              ("xenophagy", "Xenophagy activity"),
              ("pmhc", "Surface pMHC"))
    colors = ("#2563eb", "#dc2626", "#059669", "#9333ea", "#ea580c", "#0891b2")
    all_times = [row["time"] for rows in cells.values() for row in rows]
    t_min, t_max = min(all_times), max(all_times)
    if t_max <= t_min:
        t_max = t_min + 1.0

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#172033}.axis{stroke:#334155;stroke-width:1}.grid{stroke:#cbd5e1;stroke-width:1;opacity:.65}.series{fill:none;stroke-width:2}</style>',
        f'<text x="{width/2}" y="32" text-anchor="middle" font-size="22" font-weight="bold">Hard-coded bacterial entry: xenophagy response</text>',
    ]
    sorted_cells = sorted(cells.items())
    for panel, (field, ylabel) in enumerate(fields):
        y0 = top + panel * (panel_height + gap)
        values = [row[field] for rows in cells.values() for row in rows]
        v_min = min(0.0, min(values))
        v_max = max(values)
        if v_max <= v_min:
            v_max = v_min + 1.0
        for tick in range(5):
            frac = tick / 4
            y = y0 + panel_height * (1 - frac)
            value = v_min + frac * (v_max - v_min)
            svg.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{left+plot_width}" y2="{y:.2f}"/>')
            svg.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12">{value:.3g}</text>')
        svg.append(f'<line class="axis" x1="{left}" y1="{y0}" x2="{left}" y2="{y0+panel_height}"/>')
        svg.append(f'<line class="axis" x1="{left}" y1="{y0+panel_height}" x2="{left+plot_width}" y2="{y0+panel_height}"/>')
        svg.append(f'<text x="25" y="{y0+panel_height/2}" text-anchor="middle" font-size="14" transform="rotate(-90 25 {y0+panel_height/2})">{escape(ylabel)}</text>')
        for index, (cell_id, rows) in enumerate(sorted_cells):
            points = []
            for row in rows:
                x = left + (row["time"] - t_min) / (t_max - t_min) * plot_width
                y = y0 + panel_height - (row[field] - v_min) / (v_max - v_min) * panel_height
                points.append(f"{x:.2f},{y:.2f}")
            svg.append(f'<polyline class="series" stroke="{colors[index % len(colors)]}" points="{" ".join(points)}"/>')
    base_y = top + 3 * (panel_height + gap) - gap
    for tick in range(7):
        frac = tick / 6
        x = left + frac * plot_width
        value = t_min + frac * (t_max - t_min)
        svg.append(f'<text x="{x:.2f}" y="{base_y+22}" text-anchor="middle" font-size="12">{value:.0f}</text>')
    svg.append(f'<text x="{left+plot_width/2}" y="{base_y+48}" text-anchor="middle" font-size="14">PhysiCell time (min)</text>')
    legend_y = height - 18
    for index, (cell_id, rows) in enumerate(sorted_cells):
        x = left + index * 225
        label = f"cell {cell_id} ({rows[0]['type']})"
        svg.append(f'<line x1="{x}" y1="{legend_y-4}" x2="{x+24}" y2="{legend_y-4}" stroke="{colors[index % len(colors)]}" stroke-width="3"/>')
        svg.append(f'<text x="{x+30}" y="{legend_y}" font-size="12">{escape(label)}</text>')
    svg.append('</svg>')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(svg), encoding="utf-8")
    print(f"cells={len(cells)} rows={sum(map(len, cells.values()))} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
