# -*- coding: utf-8 -*-
"""
Renders one "growing" SVG frame per checkpoint: cancer-cell (tumor-lineage)
live count + divisions/deaths per 60-min interval (from growth_dynamics.csv,
written by track_growth_dynamics.py), plus a text panel of the current
domain-mean substrate concentrations (from substrate_means.csv, written by
extract_substrate_means.py). Axis ranges are fixed to the FULL run's max so
the chart fills in progressively across frames rather than rescaling.
Frames are written as SVG then rasterized to PNG via rsvg-convert (no
matplotlib/numpy in this environment). Requires both CSVs to already cover
every checkpoint (run track_growth_dynamics.py / extract_substrate_means.py
first, after the simulation is complete).
"""
import csv, os, subprocess, sys

growth_rows = []
with open("scripts/analysis/growth_dynamics.csv") as f:
    for row in csv.DictReader(f):
        growth_rows.append({k: float(v) for k, v in row.items()})

subst_rows = []
with open("scripts/analysis/substrate_means.csv") as f:
    r = csv.DictReader(f)
    subst_fields = [k for k in r.fieldnames if k != "time_min"]
    for row in r:
        subst_rows.append({k: float(v) for k, v in row.items()})

assert len(growth_rows) == len(subst_rows), "checkpoint count mismatch between the two CSVs"
N = len(growth_rows)

SUBSTRATE_LABELS = {
    "oxygen": "oxygen (mmHg)", "glucose": "glucose (mM)", "lactate": "lactate (mM)",
    "ECM": "ECM density", "TGF_beta": "TGF-β", "IFN_gamma": "IFN-γ", "Gal8_ext": "Gal-8",
}

W, H = 1400, 900
ML, MR, MT, MB = 90, 90, 70, 90
plot_w, plot_h = W - ML - MR, H - MT - MB - 260   # reserve 260px at bottom for substrate-mean text panel

t_max = max(r["time_min"] for r in growth_rows)
live_max = max(r["live_count"] for r in growth_rows) * 1.05
event_max = max(max(r["divisions_this_interval"], r["deaths_this_interval"]) for r in growth_rows) * 1.15
event_max = max(event_max, 5)

def x(t): return ML + plot_w * t / t_max
def y_live(v): return MT + plot_h * (1 - v / live_max)
def y_event(v): return MT + plot_h * (1 - v / event_max)

def polyline(points, color, width=2.5, dash=None):
    pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"{d}/>'

out_dir = "scripts/analysis/growth_frames"
os.makedirs(out_dir, exist_ok=True)

for idx in range(N):
    rows_so_far = growth_rows[:idx + 1]
    live_pts = [(x(r["time_min"]), y_live(r["live_count"])) for r in rows_so_far]
    div_pts = [(x(r["time_min"]), y_event(r["divisions_this_interval"])) for r in rows_so_far]
    death_pts = [(x(r["time_min"]), y_event(r["deaths_this_interval"])) for r in rows_so_far]

    cur = growth_rows[idx]
    cur_t = cur["time_min"]
    cur_day = cur_t / 1440.0

    svg = []
    svg.append(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Arial">')
    svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>')
    svg.append(f'<text x="{W/2}" y="32" text-anchor="middle" font-size="24" font-weight="bold">Cancer cell population dynamics -- t = {cur_t:.0f} min ({cur_day:.2f} days)</text>')

    svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')
    svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')
    svg.append(f'<line x1="{ML+plot_w}" y1="{MT}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        v = live_max * frac
        yy = y_live(v)
        svg.append(f'<line x1="{ML-5}" y1="{yy:.1f}" x2="{ML}" y2="{yy:.1f}" stroke="black"/>')
        svg.append(f'<text x="{ML-10}" y="{yy+4:.1f}" text-anchor="end" font-size="14">{int(v)}</text>')
    svg.append(f'<text x="20" y="{MT+plot_h/2:.1f}" text-anchor="middle" font-size="16" fill="#1f77b4" transform="rotate(-90 20 {MT+plot_h/2:.1f})">Live cancer cells (count)</text>')

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        v = event_max * frac
        yy = y_event(v)
        svg.append(f'<line x1="{ML+plot_w}" y1="{yy:.1f}" x2="{ML+plot_w+5}" y2="{yy:.1f}" stroke="black"/>')
        svg.append(f'<text x="{ML+plot_w+10}" y="{yy+4:.1f}" font-size="14">{int(v)}</text>')
    svg.append(f'<text x="{W-20}" y="{MT+plot_h/2:.1f}" text-anchor="middle" font-size="16" transform="rotate(-90 {W-20} {MT+plot_h/2:.1f})">Events / 60min</text>')

    for frac in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        t = t_max * frac
        xx = x(t)
        svg.append(f'<line x1="{xx:.1f}" y1="{MT+plot_h}" x2="{xx:.1f}" y2="{MT+plot_h+5}" stroke="black"/>')
        svg.append(f'<text x="{xx:.1f}" y="{MT+plot_h+25}" text-anchor="middle" font-size="14">{t/1440:.0f}d</text>')
    svg.append(f'<text x="{ML+plot_w/2:.1f}" y="{MT+plot_h+50}" text-anchor="middle" font-size="16">Simulated time (days)</text>')

    if len(live_pts) > 1:
        svg.append(polyline(live_pts, "#1f77b4", 3.5))
        svg.append(polyline(div_pts, "#2ca02c", 2, dash="4,2"))
        svg.append(polyline(death_pts, "#d62728", 2, dash="4,2"))
    elif len(live_pts) == 1:
        svg.append(f'<circle cx="{live_pts[0][0]:.1f}" cy="{live_pts[0][1]:.1f}" r="3" fill="#1f77b4"/>')

    # marker at current point
    if live_pts:
        svg.append(f'<circle cx="{live_pts[-1][0]:.1f}" cy="{live_pts[-1][1]:.1f}" r="5" fill="#1f77b4" stroke="black" stroke-width="1"/>')

    legend_items = [("Live cancer cells", "#1f77b4", False), ("Divisions / 60min", "#2ca02c", True), ("Deaths / 60min", "#d62728", True)]
    ly = MT + 10
    for label, color, dashed in legend_items:
        dash_attr = ' stroke-dasharray="4,2"' if dashed else ""
        svg.append(f'<line x1="{ML+plot_w-260}" y1="{ly}" x2="{ML+plot_w-220}" y2="{ly}" stroke="{color}" stroke-width="3"{dash_attr}/>')
        svg.append(f'<text x="{ML+plot_w-210}" y="{ly+5}" font-size="14">{label}</text>')
        ly += 24

    # current counters, top-left inside plot
    svg.append(f'<text x="{ML+15}" y="{MT+25}" font-size="15" font-weight="bold">live={int(cur["live_count"])}  '
                f'+{int(cur["divisions_this_interval"])} div / -{int(cur["deaths_this_interval"])} death (this 60min)</text>')

    # substrate-mean text panel at bottom
    panel_y0 = MT + plot_h + 90
    svg.append(f'<rect x="{ML}" y="{panel_y0}" width="{plot_w}" height="150" fill="#f5f5f5" stroke="#ccc"/>')
    svg.append(f'<text x="{ML+15}" y="{panel_y0+28}" font-size="17" font-weight="bold">Domain-mean microenvironment substrate concentrations</text>')
    s = subst_rows[idx]
    col_w = plot_w / 4
    for i, field in enumerate(subst_fields):
        col = i % 4
        row = i // 4
        px = ML + 20 + col * col_w
        py = panel_y0 + 60 + row * 42
        val = s[field]
        val_str = "0" if abs(val) < 1e-9 else f"{val:.3g}"
        svg.append(f'<text x="{px:.1f}" y="{py:.1f}" font-size="16">{SUBSTRATE_LABELS.get(field, field)}: '
                    f'<tspan font-weight="bold">{val_str}</tspan></text>')

    svg.append('</svg>')

    svg_path = os.path.join(out_dir, f"frame_{idx:04d}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

png_path_pattern = os.path.join(out_dir, "frame_%04d.png")
print(f"wrote {N} SVG frames to {out_dir}, rasterizing to PNG via rsvg-convert...")
for idx in range(N):
    svg_path = os.path.join(out_dir, f"frame_{idx:04d}.svg")
    png_path = os.path.join(out_dir, f"frame_{idx:04d}.png")
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", png_path, svg_path], check=True)

print(f"done: {N} PNG frames in {out_dir}")
