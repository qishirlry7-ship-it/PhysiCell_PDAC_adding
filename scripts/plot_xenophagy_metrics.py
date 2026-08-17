#!/usr/bin/env python3
"""Render per-PetriNet Ap-token trajectories and cell-death statistics."""

import argparse
import csv
from collections import defaultdict
from html import escape
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/petrinet_minimal/xenophagy_metrics.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/petrinet_minimal/xenophagy_metrics.svg"))
    parser.add_argument("--death-summary", type=Path, default=Path("outputs/petrinet_minimal/death_statistics.csv"))
    args = parser.parse_args()

    cells = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cells[int(row["cell_id"])].append({
                "time": float(row["time_min"]), "type": row["cell_type"],
                "bacteria": float(row["intracellular_bacteria"]),
                "ap_gal8": float(row["ap_gal8_tokens"]),
                "ap_ub": float(row["ap_ub_tokens"]),
                "pmhc": float(row["surface_pMHC"]),
                "is_dead": int(row["is_dead"]),
                "pn_death": int(row["petrinet_death_triggered"]),
                "death_time": float(row["death_time_min"]),
            })
    if not cells:
        raise SystemExit("metrics CSV contains no active PetriNet cells")
    for rows in cells.values():
        rows.sort(key=lambda row: row["time"])
    sorted_cells = sorted(cells.items())

    death_rows = []
    for cell_id, rows in sorted_cells:
        dead = any(row["is_dead"] for row in rows)
        times = [row["death_time"] for row in rows if row["death_time"] >= 0.0]
        pn_death = any(row["pn_death"] for row in rows)
        death_rows.append({
            "cell_id": cell_id, "cell_type": rows[0]["type"], "is_dead": int(dead),
            "death_source": "petrinet" if pn_death else ("physicell_other" if dead else "alive"),
            "death_time_min": min(times) if times else -1.0,
            "peak_ap_gal8_tokens": max(row["ap_gal8"] for row in rows),
            "peak_ap_ub_tokens": max(row["ap_ub"] for row in rows),
        })
    args.death_summary.parent.mkdir(parents=True, exist_ok=True)
    with args.death_summary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=death_rows[0].keys())
        writer.writeheader(); writer.writerows(death_rows)

    width, height = 1180, 1570
    left, right, top, panel_height, gap = 110, 40, 90, 235, 38
    plot_width = width - left - right
    fields = (("bacteria", "Intracellular bacteria"),
              ("ap_gal8", "Gal8-pathway Ap tokens"),
              ("ap_ub", "Ub-pathway Ap tokens"),
              ("pmhc", "Surface pMHC"))
    colors = ("#2563eb", "#dc2626", "#059669", "#9333ea", "#ea580c", "#0891b2")
    all_times = [row["time"] for rows in cells.values() for row in rows]
    t_min, t_max = min(all_times), max(all_times)
    if t_max <= t_min: t_max = t_min + 1.0
    dead_count = sum(row["is_dead"] for row in death_rows)
    pn_dead_count = sum(row["death_source"] == "petrinet" for row in death_rows)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#172033}.axis{stroke:#334155;stroke-width:1}.grid{stroke:#cbd5e1;stroke-width:1;opacity:.65}.series{fill:none;stroke-width:2}.death{fill:none;stroke:#111827;stroke-width:3}</style>',
        f'<text x="{width/2}" y="32" text-anchor="middle" font-size="22" font-weight="bold">8 h per-cell PetriNet: Gal8 / Ub autophagosome tokens and death</text>',
        f'<text x="{width/2}" y="58" text-anchor="middle" font-size="14">Observed PetriNets: {len(cells)}; deaths: {dead_count}; PetriNet-triggered deaths: {pn_dead_count}</text>',
    ]

    def axes(y0, v_min, v_max, ylabel):
        for tick in range(5):
            frac = tick / 4; y = y0 + panel_height * (1 - frac)
            value = v_min + frac * (v_max - v_min)
            svg.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{left+plot_width}" y2="{y:.2f}"/>')
            svg.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12">{value:.3g}</text>')
        svg.append(f'<line class="axis" x1="{left}" y1="{y0}" x2="{left}" y2="{y0+panel_height}"/>')
        svg.append(f'<line class="axis" x1="{left}" y1="{y0+panel_height}" x2="{left+plot_width}" y2="{y0+panel_height}"/>')
        svg.append(f'<text x="25" y="{y0+panel_height/2}" text-anchor="middle" font-size="14" transform="rotate(-90 25 {y0+panel_height/2})">{escape(ylabel)}</text>')

    for panel, (field, ylabel) in enumerate(fields):
        y0 = top + panel * (panel_height + gap)
        values = [row[field] for rows in cells.values() for row in rows]
        v_min, v_max = min(0.0, min(values)), max(values)
        if v_max <= v_min: v_max = v_min + 1.0
        axes(y0, v_min, v_max, ylabel)
        for index, (_, rows) in enumerate(sorted_cells):
            points = []
            for row in rows:
                x = left + (row["time"] - t_min) / (t_max - t_min) * plot_width
                y = y0 + panel_height - (row[field] - v_min) / (v_max - v_min) * panel_height
                points.append(f"{x:.2f},{y:.2f}")
            svg.append(f'<polyline class="series" stroke="{colors[index % len(colors)]}" points="{" ".join(points)}"/>')

    death_y0 = top + len(fields) * (panel_height + gap)
    death_max = max(1, dead_count); axes(death_y0, 0.0, float(death_max), "Cumulative dead cells")
    death_times = sorted(row["death_time_min"] for row in death_rows if row["is_dead"])
    step_points, count = [(t_min, 0)], 0
    for death_time in death_times:
        step_points.extend(((death_time, count), (death_time, count + 1))); count += 1
    step_points.append((t_max, count)); points = []
    for time, value in step_points:
        x = left + (time - t_min) / (t_max - t_min) * plot_width
        y = death_y0 + panel_height - value / death_max * panel_height
        points.append(f"{x:.2f},{y:.2f}")
    svg.append(f'<polyline class="death" points="{" ".join(points)}"/>')
    if not death_times:
        svg.append(f'<text x="{left+plot_width/2}" y="{death_y0+panel_height/2}" text-anchor="middle" font-size="18">No cell deaths observed during 8 h</text>')

    base_y = death_y0 + panel_height
    for tick in range(9):
        frac = tick / 8; x = left + frac * plot_width; value = t_min + frac * (t_max - t_min)
        svg.append(f'<text x="{x:.2f}" y="{base_y+22}" text-anchor="middle" font-size="12">{value:.0f}</text>')
    svg.append(f'<text x="{left+plot_width/2}" y="{base_y+47}" text-anchor="middle" font-size="14">PhysiCell time (min)</text>')
    legend_y = height - 45
    for index, (cell_id, rows) in enumerate(sorted_cells):
        column, row_index = index % 3, index // 3
        x, y = left + column * 340, legend_y + row_index * 20
        label = f"cell {cell_id} ({rows[0]['type']})"
        svg.append(f'<line x1="{x}" y1="{y-4}" x2="{x+24}" y2="{y-4}" stroke="{colors[index % len(colors)]}" stroke-width="3"/>')
        svg.append(f'<text x="{x+30}" y="{y}" font-size="12">{escape(label)}</text>')
    svg.append('</svg>')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(svg), encoding="utf-8")
    print(f"cells={len(cells)} deaths={dead_count} rows={sum(map(len, cells.values()))} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
