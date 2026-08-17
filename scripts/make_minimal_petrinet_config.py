#!/usr/bin/env python3
"""Create an ignored short PhysiCell config for the hard-coded PetriNet demo."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "config" / "PhysiCell_settings.xml"
output_dir = root / "outputs" / "petrinet_minimal"
output_dir.mkdir(parents=True, exist_ok=True)
target = output_dir / "PhysiCell_settings.xml"

text = source.read_text(encoding="utf-8")
replacements = {
    '<max_time units="min">21600</max_time>': '<max_time units="min">120</max_time>',
    '<dt_diffusion units="min">0.01</dt_diffusion>': '<dt_diffusion units="min">0.1</dt_diffusion>',
    '<omp_num_threads>12</omp_num_threads>': '<omp_num_threads>4</omp_num_threads>',
    '<folder>outputs/pdac_therapy</folder>': '<folder>outputs/petrinet_minimal</folder>',
    '<folder>./config/ic_cells</folder>': '<folder>./config/petrinet</folder>',
    '<filename>PDAC_TISSUE_1_hybrid.csv</filename>': '<filename>minimal_cells.csv</filename>',
    '>false</petrinet_enabled>': '>true</petrinet_enabled>',
    '>0</petrinet_demo_vacuolar_bacteria>': '>50</petrinet_demo_vacuolar_bacteria>',
    '></petrinet_metrics_csv>': '>outputs/petrinet_minimal/xenophagy_metrics.csv</petrinet_metrics_csv>',
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
print(target.relative_to(root))
