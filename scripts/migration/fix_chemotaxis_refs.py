# -*- coding: utf-8 -*-
XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

replacements = [
    ("<substrate>pro-inflammatory factor</substrate>", "<substrate>IFN_gamma</substrate>"),
    ("<substrate>anti-inflammatory factor</substrate>", "<substrate>TGF_beta</substrate>"),
    ('chemotactic_sensitivity substrate="pro-inflammatory factor"', 'chemotactic_sensitivity substrate="IFN_gamma"'),
    ('chemotactic_sensitivity substrate="anti-inflammatory factor"', 'chemotactic_sensitivity substrate="TGF_beta"'),
]
for old, new in replacements:
    n = xml.count(old)
    xml = xml.replace(old, new)
    print(f"{old!r}: {n} occurrences replaced")

# also check for any remaining stray references anywhere else
remaining_pro = xml.count("pro-inflammatory factor")
remaining_anti = xml.count("anti-inflammatory factor")
print("remaining 'pro-inflammatory factor' occurrences:", remaining_pro)
print("remaining 'anti-inflammatory factor' occurrences:", remaining_anti)

with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
