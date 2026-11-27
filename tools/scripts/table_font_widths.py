#!/usr/bin/env python3
"""Generate or check the Inter Bold advance widths embedded in table-layout.lua.

The table filter measures the longest unbreakable piece of each Word table column in em. The
widths are for Inter Bold, the header case and the widest, at 1/1000 em for ASCII 32-126. Run this
script with --write after changing the font, and with --check in the test suite.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

from fontTools.ttLib import TTFont

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parent
FONT = TOOLS / "src/handbook_toolkit/render_data/fonts/inter/Inter-Bold.ttf"
FILTER = TOOLS / "src/handbook_toolkit/render_data/filters/table-layout.lua"
BEGIN = "-- BEGIN GENERATED INTER BOLD WIDTHS"
END = "-- END GENERATED INTER BOLD WIDTHS"
FIRST, LAST = 32, 126


def widths() -> list[int]:
    """Return the advance width of ASCII 32-126 in 1/1000 em, rounded to an integer."""

    font = TTFont(FONT)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    units = font["head"].unitsPerEm
    missing = [code for code in range(FIRST, LAST + 1) if code not in cmap]
    if missing:
        raise SystemExit(f"Inter-Bold is missing ASCII code points: {missing}")
    return [round(hmtx[cmap[code]][0] * 1000 / units) for code in range(FIRST, LAST + 1)]


def block(values: list[int]) -> str:
    lines = ["local INTER_BOLD_WIDTHS = {"]
    for start in range(0, len(values), 12):
        lines.append("  " + ", ".join(str(value) for value in values[start : start + 12]) + ",")
    lines.append("}")
    return BEGIN + "\n" + "\n".join(lines) + "\n" + END


def embedded(text: str) -> list[int]:
    match = re.search(re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END), text, re.DOTALL)
    if match is None:
        raise SystemExit(f"generated width markers not found in {FILTER}")
    return [int(value) for value in re.findall(r"\d+", match.group(1))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="fail unless the embedded table matches the font")
    group.add_argument("--write", action="store_true", help="replace the embedded table from the font")
    args = parser.parse_args(argv)
    values = widths()
    if args.check:
        text = FILTER.read_text(encoding="utf-8")
        found = embedded(text)
        if found != values:
            for index, (expected, actual) in enumerate(zip(values, found)):
                if expected != actual:
                    print(
                        f"{FILTER}: ASCII {FIRST + index}: font {expected}, embedded {actual}",
                        file=sys.stderr,
                    )
                    break
            if len(found) != len(values):
                print(f"{FILTER}: {len(found)} widths, expected {len(values)}", file=sys.stderr)
            return 1
        return 0
    if args.write:
        text = FILTER.read_text(encoding="utf-8")
        replacement = block(values)
        updated, count = re.subn(re.escape(BEGIN) + r"\n.*?\n" + re.escape(END), replacement, text, flags=re.DOTALL)
        if count != 1:
            anchor = 'local utf8 = require("utf8")\n'
            if anchor not in text:
                raise SystemExit(f"cannot find the insertion anchor in {FILTER}")
            updated = text.replace(anchor, anchor + "\n" + replacement + "\n", 1)
        FILTER.write_text(updated, encoding="utf-8")
        print(f"wrote {len(values)} Inter Bold widths to {FILTER}")
        return 0
    print(block(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
