#!/usr/bin/env python3
"""Generate a short config for IFN-gamma diagnosis.

Adds frequent microenvironment saves so a short run still produces several
field snapshots, and shrinks max_time.

Usage:
    python scripts/make_ifn_diag_config.py [minutes] [out_dir]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 120
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "outputs" / "ifn_diag"
out_dir = out_dir if out_dir.is_absolute() else ROOT / out_dir

src = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")

# max_time
new, n = re.subn(r"(<max_time\b[^>]*>).*?(</max_time>)", r"\g<1>%d\g<2>" % minutes, src, count=1)
assert n == 1, "max_time not found"

# make the first <interval> (overall save interval) small so we get snapshots
new, n2 = re.subn(r"(<interval\b[^>]*>).*?(</interval>)", r"\g<1>%d\g<2>" % max(1, minutes // 4), new, count=1)

# ensure microenvironment is saved every interval (some models disable it)
if "<save_microenvironment>" in new:
    new = re.sub(r"(<save_microenvironment[^>]*>).*?(</save_microenvironment>)",
                 r"\g<1>true\g<2>", new, count=1)
else:
    new = new.replace("<options>", "<options>\n            <save_microenvironment>true</save_microenvironment>", 1)

out_dir.mkdir(parents=True, exist_ok=True)
dst = out_dir / "PhysiCell_settings.xml"
dst.write_text(new, encoding="utf-8", newline="\n")
print("wrote %s (max_time=%d min, save every %d min)" % (dst, minutes, max(1, minutes // 4)))
