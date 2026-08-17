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

Per-PetriNet Gal8/Ub observability run on the same 8-hour demo:

| Cell/PetriNet | First observation (min) | Peak Gal8 Ap tokens | Peak Ub Ap tokens | Dead |
|---:|---:|---:|---:|---:|
| 0 | 0 | 8 | 4 | no |
| 1 | 0 | 11 | 6 | no |
| 2 | 0 | 10 | 9 | no |
| 3 | 0 | 12 | 7 | no |
| 28 (daughter) | 192 | 7 | 4 | no |

No deaths occurred among the five observed PetriNet states. This is expected
for this realization because the initial vacuolar burden is 50 while the
PetriNet death threshold is 100. The SVG nevertheless includes the cumulative
death panel, and `death_statistics.csv` records one row per observed cell.

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

Unified-XML migration check: after moving all non-PhysiCell values from the
former integration JSON and C++ MHC defaults into `parameters.xml`, the
100-seed C++ parity CSV was compared line-by-line with the pre-migration CSV.
All 101 lines (header plus 100 cells) were identical. The complete 8-hour
PhysiCell demo also passed with 5 observed PetriNet states, 373 metric rows,
and zero deaths.

## 24-hour, 100-cell, 150-bacterium stress run

An independent ignored output directory was generated with 100 initial cancer
cells, `SalVac=150` per cell at time zero, 24 hours, seed 42, 6-minute
phenotype/metrics windows, division enabled, and the current unified XML model
parameters, including `mhc_r_pep=5`.

- all 100 cells had exactly 150 intracellular bacteria at time zero;
- 112 PetriNet states were observed (12 daughters);
- 25,453 metric rows were written through 1,440 minutes;
- all 112 observed states entered death: 7 PetriNet-triggered and 105 from
  independent PhysiCell death mechanisms;
- median PetriNet death time was 216 min (range 12–846 min);
- median other-PhysiCell death time was 444 min (range 48–1,338 min);
- at 24 h, 100 agents remained in the container and all were marked dead;
- maxima were bacterial burden 517, Gal8 Ap tokens 22, Ub Ap tokens 22, and
  surface pMHC 246.367;
- full wall time was 25.05 s with 4 OpenMP threads.

The dominant death source is PhysiCell (105/112), not the PetriNet hazard
(7/112). Biological interpretation of total survival requires a separate
control with PhysiCell-native death disabled or calibrated.
