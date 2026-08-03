# -*- coding: utf-8 -*-
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

new_rules = [
    # Bifidobacterium's own glucose-gated growth (same starved-floor
    # pattern as the tumor's own growth formula, step 1 of this folder)
    "Bifidobacterium_longum,glucose,increases,cycle entry,0.003,0.15,2,0",

    # colonization: tumor cell transforms to _infected on contact with
    # a live bacterium (this alone is NOT sufficient for CD4 attack --
    # matches the paper's finding that colonization without induced
    # xenophagy has no anti-tumor effect)
    "PD-L1lo_tumor,contact with Bifidobacterium_longum,increases,transform to PD-L1lo_tumor_infected,0.002,0.1,2,0",
    "PD-L1hi_tumor,contact with Bifidobacterium_longum,increases,transform to PD-L1hi_tumor_infected,0.002,0.1,2,0",

    # xenophagy induction: infected -> xenophagy-active (presenting
    # neoantigens, now attackable by CD4) is driven by the rapamycin
    # substrate on top of the small constant baseline already set in
    # transformation_rates -- default rapamycin=0 everywhere, so this
    # stage barely progresses until/unless rapamycin is administered
    # (raising its initial_condition/boundary), matching the paper
    "PD-L1lo_tumor_infected,rapamycin,increases,transform to PD-L1lo_tumor_xenophagy,0.001,0.3,2,0",
    "PD-L1hi_tumor_infected,rapamycin,increases,transform to PD-L1hi_tumor_xenophagy,0.001,0.3,2,0",

    # bacterium is consumed/depleted after successfully delivering
    # itself into a tumor cell (simplification for "spent" bacteria,
    # rather than persisting indefinitely near an already-infected cell)
    "Bifidobacterium_longum,contact with PD-L1lo_tumor_infected,increases,apoptosis,0.01,0.1,2,0",
    "Bifidobacterium_longum,contact with PD-L1hi_tumor_infected,increases,apoptosis,0.01,0.1,2,0",
]
if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print(f"added {len(new_rules)} Bifidobacterium/xenophagy rules")
