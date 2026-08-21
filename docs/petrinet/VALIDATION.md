# Validation

The current exploratory global uptake rate is `0.02/min`, applied uniformly to
all eligible target tumor cells within the configured uptake distance. This is
an uncalibrated two-fold sensitivity step from the prior `0.01/min` value; it
does not distinguish vessel or tumor subtypes.

A 10-day full-main WSL run with 1,724 initial agents, `bacteria_entry_lambda =
0.003/min/vessel`, and the global `0.02/min` uptake rate completed in 21 min
59.7 s. It produced 198 accepted uptake events involving 128 original target
IDs and 182 tracked PetriNets. Maximum pMHC-II recognition was 0.80714 and 27
tracked cells accumulated positive PhysiCell damage (maximum 54.3). Ten deaths
were PetriNet-triggered; 79 were classified as other PhysiCell deaths, of which
9 had positive damage histories. The latter are damage-associated, not a
strict causal attribution to CD4 without a matched treatment-off control.

## MHC-II–CD4 coupling smoke test

A 12-hour isolated run used one `PD-L1lo_tumor`, six adjacent CD4 cells, and a
manual 50-bacterium input (below the configured PetriNet death threshold). The
target reached `surface_pMHC=151.6`, `mhcii_cd4_recognition=0.834802`, and
ordinary PhysiCell damage `7.3`. No PetriNet death or other death occurred.
Damage first became non-zero after pMHC-II recognition rose above zero, which
confirms that the standard PhysiCell contact-attack path consumes the new
target-specific immunogenicity. The run completed at 720 minutes in 12.6
seconds under WSL.

## Extracellular uptake invariants

Interface v2 adds a one-agent/one-token `SalRuffle` entry. The engine test
locks the zero initial ruffle marking, same-time event merging, separate
pending versus compartment burden, and enabled `StayingVac` / `EnteringCyt`
propensities (0.006 and 0.004 per ruffle token). Spatial acceptance must also
preserve the audit invariant: every `accepted` row corresponds to one removed
`Bifidobacterium_longum` agent and one queued `SalRuffle` token. The uptake
rate and distance are integration parameters, not biologically calibrated
values.

The C++ end-to-end uptake smoke run used one tumor, four extracellular agents
at 5 microns, a one-minute bridge interval, and a temporary rate of 100/min to
make acceptance deterministic for the test. At minute 1 the audit contained
four unique accepted bacterial IDs targeting the tumor. At minute 6 the tumor
reported `sal_ruffle_tokens=0`, `intracellular_bacteria=4`, and
`uptaken_bacteria=4`: all four physical agents were consumed exactly once and
the enabled compartment transitions preserved their total. The committed
uptake rate was then restored to 0.01/min before generation and build checks.
Input mode is a per-run XML switch. Production and the isolated simulation
test now select agent input; manual mode remains available for locked demos.

Production-main activation was checked with a 30-minute configuration derived
from `config/PhysiCell_settings.xml`: 25 tumor cells, 50 extracellular agents,
no manual bolus, and `petrinet_input_mode=1`. The root `project` executable
completed with 12 accepted rows, 12 unique bacterial IDs, and 14 per-cell
metric rows. This confirms that uptake is active through the real root
`main.cpp`, not only through its testing copy.

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

The 24-hour output was re-rendered with population statistics. Living cells
included at 0/240/480/720/960/1200/1440 min were respectively
100/98/42/18/6/1/0. The bacterial-burden medians at the first six non-empty
points were 150/130/130/140/144/147. The 1,440-minute molecular point is absent
because no living cell remains, while the living-count curve correctly reaches
zero. PhysiCell apoptosis/necrosis parameters were not changed.
