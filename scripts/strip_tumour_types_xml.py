#!/usr/bin/env python3
"""Remove the four dedicated tumour infection/xenophagy cell definitions.

Infection state lives in custom_data, so a tumour never converts into a
separate type. Removing the definitions also requires removing the two kinds
of reference that point at them:

  - <transformation_rate name="...">  from other cell definitions
  - <attack_rate name="...">          in immune-cell interaction blocks

The definitions themselves run from their opening tag up to the next
<cell_definition, and carry a <cell_definition> ... </cell_definition> body
that must be removed as a whole.

Usage: strip_tumour_types_xml.py [--check]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "config" / "PhysiCell_settings.xml"

DEAD = [
    "PD-L1lo_tumor_infected",
    "PD-L1lo_tumor_xenophagy",
    "PD-L1hi_tumor_infected",
    "PD-L1hi_tumor_xenophagy",
]


def strip_definitions(text: str) -> tuple[str, int]:
    removed = 0
    for name in DEAD:
        pattern = re.compile(
            rf'[ \t]*<cell_definition name="{re.escape(name)}".*?</cell_definition>\s*\n',
            re.DOTALL,
        )
        text, n = pattern.subn("", text)
        removed += n
        if n != 1:
            print(f"  warning: removed {n} definitions for {name} (expected 1)")
    return text, removed


def strip_references(text: str) -> tuple[str, int, int]:
    tr = ar = 0
    for name in DEAD:
        pattern = re.compile(
            rf'[ \t]*<transformation_rate name="{re.escape(name)}"[^>]*>[^<]*</transformation_rate>\s*\n'
        )
        text, n = pattern.subn("", text)
        tr += n

        pattern = re.compile(
            rf'[ \t]*<attack_rate name="{re.escape(name)}"[^>]*>[^<]*</attack_rate>\s*\n'
        )
        text, n = pattern.subn("", text)
        ar += n
    return text, tr, ar


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    original = XML.read_text(encoding="utf-8")
    print(f"original: {len(original)} bytes, "
          f"{len(original.splitlines())} lines")

    text, removed = strip_definitions(original)
    text, tr, ar = strip_references(text)

    print(f"cell_definition blocks removed : {removed}")
    print(f"transformation_rate removed    : {tr}")
    print(f"attack_rate removed            : {ar}")

    leftover = re.findall(
        r"^.*(?:PD-L1lo_tumor_infected|PD-L1lo_tumor_xenophagy|"
        r"PD-L1hi_tumor_infected|PD-L1hi_tumor_xenophagy).*$",
        text, re.MULTILINE)
    print(f"residual references            : {len(leftover)}")
    for line in leftover[:10]:
        print(f"    {line.strip()[:120]}")

    print(f"result: {len(text)} bytes, {len(text.splitlines())} lines")

    if args.check:
        print("\n--check: nothing written")
        return 0

    XML.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {XML.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
