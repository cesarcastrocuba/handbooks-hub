"""Scale a figure that nearly fits the page Word would leave part empty in front of it.

Word cannot float an inline figure. When a figure, its caption and the heading or
lead-in kept with it do not fit the rest of a page, they move on and the page stays
part empty. This pass paginates the document in LibreOffice, finds each figure group
that starts a page below a gap of at least ``MIN_GAP`` of the text block, and scales
the figure down just enough to fit the gap when that keeps it at ``MIN_NATURAL`` or
more of its natural raster size.

Nothing moves: every figure and every table stays right after the text that
introduces it, in the order the author wrote (Owner decision of 2026-11-22: a figure
away from its description is a defect, a part-empty page is not). Tables are never
scaled. A scaled figure moves the later page breaks, so the actions of one pass are
``SPACING`` pages apart and each pass measures the document again. Desktop Word
paginates slightly differently from LibreOffice, so the Word edition is still checked
in Word.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from .build_types import BuildError
from .docx_post import _write_package
from .docx_xml import NS, W, order_properties, register_namespaces

WP = "{" + NS["wp"] + "}"
A = "{" + NS["a"] + "}"
R = "{" + NS["r"] + "}"
PACKAGE_RELATIONSHIP = "{" + NS["pr"] + "}Relationship"

PRINT_SCALE = 0.85  # every raster figure prints at this fraction of its stated size
MIN_GAP = 0.15  # act only when the previous page is at least this fraction empty
MIN_NATURAL = 0.75  # never print a raster below this fraction of its natural size
TOP_SLACK = 40.0  # points: the group must start within this distance of the top margin
SAFETY = 10.0  # points kept free for box padding and rounding
CAPTION_REACH = 40.0  # points: a caption has at most about three lines
PASSES = 4
SPACING = 3  # pages between two actions of one pass
CAPTION_STYLES = {"ImageCaption", "TableCaption", "Caption"}
OFF = {"0", "false", "off"}


@dataclass
class Unit:
    """A body-level figure: its image paragraph, its caption and the start of its keep chain."""

    image: ET.Element
    caption: ET.Element
    chain: ET.Element


@dataclass(frozen=True)
class Shrink:
    scale: float


def _style(paragraph: ET.Element) -> str:
    style = paragraph.find(W + "pPr/" + W + "pStyle")
    return style.get(W + "val", "") if style is not None else ""


def _keeps(paragraph: ET.Element) -> bool:
    keep = paragraph.find(W + "pPr/" + W + "keepNext")
    return keep is not None and keep.get(W + "val", "1").lower() not in OFF


def figure_units(body: ET.Element) -> list[Unit]:
    """Find body-level figures followed by their caption, with the keep chain above them."""
    children = list(body)
    units = []
    for i, child in enumerate(children):
        if child.tag != W + "p" or child.find(".//" + W + "drawing") is None:
            continue
        if i + 1 >= len(children) or children[i + 1].tag != W + "p":
            continue
        caption = children[i + 1]
        if _style(caption) not in CAPTION_STYLES:
            continue
        # The keep chain that Word moves with the figure: lead-in and headings.
        chain = child
        j = i - 1
        while j >= 0:
            node = children[j]
            if node.tag in {W + "bookmarkStart", W + "bookmarkEnd"}:
                j -= 1
                continue
            if node.tag == W + "p" and _keeps(node) and node.find(".//" + W + "sectPr") is None:
                chain = node
                j -= 1
                continue
            break
        units.append(Unit(child, caption, chain))
    return units


def _first_paragraph(element: ET.Element) -> ET.Element | None:
    if element.tag == W + "p":
        return element
    return next(element.iter(W + "p"), None)


def _mark(paragraph: ET.Element, name: str, identifier: int) -> None:
    start = ET.Element(W + "bookmarkStart", {W + "id": str(identifier), W + "name": name})
    paragraph.insert(1 if paragraph.find(W + "pPr") is not None else 0, start)
    ET.SubElement(paragraph, W + "bookmarkEnd", {W + "id": str(identifier)})


def mark_probe(root: ET.Element) -> list[dict[str, str]]:
    """Add measurement bookmarks to a probe copy; return the names per unit."""
    body = root.find(W + "body")
    assert body is not None
    identifier = 1 + max(
        (int(n.get(W + "id", "0")) for n in root.iter(W + "bookmarkStart") if n.get(W + "id", "0").isdecimal()),
        default=0,
    )
    names = []
    for i, unit in enumerate(figure_units(body)):
        marks = {"group": f"FigPlaceG{i}", "image": f"FigPlaceI{i}", "caption": f"FigPlaceC{i}"}
        for key, paragraph in (
            ("group", unit.chain),
            ("image", _first_paragraph(unit.image)),
            ("caption", unit.caption),
        ):
            _mark(paragraph, marks[key], identifier)
            identifier += 1
        names.append(marks)
    return names


def destination_positions(pdf: Path, bookmarks: set[str]) -> dict[str, tuple[int, float]]:
    """Page and PDF y (from the bottom) of each named destination LibreOffice wrote."""
    from .docx_pages import _run, destination_name

    names = {destination_name(bookmark): bookmark for bookmark in bookmarks}
    found: dict[str, tuple[int, float]] = {}
    pattern = re.compile(r'^\s*(\d+)\s+\[\s*XYZ\s+(-?[\d.]+|null)\s+(-?[\d.]+)\s')
    for line in _run(["pdfinfo", "-dests", str(pdf)]).splitlines():
        quoted = line.rsplit('"', 2)
        if len(quoted) != 3 or quoted[1] not in names:
            continue
        match = pattern.match(line)
        if match:
            found[names[quoted[1]]] = (int(match[1]), float(match[3]))
    return found


def page_words(pdf: Path, page: int) -> tuple[float, list[tuple[float, float]]]:
    """Page height and the (top, bottom) of every word, measured from the top."""
    from .docx_pages import _run

    text = _run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), str(pdf), "-"])
    height = re.search(r'<page width="[\d.]+" height="([\d.]+)"', text)
    words = [
        (float(a), float(b))
        for a, b in re.findall(r'yMin="([\d.]+)" xMax="[\d.]+" yMax="([\d.]+)"', text)
    ]
    return (float(height[1]) if height else 0.0), words


def caption_bottom(words: list[tuple[float, float]], caption_top: float) -> float | None:
    """Bottom of the caption lines that start at ``caption_top``; stops at the next gap."""
    lines = sorted((a, b) for a, b in words if caption_top - 2 <= a <= caption_top + CAPTION_REACH)
    if not lines:
        return None
    bottom = lines[0][1]
    for a, b in lines[1:]:
        if a > bottom + 5:
            break
        bottom = max(bottom, b)
    return bottom


def decide(
    *,
    top: float,
    bottom: float,
    group: tuple[int, float],
    image: tuple[int, float],
    caption: tuple[int, float],
    caption_end: float,
    previous_bottom: float | None,
    figure_height: float,
    natural: float | None,
) -> Shrink | None:
    """Scale the figure when its group starts a page below a gap it nearly fits.

    Positions are points from the page top. The figure is scaled just enough for
    the group to fit the gap, and never below ``MIN_NATURAL`` of its natural size.
    """
    body = bottom - top
    page = group[0]
    if page < 2 or caption[0] != page or image[0] != page:
        return None
    if group[1] - top > TOP_SLACK or previous_bottom is None:
        return None
    room = bottom - previous_bottom
    if room < MIN_GAP * body:
        return None
    need = (caption_end - group[1]) - room + SAFETY
    if need <= 0 or natural is None or need >= figure_height:
        return None
    scale = round((figure_height - need) / figure_height, 4)
    # A shortfall below rounding would be a no-op that still uses up a pass's spacing.
    if scale >= 1 or natural * scale < MIN_NATURAL:
        return None
    return Shrink(scale)


def _natural_ratio(image: ET.Element, members: dict[str, bytes], targets: dict[str, str]) -> tuple[float | None, list[ET.Element]]:
    """Printed / natural width of the paragraph's single raster, and its extent elements."""
    extents = [e for e in image.iter() if e.tag in {WP + "extent", A + "ext"}]
    blips = [b for b in image.iter(A + "blip")]
    extent = next((e for e in image.iter(WP + "extent")), None)
    if len(blips) != 1 or extent is None:
        return None, extents
    target = targets.get(blips[0].get(R + "embed", ""))
    data = members.get("word/" + target) if target else None
    if not data or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None, extents
    width = struct.unpack(">I", data[16:20])[0]
    i = 8
    while i + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[i : i + 8])
        if kind == b"pHYs" and length == 9:
            x, _y, unit = struct.unpack(">IIB", data[i + 8 : i + 17])
            if unit == 1 and x:
                natural = width / (x * 0.0254) * 914400
                return int(extent.get("cx", "0")) / natural, extents
        if kind == b"IDAT":
            break
        i += 12 + length
    return None, extents


def apply_shrink(extents: list[ET.Element], scale: float) -> None:
    for extent in extents:
        for axis in ("cx", "cy"):
            extent.set(axis, str(int(int(extent.get(axis, "0")) * scale)))


def _geometry(root: ET.Element) -> tuple[float, float, float]:
    section = root.find(W + "body/" + W + "sectPr")
    size = section.find(W + "pgSz") if section is not None else None
    margin = section.find(W + "pgMar") if section is not None else None
    if size is None or margin is None:
        raise BuildError("figure placement requires page geometry")
    height = int(size.get(W + "h")) / 20
    return height, int(margin.get(W + "top")) / 20, height - int(margin.get(W + "bottom")) / 20


def print_scale(body: ET.Element, members: dict[str, bytes], targets: dict[str, str]) -> int:
    """Print every raster figure at PRINT_SCALE of its stated size, never below MIN_NATURAL.

    Owner request of 2026-11-23: the figures looked large. The natural-size floor
    keeps diagram text at 8 pt or more, so a figure already printed near that
    floor shrinks less or not at all. The PDF applies the same rule
    (``handbook-scale-images`` in ``table-fit.typ``).
    """
    count = 0
    for unit in figure_units(body):
        natural, extents = _natural_ratio(unit.image, members, targets)
        if not natural or not extents:
            continue
        # Round first: a factor that rounds to 1.0 would leave the extent unchanged
        # but still count as a scaled figure and use up a pass's spacing.
        factor = round(max(PRINT_SCALE, min(1.0, MIN_NATURAL / natural)), 4)
        if factor < 1:
            apply_shrink(extents, factor)
            count += 1
    return count


def place_figures(
    path: Path,
    fonts: Path,
    *,
    required: bool,
    compresslevel: int | None = 9,
    passes: int = PASSES,
) -> dict[str, str]:
    if not (shutil.which("soffice") and shutil.which("pdfinfo") and shutil.which("pdftotext")):
        if required:
            raise BuildError("Word figure placement requires LibreOffice, pdfinfo and pdftotext")
        return {"docx_figure_placement": "not measured (LibreOffice or Poppler unavailable)"}
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    register_namespaces()
    root = ET.fromstring(members["word/document.xml"])
    relationships = ET.fromstring(members.get("word/_rels/document.xml.rels", b"<Relationships/>"))
    targets = {
        rel.get("Id", ""): rel.get("Target", "")
        for rel in relationships.iter(PACKAGE_RELATIONSHIP)
    }
    try:
        report = _place(root, members, targets, fonts, path, passes)
    except (BuildError, OSError, ValueError) as exc:
        if required:
            raise BuildError(f"required Word figure placement failed: {exc}") from exc
        print("Word figure placement skipped: " + str(exc), file=sys.stderr)
        return {"docx_figure_placement": "not applied (LibreOffice measurement failed; see build stderr)"}
    order_properties(root)
    members["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    _write_package(path, members, compresslevel=compresslevel)
    return report


def _place(
    root: ET.Element,
    members: dict[str, bytes],
    targets: dict[str, str],
    fonts: Path,
    path: Path,
    passes: int,
) -> dict[str, str]:
    from .docx_pages import export_pdf, font_environment

    page_height, top, bottom = _geometry(root)
    body = root.find(W + "body")
    printed = print_scale(body, members, targets) if body is not None else 0
    shrunk = measured = 0
    with tempfile.TemporaryDirectory(prefix="figure-place-", dir=path.parent) as tmp:
        directory = Path(tmp)
        env = font_environment(fonts, directory)
        for number in range(passes):
            body = root.find(W + "body")
            assert body is not None
            units = figure_units(body)
            if not units:
                break
            probe = deepcopy(root)
            names = mark_probe(probe)
            probe_members = dict(members)
            order_properties(probe)
            probe_members["word/document.xml"] = ET.tostring(probe, encoding="utf-8", xml_declaration=True)
            probe_path = directory / f"probe{number}.docx"
            _write_package(probe_path, probe_members, compresslevel=1)
            pdf = export_pdf(probe_path, directory / f"pass{number}", env=env)
            measured += 1
            wanted = {name for marks in names for name in marks.values()}
            raw = destination_positions(pdf, wanted)
            positions = {name: (page, page_height - y) for name, (page, y) in raw.items()}
            cache: dict[int, list[tuple[float, float]]] = {}

            def words(page: int) -> list[tuple[float, float]]:
                if page not in cache:
                    cache[page] = page_words(pdf, page)[1]
                return cache[page]

            actions: list[tuple[Shrink, list[ET.Element], int]] = []
            for unit, marks in zip(units, names):
                if not all(marks[key] in positions for key in ("group", "image", "caption")):
                    continue
                group, image, caption = (positions[marks[key]] for key in ("group", "image", "caption"))
                page = group[0]
                if page < 2:
                    continue
                inside = [b for a, b in words(page - 1) if a >= top - 1 and b <= bottom + 1]
                end = caption_bottom(words(caption[0]), caption[1])
                extent = next((e for e in unit.image.iter(WP + "extent")), None)
                if end is None or extent is None:
                    continue
                natural, extents = _natural_ratio(unit.image, members, targets)
                action = decide(
                    top=top,
                    bottom=bottom,
                    group=group,
                    image=image,
                    caption=caption,
                    caption_end=end,
                    previous_bottom=max(inside) if inside else None,
                    figure_height=int(extent.get("cy", "0")) / 12700,
                    natural=natural,
                )
                if action is not None:
                    actions.append((action, extents, page))
            if not actions:
                break
            # A scaled figure moves the later page breaks of its chapter; the pages
            # right after it are measured again in the next pass before they change.
            last_page = -10
            for action, extents, page in actions:
                if page - last_page >= SPACING:
                    apply_shrink(extents, action.scale)
                    shrunk += 1
                    last_page = page
    return {
        "docx_figure_placement": (
            f"figures at print scale: {printed}; "
            f"figures scaled to fit page gaps: {shrunk}; no figure or table moved "
            f"({measured} LibreOffice passes)"
        )
    }
