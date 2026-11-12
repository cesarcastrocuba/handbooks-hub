#!/usr/bin/env python3
"""Regenerate the self-hosted WOFF2 fonts with renamed internal identifiers.

The web fonts are modified subsets of Liberation Sans and JetBrains Mono, both under the SIL Open
Font License 1.1. The OFL requires a modified font with a Reserved Font Name to be renamed, and its
copyright and license to travel with every copy. This script performs the subset, rewrites the
internal family/full/PostScript names to ``Handbook Sans``/``Handbook Mono``, keeps the upstream
copyright, and writes the OFL license text and URL into the name table.

It is a maintenance tool, not a build step. It requires ``fonttools`` and ``brotli``; the generated
WOFF2 files are committed.
"""
from __future__ import annotations

from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).resolve().parents[1] / "src/handbook_toolkit/render_data/fonts"
UNICODES = [
    *range(0x0000, 0x0100),
    *range(0x0100, 0x0180),
    *range(0x2000, 0x2070),
    *range(0x20A0, 0x20C0),
    *range(0x2100, 0x2150),
    *range(0x2190, 0x2200),
    *range(0x2200, 0x2300),
    *range(0x2500, 0x2580),
    *range(0x25A0, 0x2600),
]
OFL_TEXT = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
OFL_URL = "https://openfontlicense.org"

FONTS = (
    ("liberation-sans/LiberationSans-Regular.ttf", "liberation-sans/HandbookSans-Regular.woff2", "Handbook Sans", "Regular"),
    ("liberation-sans/LiberationSans-Bold.ttf", "liberation-sans/HandbookSans-Bold.woff2", "Handbook Sans", "Bold"),
    ("liberation-sans/LiberationSans-Italic.ttf", "liberation-sans/HandbookSans-Italic.woff2", "Handbook Sans", "Italic"),
    ("liberation-sans/LiberationSans-BoldItalic.ttf", "liberation-sans/HandbookSans-BoldItalic.woff2", "Handbook Sans", "Bold Italic"),
    ("jetbrains-mono/JetBrainsMono-Regular.ttf", "jetbrains-mono/HandbookMono-Regular.woff2", "Handbook Mono", "Regular"),
    ("jetbrains-mono/JetBrainsMono-Bold.ttf", "jetbrains-mono/HandbookMono-Bold.woff2", "Handbook Mono", "Bold"),
    ("jetbrains-mono/JetBrainsMono-Italic.ttf", "jetbrains-mono/HandbookMono-Italic.woff2", "Handbook Mono", "Italic"),
)


def rename(font: TTFont, family: str, style: str) -> None:
    """Rewrite the identifying names and keep the license in the name table."""

    values = {
        1: family,
        2: style,
        3: f"{family} {style} subset; 2026; OFL-1.1",
        4: f"{family} {style}",
        6: f"{family.replace(' ', '')}-{style.replace(' ', '')}",
        16: family,
        17: style,
    }
    table = font["name"]
    for record in list(table.names):
        if record.nameID in (18, 21, 22):
            table.names.remove(record)
        elif record.nameID in values:
            encoding = record.getEncoding() or "utf_16_be"
            record.string = values[record.nameID].encode(encoding)
    table.setName(OFL_TEXT, 13, 3, 1, 0x409)
    table.setName(OFL_URL, 14, 3, 1, 0x409)


def build(source: Path, destination: Path, family: str, style: str) -> None:
    font = TTFont(source)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=UNICODES)
    subsetter.subset(font)
    rename(font, family, style)
    font.flavor = "woff2"
    font.save(destination)
    check = TTFont(destination)
    print(
        f"{destination.relative_to(FONT_DIR)}: {len(check.getBestCmap())} chars; "
        f"family={check['name'].getDebugName(1)!r}; "
        f"postscript={check['name'].getDebugName(6)!r}; "
        f"license={bool(check['name'].getDebugName(13))}"
    )


def main() -> None:
    for source, destination, family, style in FONTS:
        build(FONT_DIR / source, FONT_DIR / destination, family, style)


if __name__ == "__main__":
    main()
