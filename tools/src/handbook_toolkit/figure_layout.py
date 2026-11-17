"""Natural raster figure widths; port of MIT v3.0.0 builder at frozen 13d295b.

Only staged Markdown attributes change. Image bytes and SVG sizing remain untouched.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit
from .artifact_optimize import _chunks, _ihdr, PNG_SIGNATURE
from .build_types import BuildError
from .page_geometry import inches, text_width_inches
from .xref_links import _visible, _protected_spans, _overlaps

IMAGE = re.compile(r"!\[[^\]\n]*\]\(([^)\s]+)\)(\{[^}\n]*\})?")
WIDTH = re.compile(r'(?<!\S)width=(?:"([^"]+)"|\x27([^\x27]+)\x27|([^\s}]+))')
RASTERS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif", ".tif", ".tiff"}


@dataclass(frozen=True)
class RasterSize:
    width: int
    height: int
    dpi: float


def png_size(path: Path) -> RasterSize | None:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        return None
    width, height, *_ = _ihdr(data)
    for kind, payload in _chunks(data):
        if kind == b"pHYs" and len(payload) == 9:
            x, y, unit = struct.unpack(">IIB", payload)
            if unit == 1 and x and y:
                return RasterSize(width, height, x * 0.0254)
    return None


def figure_width(size: RasterSize, text_width: float, stated: float = 100) -> int:
    natural = math.floor(100 * size.width / size.dpi / text_width)
    ratio = size.height / size.width
    tall = math.floor(100 * 1.25 / ratio) if ratio > 1.25 else 100
    return min(math.floor(stated), natural, tall)


def stage_figures(workspace: Path, entries: list[str], config: dict) -> list[dict]:
    """Apply width once before every writer; preserve fenced/inline code."""
    records = []
    for entry in entries:
        path = workspace / entry
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        visible = _visible(text)
        for i, line in enumerate(lines):
            if i not in visible:
                continue
            code = [(a, b) for a, b in _protected_spans(line) if line[a : a + 1] == "`"]

            def replace(match: re.Match[str]) -> str:
                if _overlaps(match.span(), code):
                    return match[0]
                target = urlsplit(match[1])
                remote = bool(target.scheme or target.netloc)
                image = (
                    Path(unquote(target.path))
                    if remote
                    else (path.parent / unquote(target.path)).resolve()
                )
                if image.suffix.lower() not in RASTERS:
                    return match[0]
                try:
                    if not remote:
                        image.relative_to(workspace.resolve())
                except ValueError as exc:
                    raise BuildError("raster figure escapes staging workspace") from exc
                attrs = (match[2] or "{}")[1:-1].strip()
                width = WIDTH.search(attrs)
                stated = (
                    next((v for v in width.groups() if v is not None), None)
                    if width
                    else None
                )
                size = (
                    png_size(image)
                    if not remote and image.suffix.lower() == ".png"
                    else None
                )
                result = None
                if size:
                    column = text_width_inches(config)
                    cap = (
                        float(stated[:-1])
                        if stated and stated.endswith("%")
                        else 100 * inches(stated) / column if stated else 100
                    )
                    result = figure_width(size, column, cap)
                    attrs = WIDTH.sub("", attrs).strip()
                    attrs += f' width="{result}%"'
                if ".handbook-raster" not in attrs.split():
                    attrs += " .handbook-raster"
                identity = re.search(r"(?:^|\s)#([^\s]+)", attrs)
                records.append(
                    {
                        "source": entry,
                        "id": identity[1] if identity else None,
                        "path": (
                            match[1] if remote else str(image.relative_to(workspace))
                        ),
                        "size": asdict(size) if size else None,
                        "width_percent": result,
                        "stated": stated,
                    }
                )
                return (
                    match[0][: match.start(2) - match.start()]
                    + "{"
                    + attrs.strip()
                    + "}"
                    if match[2]
                    else match[0] + "{" + attrs.strip() + "}"
                )

            lines[i] = IMAGE.sub(replace, line)
        path.write_text("\n".join(lines), encoding="utf-8")
    return records
