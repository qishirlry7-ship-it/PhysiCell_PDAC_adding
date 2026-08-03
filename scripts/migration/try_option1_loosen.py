# -*- coding: utf-8 -*-
# Option 1: loosen half_max so more cells reach a meaningful rate
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()
repl = [
    ("PD-L1lo_tumor,oxygen,increases,cycle entry,7.2e-4,5,2,0", "PD-L1lo_tumor,oxygen,increases,cycle entry,7.2e-4,3,2,0"),
    ("PD-L1hi_tumor,oxygen,increases,cycle entry,7.2e-4,5,2,0", "PD-L1hi_tumor,oxygen,increases,cycle entry,7.2e-4,3,2,0"),
    ("PD-L1lo_tumor,glucose,increases,cycle entry,7.2e-4,0.3,2,0", "PD-L1lo_tumor,glucose,increases,cycle entry,7.2e-4,0.15,2,0"),
    ("PD-L1hi_tumor,glucose,increases,cycle entry,7.2e-4,0.3,2,0", "PD-L1hi_tumor,glucose,increases,cycle entry,7.2e-4,0.15,2,0"),
]
for old, new in repl:
    assert content.count(old) == 1, old
    content = content.replace(old, new)
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print("applied option 1 (loosened half_max: oxygen 5->3, glucose 0.3->0.15)")
