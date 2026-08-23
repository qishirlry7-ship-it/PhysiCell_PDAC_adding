# Bacterial uptake simulation test

The root `main.cpp` is the production simulation entry point. This directory
contains a byte-for-byte copy used only for testing new coupling behavior with
a smaller population. `run.sh` refuses to run if the copy is stale, so changes
to production `main.cpp` must be reviewed and copied here deliberately.

The test generates an ignored 30-minute scenario with 25 tumor cells and 50
extracellular `Bifidobacterium_longum` agents. Its run XML enables PetriNet
agent input without changing the production XML. It verifies that at least one
physical bacterium is accepted, no bacterial ID is accepted twice, and the
per-cell metrics expose the ruffle and total-uptake fields.

Run from WSL base:

```bash
bash tests/bacterial_uptake_simulation/run.sh
```
