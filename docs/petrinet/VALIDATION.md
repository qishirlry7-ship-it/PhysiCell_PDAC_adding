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
- maximum observed xenophagy activity: 9;
- maximum observed surface pMHC: 16.8972;
- final intracellular bacterial burdens: 45, 68, 84, 72, and 46;
- PhysiCell simulation runtime: 8.11 s in the recorded WSL base run;
- generated SVG is non-empty and parses as valid XML;
- `scripts/run_minimal_petrinet_demo.sh` exits successfully with `PASS`.

The tracked initial-cell CSV uses CRLF. Its loader retains the trailing `\r` in
type names under WSL, creating zero cells and causing a baseline MultiCellDS
null dereference. The smoke test used an ignored LF-normalized copy; the shared
CSV was not modified.

The 1,000-cell Python/C++ statistical comparison remains a calibration run:
this implementation intentionally replaces Python's post-event Bernoulli
checks with strict continuous-time XenoSig and death hazards. Acceptance remains
10% for key means/medians, 5 percentage points for survival, and no systematic
quantile drift; individual trajectories need not match.
