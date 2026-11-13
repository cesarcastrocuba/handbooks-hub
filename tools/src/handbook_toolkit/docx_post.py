"""Post-process the Word edition using parsed OOXML."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from . import design
from .docx_fields import add_indexes
from .docx_fonts import font_table
from .docx_xml import order_properties, register_namespaces


def _paragraph_style(paragraph: ET.Element, word: str) -> str:
    style = paragraph.find(f"./{word}pPr/{word}pStyle")
    return style.get(f"{word}val", "") if style is not None else ""


def _page_text_width(root: ET.Element, word: str) -> int:
    size = root.find(f".//{word}sectPr/{word}pgSz")
    margins = root.find(f".//{word}sectPr/{word}pgMar")
    if size is None or margins is None:
        return 9360
    width = int(size.get(f"{word}w", "11906"))
    left = int(margins.get(f"{word}left", "1247"))
    right = int(margins.get(f"{word}right", "1247"))
    return max(4000, width - left - right)


def _spacer(word: str) -> ET.Element:
    paragraph = ET.Element(f"{word}p")
    properties = ET.SubElement(paragraph, f"{word}pPr")
    spacing = ET.SubElement(properties, f"{word}spacing")
    spacing.set(f"{word}before", "0")
    spacing.set(f"{word}after", "0")
    spacing.set(f"{word}line", "120")
    spacing.set(f"{word}lineRule", "exact")
    run = ET.SubElement(paragraph, f"{word}r")
    run_properties = ET.SubElement(run, f"{word}rPr")
    size = ET.SubElement(run_properties, f"{word}sz")
    size.set(f"{word}val", "8")
    return paragraph


def _clear_paragraph_box(paragraph: ET.Element, word: str) -> None:
    properties = paragraph.find(f"./{word}pPr")
    if properties is None:
        return
    for tag in ("pBdr", "shd"):
        existing = properties.find(f"./{word}{tag}")
        if existing is not None:
            properties.remove(existing)


def _plain_callout_tables(table: ET.Element, word: str) -> None:
    for item in table.iter(f"{word}tbl"):
        look = item.find(f"./{word}tblPr/{word}tblLook")
        if look is not None:
            look.set(f"{word}noHBand", "1")
        style = item.find(f"./{word}tblPr/{word}tblStyle")
        if style is not None:
            style.set(f"{word}val", "TablePlain")


def _wrap_callout_box(
    root: ET.Element,
    body: ET.Element,
    children: list[ET.Element],
    position: int,
    group: list[ET.Element],
    word: str,
    accent: str,
    tint: str,
) -> None:
    width = _page_text_width(root, word) - 240
    table = ET.Element(f"{word}tbl")
    properties = ET.SubElement(table, f"{word}tblPr")
    table_style = ET.SubElement(properties, f"{word}tblStyle")
    table_style.set(f"{word}val", "CalloutBox")
    table_width = ET.SubElement(properties, f"{word}tblW")
    table_width.set(f"{word}w", str(width))
    table_width.set(f"{word}type", "dxa")
    ET.SubElement(properties, f"{word}tblInd", {f"{word}w": "120", f"{word}type": "dxa"})
    layout = ET.SubElement(properties, f"{word}tblLayout")
    layout.set(f"{word}type", "fixed")
    look = ET.SubElement(properties, f"{word}tblLook")
    look.set(f"{word}val", "0000")
    look.set(f"{word}firstRow", "0")
    look.set(f"{word}noHBand", "1")
    borders = ET.SubElement(properties, f"{word}tblBorders")
    for side, colour, size in (
        ("top", design.docx_values()["rule"].lstrip("#"), 4), ("left", accent, 24),
        ("bottom", design.docx_values()["rule"].lstrip("#"), 4), ("right", design.docx_values()["rule"].lstrip("#"), 4),
    ):
        border = ET.SubElement(borders, f"{word}{side}")
        border.set(f"{word}val", "single")
        border.set(f"{word}sz", str(size))
        border.set(f"{word}space", "0")
        border.set(f"{word}color", colour)
    margins = ET.SubElement(properties, f"{word}tblCellMar")
    for side, value in (("top", 80), ("left", 120), ("bottom", 80), ("right", 120)):
        margin = ET.SubElement(margins, f"{word}{side}")
        margin.set(f"{word}w", str(value))
        margin.set(f"{word}type", "dxa")
    grid = ET.SubElement(table, f"{word}tblGrid")
    column = ET.SubElement(grid, f"{word}gridCol")
    column.set(f"{word}w", str(width))
    row = ET.SubElement(table, f"{word}tr")
    row_properties = ET.SubElement(row, f"{word}trPr")
    ET.SubElement(row_properties, f"{word}cantSplit")
    cell = ET.SubElement(row, f"{word}tc")
    cell_properties = ET.SubElement(cell, f"{word}tcPr")
    cell_width = ET.SubElement(cell_properties, f"{word}tcW")
    cell_width.set(f"{word}w", str(width))
    cell_width.set(f"{word}type", "dxa")
    shade = ET.SubElement(cell_properties, f"{word}shd")
    shade.set(f"{word}val", "clear")
    shade.set(f"{word}color", "auto")
    shade.set(f"{word}fill", tint)
    for block in group:
        body.remove(block)
        cell.append(block)
    body.insert(position, table)
    body.insert(position, _spacer(word))
    body.insert(position + 2, _spacer(word))
    children.clear()
    children.extend(list(body))


def _style_docx_callouts(root: ET.Element, word: str) -> None:
    """Wrap each callout in a single-cell table.

    Paragraph borders cannot align across body paragraphs and list items: Word
    draws them at each paragraph's indent, so the left rule and the box edges
    drift. A one-cell table owns the edge, keeps the group together with
    ``cantSplit`` and lets the cell shading carry the palette tint.
    """

    values = design.docx_values()
    names = {styles["title"].replace(" ", ""): kind
             for kind, styles in design.docx_callout_styles().items()}
    body = root.find(f".//{word}body")
    if body is None:
        return
    children = list(body)
    index = 0
    while index < len(children):
        child = children[index]
        if child.tag != f"{word}p":
            index += 1
            continue
        style = _paragraph_style(child, word)
        kind = names.get(style)
        if kind is None:
            index += 1
            continue
        group = [child]
        cursor = index + 1
        end_marker = None
        while cursor < len(children):
            candidate = children[cursor]
            if candidate.tag == f"{word}tbl":
                group.append(candidate)
                cursor += 1
                continue
            if candidate.tag != f"{word}p":
                cursor += 1
                continue
            candidate_style = _paragraph_style(candidate, word)
            if candidate_style == "CalloutEnd":
                end_marker = candidate
                break
            if candidate_style.startswith("Heading") or candidate_style in names:
                break
            group.append(candidate)
            cursor += 1
        accent = values[f"callout_{kind}_accent"].lstrip("#")
        tint = values[f"callout_{kind}_tint"].lstrip("#")
        for block in group:
            if block.tag == f"{word}p":
                _clear_paragraph_box(block, word)
            else:
                _plain_callout_tables(block, word)
        _wrap_callout_box(root, body, children, index, group, word, accent, tint)
        if end_marker is not None:
            body.remove(end_marker)
        children.clear()
        children.extend(list(body))
        index += 3


def _normalise_cell_paragraph(paragraph: ET.Element, word: str) -> None:
    if _paragraph_style(paragraph, word) in {"ImageCaption", "TableCaption", "Caption", "ListingCaption"}:
        return
    properties = paragraph.findall(f"./{word}pPr")
    if not properties:
        properties = [ET.Element(f"{word}pPr")]
        paragraph.insert(0, properties[0])
    canonical = next(
        (value for value in properties if value.find(f"./{word}pStyle") is not None),
        properties[0],
    )
    for value in properties:
        if value is not canonical:
            paragraph.remove(value)
    for existing in canonical.findall(f"./{word}jc"):
        canonical.remove(existing)
    align = ET.SubElement(canonical, f"{word}jc")
    align.set(f"{word}val", "left")


def _left_align_docx_tables(root: ET.Element, word: str) -> None:
    """Keep table body text left-aligned; only captions are centred."""

    for table in root.iter(f"{word}tbl"):
        for cell in table.iter(f"{word}tc"):
            for paragraph in cell.findall(f"./{word}p"):
                _normalise_cell_paragraph(paragraph, word)


def _reflow_license_paragraph(paragraph: ET.Element, word: str) -> None:
    """Turn hard-wrapped licence lines into flowing text.

    A licensed text is stored as one code paragraph with a line break per
    source line. Short upstream lines leave half of the Word text column empty.
    Line breaks inside a paragraph become spaces; blank lines separate
    paragraphs inside the same shaded block.
    """

    lines: list[str] = []
    current = ""
    for run in paragraph.findall(f"./{word}r"):
        for node in run:
            if node.tag == f"{word}t":
                current += node.text or ""
            elif node.tag == f"{word}br":
                lines.append(current)
                current = ""
    lines.append(current)
    segments: list[str] = []
    text = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if text:
                segments.append(text.strip())
                text = ""
        else:
            text = f"{text} {stripped}".strip()
    if text:
        segments.append(text.strip())
    if not segments:
        return
    for child in list(paragraph):
        if child.tag != f"{word}pPr":
            paragraph.remove(child)
    for offset, value in enumerate(segments):
        run = ET.SubElement(paragraph, f"{word}r")
        properties = ET.SubElement(run, f"{word}rPr")
        style = ET.SubElement(properties, f"{word}rStyle")
        style.set(f"{word}val", "VerbatimChar")
        if offset:
            ET.SubElement(run, f"{word}br")
            ET.SubElement(run, f"{word}br")
        ET.SubElement(run, f"{word}t").text = value


def _reflow_docx_licenses(root: ET.Element, word: str) -> None:
    body = root.find(f".//{word}body")
    if body is None:
        return
    heading = ""
    for child in list(body):
        if child.tag == f"{word}p":
            style = _paragraph_style(child, word)
            text = "".join(node.text or "" for node in child.iter(f"{word}t")).strip()
            if style.startswith("Heading"):
                heading = text
            elif "License" in heading and style == "SourceCode":
                _reflow_license_paragraph(child, word)


def _format_table_headers(root: ET.Element, word: str) -> None:
    """Use direct header formatting and repeat only data table headers."""
    for table in root.iter(f"{word}tbl"):
        # Quarto wraps a captioned float in an outer one-cell table. Styling
        # that wrapper would paint the caption and, through the recursive run
        # walk, the nested content too. Leave wrappers alone; style the table
        # that actually holds the data.
        if any(node is not table and node.tag == f"{word}tbl" for node in table.iter()):
            continue
        rows = table.findall(f"{word}tr")
        if not rows:
            continue
        header = rows[0]
        properties = header.find(f"./{word}trPr")
        if properties is None:
            properties = ET.Element(f"{word}trPr")
            header.insert(0, properties)
        if properties.find(f"./{word}tblHeader") is None:
            ET.SubElement(properties, f"{word}tblHeader")
        for cell in header.findall(f"{word}tc"):
            cell_properties = cell.find(f"./{word}tcPr")
            if cell_properties is None:
                cell_properties = ET.Element(f"{word}tcPr")
                cell.insert(0, cell_properties)
            shade = cell_properties.find(f"./{word}shd")
            if shade is None:
                shade = ET.SubElement(cell_properties, f"{word}shd")
            shade.set(f"{word}val", "clear")
            shade.set(f"{word}color", "auto")
            shade.set(f"{word}fill", design.docx_values()["accent_solid"].lstrip("#"))
            for run in cell.iter(f"{word}r"):
                run_properties = run.find(f"./{word}rPr")
                if run_properties is None:
                    run_properties = ET.Element(f"{word}rPr")
                    run.insert(0, run_properties)
                if run_properties.find(f"./{word}b") is None:
                    ET.SubElement(run_properties, f"{word}b")
                if run_properties.find(f"./{word}bCs") is None:
                    ET.SubElement(run_properties, f"{word}bCs")
                colour = run_properties.find(f"./{word}color")
                if colour is None:
                    colour = ET.SubElement(run_properties, f"{word}color")
                colour.set(f"{word}val", design.docx_values()["on_solid"].lstrip("#"))


def _center_captions(root: ET.Element, word: str) -> None:
    for paragraph in root.iter(f"{word}p"):
        style = _paragraph_style(paragraph, word)
        if style not in {"ImageCaption", "TableCaption", "Caption", "ListingCaption"}:
            continue
        properties = paragraph.findall(f"./{word}pPr")
        if not properties:
            properties = [ET.Element(f"{word}pPr")]
            paragraph.insert(0, properties[0])
        canonical = next(
            (value for value in properties if value.find(f"./{word}pStyle") is not None),
            properties[0],
        )
        for value in properties:
            if value is not canonical:
                paragraph.remove(value)
        for existing in canonical.findall(f"./{word}jc"):
            canonical.remove(existing)
        align = ET.SubElement(canonical, f"{word}jc")
        align.set(f"{word}val", "center")


def _display_options(members: dict[str, bytes], root: ET.Element, word: str) -> None:
    background = ET.Element(f"{word}background")
    background.set(f"{word}color", design.docx_values()["canvas"].lstrip("#"))
    root.insert(0, background)
    settings = ET.fromstring(members["word/settings.xml"]) if "word/settings.xml" in members else None
    if settings is not None:
        for tag in ("updateFields", "displayBackgroundShape"):
            if settings.find(f"{word}{tag}") is None:
                ET.SubElement(settings, f"{word}{tag}")
        register_namespaces()
        order_properties(settings)
        members["word/settings.xml"] = ET.tostring(
            settings, encoding="utf-8", xml_declaration=True
        )


def _write_package(path: Path, members: dict[str, bytes]) -> None:
    temporary = path.with_suffix(".tmp.docx")
    with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
        for name, data in sorted(members.items()):
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    temporary.replace(path)


def prepare_docx(path: Path) -> None:
    """Prepare native fields and valid, deterministic Word layout properties."""
    word = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(members["word/document.xml"])
    members["word/fontTable.xml"] = font_table(members.get("word/fontTable.xml"))
    _format_table_headers(root, word)
    _style_docx_callouts(root, word)
    _left_align_docx_tables(root, word)
    _reflow_docx_licenses(root, word)
    add_indexes(root)
    _center_captions(root, word)
    _display_options(members, root, word)
    register_namespaces()
    order_properties(root)
    members["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    _write_package(path, members)
