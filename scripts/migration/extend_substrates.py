# -*- coding: utf-8 -*-
import re

XML = "config/PhysiCell_settings.xml"
RULES = "config/cell_rules.csv"

with open(XML, encoding="utf-8") as f:
    xml = f.read()

# --- 1:1 rename, behavior-preserving (no numeric changes) ---
assert xml.count('variable name="pro-inflammatory factor"') == 1
assert xml.count('variable name="anti-inflammatory factor"') == 1
xml = xml.replace('variable name="pro-inflammatory factor"', 'variable name="IFN_gamma"')
xml = xml.replace('variable name="anti-inflammatory factor"', 'variable name="TGF_beta"')

with open(RULES, encoding="utf-8") as f:
    rules = f.read()
n1 = rules.count("pro-inflammatory factor")
n2 = rules.count("anti-inflammatory factor")
rules = rules.replace("pro-inflammatory factor", "IFN_gamma")
rules = rules.replace("anti-inflammatory factor", "TGF_beta")
with open(RULES, "w", encoding="utf-8") as f:
    f.write(rules)
print(f"renamed {n1} pro-inflammatory + {n2} anti-inflammatory occurrences in cell_rules.csv")

# --- new inert substrate fields for future new cell types (reusing the
#     same diffusion/decay/initial values already justified in our own
#     PhysiCell_PDAC_TME parameter_mapping.csv, C-level, to be recalibrated
#     once the cells that actually use them are added) ---
new_vars = [
    # name, units, diffusion, decay, init
    ("IL10",          "dimensionless", 6000, 0.015, 0.0),
    ("IL6",           "dimensionless", 7000, 0.01,  0.0),
    ("CCL2",          "dimensionless", 8000, 0.02,  0.0),
    ("CXCL9_10",      "dimensionless", 8000, 0.02,  0.0),
    ("CXCL12",        "dimensionless", 5000, 0.005, 0.0),
    ("CXCL1_2_5_8",   "dimensionless", 8000, 0.02,  0.0),
    ("CCL22",         "dimensionless", 7000, 0.02,  0.0),
    ("CXCL13",        "dimensionless", 7000, 0.01,  0.0),
    ("ECM",           "dimensionless", 1e-5, 0.0,   0.0),
    ("glucose",       "mM",            15000, 0.0,  1.0),
    ("lactate",       "mM",            60000, 0.003, 0.0),
]

# find the ID of the last existing <variable> to continue numbering
existing_ids = [int(m) for m in re.findall(r'<variable name="[^"]+" units="[^"]+" ID="(\d+)"', xml)]
next_id = max(existing_ids) + 1

blocks = []
for name, units, D, decay, init in new_vars:
    block = f'''        <variable name="{name}" units="{units}" ID="{next_id}">
            <physical_parameter_set>
                <diffusion_coefficient units="micron^2/min">{D}</diffusion_coefficient>
                <decay_rate units="1/min">{decay}</decay_rate>
            </physical_parameter_set>
            <initial_condition units="{units}">{init}</initial_condition>
            <Dirichlet_boundary_condition units="{units}" enabled="False">{init}</Dirichlet_boundary_condition>
            <Dirichlet_options>
                <boundary_value ID="xmin" enabled="False">{init}</boundary_value>
                <boundary_value ID="xmax" enabled="False">{init}</boundary_value>
                <boundary_value ID="ymin" enabled="False">{init}</boundary_value>
                <boundary_value ID="ymax" enabled="False">{init}</boundary_value>
                <boundary_value ID="zmin" enabled="False">{init}</boundary_value>
                <boundary_value ID="zmax" enabled="False">{init}</boundary_value>
            </Dirichlet_options>
        </variable>
'''
    blocks.append(block)
    next_id += 1

# insert right after the last existing </variable> close, before </microenvironment_setup>
anchor = "</microenvironment_setup>"
assert xml.count(anchor) == 1
xml = xml.replace(anchor, "".join(blocks) + anchor, 1)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print("added", len(new_vars), "new substrate fields, next free ID would be", next_id)
