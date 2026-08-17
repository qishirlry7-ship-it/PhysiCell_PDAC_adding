#!/usr/bin/env python3
"""Create an ignored configurable PhysiCell PetriNet experiment."""

import argparse
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output-name", default="petrinet_minimal")
parser.add_argument("--duration-min", type=int, default=480)
parser.add_argument("--bacteria", type=int, default=50)
parser.add_argument("--cells", type=int, default=4)
args = parser.parse_args()
if args.duration_min <= 0 or args.bacteria < 0 or args.cells <= 0:
    raise SystemExit("duration/cells must be positive and bacteria non-negative")

root = Path(__file__).resolve().parents[1]
source = root / "config" / "PhysiCell_settings.xml"
output_dir = root / "outputs" / args.output_name
output_dir.mkdir(parents=True, exist_ok=True)
target = output_dir / "PhysiCell_settings.xml"

text = source.read_text(encoding="utf-8")
replacements = {
    '<max_time units="min">21600</max_time>': f'<max_time units="min">{args.duration_min}</max_time>',
    '<dt_diffusion units="min">0.01</dt_diffusion>': '<dt_diffusion units="min">0.1</dt_diffusion>',
    '<omp_num_threads>12</omp_num_threads>': '<omp_num_threads>4</omp_num_threads>',
    '<folder>outputs/pdac_therapy</folder>': f'<folder>outputs/{args.output_name}</folder>',
    '<folder>./config/ic_cells</folder>': f'<folder>./outputs/{args.output_name}/input</folder>',
    '<filename>PDAC_TISSUE_1_hybrid.csv</filename>': '<filename>initial_cells.csv</filename>',
    '>false</petrinet_enabled>': '>true</petrinet_enabled>',
    '>0</petrinet_demo_vacuolar_bacteria>': f'>{args.bacteria}</petrinet_demo_vacuolar_bacteria>',
    '></petrinet_metrics_csv>': f'>outputs/{args.output_name}/xenophagy_metrics.csv</petrinet_metrics_csv>',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"expected XML fragment not found: {old}")
    text = text.replace(old, new, 1)

# Metrics CSV is the authoritative demo output; disable periodic heavy saves.
text = text.replace(
    '<full_data>\n            <interval units="min">60</interval>\n            <enable>true</enable>',
    '<full_data>\n            <interval units="min">60</interval>\n            <enable>false</enable>',
    1,
)
text = text.replace(
    '<SVG>\n            <interval units="min">60</interval>\n            <enable>true</enable>',
    '<SVG>\n            <interval units="min">60</interval>\n            <enable>false</enable>',
    1,
)
target.write_text(text, encoding="utf-8", newline="\n")

side = math.ceil(math.sqrt(args.cells))
spacing = 30.0
offset = (side - 1) * spacing / 2.0
rows = ["x,y,z,type"]
for index in range(args.cells):
    row, column = divmod(index, side)
    cell_type = "PD-L1lo_tumor" if index % 2 == 0 else "PD-L1hi_tumor"
    rows.append(f"{column * spacing - offset:g},{row * spacing - offset:g},0,{cell_type}")
input_dir = output_dir / "input"
input_dir.mkdir(parents=True, exist_ok=True)
(input_dir / "initial_cells.csv").write_text(
    "\n".join(rows) + "\n", encoding="utf-8", newline="\n")
print(target.relative_to(root))
