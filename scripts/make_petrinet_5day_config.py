#!/usr/bin/env python3
"""Generate the 5-day PetriNet comparison arms on the production tissue layout.

Keeps the real initial condition from config/ic_cells so the stroma, myeloid
and lymphoid compartments are present -- a tumour-only grid removes every
immunosuppressive cell and makes immune attack look far stronger than it is.

Bacteria are seeded as initial agents on a ring outside the tissue, because
recruit_bacteria() is probability-driven and bacteria_entry_lambda is 0.

Usage: make_petrinet_5day_config.py [--duration-min N] [--bacteria N]
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")

INIT = """<initial_conditions>
        <cell_positions type="csv" enabled="true">
            <folder>./config/ic_cells</folder>
            <filename>PDAC_TISSUE_1_hybrid.csv</filename>
        </cell_positions>
    </initial_conditions>"""

ARMS = [
    ("baseline", ""),
    ("wt", "config/petrinet/wt_model.json"),
    ("exp", "config/petrinet/exp_model.json"),
]


def setv(doc: str, tag: str, value: str) -> str:
    out, n = re.subn(rf"(<{tag}\b[^>]*>).*?(</{tag}>)", rf"\g<1>{value}\g<2>", doc, count=1)
    if n != 1:
        raise SystemExit(f"expected XML tag not found: {tag}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-min", type=int, default=7200)
    ap.add_argument("--bacteria", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=12)
    args = ap.parse_args()

    if INIT not in SRC:
        raise SystemExit("initial_conditions block is not the expected shape")

    for arm, model in ARMS:
        name = f"petrinet_real_{args.duration_min}min_{arm}"
        out = ROOT / "outputs" / name
        out.mkdir(parents=True, exist_ok=True)

        d = setv(SRC, "max_time", str(args.duration_min))
        d = setv(d, "omp_num_threads", str(args.threads))
        d = setv(d, "petrinet_enabled", "false" if arm == "baseline" else "true")
        d = setv(d, "petrinet_input_mode", "1")
        d = setv(d, "petrinet_demo_vacuolar_bacteria", "0")
        d = setv(d, "petrinet_model_json", model)
        d = setv(d, "petrinet_metrics_csv", f"outputs/{name}/xenophagy_metrics.csv")
        d = setv(d, "petrinet_uptake_csv", f"outputs/{name}/bacterial_uptake.csv")
        d = setv(d, "petrinet_metrics_interval", "6")
        d = d.replace("<folder>outputs/pdac_therapy</folder>",
                      f"<folder>outputs/{name}</folder>", 1)

        count = 0 if arm == "baseline" else args.bacteria
        if count:
            radius = 320.0
            cells = "\n".join(
                '        <cell id="0" type="Bifidobacterium_longum">\n'
                f'            <position x="{radius * math.cos(2 * math.pi * i / count):.3f}"'
                f' y="{radius * math.sin(2 * math.pi * i / count):.3f}" z="0.000"/>\n'
                '        </cell>'
                for i in range(count)
            )
            d = d.replace(INIT, INIT.replace("    </initial_conditions>",
                                             cells + "\n    </initial_conditions>"), 1)

        (out / "PhysiCell_settings.xml").write_text(d, encoding="utf-8", newline="\n")
        print(f"{arm:9} model={model or '(disabled)':38} "
              f"bacteria={count:<6} duration={args.duration_min}min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
