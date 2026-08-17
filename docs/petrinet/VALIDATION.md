# Validation

Validation uses the WSL base environment. The C++ and Python implementations
are compared statistically, not event-for-event, because their random-number
engines differ. The acceptance run uses at least 1,000 cells and records the
exact Git commit, model hashes, seed, duration, and parameters.

Completed in WSL base:

- generated-source freshness and C++11 standalone build;
- endpoint input, same-time merge, invalid-input rejection and death bounds;
- division token conservation and capacity reconstruction;
- complete PhysiCell 1.14.1 release build;
- one-minute, 1,724-cell PhysiCell smoke run with PetriNet enabled and a
  50-bacterium vacuolar broadcast.
- repeatable four-cell minimal demo for 8 hours with a code-level `t=0`
  entry event, CSV time series, and valid SVG visualization.

Measured 8-hour minimal-demo evidence:

- 4 initial cells, one division, and 5 cells present at 480 min;
- 373 metric rows across 0–480 min at 6 min intervals;
- all four cells contain exactly 50 bacteria at `t=0`;
- maximum observed xenophagy activity: 17;
- maximum observed surface pMHC: 28.8291;
- final intracellular bacterial burdens: 37, 80, 74, 76, and 47;
- PhysiCell simulation runtime: 8.69 s in the recorded WSL base run;
- generated SVG is non-empty and parses as valid XML;
- `scripts/run_minimal_petrinet_demo.sh` exits successfully with `PASS`.

The tracked initial-cell CSV uses CRLF. Its loader retains the trailing `\r` in
type names under WSL, creating zero cells and causing a baseline MultiCellDS
null dereference. The smoke test used an ignored LF-normalized copy; the shared
CSV was not modified.

Python parity correction and 100-cell calibration completed on the 8-hour
single-cell baseline (no division, initial `SalVac=50`). The correction fixed
`Syn10` to use Python's `LC3` place and made Python's post-reaction Bernoulli
`XenoSig` rule the default. Mean relative differences were:

| Metric | Python mean | C++ mean | Relative difference |
|---|---:|---:|---:|
| ordinary SSA steps | 3171.85 | 3126.93 | 1.42% |
| final bacterial burden | 73.14 | 74.20 | 1.45% |
| peak xenophagy activity | 17.29 | 17.54 | 1.45% |
| final xenophagy activity | 3.30 | 3.22 | 2.42% |
| final `XenoSig` | 1887.18 | 1863.83 | 1.24% |
| peak surface pMHC | 25.3121 | 24.8544 | 1.81% |
| final surface pMHC | 25.3121 | 24.8540 | 1.81% |

All reported means pass the 10% criterion. This establishes statistical
PetriNet and MHC alignment for the locked baseline; it does not establish
seed-by-seed identity or parity after PhysiCell division. The formal 1,000-cell
acceptance run remains to be recorded before release.
