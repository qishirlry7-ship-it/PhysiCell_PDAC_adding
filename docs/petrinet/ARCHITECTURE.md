# Architecture

The upstream JSON and integration overrides are compiled by a standalone
standard-library Python script. Generated topology, stoichiometry, initial
marking, and propensity functions are immutable and shared by all cells.

Each active tumor cell owns only its marking, internal time, input queue, MHC
state, and deterministic cell-level random stream. Uninfected cells are lazy:
they allocate and advance no SSA state until their first entry event.

Within a phenotype window the engine repeatedly selects the earliest of the
next exponential SSA reaction, the next external entry, and the window end.
Death hazard and MHC input are integrated over every intervening interval.

PhysiCell's `cell_division_function(parent, child)` partitions state without
modifying PhysiCell core. The network is read-only under OpenMP; state is owned
per cell and pool allocation is synchronized. Observable values are mirrored
to custom data for MultiCellDS output.

Custom fields are registered on `cell_defaults` before XML inheritance. Target
tumor definitions then receive the PetriNet phenotype and division callbacks.
The main loop dispatches scheduled inputs before cell updates and reclaims
removed-cell state slots afterward.

Random streams derive from the global seed and cell ID; daughters derive a new
stream from their own ID. Network data is immutable, and each OpenMP worker
only mutates the state belonging to its current cell.
