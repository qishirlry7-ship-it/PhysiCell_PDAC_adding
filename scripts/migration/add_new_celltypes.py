# -*- coding: utf-8 -*-
"""
Adds 8 new, self-contained cell_definitions to config/PhysiCell_settings.xml,
cloned from the macrophage block (same schema: cycle/death/volume/mechanics/
motility/secretion/cell_interactions/cell_transformations/cell_integrity).

Scope discipline: these new types only get rules about THEIR OWN behavior
(their own motility/chemotaxis/secretion). None of pdac_therapy's original
9 cell types are touched, and none of the new types get attack/suppression
rules against the old types yet -- that (ECM+CXCL12 exclusion recalibration)
is a separate, later, explicitly-reviewed step.
"""
import re

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return xml[start:end]

template = get_block("macrophage")

# sanity: template must contain exactly what we expect to replace
assert template.count('ID="2"') == 1
assert 'name="macrophage"' in template

NEW_TYPES = [
    # name, ID, adhesion, repulsion, speed, bias, persistence, apoptosis_rate,
    # chemotaxis_substrate, chemotaxis_direction,
    # secretions: list of (substrate, rate, target)
    dict(name="myCAF", ID=9, adhesion=0.4, repulsion=10, speed=0.2, bias=0.3,
         persistence=60, apoptosis=0,
         chemo_substrate="TGF_beta", chemo_dir=1,
         secretions=[("ECM", 1, 10), ("CXCL12", 1, 10)]),
    dict(name="iCAF", ID=10, adhesion=0.2, repulsion=10, speed=0.3, bias=0.3,
         persistence=60, apoptosis=0,
         chemo_substrate="debris", chemo_dir=1,
         secretions=[("IL6", 1, 10), ("CCL2", 1, 10)]),
    dict(name="Treg", ID=11, adhesion=0, repulsion=10, speed=1, bias=0.5,
         persistence=5, apoptosis=0,
         chemo_substrate="IFN_gamma", chemo_dir=1,
         secretions=[("TGF_beta", 1, 10), ("IL10", 1, 10)]),
    dict(name="M_MDSC", ID=12, adhesion=0, repulsion=10, speed=1, bias=0.5,
         persistence=5, apoptosis=0,
         chemo_substrate="CCL2", chemo_dir=1,
         secretions=[("IL10", 1, 10)]),
    dict(name="PMN_MDSC", ID=13, adhesion=0, repulsion=10, speed=1, bias=0.5,
         persistence=5, apoptosis=0,
         chemo_substrate="CXCL1_2_5_8", chemo_dir=1,
         secretions=[("IL10", 0.5, 10)]),
    dict(name="cDC1", ID=14, adhesion=0, repulsion=10, speed=1, bias=0.25,
         persistence=5, apoptosis=0,
         chemo_substrate="debris", chemo_dir=1,
         secretions=[("IFN_gamma", 0.2, 10)]),
    dict(name="B_cell", ID=15, adhesion=0, repulsion=10, speed=1, bias=0.25,
         persistence=5, apoptosis=0,
         chemo_substrate="CXCL13", chemo_dir=1,
         secretions=[]),
    dict(name="NK_cell", ID=16, adhesion=0, repulsion=10, speed=1, bias=0.5,
         persistence=5, apoptosis=0,
         chemo_substrate="CXCL9_10", chemo_dir=1,
         secretions=[("IFN_gamma", 0.5, 10)]),
]

def build_secretion_block(secretions):
    subs = []
    for name, rate, target in secretions:
        subs.append(f'''                    <substrate name="{name}">
                        <secretion_rate units="1/min">{rate}</secretion_rate>
                        <secretion_target units="substrate density">{target}</secretion_target>
                        <uptake_rate units="1/min">0</uptake_rate>
                        <net_export_rate units="total substrate/min">0.0</net_export_rate>
                    </substrate>
''')
    return "".join(subs)

new_blocks = []
for spec in NEW_TYPES:
    b = template
    b = b.replace('name="macrophage" ID="2"', f'name="{spec["name"]}" ID="{spec["ID"]}"')
    # apoptosis rate (first occurrence only -- the necrosis model's own
    # death_rate stays 0 as in the template)
    b = b.replace(
        '<death_rate units="1/min">0</death_rate>',
        f'<death_rate units="1/min">{spec["apoptosis"]}</death_rate>',
        1
    )
    # mechanics
    b = b.replace(
        '<cell_cell_adhesion_strength units="micron/min">0</cell_cell_adhesion_strength>',
        f'<cell_cell_adhesion_strength units="micron/min">{spec["adhesion"]}</cell_cell_adhesion_strength>'
    )
    b = b.replace(
        '<cell_cell_repulsion_strength units="micron/min">10.0</cell_cell_repulsion_strength>',
        f'<cell_cell_repulsion_strength units="micron/min">{spec["repulsion"]}</cell_cell_repulsion_strength>'
    )
    # motility
    b = b.replace('<speed units="micron/min">1</speed>', f'<speed units="micron/min">{spec["speed"]}</speed>')
    b = b.replace('<persistence_time units="min">5</persistence_time>', f'<persistence_time units="min">{spec["persistence"]}</persistence_time>')
    b = b.replace('<migration_bias units="dimensionless">0.25</migration_bias>', f'<migration_bias units="dimensionless">{spec["bias"]}</migration_bias>')
    b = b.replace('<substrate>debris</substrate>', f'<substrate>{spec["chemo_substrate"]}</substrate>')
    b = b.replace('<direction>1</direction>', f'<direction>{spec["chemo_dir"]}</direction>', 1)

    # strip out the old macrophage-specific secretion block (oxygen/debris/
    # IFN_gamma/TGF_beta with macrophage's own rates) and replace with a
    # minimal oxygen+debris zero block plus this type's own secretions
    i = b.find("<secretion>")
    j = b.find("</secretion>") + len("</secretion>")
    new_secretion = (
        "<secretion>\n"
        '                    <substrate name="oxygen">\n'
        '                        <secretion_rate units="1/min">0</secretion_rate>\n'
        '                        <secretion_target units="substrate density">1</secretion_target>\n'
        '                        <uptake_rate units="1/min">10</uptake_rate>\n'
        '                        <net_export_rate units="total substrate/min">0</net_export_rate>\n'
        "                    </substrate>\n"
        + build_secretion_block(spec["secretions"]) +
        "                </secretion>"
    )
    b = b[:i] + new_secretion + b[j:]

    # strip the named affinity/attack/phagocytosis/fusion/transformation
    # lists down to empty (no cross-effects on old types in this step;
    # PhysiCell defaults affinity->1.0, attack/phago/fusion/transform->0
    # for any unlisted type)
    for tag in ["cell_adhesion_affinities", "live_phagocytosis_rates", "attack_rates", "fusion_rates", "transformation_rates"]:
        i = b.find(f"<{tag}>")
        j = b.find(f"</{tag}>") + len(f"</{tag}>")
        b = b[:i] + f"<{tag}>\n                    </{tag}>" + b[j:]

    new_blocks.append(b)

anchor = "</cell_definitions>"
assert xml.count(anchor) == 1
xml = xml.replace(anchor, "\n".join(new_blocks) + "\n" + anchor, 1)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("added", len(NEW_TYPES), "new cell definitions")
