# -*- coding: utf-8 -*-
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

new_rules = [
    "myCAF,TGF_beta,increases,ECM secretion,2,1,2,0",
]

if not content.endswith("\n"):
    content += "\n"
content += "\n".join(new_rules) + "\n"

with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)

print("added", len(new_rules), "new rule(s)")
