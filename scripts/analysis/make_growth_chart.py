# -*- coding: utf-8 -*-
"""Hand-rolled SVG line chart (no matplotlib/numpy available in this
environment) for cancer cell count + division/death rate over time,
dual y-axis (left: live count, right: events per 60-min interval)."""
import csv

rows = []
with open("scripts/analysis/growth_dynamics.csv") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append({k: float(v) for k, v in row.items()})

W, H = 1400, 800
ML, MR, MT, MB = 90, 90, 60, 90
plot_w, plot_h = W - ML - MR, H - MT - MB

t_max = max(r["time_min"] for r in rows)
live_max = max(r["live_count"] for r in rows) * 1.05
event_max = max(max(r["divisions_this_interval"], r["deaths_this_interval"]) for r in rows) * 1.15
event_max = max(event_max, 5)

def x(t): return ML + plot_w * t / t_max
def y_live(v): return MT + plot_h * (1 - v / live_max)
def y_event(v): return MT + plot_h * (1 - v / event_max)

def polyline(points, color, width=2.5, dash=None):
    pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"{d}/>'

live_pts = [(x(r["time_min"]), y_live(r["live_count"])) for r in rows]
div_pts = [(x(r["time_min"]), y_event(r["divisions_this_interval"])) for r in rows]
death_pts = [(x(r["time_min"]), y_event(r["deaths_this_interval"])) for r in rows]
net_pts = [(x(r["time_min"]), y_event(r["net_this_interval"] + event_max/2)) for r in rows]  # centered

svg = []
svg.append(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Arial">')
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>')
svg.append(f'<text x="{W/2}" y="30" text-anchor="middle" font-size="24" font-weight="bold">PhysiCell_PDAC_hybrid_v2: cancer cell (tumor-lineage) population dynamics</text>')

# axes
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')
svg.append(f'<line x1="{ML+plot_w}" y1="{MT}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="black" stroke-width="1.5"/>')

# y ticks left (live count)
for frac in [0, 0.25, 0.5, 0.75, 1.0]:
    v = live_max * frac
    yy = y_live(v)
    svg.append(f'<line x1="{ML-5}" y1="{yy:.1f}" x2="{ML}" y2="{yy:.1f}" stroke="black"/>')
    svg.append(f'<text x="{ML-10}" y="{yy+4:.1f}" text-anchor="end" font-size="14">{int(v)}</text>')
svg.append(f'<text x="20" y="{MT+plot_h/2:.1f}" text-anchor="middle" font-size="16" fill="#1f77b4" transform="rotate(-90 20 {MT+plot_h/2:.1f})">Live cancer cells (count)</text>')

# y ticks right (events)
for frac in [0, 0.25, 0.5, 0.75, 1.0]:
    v = event_max * frac
    yy = y_event(v)
    svg.append(f'<line x1="{ML+plot_w}" y1="{yy:.1f}" x2="{ML+plot_w+5}" y2="{yy:.1f}" stroke="black"/>')
    svg.append(f'<text x="{ML+plot_w+10}" y="{yy+4:.1f}" font-size="14">{int(v)}</text>')
svg.append(f'<text x="{W-20}" y="{MT+plot_h/2:.1f}" text-anchor="middle" font-size="16" transform="rotate(-90 {W-20} {MT+plot_h/2:.1f})">Events per 60-min interval</text>')

# x ticks
for frac in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
    t = t_max * frac
    xx = x(t)
    svg.append(f'<line x1="{xx:.1f}" y1="{MT+plot_h}" x2="{xx:.1f}" y2="{MT+plot_h+5}" stroke="black"/>')
    svg.append(f'<text x="{xx:.1f}" y="{MT+plot_h+25}" text-anchor="middle" font-size="14">{int(t)}</text>')
svg.append(f'<text x="{ML+plot_w/2:.1f}" y="{H-20}" text-anchor="middle" font-size="16">Simulated time (min)</text>')

svg.append(polyline(live_pts, "#1f77b4", 3.5))
svg.append(polyline(div_pts, "#2ca02c", 2, dash="4,2"))
svg.append(polyline(death_pts, "#d62728", 2, dash="4,2"))

# legend
legend_items = [("Live cancer cells", "#1f77b4", False), ("Divisions / 60min", "#2ca02c", True), ("Deaths / 60min", "#d62728", True)]
ly = MT + 10
for label, color, dashed in legend_items:
    dash_attr = ' stroke-dasharray="4,2"' if dashed else ""
    svg.append(f'<line x1="{ML+plot_w-260}" y1="{ly}" x2="{ML+plot_w-220}" y2="{ly}" stroke="{color}" stroke-width="3"{dash_attr}/>')
    svg.append(f'<text x="{ML+plot_w-210}" y="{ly+5}" font-size="14">{label}</text>')
    ly += 24

svg.append('</svg>')

with open("scripts/analysis/growth_chart.svg", "w") as f:
    f.write("\n".join(svg))
print("wrote scripts/analysis/growth_chart.svg")
