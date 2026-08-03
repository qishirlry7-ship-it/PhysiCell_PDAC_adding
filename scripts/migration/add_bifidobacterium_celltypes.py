# -*- coding: utf-8 -*-
import re

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(xml, name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return start, end, xml[start:end]

def next_id(xml):
    ids = [int(m) for m in re.findall(r'<cell_definition name="[^"]+" ID="(\d+)"', xml)]
    return max(ids) + 1

def clear_named_lists(block):
    for tag in ["cell_adhesion_affinities", "live_phagocytosis_rates", "attack_rates", "fusion_rates", "transformation_rates"]:
        i = block.find(f"<{tag}>")
        j = block.find(f"</{tag}>") + len(f"</{tag}>")
        block = block[:i] + f"<{tag}>\n                    </{tag}>" + block[j:]
    return block

# ---------------------------------------------------------------------
# 1. Bifidobacterium_longum, cloned from macrophage's template
# ---------------------------------------------------------------------
s, e, template = get_block(xml, "macrophage")
own_id = re.search(r'ID="(\d+)"', template).group(1)
nid = next_id(xml)
b = template.replace(f'name="macrophage" ID="{own_id}"', f'name="Bifidobacterium_longum" ID="{nid}"')

# small volume: real bacteria are much smaller than the project's
# uniform 2494 um^3 mammalian-cell default -- scale simplification
b = b.replace('<total units="micron^3">2494</total>', '<total units="micron^3">100</total>')

# apoptosis baseline: modest finite lifespan (order-of-magnitude only,
# no precise literature value found for tumor-microenvironment survival)
b = re.sub(r'(<model code="100" name="apoptosis">\s*<death_rate units="1/min">)0(</death_rate>)', r'\g<1>0.001\g<2>', b, count=1)

# cycle: starts non-dividing baseline like everything else in this
# project; glucose-gated growth added via Rules below (same pattern as
# the tumor's own growth formula) -- baseline set to a starved floor
b = re.sub(
    r'<rate start_index="0" end_index="0" fixed_duration="false">0</rate>',
    '<rate start_index="0" end_index="0" fixed_duration="false">1e-4</rate>',
    b, count=1
)

# motility: non-motile in reality (no flagella, relies on passive/
# blood-flow translocation) -- low residual speed for passive drift,
# not directed swimming; negative oxygen chemotaxis (selectively
# colonizes hypoxic tumor regions)
b = b.replace('<speed units="micron/min">1</speed>', '<speed units="micron/min">0.3</speed>')
b = b.replace('<substrate>debris</substrate>', '<substrate>oxygen</substrate>')
b = re.sub(r'(<substrate>oxygen</substrate>\s*<direction>)1(</direction>)', r'\g<1>-1\g<2>', b, count=1)

# secretion: strip macrophage's own (oxygen uptake, TGF_beta secretion)
# down to just a minimal oxygen uptake entry
i = b.find("<secretion>")
j = b.find("</secretion>") + len("</secretion>")
b = b[:i] + (
    "<secretion>\n"
    '                    <substrate name="oxygen">\n'
    '                        <secretion_rate units="1/min">0</secretion_rate>\n'
    '                        <secretion_target units="substrate density">1</secretion_target>\n'
    '                        <uptake_rate units="1/min">1</uptake_rate>\n'
    '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
    "                    </substrate>\n"
    "                </secretion>"
) + b[j:]

b = clear_named_lists(b)

xml = xml.replace(f'</cell_definitions>', b + '\n</cell_definitions>', 1)
print(f"added Bifidobacterium_longum (ID={nid})")

# ---------------------------------------------------------------------
# 2/3. tumor _infected and _xenophagy variants, cloned verbatim from
#      the two original tumor types (identical growth/death/mechanics),
#      renamed only
# ---------------------------------------------------------------------
new_type_names = {}
for base in ["PD-L1lo_tumor", "PD-L1hi_tumor"]:
    for suffix in ["_infected", "_xenophagy"]:
        s, e, template = get_block(xml, base)
        own_id = re.search(r'ID="(\d+)"', template).group(1)
        nid = next_id(xml)
        new_name = base + suffix
        b = template.replace(f'name="{base}" ID="{own_id}"', f'name="{new_name}" ID="{nid}"')
        b = clear_named_lists(b)
        xml = xml.replace('</cell_definitions>', b + '\n</cell_definitions>', 1)
        new_type_names[new_name] = nid
        print(f"added {new_name} (ID={nid})")

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("step 2/4 done (cell types)")
