"""Keep page-sized Word tables together using a real isolated pagination probe."""

from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import shutil
import re
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from .build_types import BuildError
from .docx_xml import W, register_namespaces, order_properties
from .docx_fields import _ensure_bookmark
from .docx_post import CALLOUT_STYLE, _write_package


CAPTION_STYLES = {"TableCaption", "ImageCaption"}


def release_callout_keeps(root: ET.Element) -> int:
    """Turn off keep-with-next on every paragraph inside a callout box.

    A callout box is one unsplittable row, so a keep inside it has nothing to
    hold together. Desktop Word, however, keeps a table row with what follows
    when a paragraph in the row keeps with next. The callout title styles carry
    keepNext, so every pitfall was chained through the spacers to its decision,
    and both moved to the next page when the decision did not fit (Owner Word
    check of 2026-11-25: 1.1.5, 1.2.13, 1.3.2). LibreOffice ignores keeps inside
    a table, so its render never showed it. An explicit ``w:val="0"`` overrides
    the style.
    """
    count = 0
    for table in root.iter(W + "tbl"):
        style = table.find(W + "tblPr/" + W + "tblStyle")
        if style is None or style.get(W + "val") != CALLOUT_STYLE:
            continue
        count += 1
        for p in table.iter(W + "p"):
            pp = p.find(W + "pPr")
            if pp is None:
                pp = ET.Element(W + "pPr")
                p.insert(0, pp)
            keep = pp.find(W + "keepNext")
            if keep is None:
                keep = ET.SubElement(pp, W + "keepNext")
            keep.set(W + "val", "0")
    return count


def candidates(root: ET.Element) -> list[tuple[ET.Element, ET.Element | None, bool]]:
    body = root.find(W + "body")
    if body is None:
        return []
    parents = {child: parent for parent in root.iter() for child in parent}
    found = []
    used = set()
    for table in root.iter(W + "tbl"):
        look = table.find(W + "tblPr/" + W + "tblLook")
        if look is None or look.get(W + "firstRow") not in {"1", "true", "on"}:
            continue
        children = list(parents[table])
        i = children.index(table)
        style = table.find(W + "tblPr/" + W + "tblStyle")
        if style is None or style.get(W + "val") not in {"Table", "TablePlain"}:
            continue
        caption = None
        after = True
        for direction in (1, -1):
            j = i + direction
            while 0 <= j < len(children):
                p = children[j]
                if p.tag != W + "p":
                    break
                ps = p.find(W + "pPr/" + W + "pStyle")
                # Quarto places a table float's caption in the same layout cell and
                # styles it ImageCaption, like a figure caption.
                if (
                    ps is not None
                    and ps.get(W + "val") in CAPTION_STYLES
                    and id(p) not in used
                ):
                    caption = p
                    after = direction == 1
                    break
                if "".join(p.itertext()).strip():
                    break
                j += direction
            if caption is not None:
                break
        if caption is not None:
            used.add(id(caption))
        found.append((table, caption, after))
    return found


def keep_rows(
    table: ET.Element,
    caption: ET.Element | None,
    after: bool,
    wrapper: ET.Element | None = None,
) -> None:
    rows = table.findall(W + "tr")
    for i, row in enumerate(rows):
        rp = row.find(W + "trPr")
        if rp is None:
            rp = ET.Element(W + "trPr")
            row.insert(0, rp)
        if rp.find(W + "cantSplit") is None:
            ET.SubElement(rp, W + "cantSplit")
        if i < len(rows) - 1 or (caption is not None and after):
            for p in row.iter(W + "p"):
                pp = p.find(W + "pPr")
                if pp is None:
                    pp = ET.Element(W + "pPr")
                    p.insert(0, pp)
                if pp.find(W + "keepNext") is None:
                    ET.SubElement(pp, W + "keepNext")
    # Quarto puts the table caption in the same cell of a one-row layout table.
    # Guard that wrapper row as a unit: keepNext alone does not cross the table boundary.
    if wrapper is not None:
        rp = wrapper.find(W + "trPr")
        if rp is None:
            rp = ET.Element(W + "trPr")
            wrapper.insert(0, rp)
        if rp.find(W + "cantSplit") is None:
            ET.SubElement(rp, W + "cantSplit")
    if caption is not None and not after:
        pp = caption.find(W + "pPr")
        if pp is None:
            pp = ET.Element(W + "pPr")
            caption.insert(0, pp)
        if pp.find(W + "keepNext") is None:
            ET.SubElement(pp, W + "keepNext")


def _style_name(paragraph: ET.Element) -> str:
    style = paragraph.find(W + "pPr/" + W + "pStyle")
    return style.get(W + "val", "") if style is not None else ""


def _set_keep_next(paragraph: ET.Element) -> None:
    properties = paragraph.find(W + "pPr")
    if properties is None:
        properties = ET.Element(W + "pPr")
        paragraph.insert(0, properties)
    keep = properties.find(W + "keepNext")
    if keep is None:
        keep = ET.SubElement(properties, W + "keepNext")
    keep.set(W + "val", "1")


def unwrap_float_layouts(root: ET.Element) -> tuple[int, int]:
    """Replace Quarto's one-cell float layout tables with their content.

    Quarto writes every captioned table and figure into a one-row, one-cell
    layout table that holds the data table or the image paragraph and the
    caption. Desktop Word does not carry a heading's keep-with-next into that
    wrapper, so a heading or a short introduction stays at the foot of a page
    while the float moves on; LibreOffice does carry it, so its rendering hid
    the defect. Unwrapped, the data table, its caption and the image paragraph
    are ordinary body blocks, as Pandoc writes an uncaptioned table, and the
    keep chain below reaches them in both engines. Callouts and other one-cell
    tables have no caption in their cell and are left alone.
    """
    body = root.find(W + "body")
    if body is None:
        return 0, 0
    tables = figures = 0
    for wrapper in list(body.findall(W + "tbl")):
        rows = wrapper.findall(W + "tr")
        if len(rows) != 1:
            continue
        cells = rows[0].findall(W + "tc")
        if len(cells) != 1:
            continue
        content = [child for child in cells[0] if child.tag != W + "tcPr"]
        captions = [
            child
            for child in content
            if child.tag == W + "p" and _style_name(child) in CAPTION_STYLES
        ]
        nested = [child for child in content if child.tag == W + "tbl"]
        images = [
            child
            for child in content
            if child.tag == W + "p" and child.find(".//" + W + "drawing") is not None
        ]
        if len(captions) != 1 or len(nested) + len(images) != 1:
            continue
        if nested:
            tables += 1
        else:
            figures += 1
            # A figure's image paragraph stays with the caption that follows it.
            if content.index(images[0]) < content.index(captions[0]):
                _set_keep_next(images[0])
        at = list(body).index(wrapper)
        body.remove(wrapper)
        for offset, child in enumerate(content):
            body.insert(at + offset, child)
    return tables, figures


def keep_section_intros(root: ET.Element) -> int:
    """Keep a heading's one short introduction with the heading that follows it.

    "9.3 Responsibilities …" followed by a two-sentence introduction and then
    "9.3.1 …" must not leave the heading and its introduction at the foot of a
    page. Headings already keep with the next paragraph; the introduction now
    keeps with the next heading, so the group moves only when it would be left
    alone. The limits are those of a float lead-in.
    """
    body = root.find(W + "body")
    if body is None:
        return 0
    blocks = [
        child
        for child in body
        if child.tag not in {W + "bookmarkStart", W + "bookmarkEnd"}
    ]
    changed = 0
    for before, intro, after in zip(blocks, blocks[1:], blocks[2:]):
        if not all(block.tag == W + "p" for block in (before, intro, after)):
            continue
        if not (
            _style_name(before).startswith("Heading")
            and _style_name(after).startswith("Heading")
        ):
            continue
        if _style_name(intro) not in {"", "Normal", "BodyText", "FirstParagraph", "Compact"}:
            continue
        text = "".join(t.text or "" for t in intro.iter(W + "t")).strip()
        if (
            not text
            or len(text.split()) > 80
            or len(text) > 600
            or intro.find(W + "pPr/" + W + "numPr") is not None
            or intro.find(".//" + W + "sectPr") is not None
            or any(br.get(W + "type") == "page" for br in intro.iter(W + "br"))
        ):
            continue
        _set_keep_next(intro)
        changed += 1
    return changed


def keep_leadins(root: ET.Element) -> int:
    """Keep headings and one short introduction with the following float."""
    changed = set()
    for container in root.iter():
        if container.tag not in {W + "body", W + "tc"}:
            continue
        children = list(container)
        for i, item in enumerate(children):
            is_float = item.find(".//" + W + "drawing") is not None
            if item.tag == W + "tbl":
                is_float = is_float or any(
                    look.get(W + "firstRow") in {"1", "true", "on"}
                    for look in item.iter(W + "tblLook")
                )
            if not is_float:
                continue
            lead = False
            for p in reversed(children[:i]):
                if p.tag in {W + "bookmarkStart", W + "bookmarkEnd"}:
                    continue
                if p.tag != W + "p" or p.find(".//" + W + "sectPr") is not None:
                    break
                if any(br.get(W + "type") == "page" for br in p.iter(W + "br")):
                    break
                text = "".join(t.text or "" for t in p.iter(W + "t")).strip()
                style = p.find(W + "pPr/" + W + "pStyle")
                name = style.get(W + "val", "") if style is not None else ""
                heading = name.startswith("Heading")
                if not heading and text:
                    if lead or name not in {
                        "",
                        "Normal",
                        "BodyText",
                        "FirstParagraph",
                        "Compact",
                    }:
                        break
                    if (
                        len(text.split()) > 80
                        or len(text) > 600
                        or p.find(W + "pPr/" + W + "numPr") is not None
                    ):
                        break
                    lead = True
                pp = p.find(W + "pPr")
                if pp is None:
                    pp = ET.Element(W + "pPr")
                    p.insert(0, pp)
                keep = pp.find(W + "keepNext")
                if keep is None:
                    keep = ET.SubElement(pp, W + "keepNext")
                keep.set(W + "val", "1")
                changed.add(id(p))
                if heading:
                    lead = True
    return len(changed)


def keep_fitting_tables(
    path: Path, fonts: Path, *, required: bool, compresslevel: int | None = 9
) -> dict[str, str]:
    from .docx_pages import export_pdf, font_environment, destination_pages

    with ZipFile(path) as archive:
        members = {n: archive.read(n) for n in archive.namelist()}
    root = ET.fromstring(members["word/document.xml"])
    unwrapped_tables, unwrapped_figures = unwrap_float_layouts(root)
    leads = keep_leadins(root)
    intros = keep_section_intros(root)
    lead_info = {
        "docx_float_layouts": (
            f"{unwrapped_tables} table and {unwrapped_figures} figure layout tables unwrapped"
        ),
        "docx_float_leadins": f"{leads} heading/lead-in paragraphs kept with floats",
        "docx_section_intros": f"{intros} section introductions kept with the next heading",
    }
    available = shutil.which("soffice") and shutil.which("pdfinfo")
    if required and not available:
        raise BuildError("Word table measurement requires LibreOffice and pdfinfo")
    tables = candidates(root)
    lead_info["docx_callout_keeps"] = "callout boxes released from keep-with-next: {}"
    if not tables or not available:
        lead_info["docx_callout_keeps"] = lead_info["docx_callout_keeps"].format(release_callout_keeps(root))
        order_properties(root)
        members["word/document.xml"] = ET.tostring(
            root, encoding="utf-8", xml_declaration=True
        )
        _write_package(path, members, compresslevel=compresslevel)
        return {
            **lead_info,
            "docx_table_fit": (
                "no data tables"
                if not tables
                else "not measured (LibreOffice or pdfinfo unavailable)"
            ),
        }
    probe = deepcopy(root)
    body = probe.find(W + "body")
    assert body is not None
    section = deepcopy(body.find(W + "sectPr"))
    if section is None:
        raise BuildError("Word table measurement requires page geometry")
    body.clear()
    parents = {child: parent for parent in root.iter() for child in parent}
    marks = set()
    boundaries = []
    for i, (table, caption, after) in enumerate(tables):
        # Quarto wraps a captioned float in a one-cell layout table. Measure that
        # wrapper, not a flattened table and caption: its cell padding is part of
        # the space the float occupies on the page.
        wrapper = parents.get(caption) if caption is not None else None
        if wrapper is not None:
            row = parents.get(wrapper)
            wrapper = parents.get(row) if row is not None and wrapper.tag == W + "tc" else None
            wrapper = wrapper if wrapper is not None and wrapper.tag == W + "tbl" else None
        if wrapper is not None:
            unit = deepcopy(wrapper)
            cell = unit.find(W + "tr/" + W + "tc")
            assert cell is not None
            t = cell.find(W + "tbl")
            assert t is not None
            c = next(
                (
                    p
                    for p in cell.iter(W + "p")
                    if (style := p.find(W + "pPr/" + W + "pStyle")) is not None
                    and style.get(W + "val") in CAPTION_STYLES
                ),
                None,
            )
            blocks = [unit]
        else:
            t = deepcopy(table)
            c = deepcopy(caption) if caption is not None else None
            blocks = (
                [c, t] if c is not None and not after else [t, c] if c is not None else [t]
            )
        for block in blocks:
            body.append(block)
        first = next(t.iter(W + "p"))
        start = _ensure_bookmark(first, probe, f"TableFitStart{i}")
        ends = []
        # Every final-row cell matters: the final XML cell need not be the tallest.
        last_row = t.findall(W + "tr")[-1]
        tail = [list(cell.iter(W + "p"))[-1] for cell in last_row.findall(W + "tc")]
        if c is not None and after:
            tail.append(c)
        for j, p in enumerate(tail):
            name = _ensure_bookmark(p, probe, f"TableFitEnd{i}_{j}")
            marker = next(
                n for n in p.findall(W + "bookmarkStart") if n.get(W + "name") == name
            )
            end = next(
                n
                for n in p.findall(W + "bookmarkEnd")
                if n.get(W + "id") == marker.get(W + "id")
            )
            p.remove(marker)
            p.remove(end)
            # LO discards empty end bookmarks. Mark the last actual character,
            # preserving its run formatting and its position on wrapped lines.
            text = next(
                (
                    n
                    for n in reversed(list(p.iter(W + "t")))
                    if n.text and n.text.strip()
                ),
                None,
            )
            if text is None:
                run = ET.SubElement(p, W + "r")
                text = ET.SubElement(run, W + "t")
                text.text = "\u2060"
            owners = {child: parent for parent in p.iter() for child in parent}
            run = owners[text]
            container = owners[run]
            match = re.search(r"\S(?=\s*$)", text.text)
            assert match is not None
            tail = text.text[match.start() :]
            text.text = text.text[: match.start()]
            last_run = ET.Element(W + "r")
            rp = run.find(W + "rPr")
            if rp is not None:
                last_run.append(deepcopy(rp))
            final = ET.SubElement(last_run, W + "t", dict(text.attrib))
            final.text = tail
            position = list(container).index(run) + 1
            for offset, node in enumerate([marker, last_run, end]):
                container.insert(position + offset, node)
            ends.append(name)
        marks.update([start, *ends])
        boundaries.append((start, ends))
        # Section breaks after each sample give the next table the entire body,
        # without adding a measurement paragraph above its first row.
        sep = ET.SubElement(body, W + "p")
        props = ET.SubElement(sep, W + "pPr")
        s = deepcopy(section)
        kind = s.find(W + "type")
        if kind is None:
            kind = ET.SubElement(s, W + "type")
        kind.set(W + "val", "nextPage")
        props.append(s)
    body.append(deepcopy(section))
    with tempfile.TemporaryDirectory(prefix="table-fit-", dir=path.parent) as tmp:
        directory = Path(tmp)
        env = font_environment(fonts, directory)
        register_namespaces()
        order_properties(probe)
        probe_members = dict(members)
        probe_members["word/document.xml"] = ET.tostring(
            probe, encoding="utf-8", xml_declaration=True
        )
        probe_path = directory / "probe.docx"
        _write_package(probe_path, probe_members, compresslevel=compresslevel)
        pdf = export_pdf(probe_path, directory / "pdf", env=env)
        pages = destination_pages(pdf, marks)
    kept = 0
    for i, (table, caption, after) in enumerate(tables):
        start, ends = boundaries[i]
        if all(pages[start] == pages[end] for end in ends):
            wrapper = None
            cell = parents.get(caption) if caption is not None else None
            if cell is not None and cell.tag == W + "tc":
                row = parents.get(cell)
                if row is not None and row.tag == W + "tr":
                    wrapper = row
            keep_rows(table, caption, after, wrapper)
            kept += 1
    lead_info["docx_callout_keeps"] = lead_info["docx_callout_keeps"].format(release_callout_keeps(root))
    order_properties(root)
    members["word/document.xml"] = ET.tostring(
        root, encoding="utf-8", xml_declaration=True
    )
    _write_package(path, members, compresslevel=compresslevel)
    return {
        **lead_info,
        "docx_table_fit": f"{kept}/{len(tables)} page-sized tables kept together (isolated LibreOffice measurement)",
    }
