# -*- coding: utf-8 -*-
"""
1. Slow Bifidobacterium_longum's division ceiling: 0.003/min (~3.85h
   doubling, too fast -- was competing successfully against 600+ tumor
   cells for the same glucose in the first test) -> 4.8e-4/min (~24h
   doubling under best-case glucose, ln2/1440). Still a C-level
   estimate (no precise literature doubling time found for this
   context), but chosen to be slow enough for chronic colonization
   rather than out-growing the tumor.
2. Add NK_cell direct antibacterial cytotoxicity against
   Bifidobacterium_longum -- real, well-documented mechanism (NK cells
   kill extracellular bacteria via contact-dependent granzyme B/H
   release, PMC8903247 / PLOS Pathogens 2022). PMN_MDSC deliberately
   NOT given this -- MDSCs are specifically immunosuppressed/
   dysfunctional neutrophil-lineage cells (that dysfunction is their
   defining feature), so giving them robust bactericidal function would
   contradict their own biology, even though healthy neutrophils are
   the primary real-world bacterial phagocyte.
"""
RULES = "config/cell_rules.csv"
with open(RULES, encoding="utf-8") as f:
    content = f.read()

old = "Bifidobacterium_longum,glucose,increases,cycle entry,0.003,0.15,2,0"
new = "Bifidobacterium_longum,glucose,increases,cycle entry,4.8e-4,0.15,2,0"
assert content.count(old) == 1
content = content.replace(old, new)
with open(RULES, "w", encoding="utf-8") as f:
    f.write(content)
print("slowed Bifidobacterium division ceiling: 0.003 -> 4.8e-4/min")

XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

def get_block(xml, name):
    start = xml.find(f'<cell_definition name="{name}"')
    end = xml.find('</cell_definition>', start) + len('</cell_definition>')
    return start, end, xml[start:end]

def add_entries(xml, cell_name, tag, entries):
    s, e, block = get_block(xml, cell_name)
    anchor = f"</{tag}>"
    i = block.find(anchor)
    new_text = "".join(
        f'                        <attack_rate name="{name}" units="1/min">{rate}</attack_rate>\n'
        for name, rate in entries
    )
    block = block[:i] + new_text + block[i:]
    return xml[:s] + block + xml[e:]

xml = add_entries(xml, "NK_cell", "attack_rates", [("Bifidobacterium_longum", 0.05)])

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print("added NK_cell attack_rate against Bifidobacterium_longum (0.05/min)")
