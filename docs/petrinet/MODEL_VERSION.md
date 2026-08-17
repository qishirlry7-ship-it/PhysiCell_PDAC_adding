# Model version

The generated C++ banner is the authoritative manifest for the source JSON,
unified parameter XML, generator version, and SHA-256 values. Update this
page with the validation commit whenever a new upstream snapshot is published.

- Interface: v1
- Upstream snapshot: `config/petrinet/xenophagy_model.json`
- Unified non-PhysiCell parameters: `config/petrinet/parameters.xml`
- Places / transitions: 57 / 80
- Model SHA-256: `beaafd39036a29aab6eb846082b6d4f2ceef830d7c2d83594d976bd681b5c305`
- Parameters SHA-256: `776a561ca34be159148565ffcbb01d27b999de8629371288f2f98af9fc6d6fde`
- Generator: `scripts/generate_petrinet_cpp.py` 2.0.0

Run `python3 scripts/generate_petrinet_cpp.py --check` before review and update
this manifest whenever the model snapshot or unified parameter XML changes.
