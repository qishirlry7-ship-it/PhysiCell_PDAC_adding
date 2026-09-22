#!/usr/bin/env python3
"""Remove the four dedicated tumour infection/xenophagy cell types.

Infection state lives in custom_data (pn_active, sal_ruffle_tokens,
intracellular_bacteria, surface_pMHC_I/II, xenophagy_activity, ...), so a
tumour no longer needs to convert into a separate type to be tracked. This
drops those types from the rules file.

Three kinds of edit:

1. Rules whose SUBJECT is a dead type are deleted -- nothing can ever be that
   type, so they can never fire.
2. Rules of the form "... transform to <dead type>" are deleted -- the
   transformation has no destination.
3. Rules where a bacterium reacts to CONTACT WITH a dead type are rewritten to
   react to the base tumour types instead, because the bacterium still needs to
   die on contact with an infected tumour, and it can no longer tell the
   difference.

Usage: strip_tumour_infection_types.py [--check]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "config" / "cell_rules.csv"

DEAD = (
    "PD-L1lo_tumor_infected",
    "PD-L1hi_tumor_infected",
    "PD-L1lo_tumor_xenophagy",
    "PD-L1hi_tumor_xenophagy",
)
# contact-with rewrites: dead type -> the base type that stands in for it
CONTACT_MAP = {
    "PD-L1lo_tumor_infected": "PD-L1lo_tumor",
    "PD-L1hi_tumor_infected": "PD-L1hi_tumor",
    "PD-L1lo_tumor_xenophagy": "PD-L1lo_tumor",
    "PD-L1hi_tumor_xenophagy": "PD-L1hi_tumor",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    original = RULES.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    kept: list[str] = []
    deleted_subject = 0
    deleted_target = 0
    rewritten = 0
    rewritten_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Comments, blank lines and the header pass through untouched.
        if not stripped or stripped.startswith("//") or stripped.startswith("#"):
            kept.append(line)
            continue
        if stripped.startswith("cell_type,"):
            kept.append(line)
            continue

        parts = stripped.split(",")
        if len(parts) < 4:
            kept.append(line)
            continue

        subject = parts[0]
        behaviour = parts[3]

        # 1. Subject is a dead type -> unreachable rule.
        if subject in DEAD:
            deleted_subject += 1
            continue

        # 2. Destination is a dead type -> no destination.
        if behaviour.startswith("transform to "):
            dest = behaviour[len("transform to "):].strip()
            if dest in DEAD:
                deleted_target += 1
                continue

        # 3. Contact-with a dead type -> retarget to the base tumour type.
        # The contact signal lives in column 2 (signal), not column 4
        # (behaviour), so match against the whole row. Use [^,]+ rather than
        # \S+: commas are not whitespace, so \S+ would swallow the rest of the
        # row and never equal a bare type name.
        m = re.search(r"contact with ([^,]+)", stripped)
        if m and m.group(1).strip() in CONTACT_MAP:
            new_line = line.replace(m.group(1), CONTACT_MAP[m.group(1).strip()])
            rewritten += 1
            rewritten_lines.append(f"    {stripped}\n      -> {new_line.strip()}")
            kept.append(new_line)
            continue

        kept.append(line)

    result = "".join(kept)
    print(f"deleted (dead subject) : {deleted_subject}")
    print(f"deleted (dead target)  : {deleted_target}")
    print(f"rewritten (contact)    : {rewritten}")
    if rewritten_lines:
        print("rewrites:")
        for entry in rewritten_lines:
            print(entry)
    print(f"lines: {len(lines)} -> {len(kept)}")

    if args.check:
        print("\n--check: nothing written")
        return 0

    RULES.write_text(result, encoding="utf-8", newline="\n")
    print(f"wrote {RULES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
