# -*- coding: utf-8 -*-
"""
Makes the 4 CD8 checkpoint subtypes dynamic instead of fixed-for-life,
using PhysiCell's native transformation_rates + Rules "transform to X"
mechanism (the same low-risk, custom.cpp-free approach already used for
CAF state switching in PhysiCell_PDAC_TME) -- NOT a parallel continuous-
state system, to stay maximally consistent with how pdac_therapy itself
represents checkpoint status (discrete cell types, not custom_data).

Only CD8 gets dynamic states. CD4's PD-1hi/lo split has zero effect on
any CD4 rule in pdac_therapy's own cell_rules.csv (checked: both CD4
subtypes have byte-identical rules) -- there is nothing for a CD4
transformation to meaningfully change yet, so it's skipped rather than
adding inert machinery. Not touched: Treg, or any non-T-cell type.

8 directed edges across the 2x2 PD-1 x CD137 grid (diagonal jumps are
not allowed -- only one axis changes per transition):
  PD1hi/CD137lo -> PD1lo/CD137lo : constant 0.0005/min (spontaneous de-exhaustion)
  PD1hi/CD137hi -> PD1lo/CD137hi : constant 0.0005/min
  PD1lo/CD137lo -> PD1hi/CD137lo : baseline 5e-5, + TGF_beta increases (chronic
                                    immunosuppressive exposure -> exhaustion onset;
                                    directly links back to step 5's CAF/ECM/TGF_beta
                                    barrier -- cells trapped near it get more exhausted)
  PD1lo/CD137hi -> PD1hi/CD137hi : baseline 5e-5, + TGF_beta increases
  PD1hi/CD137lo -> PD1hi/CD137hi : baseline 5e-5, + contact with cDC1 increases
                                    (costimulation gain from professional APC contact)
  PD1lo/CD137lo -> PD1lo/CD137hi : baseline 5e-5, + contact with cDC1 increases
  PD1hi/CD137hi -> PD1hi/CD137lo : constant 0.0001/min (costimulation waning)
  PD1lo/CD137hi -> PD1lo/CD137lo : constant 0.0001/min
"""
XML = "config/PhysiCell_settings.xml"
RULES = "config/cell_rules.csv"

with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return start, end, xml[start:end]

# (source_type, target_type, baseline_rate)
EDGES = [
    ("PD-1hi_CD137lo_CD8_Tcell", "PD-1lo_CD137lo_CD8_Tcell", 0.0005),
    ("PD-1hi_CD137hi_CD8_Tcell", "PD-1lo_CD137hi_CD8_Tcell", 0.0005),
    ("PD-1lo_CD137lo_CD8_Tcell", "PD-1hi_CD137lo_CD8_Tcell", 5e-5),
    ("PD-1lo_CD137hi_CD8_Tcell", "PD-1hi_CD137hi_CD8_Tcell", 5e-5),
    ("PD-1hi_CD137lo_CD8_Tcell", "PD-1hi_CD137hi_CD8_Tcell", 5e-5),
    ("PD-1lo_CD137lo_CD8_Tcell", "PD-1lo_CD137hi_CD8_Tcell", 5e-5),
    ("PD-1hi_CD137hi_CD8_Tcell", "PD-1hi_CD137lo_CD8_Tcell", 0.0001),
    ("PD-1lo_CD137hi_CD8_Tcell", "PD-1lo_CD137lo_CD8_Tcell", 0.0001),
]

by_source = {}
for src, tgt, rate in EDGES:
    by_source.setdefault(src, []).append((tgt, rate))

for src, targets in by_source.items():
    s, e, block = get_block(src)
    anchor = "</transformation_rates>"
    i = block.find(anchor)
    new_entries = "".join(
        f'                        <transformation_rate name="{tgt}" units="1/min">{rate}</transformation_rate>\n'
        for tgt, rate in targets
    )
    block = block[:i] + new_entries + block[i:]
    xml = xml[:s] + block + xml[e:]

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print(f"added transformation_rate entries for {sum(len(v) for v in by_source.values())} edges across {len(by_source)} CD8 subtypes")

# --- Rules: modulate the 4 signal-driven edges (the other 4 are constant,
#     no Rules needed) ---
with open(RULES, encoding="utf-8") as f:
    content = f.read()

new_rules = [
    "PD-1lo_CD137lo_CD8_Tcell,TGF_beta,increases,transform to PD-1hi_CD137lo_CD8_Tcell,0.002,2,2,0",
    "PD-1lo_CD137hi_CD8_Tcell,TGF_beta,increases,transform to PD-1hi_CD137hi_CD8_Tcell,0.002,2,2,0",
    "PD-1hi_CD137lo_CD8_Tcell,contact with cDC1,increases,transform to PD-1hi_CD137hi_CD8_Tcell,0.002,0.5,2,0",
    "PD-1lo_CD137lo_CD8_Tcell,contact with cDC1,increases,transform to PD-1lo_CD137hi_CD8_Tcell,0.002,0.5,2,0",
]
if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print(f"added {len(new_rules)} transformation-modulating rules")
