# -*- coding: utf-8 -*-
# revert option 2's floor change back to the original 3.6e-5, keep option 1's
# loosened half_max (the empirically-chosen final combination)
XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()
old_count = xml.count('<rate start_index="0" end_index="0" fixed_duration="false">1e-4</rate>')
assert old_count == 2, old_count
xml = xml.replace(
    '<rate start_index="0" end_index="0" fixed_duration="false">1e-4</rate>',
    '<rate start_index="0" end_index="0" fixed_duration="false">3.6e-5</rate>'
)
with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

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
print("finalized on option 1: floor=3.6e-5, oxygen half_max=3, glucose half_max=0.15")
