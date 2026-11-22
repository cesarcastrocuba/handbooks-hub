"""Fill the pages that Word would leave part empty in front of a float.

Word cannot float an inline figure or a table kept on one page. When such a
float and the lead-in kept with it do not fit the rest of a page, they move on
and the page stays part empty. This pass paginates the document in LibreOffice,
finds each float group that starts a page below a gap of at least ``MIN_GAP``
of the text block, and then either

* defers it: the blocks that follow the float in its section and fit the gap
  move up in front of it, as a typesetter moves a float to the top of the next
  page; a plain paragraph that crosses the foot of the page also moves, because
  it breaks across pages; or
* when nothing can move, scales a figure down just enough to fit the gap, when
  that keeps it at ``MIN_NATURAL`` or more of its natural raster size. Tables
  are never scaled.

A float never passes a heading, a section or page break or another float, so
captions keep their order, and a block kept with the next one never leaves it.
A run of callouts counts as kept together, so a float never lands inside it.
An action moves the later page breaks, so the actions of one pass are
``SPACING`` pages apart and each pass measures the document again. Desktop Word
paginates slightly differently from LibreOffice, so the Word edition is still
checked in Word.
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

MIN_GAP = 0.15  # act only when the previous page is at least this fraction empty
MIN_NATURAL = 0.75  # never print a raster below this fraction of its natural size
MIN_MOVE = 0.08  # a deferral must fill at least this fraction of the text block
TOP_SLACK = 40.0  # points: the group must start within this distance of the top margin
SAFETY = 10.0  # points kept free for box padding and rounding
CAPTION_REACH = 40.0  # points: a caption has at most about three lines
LOOKAHEAD = 24  # blocks examined after a figure
PASSES = 4
SPACING = 3  # pages between two actions of one pass
PREFER_SHRINK = False  # deferral keeps the figure at its size; scaling is the fallback
CAPTION_STYLES = {"ImageCaption", "TableCaption", "Caption"}
CALLOUT_STYLE = "CalloutBox"  # the one-cell table docx_post wraps each callout in
OFF = {"0", "false", "off"}


@dataclass
class Unit:
    """A body-level float: its own bookmarks, image paragraph or data table, and caption."""

    nodes: list[ET.Element]
    image: ET.Element
    caption: ET.Element
    chain: ET.Element
    before: ET.Element | None
    blocks: list[list[ET.Element]]
    stop: ET.Element | None
    kind: str = "figure"
    complete: bool = True  # False when the lookahead ended before a barrier


@dataclass(frozen=True)
class Shrink:
    scale: float


@dataclass(frozen=True)
class Defer:
    blocks: int


def _style(paragraph: ET.Element) -> str:
    style = paragraph.find(W + "pPr/" + W + "pStyle")
    return style.get(W + "val", "") if style is not None else ""


def _keeps(paragraph: ET.Element) -> bool:
    keep = paragraph.find(W + "pPr/" + W + "keepNext")
    return keep is not None and keep.get(W + "val", "1").lower() not in OFF


def _bound(block: list[ET.Element]) -> bool:
    """Whether the block is kept with the block that follows it.

    A table is kept with the next block by the paragraphs of its last row; a table
    nested in that row (the options table of a decision callout) keeps its own rows
    together and does not hold the outer table to what follows.
    """
    element = next(node for node in block if node.tag in {W + "p", W + "tbl"})
    if element.tag == W + "p":
        return _keeps(element)
    rows = element.findall(W + "tr")
    return bool(rows) and any(
        _keeps(p) for cell in rows[-1].findall(W + "tc") for p in cell.findall(W + "p")
    )


def _callout(block: list[ET.Element]) -> bool:
    element = next(node for node in block if node.tag in {W + "p", W + "tbl"})
    style = element.find(W + "tblPr/" + W + "tblStyle")
    return element.tag == W + "tbl" and style is not None and style.get(W + "val") == CALLOUT_STYLE


def _spacer(block: list[ET.Element]) -> bool:
    element = next(node for node in block if node.tag in {W + "p", W + "tbl"})
    return (
        element.tag == W + "p"
        and not "".join(element.itertext()).strip()
        and element.find(".//" + W + "drawing") is None
    )


def callout_runs(blocks: list[list[ET.Element]], complete: bool = True) -> list[bool]:
    """Whether each block is joined to the next one inside a run of callouts.

    A callout followed by another callout, with only empty spacers between them,
    starts or continues a run: a pitfall and its decision read as one unit, so a
    float goes in front of the run or after all of it. Word may still break the
    page inside the run. When the lookahead ends inside a run (``complete``
    false), the run is joined to its last examined block.
    """
    runs = [False] * len(blocks)
    for i, block in enumerate(blocks):
        if not _callout(block):
            continue
        j = i + 1
        while j < len(blocks) and _spacer(blocks[j]):
            j += 1
        if (j < len(blocks) and _callout(blocks[j])) or (j == len(blocks) and not complete):
            for k in range(i, j):
                runs[k] = True
    return runs


def kept_with_next(blocks: list[list[ET.Element]], complete: bool = True) -> list[bool]:
    """Whether a deferred float may not land right after each block (``keepNext`` or a run)."""
    runs = callout_runs(blocks, complete)
    return [_bound(block) or joined for block, joined in zip(blocks, runs)]


def _is_data_table(element: ET.Element) -> bool:
    if element.tag != W + "tbl":
        return False
    style = element.find(W + "tblPr/" + W + "tblStyle")
    look = element.find(W + "tblPr/" + W + "tblLook")
    return (
        style is not None
        and style.get(W + "val") in {"Table", "TablePlain"}
        and look is not None
        and look.get(W + "firstRow") in {"1", "true", "on"}
    )


def _kept_whole(table: ET.Element) -> bool:
    """A data table the table measurement keeps on one page (every row keeps with the next)."""
    rows = table.findall(W + "tr")
    return bool(rows) and all(any(_keeps(p) for p in row.iter(W + "p")) for row in rows[:-1])


def _float_kind(element: ET.Element) -> str | None:
    if element.tag == W + "p" and element.find(".//" + W + "drawing") is not None:
        return "figure"
    if _is_data_table(element) and element.find(".//" + W + "drawing") is None:
        return "table"
    return None


def _whole(block: list[ET.Element]) -> bool:
    """A block that Word keeps on one page: a table whose rows do not split, or a kept paragraph."""
    element = next(node for node in block if node.tag in {W + "p", W + "tbl"})
    if element.tag == W + "p":
        keep = element.find(W + "pPr/" + W + "keepLines")
        return keep is not None and keep.get(W + "val", "1").lower() not in OFF
    rows = element.findall(W + "tr")
    return bool(rows) and all(
        (flag := row.find(W + "trPr/" + W + "cantSplit")) is not None
        and flag.get(W + "val", "1").lower() not in OFF
        for row in rows
    ) and (len(rows) == 1 or _kept_whole(element))


def _splits(block: list[ET.Element]) -> bool:
    """A plain paragraph that Word may break across pages."""
    element = next(node for node in block if node.tag in {W + "p", W + "tbl"})
    return (
        element.tag == W + "p"
        and element.find(W + "pPr/" + W + "keepLines") is None
        and not _keeps(element)
        and len("".join(element.itertext()).split()) >= 30
    )


def page_break_styles(styles: bytes | None) -> frozenset[str]:
    """Paragraph style ids that start a page, directly or through ``basedOn``."""
    if not styles:
        return frozenset()
    root = ET.fromstring(styles)
    parents: dict[str, str] = {}
    own: dict[str, bool] = {}
    for style in root.iter(W + "style"):
        if style.get(W + "type") != "paragraph":
            continue
        identifier = style.get(W + "styleId", "")
        based = style.find(W + "basedOn")
        if based is not None:
            parents[identifier] = based.get(W + "val", "")
        flag = style.find(W + "pPr/" + W + "pageBreakBefore")
        if flag is not None:
            own[identifier] = flag.get(W + "val", "1").lower() not in OFF

    def breaks(identifier: str) -> bool:
        seen = set()
        while identifier not in own:
            if identifier in seen or identifier not in parents:
                return False  # a cycle or the root of the chain without a flag
            seen.add(identifier)
            identifier = parents[identifier]
        return own[identifier]

    return frozenset(identifier for identifier in parents.keys() | own.keys() if breaks(identifier))


def _starts_page(paragraph: ET.Element, breaking: frozenset[str]) -> bool:
    flag = paragraph.find(W + "pPr/" + W + "pageBreakBefore")
    if flag is not None:
        return flag.get(W + "val", "1").lower() not in OFF
    return _style(paragraph) in breaking


def _barrier(element: ET.Element, kind: str, breaking: frozenset[str] = frozenset()) -> bool:
    """Where a deferred float must stop: a heading, a break or another float.

    Floats keep their relative order, so captions stay in numeric order and no
    float is separated from a lead-in that another float carries. A paragraph
    that starts a page (``pageBreakBefore``, directly or through its style) is a
    break even when its style is not a ``Heading``.
    """
    if element.tag == W + "tbl":
        return element.find(".//" + W + "drawing") is not None or _is_data_table(element)
    if element.tag != W + "p":
        return True
    return (
        _style(element).startswith("Heading")
        or _starts_page(element, breaking)
        or element.find(".//" + W + "sectPr") is not None
        or element.find(".//" + W + "drawing") is not None
        or any(br.get(W + "type") == "page" for br in element.iter(W + "br"))
    )


def figure_units(body: ET.Element, breaking: frozenset[str] = frozenset()) -> list[Unit]:
    """Find body-level figures and kept-whole data tables followed by their caption."""
    children = list(body)
    units = []
    for i, child in enumerate(children):
        kind = _float_kind(child)
        if kind is None or (kind == "table" and not _kept_whole(child)):
            continue
        if i + 1 >= len(children) or children[i + 1].tag != W + "p":
            continue
        caption = children[i + 1]
        if _style(caption) not in CAPTION_STYLES:
            continue
        start = i
        while start > 0 and children[start - 1].tag == W + "bookmarkStart":
            start -= 1
        own = {node.get(W + "id") for node in children[start:i]}
        end = i + 1
        while (
            end + 1 < len(children)
            and children[end + 1].tag == W + "bookmarkEnd"
            and children[end + 1].get(W + "id") in own
        ):
            end += 1
        closed = {node.get(W + "id") for node in children[i + 2 : end + 1]}
        if closed != own:
            continue  # the figure's own bookmark does not close right after it
        # The keep chain that moves with the figure: lead-in and headings.
        chain = child
        j = start - 1
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
        lead = None
        k = start - 1
        while k >= 0 and children[k].tag in {W + "bookmarkStart", W + "bookmarkEnd"}:
            k -= 1
        if k >= 0 and children[k].tag == W + "p" and _keeps(children[k]):
            lead = children[k]
        blocks: list[list[ET.Element]] = []
        pending: list[ET.Element] = []
        stop = None
        barrier = False
        k = end + 1
        while k < len(children) and len(blocks) < LOOKAHEAD:
            node = children[k]
            if node.tag == W + "bookmarkStart":
                pending.append(node)
            elif node.tag == W + "bookmarkEnd":
                if blocks and not pending:
                    blocks[-1].append(node)
                else:
                    pending.append(node)
            elif node.tag in {W + "p", W + "tbl"} and not _barrier(node, kind, breaking):
                blocks.append([*pending, node])
                pending = []
            else:
                stop = node if node.tag in {W + "p", W + "tbl"} else None
                barrier = True
                break
            k += 1
        truncated = not barrier and k < len(children)
        units.append(
            Unit(
                children[start : end + 1], child, caption, chain, lead, blocks, stop, kind,
                complete=not truncated,
            )
        )
    return units


def _first_paragraph(element: ET.Element) -> ET.Element | None:
    if element.tag == W + "p":
        return element
    return next(element.iter(W + "p"), None)


def _mark(paragraph: ET.Element, name: str, identifier: int) -> None:
    start = ET.Element(W + "bookmarkStart", {W + "id": str(identifier), W + "name": name})
    paragraph.insert(1 if paragraph.find(W + "pPr") is not None else 0, start)
    ET.SubElement(paragraph, W + "bookmarkEnd", {W + "id": str(identifier)})


def mark_probe(root: ET.Element, breaking: frozenset[str] = frozenset()) -> list[dict[str, str]]:
    """Add measurement bookmarks to a probe copy; return the names per unit."""
    body = root.find(W + "body")
    assert body is not None
    identifier = 1 + max(
        (int(n.get(W + "id", "0")) for n in root.iter(W + "bookmarkStart") if n.get(W + "id", "0").isdecimal()),
        default=0,
    )
    names = []
    for i, unit in enumerate(figure_units(body, breaking)):
        marks = {"group": f"FigPlaceG{i}", "image": f"FigPlaceI{i}", "caption": f"FigPlaceC{i}"}
        for key, paragraph in (
            ("group", unit.chain),
            ("image", _first_paragraph(unit.image)),
            ("caption", unit.caption),
        ):
            _mark(paragraph, marks[key], identifier)
            identifier += 1
        for k, block in enumerate([*unit.blocks, [unit.stop] if unit.stop is not None else []]):
            element = next((n for n in block if n.tag in {W + "p", W + "tbl"}), None)
            paragraph = _first_paragraph(element) if element is not None else None
            if paragraph is None:
                continue
            marks[f"block{k}"] = f"FigPlaceN{i}_{k}"
            _mark(paragraph, marks[f"block{k}"], identifier)
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
    blocks: list[tuple[int, float]],
    bound: list[bool],
    splits: list[bool] | None = None,
    whole: list[bool] | None = None,
    page_end: float | None = None,
    runs: list[bool] | None = None,
) -> Shrink | Defer | None:
    """Choose an action from measured positions (points from the page top).

    ``page_end`` is where the text of the float's page ends; it measures the last
    block on that page when the block cannot break across pages (``whole``).
    ``runs`` marks the blocks joined to the next one in a run of callouts (they
    are also ``bound``): when the first callout of a run fits the gap, the float
    moves after the whole run and the rest of the run starts the next page.
    """
    body = bottom - top
    splits = splits if splits is not None else [False] * len(bound)
    whole = whole if whole is not None else [False] * len(bound)
    runs = runs if runs is not None else [False] * len(bound)
    page = group[0]
    if page < 2 or caption[0] != page or image[0] != page:
        return None
    if group[1] - top > TOP_SLACK or previous_bottom is None:
        return None
    room = bottom - previous_bottom
    if room < MIN_GAP * body:
        return None
    need = (caption_end - group[1]) - room + SAFETY
    if need <= 0:
        return None
    shrink = None
    if natural is not None and need < figure_height:
        scale = (figure_height - need) / figure_height
        if natural * scale >= MIN_NATURAL:
            shrink = Shrink(round(scale, 4))
    if PREFER_SHRINK and shrink is not None:
        return shrink
    if not blocks or blocks[0][0] != page:
        return shrink
    chain = image[1] - group[1]
    best = 0
    for k in range(1, len(blocks) + 1):
        if k == len(blocks) or blocks[k][0] != page:
            # The last block on the page ends where the page's text ends, when it
            # cannot continue on the next page.
            if (
                k <= len(bound)
                and page_end is not None
                and whole[k - 1]
                and not bound[k - 1]
                and chain + page_end - blocks[0][1] <= room - SAFETY
            ):
                best = k
            break
        moved = chain + blocks[k][1] - blocks[0][1]
        if moved > room - SAFETY:
            # The block that crosses the foot of the page fills it when it can
            # break across pages; the rest of it flows on before the figure.
            if splits[k - 1] and not bound[k - 1]:
                best = k
            break
        if not bound[k - 1]:
            best = k
    moved_end = blocks[best][1] if best < len(blocks) and blocks[best][0] == page else page_end
    filled = moved_end - blocks[0][1] if best and moved_end is not None else 0.0
    # A run of callouts that starts on the page: its first callout fills the gap
    # and the float goes after the whole run instead of in front of it.
    start = next((k for k in range(best, min(len(runs), len(blocks))) if runs[k]), None)
    if start is not None and blocks[start][0] == page and whole[start]:
        after = start + 1  # the spacer or callout that follows the first callout
        end_top = None
        if after < len(blocks):
            end_top = blocks[after][1] if blocks[after][0] == page else page_end
        last = start
        while last < len(runs) and runs[last]:
            last += 1
        if (
            end_top is not None
            and last < len(runs)  # the run ends inside the lookahead
            and not bound[last]  # and its last callout is not kept with what follows
            and chain + end_top - blocks[0][1] <= room - SAFETY
            and end_top - blocks[0][1] > filled
        ):
            best, filled = last + 1, end_top - blocks[0][1]
    if best and filled >= MIN_MOVE * body:
        return Defer(best)
    return shrink


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


def apply_defer(body: ET.Element, unit: Unit, count: int) -> None:
    """Move the figure after ``count`` following blocks; its lead-in stops keeping with it."""
    last = unit.blocks[count - 1][-1]
    for node in unit.nodes:
        body.remove(node)
    position = list(body).index(last) + 1
    for offset, node in enumerate(unit.nodes):
        body.insert(position + offset, node)
    if unit.before is not None and not _style(unit.before).startswith("Heading"):
        keep = unit.before.find(W + "pPr/" + W + "keepNext")
        if keep is not None:
            unit.before.find(W + "pPr").remove(keep)


def _geometry(root: ET.Element) -> tuple[float, float, float]:
    section = root.find(W + "body/" + W + "sectPr")
    size = section.find(W + "pgSz") if section is not None else None
    margin = section.find(W + "pgMar") if section is not None else None
    if size is None or margin is None:
        raise BuildError("figure placement requires page geometry")
    height = int(size.get(W + "h")) / 20
    return height, int(margin.get(W + "top")) / 20, height - int(margin.get(W + "bottom")) / 20


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
    breaking = page_break_styles(members.get("word/styles.xml"))
    shrunk = deferred = measured = tables = 0
    with tempfile.TemporaryDirectory(prefix="figure-place-", dir=path.parent) as tmp:
        directory = Path(tmp)
        env = font_environment(fonts, directory)
        for number in range(passes):
            body = root.find(W + "body")
            assert body is not None
            units = figure_units(body, breaking)
            if not units:
                break
            probe = deepcopy(root)
            names = mark_probe(probe, breaking)
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

            actions: list[tuple[Unit, Shrink | Defer, list[ET.Element], int]] = []
            for unit, marks in zip(units, names):
                if not all(marks[key] in positions for key in ("group", "image", "caption")):
                    continue
                group, image, caption = (positions[marks[key]] for key in ("group", "image", "caption"))
                page = group[0]
                if page < 2:
                    continue
                inside = [b for a, b in words(page - 1) if a >= top - 1 and b <= bottom + 1]
                previous = max(inside) if inside else None
                end = caption_bottom(words(caption[0]), caption[1])
                if end is None:
                    continue
                tops = []
                for k in range(len(unit.blocks) + 1):
                    name = marks.get(f"block{k}")
                    if name is None or name not in positions:
                        break
                    tops.append(positions[name])
                if unit.kind == "figure":
                    natural, extents = _natural_ratio(unit.image, members, targets)
                    extent = next((e for e in unit.image.iter(WP + "extent")), None)
                    if extent is None:
                        continue
                    height = int(extent.get("cy", "0")) / 12700
                else:
                    natural, extents, height = None, [], 0.0
                action = decide(
                    top=top,
                    bottom=bottom,
                    group=group,
                    image=image,
                    caption=caption,
                    caption_end=end,
                    previous_bottom=previous,
                    figure_height=height,
                    natural=natural,
                    blocks=tops,
                    bound=kept_with_next(unit.blocks, unit.complete),
                    runs=callout_runs(unit.blocks, unit.complete),
                    splits=[_splits(block) for block in unit.blocks],
                    whole=[_whole(block) for block in unit.blocks],
                    page_end=max(
                        (b for a, b in words(page) if a >= top - 1 and b <= bottom + 1), default=None
                    ),
                )
                if action is not None:
                    actions.append((unit, action, extents, page))
            if not actions:
                break
            # An action moves the later page breaks of its chapter; the pages right
            # after it are measured again in the next pass before they are changed.
            spaced = []
            last_page = -10
            for entry in actions:
                if entry[3] - last_page >= SPACING:
                    spaced.append(entry)
                    last_page = entry[3]
            actions = spaced
            for unit, action, extents, _page in actions:
                if isinstance(action, Shrink):
                    apply_shrink(extents, action.scale)
                    shrunk += 1
                else:
                    apply_defer(body, unit, action.blocks)
                    deferred += 1
                    tables += unit.kind == "table"
    return {
        "docx_figure_placement": (
            f"{shrunk} figures scaled and {deferred} floats deferred ({tables} tables) to fill page gaps "
            f"({measured} LibreOffice passes)"
        )
    }
