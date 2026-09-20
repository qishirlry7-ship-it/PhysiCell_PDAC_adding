# PhysiCell–PetriNet design

This document is the design authority for implementation structure and planned
couplings. Stable field and API contracts belong in `INTERFACE.md`.

## Runtime architecture

The upstream JSON topology is parsed at run time by the self-contained
`petrinet::` runtime library in `custom_modules/petrinet/runtime/` (`json.cpp`,
`model.cpp`, `expression.cpp`, `ssa.cpp`). `xenophagy::PetriNetEngine` is a thin
wrapper over it and resolves place indices by name against the loaded model, so
place ordering is an implementation detail rather than a compiled-in contract.
PhysiCell has no runtime dependency on Python or `petrinettool`. Editing the
model or its parameters no longer requires recompiling — only replacing the
JSON.

Each infected tumor owns a `CellPetriNetState`: marking, internal time, queued
inputs, MHC state and deterministic random stream. Uninfected cells allocate no
state until their first entry. During a phenotype window the engine repeatedly
selects the earliest SSA reaction, external input or window end. Death hazard
and MHC dynamics are integrated over each intervening interval.

The topology is shared read-only under OpenMP. Each worker mutates only its
current cell state. PhysiCell `custom_data` stores the pool index and exported
observables. Division partitions ordinary tokens binomially, rebuilds capacity,
partitions MHC molecules and assigns the daughter a separate random stream.

## Extracellular bacterial bridge

Living vessel agents probabilistically create `Bifidobacterium_longum` agents.
For every living bacterium, the bridge scans its mechanics voxel and adjacent
Moore voxels, selects at most one eligible living tumor within the configured
distance, enqueues one `SalRuffle` token and removes the physical agent. One
agent therefore always maps to one token. `StayingVac` and `EnteringCyt` retain
the original PetriNet competition; capacity limits replication, not uptake.

Collection and mutation are separate serial phases. Decisions are sorted by
bacterial ID before tokens are committed, which prevents duplicate uptake and
keeps runs reproducible across OpenMP thread counts.

## Death and immune coupling

PetriNet death is a window hazard and PhysiCell performs one Bernoulli draw per
window. It is not also written into a PhysiCell death rate. Independent
PhysiCell apoptosis, necrosis, damage and immune death remain active.

Gal8/Ub xenophagy activity drives the four-state MHC-II ODE. Surface pMHC-II is
mapped through a Hill response to per-target CD4 immunogenicity, after which
PhysiCell's standard contact attack accumulates damage. The former requirement
to transform into a `*_tumor_xenophagy` type is not used for this coupling.

## IFN-gamma to MHC-II: identified missing coupling

Python defines IFN-gamma-dependent MHC-II synthesis as

\[
S_M(c)=S_{M,base}+V_{M,IFN}\frac{c}{K_{M,IFN}+c}.
\]

The C++ engine does **not** implement this term. IFN-gamma dependence was
deliberately removed: the model targets a uniformly high-IFN-gamma state, so
the saturating factor is effectively constant and contributes no spatial
contrast, while it carried three parameters and an unresolved unit mismatch
(the PhysiCell field is dimensionless, the PetriNet parameter was annotated
`ng/mL`). MHC synthesis is therefore a constant:

\[
S_M=\text{const},
\]

set to the old expression's value at the high-IFN-gamma operating point, so
presentation levels are numerically unchanged. The spatial PhysiCell
`IFN_gamma` field still exists and still drives the CD8 rules; only the
PetriNet coupling is absent.

Re-introducing the coupling, if it is ever wanted, means: define the PhysiCell
field in physical units (or add an XML conversion factor), read each target
cell's local concentration at phenotype update, and pass it into `advance()`.
Keep a fixed-value mode for parity tests either way.

Previous MHC smoke tests demonstrate the downstream pMHC-II-to-CD4 path only.

## Baseline calibration before efficacy claims

The present tumor baseline is a net-decline system: base cycle entry is
`3.6e-5/min`, base apoptosis is `7.2e-5/min`, pressure suppresses proliferation,
nutrient loss activates necrosis and immune attack remains enabled. Therefore
the current 10-day treatment run cannot isolate treatment efficacy.

Calibrate in layers: pure tumor with fixed nutrients; add pressure; add vessels
and nutrient limitation; add non-attacking immune cells; enable baseline immune
attack; finally compare bacteria/PetriNet/MHC treatment arms with matched seeds.
Record division and apoptosis, necrosis, immune/damage and PetriNet death as
separate outcomes.

## Planned x-axis vessel geometry

The preferred interpretable geometry is a hybrid vessel across the x-axis:

- a BioFVM voxel line supplies continuous oxygen and glucose;
- sparse fixed vessel agents provide visualization and bacterial release;
- vessel agents do not mechanically repel ordinary cells;
- release is parameterized per vessel length, so changing node spacing does not
  change total bacterial input;
- later variants may add parallel vessels and compressed low-supply segments.

## Concurrency and reproducibility

Cell streams derive from the global seed and cell ID; daughters use their own
IDs. Generated network data are immutable. Metrics are emitted by the main
thread. Statistical Python/C++ parity is required because RNG implementations
differ; event-for-event equality is not expected.
