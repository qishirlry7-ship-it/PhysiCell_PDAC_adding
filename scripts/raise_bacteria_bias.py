#!/usr/bin/env python3
"""Raise migration_bias for both Bifidobacterium types from 0.25 to 0.7.

Both bacterium cell_definitions have byte-identical <motility> blocks, so a
global text replace cannot tell them apart. This script locates each
definition by name and edits only inside its own range.

Rationale for 0.7 (also written into the XML as a comment):
  Tracking SVG snapshots showed only 2 of 5 measurable bacterium tracks moved
  closer to the tumour; median change in distance-to-tumour was +138 micron --
  they were drifting AWAY. The chemotaxis direction was already correct
  (oxygen, -1 = toward hypoxia); at bias 0.25 three quarters of every
  persistence interval was a random walk, which swamped the directional term.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "config" / "PhysiCell_settings.xml"
t = p.read_text(encoding="utf-8")

OLD_BIAS = '<migration_bias units="dimensionless">0.25</migration_bias>'
NEW_BIAS = ('<!-- RAISED from 0.25 to 0.7. Tracking the SVG snapshots showed\n'
            '                         only 2 of 5 measurable bacterium tracks moved closer to\n'
            '                         the tumour (median change in distance-to-tumour +138 micron,\n'
            '                         i.e. drifting AWAY). The chemotaxis direction was already\n'
            '                         correct (oxygen, -1 = toward hypoxia); at bias 0.25 three\n'
            '                         quarters of every persistence interval was a random walk,\n'
            '                         which swamped the directional term. B. longum is a motile\n'
            '                         obligate anaerobe whose value as a tumour vector rests on it\n'
            '                         actively seeking hypoxic tissue, so a dominant directional\n'
            '                         component is the intended behaviour. -->\n'
            '                    <migration_bias units="dimensionless">0.7</migration_bias>')

TYPES = ["Bifidobacterium_longum", "Bifidobacterium_longum_Gal8"]
changed = 0
out = t
for name in TYPES:
    i = out.index('<cell_definition name="%s"' % name)
    j = out.find("<cell_definition name=", i + 10)
    if j < 0:
        j = len(out)
    blk = out[i:j]
    n = blk.count(OLD_BIAS)
    if n != 1:
        raise SystemExit("%s: expected 1 occurrence of the 0.25 bias, found %d" % (name, n))
    blk2 = blk.replace(OLD_BIAS, NEW_BIAS, 1)
    out = out[:i] + blk2 + out[j:]
    changed += 1
    print("%s: migration_bias 0.25 -> 0.7" % name)

if changed != 2:
    raise SystemExit("expected to change 2 definitions, changed %d" % changed)

p.write_text(out, encoding="utf-8", newline="\n")
print("wrote %s" % p)
