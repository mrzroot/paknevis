"""Regenerate ``*.out.*`` fixture files from ``*.in.*`` (review the diff before committing!)."""

from __future__ import annotations

import sys
from pathlib import Path

import paknevis
from paknevis.formats import detect_syntax

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def main() -> int:
    for source in sorted(FIXTURES.glob("*.in.*")):
        target = source.with_name(source.name.replace(".in.", ".out."))
        text = source.read_text(encoding="utf-8")
        fixed = paknevis.fix(text, syntax=detect_syntax(source))
        if not target.exists() or target.read_text(encoding="utf-8") != fixed:
            target.write_text(fixed, encoding="utf-8")
            print(f"updated {target.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
