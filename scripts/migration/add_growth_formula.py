# -*- coding: utf-8 -*-
"""
Makes tumor proliferation (cycle entry) responsive to local oxygen and
glucose, on top of the existing pressure-based contact inhibition rule
(untouched). Same "starved floor + increases-rules pull it back up"
pattern already used for necrosis in step 4 (there: high-at-zero-signal
baseline pulled DOWN by "decreases" rules; here: low-at-zero-signal
baseline pulled UP by "increases" rules) -- confirmed with the user
this technical approach (has to change the XML baseline itself, Rules
always anchors behavior(signal=0)=XML value) is acceptable before
implementing.

Literature basis (see chat for full citation list):
  - oxygen: PhysiCell's own official oxygen-linear-interpolation
    proliferation model (Ghaffarizadeh et al. 2018, PLOS Comp Biol) is
    the methodological precedent for gating cycle entry by oxygen via a
    Hill/interpolation response rather than inventing a new mechanism.
  - glucose: high glucose promotes PDAC proliferation via EGF/EGFR
    transactivation (Ma et al., PLOS ONE 2011); PI3K/Akt and glycolytic
    reprogramming under high glucose (multiple PMC reviews).
  - ECM/ stiffness deliberately NOT included as a growth driver: direct
    literature conflict (YAP/PD-L1/Ki67 increases with stiffness in
    lung adenocarcinoma vs. decreased spheroid proliferation with
    stiffness in breast cancer 3D collagen gels) with no PDAC-specific
    resolution found -- flagged to the user as omitted rather than
    guessed.
  - baseline calibration reference: MIA PaCa-2 in vitro doubling time =
    40h (ATCC, multiple sources) -- kept as a documented calibration
    anchor even though pdac_therapy's own original value (7.2e-4/min,
    ~23.1h) is used unchanged as the ceiling here, not replaced by the
    40h-derived rate, since changing the original ceiling itself is a
    separate decision from adding environmental gating.

Cell-cycle transition being stochastic (fixed_duration="false" already
in the XML, confirmed with the user against the Smith-Martin transition
probability model literature, Smith & Martin 1973 Nature) is NOT
changed by this step -- these rules only change the RATE, PhysiCell's
existing stochastic sampling mechanism is untouched.
"""
XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

FLOOR = "3.6e-5"   # 5% of the original 7.2e-4 ceiling -- severely starved residual rate
CEILING = "7.2e-4" # pdac_therapy's own original, unchanged, well-fed ceiling

old_count = xml.count(f'<rate start_index="0" end_index="0" fixed_duration="false">7.20E-04</rate>')
assert old_count == 2, f"expected 2 tumor cycle-rate occurrences, found {old_count}"
xml = xml.replace(
    '<rate start_index="0" end_index="0" fixed_duration="false">7.20E-04</rate>',
    f'<rate start_index="0" end_index="0" fixed_duration="false">{FLOOR}</rate>'
)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print(f"replaced {old_count} tumor cycle-rate baselines: 7.2e-4 -> {FLOOR} (starved floor)")

RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

new_rules = [
    f"PD-L1lo_tumor,oxygen,increases,cycle entry,{CEILING},5,2,0",
    f"PD-L1hi_tumor,oxygen,increases,cycle entry,{CEILING},5,2,0",
    f"PD-L1lo_tumor,glucose,increases,cycle entry,{CEILING},0.3,2,0",
    f"PD-L1hi_tumor,glucose,increases,cycle entry,{CEILING},0.3,2,0",
]
if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print(f"added {len(new_rules)} growth-modulation rules")
