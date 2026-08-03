# -*- coding: utf-8 -*-
"""
Adds Bifidobacterium longum + a 2-stage xenophagy mechanism, matching
Li, Liu, Zhu et al. 2026 Cell Host & Microbe as closely as practical
without full PK/PD modeling. Confirmed design with the user:
  - CD8's existing killing mechanism is completely untouched.
  - CD4 only gets attack capability against tumor cells that have
    reached the "xenophagy_active" (neoantigen-presenting) stage --
    not a general CD4 attack rate.
  - Colonization alone is NOT sufficient (matches the paper's own
    finding that anti-tumor effect required rapamycin-induced
    xenophagy, not spontaneous bacterial degradation) -- represented
    as a genuine 2-stage pipeline, not collapsed into one step.

Implemented entirely via native PhysiCell mechanics (transformation_
rates + Rules "transform to X", the same pattern already used for CD8
checkpoint-state dynamics in the parent hybrid project's step 6) --
NO custom.cpp logic needed, consistent with this project's established
"biology lives in XML/Rules" design.

Pipeline:
  PD-L1lo/hi_tumor
    --[contact with Bifidobacterium_longum]-->
  PD-L1lo/hi_tumor_infected  (bacterium inside, NOT yet presenting --
    CD4 attack_rate = 0, matching "colonization alone insufficient")
    --[rapamycin substrate increases the rate]-->
  PD-L1lo/hi_tumor_xenophagy  (neoantigens presented via degraded
    bacteria -- CD4 attack_rate > 0 ONLY for this type)

New "rapamycin" substrate: inert placeholder (initial_condition=0,
Dirichlet disabled), same pattern as step 1's other new fields --
default is the paper's "no-drug" condition, matching the finding that
colonization alone doesn't work. Raising its initial_condition/boundary
later is how a future "give rapamycin" experiment would be run,
without touching any code.

Bifidobacterium_longum itself: cloned from macrophage's template (same
schema convenience), then customized:
  - small volume (100 vs the project's uniform 2494 um^3 default) --
    real bacteria are orders of magnitude smaller than mammalian cells,
    flagged as a scale simplification, not claimed as calibrated
  - literature is explicit that B. longum has no flagella / is
    generally non-motile (relies on passive/blood-flow translocation,
    not active swimming) -- given a low residual speed (0.3 um/min)
    representing passive drift/Brownian-like movement, not directed
    swimming
  - negative oxygen chemotaxis (selectively colonizes hypoxic tumor
    regions -- Orally Administered Bifidobacteria as Vehicles paper,
    PMC2911250)
  - division rate gated by glucose (carbohydrate-dependent growth rate,
    PMC10059941), same starved-floor pattern as the tumor's own growth
    formula; exact baseline rate has no precise literature value found
    for this specific context, flagged C-level/order-of-magnitude only
  - can be phagocytosed by macrophage (PMC5412050, capsule-dependent,
    not modeled here -- flat baseline rate)
"""
import re

XML = "config/PhysiCell_settings.xml"
RULES = "config/cell_rules.csv"

with open(XML, encoding="utf-8") as f:
    xml = f.read()

# --- 1. new "rapamycin" substrate field (inert by default) ---
anchor = "</microenvironment_setup>"
assert xml.count(anchor) == 1
rapamycin_block = '''        <variable name="rapamycin" units="dimensionless" ID="99">
            <physical_parameter_set>
                <diffusion_coefficient units="micron^2/min">100000</diffusion_coefficient>
                <decay_rate units="1/min">0.01</decay_rate>
            </physical_parameter_set>
            <initial_condition units="dimensionless">0</initial_condition>
            <Dirichlet_boundary_condition units="dimensionless" enabled="False">0</Dirichlet_boundary_condition>
            <Dirichlet_options>
                <boundary_value ID="xmin" enabled="False">0</boundary_value>
                <boundary_value ID="xmax" enabled="False">0</boundary_value>
                <boundary_value ID="ymin" enabled="False">0</boundary_value>
                <boundary_value ID="ymax" enabled="False">0</boundary_value>
                <boundary_value ID="zmin" enabled="False">0</boundary_value>
                <boundary_value ID="zmax" enabled="False">0</boundary_value>
            </Dirichlet_options>
        </variable>
'''
xml = xml.replace(anchor, rapamycin_block + anchor, 1)

# fix the placeholder ID=99 to the real next free substrate ID
existing_ids = [int(m) for m in re.findall(r'<variable name="[^"]+" units="[^"]+" ID="(\d+)"', xml) if int(m) != 99]
real_id = max(existing_ids) + 1
xml = xml.replace('name="rapamycin" units="dimensionless" ID="99"', f'name="rapamycin" units="dimensionless" ID="{real_id}"')
print(f"added 'rapamycin' substrate field, ID={real_id}")

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("step 1/4 done (substrate)")
