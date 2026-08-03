# -*- coding: utf-8 -*-
XML = "config/PhysiCell_settings.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()
old = '<variable name="rapamycin" units="dimensionless" ID="15">\n            <physical_parameter_set>\n                <diffusion_coefficient units="micron^2/min">100000</diffusion_coefficient>\n                <decay_rate units="1/min">0.01</decay_rate>\n            </physical_parameter_set>\n            <initial_condition units="dimensionless">0</initial_condition>'
new = old.replace('<initial_condition units="dimensionless">0</initial_condition>', '<initial_condition units="dimensionless">5</initial_condition>')
assert xml.count(old) == 1
xml = xml.replace(old, new)
with open(XML, "w", encoding="utf-8") as f:
    f.write(xml)
print("rapamycin initial_condition set to 5 (test only)")
