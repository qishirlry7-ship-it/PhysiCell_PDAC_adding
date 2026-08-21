#!/usr/bin/env python3
"""Statistically compare Python and C++ 8-hour single-cell baselines."""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import subprocess
import sys
from pathlib import Path

import numpy as np


FIELDS = ("steps", "burden_final", "activity_peak", "activity_final",
          "xenosig_final", "pmhc_peak", "pmhc_final")


def python_rows(upstream: Path, samples: int) -> list[dict[str, float]]:
    sys.path.insert(0, str(upstream.resolve()))
    from agent_core import SimConfig, simulate_cell
    from enter_influx import FunctionEnterInflux
    from MHC import DEFAULT_PARAMS, _make_phi_step, simulate_mhc

    rows = []
    zero_input = FunctionEnterInflux(lambda _t: 0.0, moi=150, cyt_frac=0.0)
    grid_h = np.arange(0.0, 8.0 + 0.1, 0.1)
    for seed in range(samples):
        cfg = SimConfig(t_end=8 * 3600.0, influx=zero_input,
                        extra_init={"SalVac": 50}, k_death=1e-7)
        # petrinettool emits repeated queue diagnostics while constructing
        # each model; they are unrelated to the statistical report.
        with contextlib.redirect_stdout(io.StringIO()):
            cell = simulate_cell(cfg, seed=seed, record_prot=False)
        activity = cell.ap_gal8_total + cell.ap_ub_total
        phi = _make_phi_step(cell.t / 3600.0, activity, cell.t_end / 3600.0)
        mhc = simulate_mhc(DEFAULT_PARAMS, phi_xeno=phi, t_span=(0.0, 8.0),
                           t_eval=grid_h, ifn_gamma=5.0, mature=False)
        burden = cell.salcyt + cell.adapsalcyt + cell.salvac + cell.adapsalvac
        rows.append({
            "steps": cell.n_steps,
            "burden_final": burden[-1],
            "activity_peak": activity.max(),
            "activity_final": activity[-1],
            "xenosig_final": cell.xenosig[-1],
            "pmhc_peak": mhc["P"].max(),
            "pmhc_final": mhc["P"][-1],
        })
    return rows


def cpp_rows(executable: Path | None, csv_path: Path | None,
             samples: int) -> list[dict[str, float]]:
    if csv_path is not None:
        output = csv_path.read_text(encoding="utf-8")
    else:
        output = subprocess.check_output(
            [str(executable.resolve()), str(samples)], text=True)
    return [{key: float(row[key]) for key in FIELDS}
            for row in csv.DictReader(output.splitlines())]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path,
                        default=Path("../PopulationPetriNet/populationPN"))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--cpp", type=Path)
    source.add_argument("--cpp-csv", type=Path)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    py = python_rows(args.upstream, args.samples)
    cpp = cpp_rows(args.cpp, args.cpp_csv, args.samples)
    if len(cpp) != args.samples:
        raise ValueError(f"C++ rows {len(cpp)} != requested samples {args.samples}")
    failed = False
    print("metric,python_mean,cpp_mean,relative_difference,python_median,cpp_median")
    for field in FIELDS:
        pa = np.asarray([row[field] for row in py], dtype=float)
        ca = np.asarray([row[field] for row in cpp], dtype=float)
        pmean, cmean = pa.mean(), ca.mean()
        rel = abs(cmean - pmean) / max(abs(pmean), 1e-12)
        print(f"{field},{pmean:.8g},{cmean:.8g},{rel:.6g},"
              f"{np.median(pa):.8g},{np.median(ca):.8g}")
        failed |= rel > args.tolerance
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
