# -*- coding: utf-8 -*-
"""
Adds a second, compressed/dysfunctional vessel subtype inside the tumor
core, alongside the existing peripheral ring (step 3 of the earlier
hybrid project). Reflects the mixed PDAC vasculature literature already
shown to the user: some studies find HIGHER microvessel density inside
the tumor than in peritumoral stroma (Springer 2013, "High microvessel
density in PDAC is associated with high grade"), while others confirm
overall hypovascularity and pancreatic-stellate-cell-mediated vessel
compression specifically in the stroma (Sada et al., ScienceDirect
2016/PMC5123629). Resolution used here (approved in principle by the
user, "数量更少、更容易被压缩/失活...细节后续讨论"): intratumoral
vessels DO exist (few), but secrete less than the peripheral ring,
representing partial compression rather than being fully absent or
fully functional.

New cell type "fixed_vessel_source_compressed": same as
fixed_vessel_source in every respect except oxygen/glucose
secretion_rate reduced to 40% (200->80, 100->40) -- a placeholder
compression fraction, explicitly flagged as provisional/adjustable.
"""
XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

start = xml.find('<cell_definition name="fixed_vessel_source"')
end = xml.find('</cell_definition>', start) + len('</cell_definition>')
template = xml[start:end]

# find the next free ID
import re
ids = [int(m) for m in re.findall(r'<cell_definition name="[^"]+" ID="(\d+)"', xml)]
next_id = max(ids) + 1

own_id = re.search(r'<cell_definition name="fixed_vessel_source" ID="(\d+)"', template).group(1)
b = template.replace(
    f'name="fixed_vessel_source" ID="{own_id}"',
    f'name="fixed_vessel_source_compressed" ID="{next_id}"'
)
assert 'name="fixed_vessel_source_compressed"' in b

b = b.replace(
    '<secretion_rate units="1/min">200</secretion_rate>',
    '<secretion_rate units="1/min">80</secretion_rate>'
)
b = b.replace(
    '<secretion_rate units="1/min">100</secretion_rate>',
    '<secretion_rate units="1/min">40</secretion_rate>'
)

anchor = "</cell_definitions>"
assert xml.count(anchor) == 1
xml = xml.replace(anchor, b + "\n" + anchor, 1)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print(f"added fixed_vessel_source_compressed (ID={next_id}), secretion 40% of peripheral vessels")
