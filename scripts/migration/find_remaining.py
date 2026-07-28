# -*- coding: utf-8 -*-
with open("config/PhysiCell_settings.xml", encoding="utf-8") as f:
    xml = f.read()

before_pro = xml.count("pro-inflammatory factor")
before_anti = xml.count("anti-inflammatory factor")

xml = xml.replace('<substrate name="pro-inflammatory factor">', '<substrate name="IFN_gamma">')
xml = xml.replace('<substrate name="anti-inflammatory factor">', '<substrate name="TGF_beta">')

after_pro = xml.count("pro-inflammatory factor")
after_anti = xml.count("anti-inflammatory factor")
print(f"pro-inflammatory: {before_pro} -> {after_pro}")
print(f"anti-inflammatory: {before_anti} -> {after_anti}")

with open("config/PhysiCell_settings.xml", "w", encoding="utf-8") as f:
    f.write(xml)
