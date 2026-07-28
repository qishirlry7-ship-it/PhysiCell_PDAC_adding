# -*- coding: utf-8 -*-
"""
The first pass (necrosis_rate baseline 0.02/min, oxygen half_max=3
hill_power=8 copied directly from PhysiCell_PDAC_TME) turned out much
too aggressive here: total agents dropped from 1719 to 957 (-44%) within
just 2400 of 21600 simulated minutes. That number was borrowed from a
different project with oxygen decay_rate=0 (infinite-range diffusion);
this project's oxygen decay_rate=0.1/min gives a much shorter, ~1000um
diffusion length and a genuinely lower ambient oxygen floor (~2.8-20.7
here vs designed for a different regime there), so half_max=3 with an
extremely steep hill_power=8 was putting much of the tumor core's
*normal* operating range inside the steep part of the necrosis curve,
not just genuinely extreme hypoxia. Softening based on the actually-
observed field range (oxygen min~2.8, mean~6.6; glucose min~0.29,
mean~0.62) rather than re-copying the other project's numbers blind.
"""
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

replacements = [
    ("PD-L1lo_tumor,oxygen,decreases,necrosis,0,3,8,0", "PD-L1lo_tumor,oxygen,decreases,necrosis,0,2,4,0"),
    ("PD-L1hi_tumor,oxygen,decreases,necrosis,0,3,8,0", "PD-L1hi_tumor,oxygen,decreases,necrosis,0,2,4,0"),
    ("PD-L1lo_tumor,glucose,decreases,necrosis,0,0.1,4,0", "PD-L1lo_tumor,glucose,decreases,necrosis,0,0.05,3,0"),
    ("PD-L1hi_tumor,glucose,decreases,necrosis,0,0.1,4,0", "PD-L1hi_tumor,glucose,decreases,necrosis,0,0.05,3,0"),
]
for old, new in replacements:
    assert content.count(old) == 1, old
    content = content.replace(old, new)
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()
old_count = xml.count('<death_rate units="1/min">0.02</death_rate>')
xml = xml.replace('<death_rate units="1/min">0.02</death_rate>', '<death_rate units="1/min">0.005</death_rate>')
with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)

print(f"softened necrosis rules; replaced {old_count} necrosis baseline(s) 0.02 -> 0.005")
