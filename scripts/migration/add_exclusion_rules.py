# -*- coding: utf-8 -*-
"""
Wires up the literature-grounded exclusion mechanism (Feig 2013 CAF-CXCL12
retention via CXCR4; Ene-Obong 2013 stellate-cell sequestration; Hartmann
2014 collagen/ECM contact-guidance as the PREVAILING trapping mechanism,
stronger than chemokines alone) onto the T cell types.

myCAF already deposits ECM and secretes CXCL12 (step 2), and ECM/CXCL12
both have decay_rate=0/very-low-diffusion so they build up sharply and
stay concentrated right where the CAFs are (0-320um, in/around the tumor)
-- this step only adds the RESPONSE side: ECM and CXCL12 each
independently suppress migration speed for every T cell type (4 CD8
subtypes, 2 CD4 subtypes, Treg), combined via PhysiCell's existing
multi-signal Rules mechanism, the same way "TGF_beta decreases migration
speed" already combines with "contact with tumor decreases migration
speed" for CD8. This does NOT touch attack rates or the existing
contact-based rules at all -- scope is deliberately limited to the
spatial/migration side of exclusion, matching what was actually asked.
"""
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

T_CELL_TYPES = [
    "PD-1hi_CD137lo_CD8_Tcell",
    "PD-1lo_CD137lo_CD8_Tcell",
    "PD-1hi_CD137hi_CD8_Tcell",
    "PD-1lo_CD137hi_CD8_Tcell",
    "PD-1hi_CD4_Tcell",
    "PD-1lo_CD4_Tcell",
    "Treg",
]

new_rules = []
for t in T_CELL_TYPES:
    new_rules.append(f"{t},ECM,decreases,migration speed,0,2,3,0")
    new_rules.append(f"{t},CXCL12,decreases,migration speed,0,2,2,0")

if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)

print(f"added {len(new_rules)} exclusion rules (ECM + CXCL12 -> migration speed) across {len(T_CELL_TYPES)} T cell types")
