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
from .docx_post import _write_package


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
                if (
                    ps is not None
                    and ps.get(W + "val") == "TableCaption"
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


def keep_rows(table: ET.Element, caption: ET.Element | None, after: bool) -> None:
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
    if caption is not None and not after:
        pp = caption.find(W + "pPr")
        if pp is None:
            pp = ET.Element(W + "pPr")
            caption.insert(0, pp)
        if pp.find(W + "keepNext") is None:
            ET.SubElement(pp, W + "keepNext")


def keep_fitting_tables(
    path: Path, fonts: Path, *, required: bool, compresslevel: int | None = 9
) -> dict[str, str]:
    from .docx_pages import export_pdf, font_environment, destination_pages

    if not shutil.which("soffice") or not shutil.which("pdfinfo"):
        if required:
            raise BuildError("Word table measurement requires LibreOffice and pdfinfo")
        return {"docx_table_fit": "not measured (LibreOffice or pdfinfo unavailable)"}
    with ZipFile(path) as archive:
        members = {n: archive.read(n) for n in archive.namelist()}
    root = ET.fromstring(members["word/document.xml"])
    tables = candidates(root)
    if not tables:
        return {"docx_table_fit": "no data tables"}
    probe = deepcopy(root)
    body = probe.find(W + "body")
    assert body is not None
    section = deepcopy(body.find(W + "sectPr"))
    if section is None:
        raise BuildError("Word table measurement requires page geometry")
    body.clear()
    marks = set()
    boundaries = []
    for i, (table, caption, after) in enumerate(tables):
        t = deepcopy(table)
        c = deepcopy(caption) if caption is not None else None
        blocks = (
            [c, t] if c is not None and not after else [t, c] if c is not None else [t]
        )
        for block in blocks:
            body.append(block)
        first = next(blocks[0].iter(W + "p")) if blocks[0].tag != W + "p" else blocks[0]
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
            parents = {child: parent for parent in p.iter() for child in parent}
            run = parents[text]
            container = parents[run]
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
            keep_rows(table, caption, after)
            kept += 1
    order_properties(root)
    members["word/document.xml"] = ET.tostring(
        root, encoding="utf-8", xml_declaration=True
    )
    _write_package(path, members, compresslevel=compresslevel)
    return {
        "docx_table_fit": f"{kept}/{len(tables)} page-sized tables kept together (isolated LibreOffice measurement)"
    }
