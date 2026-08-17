# PhysiCell–PetriNet integration

This directory is the collaboration contract for the xenophagy Petri-net
integration. The runtime is C++ only. Python is used at build time to convert
the upstream JSON snapshot into deterministic C++ source.

## WSL base workflow

From the PhysiCell repository in the WSL base environment:

```bash
python3 scripts/generate_petrinet_cpp.py
python3 scripts/generate_petrinet_cpp.py --check
make
make petrinet-test
```

The checked-in generated source lets collaborators compile without running the
generator. `--check` is the required stale-model check before review.

See [INTERFACE.md](INTERFACE.md) for the stable interface and
[ARCHITECTURE.md](ARCHITECTURE.md) for ownership and data flow.
