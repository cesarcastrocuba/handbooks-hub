"""Transparent print copies of white-backed raster figures.

Print editions paint the page with the canvas colour, so an opaque white figure background
shows as a white box. The HTML editions keep the original PNGs (the light theme blends them
with CSS ``mix-blend-mode: multiply`` and the dark theme keeps the white backing readable).

Only staged copies change: a PNG is converted to colour-to-alpha against white and referenced
by a print-only path for the Typst and Word renders. The Markdown is restored to the original
references before the HTML render, and the source image bytes in the book repository are never
touched.
"""

from __future__ import annotations

from dataclasses import dataclass
import posixpath
import re
import struct
import zlib
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .artifact_optimize import PNG_SIGNATURE, _chunk, _chunks, _ihdr, png_pixels
from .build_types import BuildError
from .figure_layout import IMAGE, RASTERS
from .render_resources import RENDER_DIRECTORY
from .xref_links import _overlaps, _protected_spans, _visible

PRINT_FIGURES = f"{RENDER_DIRECTORY}/print-figures"
NEAR_WHITE = 250
BORDER_SHARE = 0.9
DROP_CHUNKS = {b"IHDR", b"IDAT", b"IEND", b"tRNS", b"PLTE", b"bKGD", b"hIST"}


def _near_white(pixels: bytes, offset: int) -> bool:
    return all(pixels[offset + channel] >= NEAR_WHITE for channel in range(3))


def _white_border(pixels: bytes, width: int, height: int, channels: int) -> bool:
    """A figure has a white-backed canvas when its one-pixel perimeter is near white."""
    offsets = [x * channels for x in range(width)]
    offsets += [((height - 1) * width + x) * channels for x in range(width)]
    for y in range(height):
        offsets.append(y * width * channels)
        offsets.append((y * width + width - 1) * channels)
    share = sum(_near_white(pixels, offset) for offset in offsets) / len(offsets)
    return share >= BORDER_SHARE


def transparent_png(data: bytes) -> bytes | None:
    """Return a colour-to-alpha PNG, or None when the image is not a white-backed raster.

    Only 8-bit, non-interlaced RGB and RGBA PNGs with a near-white perimeter qualify. JPEG and
    other formats keep the original because photographs do not have a white canvas.
    """
    width, height, bit_depth, color_type, _, _, interlace = _ihdr(data)
    if interlace or bit_depth != 8 or color_type not in {2, 6}:
        return None
    pixels = png_pixels(data)
    channels = 3 if color_type == 2 else 4
    if not _white_border(pixels, width, height, channels):
        return None
    rgba = bytearray(width * height * 4)
    row_bytes = width * channels
    white_row = b"\xff" * row_bytes
    for row_start in range(0, len(pixels), row_bytes):
        row = pixels[row_start : row_start + row_bytes]
        if row == white_row:
            continue
        base = (row_start // channels) * 4
        for offset in range(0, row_bytes, channels):
            source = offset
            target = base + (offset // channels) * 4
            if channels == 3:
                red, green, blue = row[source], row[source + 1], row[source + 2]
                alpha_in = 255
            else:
                red, green, blue, alpha_in = (
                    row[source],
                    row[source + 1],
                    row[source + 2],
                    row[source + 3],
                )
            if alpha_in == 255:
                low = red if red < green else green
                low = low if low < blue else blue
                if low == 255:
                    continue
                alpha = 255 - low
                rgba[target] = ((red - low) * 255 + alpha // 2) // alpha
                rgba[target + 1] = ((green - low) * 255 + alpha // 2) // alpha
                rgba[target + 2] = ((blue - low) * 255 + alpha // 2) // alpha
                rgba[target + 3] = alpha
                continue
            # Composite over white first, so an existing alpha is part of the visible colour.
            over_white = [
                (value * alpha_in + 255 * (255 - alpha_in) + 127) // 255
                for value in (red, green, blue)
            ]
            alpha = max(255 - value for value in over_white)
            if alpha == 0:
                continue
            for channel in range(3):
                value = ((over_white[channel] - 255 + alpha) * 255 + alpha // 2) // alpha
                rgba[target + channel] = min(255, max(0, value))
            rgba[target + 3] = alpha
    filtered = b"".join(
        b"\x00" + rgba[offset : offset + width * 4]
        for offset in range(0, len(rgba), width * 4)
    )
    compressed = zlib.compress(filtered, 9)
    out: list[bytes] = [PNG_SIGNATURE]
    for kind, payload in _chunks(data):
        if kind == b"IHDR":
            out.append(
                _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            )
        elif kind == b"IDAT":
            continue
        elif kind == b"IEND":
            out.append(_chunk(b"IDAT", compressed))
            out.append(_chunk(b"IEND", payload))
        elif kind not in DROP_CHUNKS:
            out.append(_chunk(kind, payload))
    return b"".join(out)


@dataclass
class PrintFigures:
    """Original entry text, restored after the print renders."""

    originals: dict[str, str]

    def restore(self, workspace: Path) -> None:
        for entry, text in self.originals.items():
            (workspace / entry).write_text(text, encoding="utf-8")


def stage_print_figures(workspace: Path, entries: list[str]) -> PrintFigures:
    """Write transparent print copies and point the staged Markdown at them."""
    workspace = workspace.resolve()
    originals: dict[str, str] = {}
    copies: dict[Path, Path | None] = {}
    for entry in entries:
        path = workspace / entry
        text = path.read_text(encoding="utf-8")
        originals[entry] = text
        lines = text.split("\n")
        visible = _visible(text)
        for index, line in enumerate(lines):
            if index not in visible:
                continue
            code = [(a, b) for a, b in _protected_spans(line) if line[a : a + 1] == "`"]

            def replace(match: re.Match[str]) -> str:
                if _overlaps(match.span(), code):
                    return match[0]
                target = urlsplit(match[1])
                if target.scheme or target.netloc:
                    return match[0]
                image = (path.parent / unquote(target.path)).resolve()
                if image.suffix.lower() not in RASTERS:
                    return match[0]
                if image.suffix.lower() != ".png":
                    return match[0]
                try:
                    relative = image.relative_to(workspace)
                except ValueError as exc:
                    raise BuildError("raster figure escapes staging workspace") from exc
                if image not in copies:
                    result = transparent_png(image.read_bytes())
                    if result is None:
                        copies[image] = None
                    else:
                        print_path = workspace / PRINT_FIGURES / relative
                        print_path.parent.mkdir(parents=True, exist_ok=True)
                        print_path.write_bytes(result)
                        copies[image] = print_path
                print_path = copies[image]
                if print_path is None:
                    return match[0]
                replacement = posixpath.relpath(print_path, path.parent)
                start = match.start(1) - match.start(0)
                return match[0][:start] + replacement + match[0][start + len(match[1]) :]

            lines[index] = IMAGE.sub(replace, line)
        staged = "\n".join(lines)
        if staged != text:
            path.write_text(staged, encoding="utf-8")
    return PrintFigures(originals)
