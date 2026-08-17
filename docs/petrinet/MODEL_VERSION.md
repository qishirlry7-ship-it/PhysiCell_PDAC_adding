# Model version

The generated C++ banner is the authoritative manifest for the source JSON,
integration configuration, generator version, and SHA-256 values. Update this
page with the validation commit whenever a new upstream snapshot is published.

- Interface: v1
- Upstream snapshot: `config/petrinet/xenophagy_model.json`
- Integration overrides: `config/petrinet/integration.json`
- Places / transitions: 57 / 80
- Model SHA-256: `beaafd39036a29aab6eb846082b6d4f2ceef830d7c2d83594d976bd681b5c305`
- Integration SHA-256: `0f63f40a98aacf1b6aa376275a2670fd506bb0a3a5d07b20dbd11428eb7949f1`
- Generator: `scripts/generate_petrinet_cpp.py` 1.0.0

Run `python3 scripts/generate_petrinet_cpp.py --check` before review and update
this manifest whenever the model snapshot or integration configuration changes.
