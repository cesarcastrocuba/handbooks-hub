#!/usr/bin/env python3
"""Regenerate the self-hosted WOFF2 fonts from the committed TTF files.

The toolkit ships three font families under ``render_data/fonts/``: Source Sans 3 (body text),
Source Serif 4 (display) and JetBrains Mono (code), all under the SIL Open Font License 1.1. The OFL
requires a modified font with a Reserved Font Name to be renamed, and its copyright and license to
travel with every copy.

The path from the upstream files to the shipped WOFF2 files is:

1. The TTF files are committed in each family directory. The JetBrains Mono files keep their upstream
   names. The Source Sans 3 and Source Serif 4 files are already renamed to ``Handbook Sans`` and
   ``Handbook Serif`` when they enter the repository; obtaining and renaming them is manual and is
   not scripted here.
2. ``FONTS`` pairs each committed TTF with the WOFF2 file this script writes.
3. For each pair the script subsets the glyphs to ``UNICODES`` while keeping the layout features and
   every name record, rewrites name IDs 1, 2, 3, 4, 6, 16 and 17 to the Handbook family and style,
   drops name IDs 18, 21 and 22, keeps the upstream copyright (name ID 0), and sets name IDs 13 and
   14 to the OFL statement and URL. It saves the result as WOFF2.
4. The committed ``OFL.txt`` in each family directory is what the build publishes beside the fonts.

It is a maintenance tool, not a build step. It requires ``fonttools`` and ``brotli``; the generated
WOFF2 files are committed. Rerunning it reproduces the WOFF2 files from the committed TTF files only;
it cannot reproduce the renamed Adobe TTF files, and the upstream download and hash check are not
recorded.
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
    ("source-sans3/HandbookSans-Regular.ttf", "source-sans3/HandbookSans-Regular.woff2", "Handbook Sans", "Regular"),
    ("source-sans3/HandbookSans-Bold.ttf", "source-sans3/HandbookSans-Bold.woff2", "Handbook Sans", "Bold"),
    ("source-sans3/HandbookSans-Italic.ttf", "source-sans3/HandbookSans-Italic.woff2", "Handbook Sans", "Italic"),
    ("source-sans3/HandbookSans-BoldItalic.ttf", "source-sans3/HandbookSans-BoldItalic.woff2", "Handbook Sans", "Bold Italic"),
    ("source-serif4/HandbookSerif-Regular.ttf", "source-serif4/HandbookSerif-Regular.woff2", "Handbook Serif", "Regular"),
    ("source-serif4/HandbookSerif-Semibold.ttf", "source-serif4/HandbookSerif-Semibold.woff2", "Handbook Serif", "Semibold"),
    ("source-serif4/HandbookSerif-Bold.ttf", "source-serif4/HandbookSerif-Bold.woff2", "Handbook Serif", "Bold"),
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
