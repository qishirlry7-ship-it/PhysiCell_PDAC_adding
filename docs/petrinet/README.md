# PhysiCell–PetriNet integration

This directory is the collaboration contract for the xenophagy Petri-net
integration. The runtime is C++ only. Python is used at build time to convert
the upstream JSON topology plus `config/petrinet/parameters.xml` into
deterministic C++ source. That XML is the sole source for all non-PhysiCell
numeric parameters, initial marking, transition overrides, and MHC settings.

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

Before opening or merging a PR, also verify that the default-disabled
integration leaves the baseline PhysiCell run operational:

```bash
bash scripts/run_petrinet_disabled_smoke.sh
```

This one-minute smoke run asserts that PhysiCell exits normally while no
PetriNet state metrics or demo injection are produced.

See [INTERFACE.md](INTERFACE.md) for the stable interface and
[ARCHITECTURE.md](ARCHITECTURE.md) for ownership and data flow.

Enable the runtime through `petrinet_enabled`, `petrinet_entry_csv`, and
`petrinet_global_seed` in the PhysiCell XML. Use
`config/petrinet/manual_entries.example.csv` as the schedule template. Pressure
tests are available in `scripts/run_petrinet_benchmark_quick.sh` and
`scripts/run_petrinet_benchmark.sh`.

Each PhysiCell run XML selects bacterial input with
`petrinet_input_mode`: `0` keeps the current manual demo/CSV workflow, `1`
uses one-to-one uptake of extracellular `Bifidobacterium_longum` agents, and
`2` enables both intentionally. Agent uptake enters `SalRuffle`; the Petri-net
then chooses vacuole versus cytosol. This scenario switch does not require
regeneration or recompilation. Set `petrinet_uptake_csv` in the same run XML
when a conservation audit log is required.

Do not edit generated files manually. Update `INTERFACE.md` before changing a
public JSON, XML, CSV, or C++ contract; regenerate and commit the model
snapshot, unified parameter XML, generated pair, and version hashes together.

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
- `outputs/petrinet_minimal/death_statistics.csv`
- `outputs/petrinet_minimal/run.log`

The script asserts that the generated model and unit tests pass, both output
artifacts are non-empty, and the hard-coded injection was reported by the
PhysiCell executable.

The SVG is population-oriented. At each sample time it excludes rows with
`is_dead=1`, then draws the living-cell median and `median ± population sigma`
for bacterial burden, Gal8-pathway Ap tokens, Ub-pathway Ap tokens, and pMHC.
The final panel shows living cells included, all cumulative deaths, and the
PetriNet-triggered subset as a separate red dashed curve. Their difference is
death attributed to other PhysiCell mechanisms. The death CSV still reports
source/time and pathway peaks per cell.

Generate a larger independent experiment without changing the 8-hour baseline:

```bash
python scripts/make_minimal_petrinet_config.py \
  --output-name petrinet_24h_100 --duration-min 1440 \
  --bacteria 150 --cells 100
./project outputs/petrinet_24h_100/PhysiCell_settings.xml
python scripts/plot_xenophagy_metrics.py \
  --input outputs/petrinet_24h_100/xenophagy_metrics.csv \
  --output outputs/petrinet_24h_100/xenophagy_metrics.svg \
  --death-summary outputs/petrinet_24h_100/death_statistics.csv
```

For an agent-input experiment, create nearby physical bacteria without a
manual bolus and select the mode in the generated run XML:

```bash
python3 scripts/make_minimal_petrinet_config.py \
  --output-name petrinet_uptake --duration-min 60 --bacteria 0 --cells 1 \
  --extracellular-bacteria 20 --input-mode agent
./project outputs/petrinet_uptake/PhysiCell_settings.xml
```

The corresponding one-agent/one-token audit is written to
`outputs/petrinet_uptake/bacterial_uptake.csv`.

For routine development, keep the root `main.cpp` as the production entry
point and run the smaller copied-main scenario instead:

```bash
bash tests/bacterial_uptake_simulation/run.sh
```

That test builds `project_petrinet_uptake_test`, checks that its copied main is
current, and runs 25 tumor cells plus 50 extracellular bacterial agents without
changing the production XML or executable.

## Python parity check

`run_petrinet_tests.sh` also compiles `/tmp/petrinet_parity_driver`. Compare
the locked 8-hour, non-dividing, initial-`SalVac=50` baseline with:

```bash
python scripts/compare_python_cpp_parity.py \
  --cpp /tmp/petrinet_parity_driver --samples 100
```

If numerical Python runs on Windows while the driver runs in WSL, redirect the
driver output to CSV and use `--cpp-csv <path>`.
