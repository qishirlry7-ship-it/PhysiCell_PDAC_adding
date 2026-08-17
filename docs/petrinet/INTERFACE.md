# PetriNet–PhysiCell interface v1

## Upstream JSON

The upstream JSON shape is unchanged. It contains `name`, `places`, and
`transitions`; optional top-level `params` is accepted. A place has `id` and
integer `tokens`. A transition has `id`, optional numeric `rate`, optional
string `expression`, and `input` / `output` arc arrays. Input arcs use `from`,
output arcs use `to`, and both use a positive integer `weight` (default 1).

For a numeric rate, propensity is

\[
a_j(x)=k_j\prod_i {x_i \choose w_{ij}}.
\]

An expression is the complete propensity and may reference place identifiers,
numeric parameters, arithmetic operators, and `min`, `max`, `abs`, `sqrt`,
`exp`, or `log`. Negative and non-finite results are clamped to zero.

The single non-PhysiCell parameter source is
`config/petrinet/parameters.xml`. It contains engine/death/sigmoid/capacity
parameters, all MHC parameters and initial conditions, initial Petri-net
marking, signal mode, MHC integration step, division fraction, disabled
transitions, and transition expression overrides. The build
generator validates it and compiles it into the checked-in C++ pair.
`EnteringCyt` and `StayingVac` are disabled because entry is external. There
are no independent C++ numeric defaults that override this XML.

The XML root is `petrinet_parameters`. Scalars are `<parameter>` nodes under
`engine` or `mhc`; marking uses `<place id="..." tokens="..."/>`; transition
rules use `<disable id="..."/>` and `<override id="...">expression`. Names
must be unique and values finite. Renaming/removing a required parameter or
changing its meaning requires an interface version increment.

## Time and input

- PhysiCell public time: minutes.
- Petri-net internal time and rates: seconds.
- MHC rates in `parameters.xml`: hours; conversion occurs inside the engine.

External input API:

```cpp
void enqueue_bacterial_entry(
    PhysiCell::Cell* cell,
    double time_minutes,
    int to_cytosol,
    int to_vacuole);
```

CSV input has the exact header:

```text
time_min,cell_id,to_cytosol,to_vacuole
```

Counts and time must be non-negative. `cell_id=-1` broadcasts to living tumor
cells selected by the adapter. Events for one cell at one time are merged.

## Window API and output

Queued entries are stored on `CellPetriNetState`; the implemented engine API is:

```cpp
void PetriNetEngine::enqueue(CellPetriNetState&, const EntryEvent&) const;
WindowResult PetriNetEngine::advance(CellPetriNetState&, double window_end_seconds) const;
```

`advance` interleaves external entries with SSA reactions and returns
intracellular burden, xenophagy signal, antigen flux, integrated death hazard,
and death probability. Events at a window endpoint are applied before return.
Past events and negative counts are rejected. Broadcasts are expanded at
dispatch time, so daughters existing at that time are included.

The default `EngineConfig::XenoSignalMode` reproduces `agent_core.py`: the
exponential waiting time is sampled from ordinary Petri-net propensities, an
ordinary transition fires, and then at most one `XenoSig` token is added with
the Python probability `sigmoid(t, burden) * dt`. The alternative
`ContinuousCompetingHazard` mode treats the sigmoid as an independent
continuous-time event; it is intentionally not used for Python parity.

For piecewise-constant bacterial burden,

\[
H=\sum_k k_{death}\max(N_{bac,k}-N_{threshold},0)\Delta t_k,
\qquad P_{death}=1-e^{-H}.
\]

PhysiCell performs exactly one Bernoulli draw from this probability per
phenotype window and calls `Cell::start_death`. The same hazard must not also be
written to a PhysiCell death rate.

## Division

Ordinary discrete places use binomial partitioning. `CapCyt` and `CapVac` are
derived after partitioning:

```text
CapCyt = max(0, cap_cyt_initial - SalCyt - AdapSalCyt)
CapVac = max(0, cap_vac_initial - SalVac - AdapSalVac)
```

MHC molecule counts are partitioned by the same volume fraction. Parent and
child keep the same physical time and receive distinct random streams.

## Runtime configuration and observables

XML parameters are `petrinet_enabled` (bool), `petrinet_global_seed` (int),
`petrinet_entry_csv` (string), `petrinet_demo_vacuolar_bacteria` (int),
`petrinet_metrics_csv` (string), and `petrinet_metrics_interval` (minutes).

`petrinet_demo_vacuolar_bacteria > 0` is a minimal-test-only hard-coded event:
after tissue creation at `t=0`, that many bacteria are added to `SalVac` for
every living target tumor cell. It is independent of the scheduled CSV input.

The metrics CSV schema is:

```text
time_min,cell_id,cell_type,intracellular_bacteria,ap_gal8_tokens,ap_ub_tokens,xenophagy_activity,surface_pMHC,death_probability,is_dead,petrinet_death_triggered,death_time_min
```

`ap_gal8_tokens` sums `Ap_Gal8`, `Ap_Gal8_Ub`, `Ap_Gal8_Ub_OPTNp`, and
`Ap_Gal8_Ub_N_S`. `ap_ub_tokens` sums `Ap_Ub`, `Ap_Ub_OPTNp`, and
`Ap_Ub_N_S`. Every active cell/PetriNet therefore has separate Gal8- and
Ub-pathway time series. `death_time_min=-1` means no death has been observed;
`petrinet_death_triggered=1` distinguishes the PetriNet hazard from independent
PhysiCell death mechanisms.

Population visualization groups rows by `time_min` and filters to
`is_dead=0` before computing each point. The center is the median and the band
is median plus/minus the population standard deviation (`pstdev`, denominator
N). If no living cells remain at a time point, no molecular summary is drawn;
the living-cell count is still drawn as zero.

MultiCellDS custom data exposes
`pn_state_index`, `pn_active`, `intracellular_bacteria`,
`ap_gal8_tokens`, `ap_ub_tokens`, `xenophagy_activity`, `surface_pMHC`, and
`pn_death_probability`.

## Python parity condition

The reproducibility baseline is one non-dividing cell for 8 hours with 50
tokens placed directly in `SalVac` at time zero, `k_death=1e-7`, IFN-gamma 5,
immature `d_P=0.069`, and no further bacterial input. Direct initialization is
required because Python's function-input strategy is sampled only after its
first ordinary SSA reaction. Random engines differ, so acceptance is
distributional rather than seed-by-seed.
