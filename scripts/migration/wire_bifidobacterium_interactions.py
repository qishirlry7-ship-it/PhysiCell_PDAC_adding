# -*- coding: utf-8 -*-
"""
Adds the specific named entries needed for the xenophagy pipeline:
  - PD-L1lo/hi_tumor: transformation_rate entry targeting their own
    _infected variant (baseline 0, Rules below drive it via contact)
  - PD-L1lo/hi_tumor_infected: transformation_rate entry targeting
    their own _xenophagy variant (small baseline + rapamycin-driven,
    via Rules below)
  - PD-1hi/lo_CD4_Tcell: attack_rate entries against ONLY the two
    _xenophagy types (0.15/min -- moderate, CD4 CTL activity is
    generally less potent than CD8's per general immunology, no
    PDAC-specific CD4-cytotoxicity rate found in literature, C-level).
    Attack rate against the original tumor types and the _infected
    stage stays exactly 0 (never added), matching the confirmed design.
  - macrophage: live_phagocytosis_rate entry against
    Bifidobacterium_longum (0.02/min, baseline clearance)
"""
import re

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(xml, name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return start, end, xml[start:end]

def add_entries(xml, cell_name, tag, entries):
    s, e, block = get_block(xml, cell_name)
    anchor = f"</{tag}>"
    i = block.find(anchor)
    tag_singular = {"transformation_rates": "transformation_rate", "attack_rates": "attack_rate",
                     "live_phagocytosis_rates": "phagocytosis_rate"}[tag]
    new_text = "".join(
        f'                        <{tag_singular} name="{name}" units="1/min">{rate}</{tag_singular}>\n'
        for name, rate in entries
    )
    block = block[:i] + new_text + block[i:]
    return xml[:s] + block + xml[e:]

xml = add_entries(xml, "PD-L1lo_tumor", "transformation_rates", [("PD-L1lo_tumor_infected", 0)])
xml = add_entries(xml, "PD-L1hi_tumor", "transformation_rates", [("PD-L1hi_tumor_infected", 0)])
xml = add_entries(xml, "PD-L1lo_tumor_infected", "transformation_rates", [("PD-L1lo_tumor_xenophagy", 1e-5)])
xml = add_entries(xml, "PD-L1hi_tumor_infected", "transformation_rates", [("PD-L1hi_tumor_xenophagy", 1e-5)])

xml = add_entries(xml, "PD-1hi_CD4_Tcell", "attack_rates",
                   [("PD-L1lo_tumor_xenophagy", 0.15), ("PD-L1hi_tumor_xenophagy", 0.15)])
xml = add_entries(xml, "PD-1lo_CD4_Tcell", "attack_rates",
                   [("PD-L1lo_tumor_xenophagy", 0.15), ("PD-L1hi_tumor_xenophagy", 0.15)])

xml = add_entries(xml, "macrophage", "live_phagocytosis_rates", [("Bifidobacterium_longum", 0.02)])

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("wired transformation_rates (tumor->infected->xenophagy), CD4 attack_rates (xenophagy-only), macrophage phagocytosis of bacteria")
