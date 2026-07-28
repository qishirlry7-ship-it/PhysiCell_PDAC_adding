# -*- coding: utf-8 -*-
"""
Adds glucose/lactate metabolism + hypoxia/glucose-driven necrosis to the
two tumor cell types, and glucose supply to the vessels (real vessels
carry glucose as well as oxygen -- extends step 3's vessel mechanism
rather than leaving glucose as a strictly-depleting resource with no
source at all).

This is the first step that changes values already active in pdac_therapy's
original 9 cell types (specifically: tumor's necrosis death_rate, which
was 0 -- i.e. this death pathway never fired at all before -- and adds
glucose uptake + lactate secretion, which were simply absent/zero
before). Disclosed explicitly in the commit message, same as step 3's
oxygen-boundary replacement.
"""
import re

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return start, end, xml[start:end]

# --- 1. vessels also supply glucose (rate/target chosen the same way as
#        step 3's oxygen fix: reuse the value already learned to work in
#        PhysiCell_PDAC_TME for the same sparse-source-vs-many-consumers
#        problem) ---
vs, ve, vblock = get_block("fixed_vessel_source")
i = vblock.find("</secretion>")
glucose_sub = (
    '                    <substrate name="glucose">\n'
    '                        <secretion_rate units="1/min">100</secretion_rate>\n'
    '                        <secretion_target units="substrate density">1</secretion_target>\n'
    '                        <uptake_rate units="1/min">0</uptake_rate>\n'
    '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
    "                    </substrate>\n"
)
vblock = vblock[:i] + glucose_sub + vblock[i:]
xml = xml[:vs] + vblock + xml[ve:]

# --- 2. tumor cells: glucose uptake, lactate secretion (Warburg baseline
#        + hypoxia amplification via Rules below), and turn on the
#        necrosis death model (baseline set to the fully-starved/hypoxic
#        rate, Rules below bring it down as oxygen/glucose recover) ---
for tumor_name in ["PD-L1lo_tumor", "PD-L1hi_tumor"]:
    ts, te, tblock = get_block(tumor_name)

    # necrosis baseline: was 0 (this death pathway never fired). Set to
    # 0.02/min (same magnitude used for the equivalent mechanism in
    # PhysiCell_PDAC_TME) at the O2=0/glucose=0 anchor; Rules pull it
    # down as either recovers.
    necrosis_marker = '<model code="101" name="necrosis">\n                        <death_rate units="1/min">0</death_rate>'
    assert tblock.count(necrosis_marker) == 1, tumor_name
    tblock = tblock.replace(
        necrosis_marker,
        '<model code="101" name="necrosis">\n                        <death_rate units="1/min">0.02</death_rate>'
    )

    i = tblock.find("</secretion>")
    new_subs = (
        '                    <substrate name="glucose">\n'
        '                        <secretion_rate units="1/min">0</secretion_rate>\n'
        '                        <secretion_target units="substrate density">1</secretion_target>\n'
        '                        <uptake_rate units="1/min">5</uptake_rate>\n'
        '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
        "                    </substrate>\n"
        '                    <substrate name="lactate">\n'
        '                        <secretion_rate units="1/min">1.0</secretion_rate>\n'
        '                        <secretion_target units="substrate density">10</secretion_target>\n'
        '                        <uptake_rate units="1/min">0</uptake_rate>\n'
        '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
        "                    </substrate>\n"
    )
    tblock = tblock[:i] + new_subs + tblock[i:]

    xml = xml[:ts] + tblock + xml[te:]
    # re-find offsets since string length changed -- refresh via get_block
    # is not needed further since we process tumor types independently
    # and re-search from the (now-updated) xml each iteration
    ts, te, tblock = get_block(tumor_name)  # sanity re-fetch, unused

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("vessels now supply glucose; both tumor types have glucose uptake, lactate secretion, and a nonzero necrosis baseline")

# --- 3. Rules: hypoxia/glucose-starvation drive necrosis; hypoxia
#        amplifies lactate secretion above its Warburg baseline ---
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

new_rules = [
    "PD-L1lo_tumor,oxygen,decreases,necrosis,0,3,8,0",
    "PD-L1hi_tumor,oxygen,decreases,necrosis,0,3,8,0",
    "PD-L1lo_tumor,glucose,decreases,necrosis,0,0.1,4,0",
    "PD-L1hi_tumor,glucose,decreases,necrosis,0,0.1,4,0",
    "PD-L1lo_tumor,oxygen,decreases,lactate secretion,0.1,5,3,0",
    "PD-L1hi_tumor,oxygen,decreases,lactate secretion,0.1,5,3,0",
]
if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print(f"added {len(new_rules)} new rules")
