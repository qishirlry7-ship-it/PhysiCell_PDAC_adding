# PetriNet–PhysiCell interface v3

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
transitions, and transition expression overrides. The engine validates it at
load time. Agent-based uptake enters through `SalRuffle`; `EnteringCyt` and `StayingVac`
remain enabled and decide the intracellular compartment through ordinary SSA
competition. There are no independent C++ numeric defaults that override this
XML.

The XML root is `petrinet_parameters`. Scalars are `<parameter>` nodes under
`engine`, `mhc`, or `coupling`; marking uses `<place id="..." tokens="..."/>`; transition
rules use `<disable id="..."/>` and `<override id="...">expression`. Names
must be unique and values finite. Renaming/removing a required parameter or
changing its meaning requires an interface version increment.

## Time and input

- PhysiCell public time: minutes.
- Petri-net internal time and rates: seconds.
- MHC rates in `parameters.xml`: hours; conversion occurs inside the engine.

`petrinet_input_mode` in the PhysiCell run XML selects the source: `0=manual`, `1=agent`, and
`2=hybrid`. Manual is the compatibility default. In agent or hybrid mode, one
extracellular `Bifidobacterium_longum` agent maps to exactly one `SalRuffle`
token through:

```cpp
void enqueue_bacterial_uptake(
    PhysiCell::Cell* tumor,
    double time_minutes,
    int bacteria_count = 1);
```

This API does not select cytosol versus vacuole and does not inspect capacity.
`CapCyt` and `CapVac` constrain proliferation only. For the nearest living
target tumor within `bacterial_uptake_distance`, uptake over one bridge update
has probability

\[
P_{uptake}=1-\exp(-k_{uptake}\Delta t).
\]

The bridge collects decisions before mutation, sorts by bacterial ID, then
enqueues one token and removes one extracellular agent. Exact distance ties
are resolved by tumor cell ID.

The stable manual input API is:

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

## MHC-II to CD4 coupling

`surface_pMHC` is the antigen-specific MHC-II complex count on each target
tumor. It replaces the former discrete requirement that CD4 cells only attack
`*_tumor_xenophagy`. For a target with surface count `P`, its immunogenicity to
both configured CD4 types is

\[
I_{CD4}(P)=\frac{P^n}{K^n+P^n}.
\]

`mhcii_cd4_attack_max` is installed as the CD4 attack rate against every target
tumor type; `mhcii_cd4_half_max` is `K`, and `mhcii_cd4_hill` is `n`. PhysiCell's
standard interaction probability remains `attack_rate * target_immunogenicity
* dt`. Uninfected tumors have zero CD4 immunogenicity. The old fixed xenophagy
attack is therefore not added a second time. CD8 behavior is unchanged because
this interface represents MHC-II, not MHC-I.

The MHC-II synthesis input is the constant `mhc_S_M_base` in
`config/petrinet/parameters.xml`. IFN-gamma dependence is deliberately absent
(see `DESIGN.md`): the model targets a uniformly high-IFN-gamma state, so the
saturating term was constant in practice. The spatial PhysiCell `IFN_gamma`
substrate is unaffected and still drives CD8 rules. Re-introducing the coupling
would change the `advance()` contract and require an interface version
increment.

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

XML parameters are `petrinet_enabled` (bool), `petrinet_input_mode` (int),
`petrinet_global_seed` (int),
`petrinet_entry_csv` (string), `petrinet_demo_vacuolar_bacteria` (int),
`petrinet_metrics_csv` (string), `petrinet_uptake_csv` (string), and
`petrinet_metrics_interval` (minutes).

`petrinet_demo_vacuolar_bacteria > 0` is a minimal-test-only hard-coded event:
after tissue creation at `t=0`, that many bacteria are added to `SalVac` for
every living target tumor cell. It is independent of the scheduled CSV input.

The metrics CSV schema is:

```text
time_min,cell_id,cell_type,intracellular_bacteria,sal_ruffle_tokens,uptaken_bacteria,ap_gal8_tokens,ap_ub_tokens,xenophagy_activity,surface_pMHC,mhcii_cd4_recognition,physicell_damage,death_probability,is_dead,petrinet_death_triggered,death_time_min
```

`intracellular_bacteria` retains its existing definition and excludes
`SalRuffle`; `uptaken_bacteria` includes it. The pending token is visible for
conservation audits but does not contribute to death hazard.

The optional uptake audit CSV schema is:

```text
time_min,bacteria_id,tumor_id,tokens,entry_place,result
```

`ap_gal8_tokens` sums `Ap_Gal8`, `Ap_Gal8_Ub`, `Ap_Gal8_Ub_OPTNp`, and
`Ap_Gal8_Ub_N_S`. `ap_ub_tokens` sums `Ap_Ub`, `Ap_Ub_OPTNp`, and
`Ap_Ub_N_S`. Every active cell/PetriNet therefore has separate Gal8- and
Ub-pathway time series. `death_time_min=-1` means no death has been observed;
`petrinet_death_triggered=1` distinguishes the PetriNet hazard from independent
PhysiCell death mechanisms.

`mhcii_cd4_recognition` is the bounded target immunogenicity used by the
standard PhysiCell attack sampler. `physicell_damage` exposes damage accumulated
from immune attack and other PhysiCell mechanisms; it is not PetriNet hazard.

Population visualization groups rows by `time_min` and filters to
`is_dead=0` before computing each point. The center is the median and the band
is median plus/minus the population standard deviation (`pstdev`, denominator
N). If no living cells remain at a time point, no molecular summary is drawn;
the living-cell count is still drawn as zero.

MultiCellDS custom data exposes
`pn_state_index`, `pn_active`, `intracellular_bacteria`,
`sal_ruffle_tokens`, `uptaken_bacteria`,
`ap_gal8_tokens`, `ap_ub_tokens`, `xenophagy_activity`, `surface_pMHC`, and
`mhcii_cd4_recognition`, and `pn_death_probability`.

## Python parity condition

The reproducibility baseline is one non-dividing cell for 8 hours with 50
tokens placed directly in `SalVac` at time zero, `k_death=1e-7`, IFN-gamma 5,
immature `d_P=0.069`, and no further bacterial input. Direct initialization is
required because Python's function-input strategy is sampled only after its
first ordinary SSA reaction. Random engines differ, so acceptance is
distributional rather than seed-by-seed.
