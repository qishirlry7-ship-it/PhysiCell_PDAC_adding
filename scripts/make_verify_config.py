#!/usr/bin/env python3
"""Generate a short smoke-test config (default 60 min) from the production
PhysiCell_settings.xml, WITHOUT touching the original.

Usage:
    python scripts/make_verify_config.py [minutes] [out_dir]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 60
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "outputs" / "petrinet_types_check"
out_dir = out_dir if out_dir.is_absolute() else ROOT / out_dir

src = (ROOT / "config" / "PhysiCell_settings.xml").read_text(encoding="utf-8")
new, n = re.subn(r"(<max_time\b[^>]*>).*?(</max_time>)", r"\g<1>%d\g<2>" % minutes, src, count=1)
if n != 1:
    raise SystemExit("could not find <max_time>")

# also shrink the save interval so we get at least one output snapshot
new, n2 = re.subn(r"(<interval\b[^>]*>).*?(</interval>)", r"\g<1>%d\g<2>" % max(1, minutes), new, count=1)

out_dir.mkdir(parents=True, exist_ok=True)
dst = out_dir / "PhysiCell_settings.xml"
dst.write_text(new, encoding="utf-8", newline="\n")
print("wrote %s (max_time=%d min, save interval replacements=%d)" % (dst, minutes, n2))
