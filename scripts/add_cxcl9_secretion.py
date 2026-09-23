#!/usr/bin/env python3
"""Register a CXCL9_10 secretion block on the cell types that now secrete it.

WHY: PhysiCell only applies a Rules-driven `CXCL9_10 secretion` behaviour if
that substrate is present in the cell's own <secretion> list -- the rule writes
into phenotype.secretion.secretion_rates[idx] / saturation_densities[idx], and
those arrays are built from the <substrate name=...> entries actually declared
under the definition. Neither PD-L1lo_tumor nor PD-L1hi_tumor nor macrophage
declared one, so the rules added to cell_rules.csv would have been silently
ignored.

`secretion_target` matters here: the source term is rate * (target - c), so a
target of 0 would let the cell only ever take CXCL9_10 UP, never release it.
We set a moderate target so the field stays spatially graded instead of
saturating everywhere.

Idempotent: types that already have a CXCL9_10 block are left alone.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "config" / "PhysiCell_settings.xml"
t = p.read_text(encoding="utf-8")

TARGETS = ["PD-L1lo_tumor", "PD-L1hi_tumor", "macrophage"]

BLOCK = """                    <substrate name="CXCL9_10">
                        <secretion_rate units="1/min">0</secretion_rate>
                        <secretion_target units="substrate density">10</secretion_target>
                        <uptake_rate units="1/min">0</uptake_rate>
                        <net_export_rate units="total substrate/min">0</net_export_rate>
                    </substrate>
"""

# anchor: the closing of the TGF_beta substrate block, which every one of these
# definitions has, immediately inside <secretion>
ANCHOR = """                    <substrate name="TGF_beta">
                        <secretion_rate units="1/min">{RATE}</secretion_rate>
                        <secretion_target units="substrate density">{TGT}</secretion_target>
                        <uptake_rate units="1/min">{UP}</uptake_rate>
                        <net_export_rate units="total substrate/min">{EXP}</net_export_rate>
                    </substrate>
"""


def find_anchor(blk):
    m = re.search(
        r'(<substrate name="TGF_beta">\s*'
        r'<secretion_rate[^>]*>[^<]*</secretion_rate>\s*'
        r'<secretion_target[^>]*>[^<]*</secretion_target>\s*'
        r'<uptake_rate[^>]*>[^<]*</uptake_rate>\s*'
        r'<net_export_rate[^>]*>[^<]*</net_export_rate>\s*'
        r'</substrate>\s*)', blk)
    return m


changed = []
for name in TARGETS:
    i = t.index('<cell_definition name="%s"' % name)
    j = t.find("<cell_definition name=", i + 10)
    if j < 0:
        j = len(t)
    blk = t[i:j]
    if '<substrate name="CXCL9_10"' in blk:
        print("%-16s already has CXCL9_10, skipped" % name)
        continue
    m = find_anchor(blk)
    if not m:
        raise SystemExit("%s: could not locate the TGF_beta secretion anchor" % name)
    new_blk = blk[:m.end(1)] + BLOCK + blk[m.end(1):]
    t = t[:i] + new_blk + t[j:]
    changed.append(name)
    print("%-16s CXCL9_10 secretion block added" % name)

if changed:
    p.write_text(t, encoding="utf-8", newline="\n")
    print("\nwrote %s (%d definition(s) updated)" % (p, len(changed)))
else:
    print("\nnothing to do")
