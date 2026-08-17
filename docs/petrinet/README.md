# PhysiCell–PetriNet integration

This directory is the collaboration contract for the xenophagy Petri-net
integration. The runtime is C++ only. Python is used at build time to convert
the upstream JSON snapshot into deterministic C++ source.

## WSL base workflow

From the PhysiCell repository in the WSL base environment:

```bash
python3 scripts/generate_petrinet_cpp.py
python3 scripts/generate_petrinet_cpp.py --check
bash scripts/run_petrinet_tests.sh
make -j4
```

The checked-in generated source lets collaborators compile without running the
generator. `--check` is the required stale-model check before review.

See [INTERFACE.md](INTERFACE.md) for the stable interface and
[ARCHITECTURE.md](ARCHITECTURE.md) for ownership and data flow.

Enable the runtime through `petrinet_enabled`, `petrinet_entry_csv`, and
`petrinet_global_seed` in the PhysiCell XML. Use
`config/petrinet/manual_entries.example.csv` as the schedule template. Pressure
tests are available in `scripts/run_petrinet_benchmark_quick.sh` and
`scripts/run_petrinet_benchmark.sh`.

Do not edit generated files manually. Update `INTERFACE.md` before changing a
public JSON, CSV, or C++ contract; regenerate and commit the model snapshot,
integration configuration, generated pair, and version hashes together.

## Verified minimal demo

The following single command starts four tumor cells and runs for 8 hours,
injects 50 vacuolar bacteria into every initial cell at `t=0`, exports per-cell
xenophagy trajectories, and renders a dependency-free SVG:

```bash
bash scripts/run_minimal_petrinet_demo.sh
```

Outputs are intentionally ignored runtime artifacts:

- `outputs/petrinet_minimal/xenophagy_metrics.csv`
- `outputs/petrinet_minimal/xenophagy_metrics.svg`
- `outputs/petrinet_minimal/run.log`

The script asserts that the generated model and unit tests pass, both output
artifacts are non-empty, and the hard-coded injection was reported by the
PhysiCell executable.
