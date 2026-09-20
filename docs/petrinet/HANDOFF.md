# Project handoff

Status date: 2026-08-21
Branch: `codex/petrinet-integration`

## Delivered

- run-time JSON model loading with a self-contained `petrinet::` runtime;
- 57-place/80-transition xenophagy SSA engine;
- independent lazy PetriNet state per infected tumor;
- arbitrary manual input and one-agent/one-token extracellular uptake;
- state-conserving cell division and reconstructed capacity;
- PetriNet death hazard sampled by PhysiCell;
- Gal8/Ub, bacterial burden, pMHC-II and death observability;
- living-cell median plus population-sigma visualization;
- pMHC-II-to-CD4 target immunogenicity coupling;
- production `main.cpp` activation and WSL tests;
- 10-day visualization video at
  `outputs/main_10d_uptake002/main_10d_uptake002.mp4`.

## Evidence summary

- 8-hour four-cell demo: five observed states after one division, visible
  Gal8/Ub activity and pMHC-II, 8.69 s wall time;
- 100-sample Python/C++ parity: all reported mean differences below 2.5%;
- 24-hour 100-cell/150-bacterium stress run: 112 states, 25.05 s, but all cells
  died and 105/112 deaths came from PhysiCell rather than PetriNet;
- uptake invariant: four physical agents produced exactly four tokens;
- 12-hour MHC-II/CD4 smoke test: pMHC-II caused target recognition and damage;
- 10-day production run: 1,724 initial agents, 198 accepted uptake events,
  10 PetriNet deaths, 79 other PhysiCell deaths and 1,253 final agents;
- standalone 10,000-cell/24-hour SSA benchmark: 28.76 s with eight threads.

Detailed conditions and tables remain in `VALIDATION.md`.

## Main findings

1. Per-cell continuous-time PetriNets are computationally practical in
   PhysiCell.
2. Locked Python/C++ PetriNet and MHC dynamics are statistically aligned.
3. The full bacterial release-to-uptake-to-xenophagy-to-pMHC-II-to-CD4 chain
   executes, but treatment efficacy has not been established.
4. The no-treatment tumor baseline is not calibrated and naturally declines.
5. Local PhysiCell IFN-gamma is not yet connected to MHC-II synthesis; current
   C++ uses a fixed value of 5 ng/mL.
6. Bacterial release and uptake parameters are exploratory, not calibrated.

## Next actions, in order

1. Build a matched, no-bacteria baseline with attributable death categories.
2. Calibrate division, apoptosis, nutrient necrosis and immune attack in layers.
3. Implement and validate local IFN-gamma-to-MHC-II coupling with explicit units.
4. Replace scattered vessel sources with the designed x-axis hybrid vessel.
5. Run matched baseline, bacteria-only, xenophagy-only and full-treatment arms.
6. Complete the formal 1,000-cell Python/C++ acceptance run.
7. Calibrate bacterial release, uptake and MHC/CD4 parameters from evidence.

## Model manifest

- interface: v3;
- JSON: `config/petrinet/xenophagy_model.json`;
- parameters: `config/petrinet/parameters.xml`;
- places/transitions: 57/80;
- JSON SHA-256: `beaafd39036a29aab6eb846082b6d4f2ceef830d7c2d83594d976bd681b5c305`;
- parameter SHA-256: `2a32bf28b0e1e7b6fdb39272defbb2ddba358be091794c5cf87dffd0d370a904`;
- runtime: `custom_modules/petrinet/runtime/` (JSON loaded at run time).

The JSON and parameter XML are the authoritative model definition. They are no
longer compiled into C++ at build time, so there is no generated banner to
reconcile -- recompute the hashes above whenever either file changes.

## Working-tree warning at handoff

The following local items existed before this documentation commit and are not
part of it:

- `config/PhysiCell_settings.xml`: local duration and bacterial release edits;
- `config/ic_cells/PDAC_TISSUE_1_hybrid.csv`: line-ending/worktree change;
- `tests/baseline/`: untracked exploratory apoptosis-half baseline.

Do not stage these implicitly. Review and commit them separately only after the
owner confirms the intended baseline configuration.
