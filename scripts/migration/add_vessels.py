# -*- coding: utf-8 -*-
"""
Replaces pdac_therapy's single domain-edge Dirichlet oxygen boundary with
discrete, stationary vessel point-source agents (new cell type
"fixed_vessel_source"), matching the fixed_vessel_source design already
used in PhysiCell_PDAC_TME. Disables the oxygen Dirichlet boundary
(all 6 faces) since it's being replaced, not supplemented.
"""
import re

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

# --- 1. disable the oxygen Dirichlet boundary (being replaced by vessels) ---
i = xml.find('<variable name="oxygen"')
j = xml.find('</variable>', i) + len('</variable>')
ox_block = xml[i:j]
before = ox_block
ox_block = ox_block.replace(
    '<Dirichlet_boundary_condition units="mmHg" enabled="True">38</Dirichlet_boundary_condition>',
    '<Dirichlet_boundary_condition units="mmHg" enabled="False">38</Dirichlet_boundary_condition>'
)
ox_block = re.sub(
    r'(<boundary_value ID="[a-z]+") enabled="True">38</boundary_value>',
    r'\1 enabled="False">38</boundary_value>',
    ox_block
)
assert ox_block != before, "no boundary flags were changed -- check the oxygen block format"
xml = xml[:i] + ox_block + xml[j:]

# --- 2. add the fixed_vessel_source cell type, cloned from macrophage,
#        stripped down to: no motility, no division, no death, secretes
#        only oxygen. Reuses the secretion_rate=200 we already learned
#        was needed to get a non-degenerate oxygen field in
#        PhysiCell_PDAC_TME (documented there as a pragmatic, not fully
#        calibrated, C-level fix for the same "sparse point sources vs
#        many consuming cells" supply problem). ---
start = xml.find('<cell_definition name="macrophage"')
end = xml.find('</cell_definition>', start) + len('</cell_definition>')
template = xml[start:end]

b = template.replace('name="macrophage" ID="2"', 'name="fixed_vessel_source" ID="17"')
b = b.replace('<death_rate units="1/min">0</death_rate>', '<death_rate units="1/min">0</death_rate>')  # already 0
b = b.replace(
    '<cell_cell_adhesion_strength units="micron/min">0</cell_cell_adhesion_strength>',
    '<cell_cell_adhesion_strength units="micron/min">0</cell_cell_adhesion_strength>'
)
# disable motility entirely (stationary point source, like the tumor's own
# convention for a non-motile type)
b = re.sub(r'<options>\s*<enabled>true</enabled>', '<options>\n                        <enabled>false</enabled>', b, count=1)

i2 = b.find("<secretion>")
j2 = b.find("</secretion>") + len("</secretion>")
new_secretion = (
    "<secretion>\n"
    '                    <substrate name="oxygen">\n'
    '                        <secretion_rate units="1/min">200</secretion_rate>\n'
    '                        <secretion_target units="substrate density">38</secretion_target>\n'
    '                        <uptake_rate units="1/min">0</uptake_rate>\n'
    '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
    "                    </substrate>\n"
    "                </secretion>"
)
b = b[:i2] + new_secretion + b[j2:]

for tag in ["cell_adhesion_affinities", "live_phagocytosis_rates", "attack_rates", "fusion_rates", "transformation_rates"]:
    ii = b.find(f"<{tag}>")
    jj = b.find(f"</{tag}>") + len(f"</{tag}>")
    b = b[:ii] + f"<{tag}>\n                    </{tag}>" + b[jj:]

anchor = "</cell_definitions>"
assert xml.count(anchor) == 1
xml = xml.replace(anchor, b + "\n" + anchor, 1)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("oxygen Dirichlet boundary disabled; fixed_vessel_source cell type added (ID=17)")
