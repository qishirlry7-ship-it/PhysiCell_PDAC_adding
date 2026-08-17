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

The build-time integration configuration may replace expressions and disable
transitions. `EnteringCyt` and `StayingVac` are disabled because entry is an
external event. Adding optional JSON fields is backward compatible; changing
or removing the fields above requires a new interface version.

## Time and input

- PhysiCell public time: minutes.
- Petri-net internal time and rates: seconds.
- MHC parameters: hours; conversion occurs inside the adapter.

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

`advance(state, window_end_seconds, entries)` advances one cell by exact SSA,
interleaving external entries with reactions. It returns intracellular burden,
xenophagy signal, antigen flux, integrated death hazard, and death probability.

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
