#!/usr/bin/env python3
"""Generate the packaged DOCX reference document from the style table below.

This replaces the former document derived from the Pandoc default, so no Pandoc
template part is copied. The style identifiers are the ones Pandoc looks up by
name, and a few spacing values match its defaults. Pandoc reads these styles and
the page setup when building the DOCX edition.

Usage: python3 tools/scripts/generate_reference_docx.py [output.docx]
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from handbook_toolkit.design import docx_callout_styles, docx_values
from handbook_toolkit.docx_fonts import font_table
from handbook_toolkit.docx_xml import W, register_namespaces

TOKENS = Path(__file__).resolve().parents[1] / "src/handbook_toolkit/design/tokens.json"
_TOKENS = json.loads(TOKENS.read_text(encoding="utf-8"))
_PRINT = {role: values["print"].lstrip("#") for role, values in _TOKENS["color"].items()}
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1] / "src/handbook_toolkit/render_data/docx/reference.docx"
)
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
BODY_FONT = _TOKENS["type"]["brand"]["docx_text_family"]
DISPLAY_FONT = _TOKENS["type"]["brand"]["docx_display_family"]
CODE_FONT = _TOKENS["type"]["code"]["print_family"]
INK = _PRINT["text"]
MUTED = _PRINT["muted"]
BLUE = _PRINT["accent"]
RULE = _PRINT["border"]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def fonts(name: str) -> str:
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}" w:cs="{name}"/>'


def run(*, font=None, bold=None, italic=False, color=None, size=None, tracking=None) -> str:
    # Element order follows the CT_RPr schema sequence.
    parts = []
    if font:
        parts.append(fonts(font))
    if bold is True:
        parts.append("<w:b/><w:bCs/>")
    if bold is False:
        parts.append('<w:b w:val="0"/><w:bCs w:val="0"/>')
    if italic:
        parts.append("<w:i/><w:iCs/>")
    if color:
        parts.append(f'<w:color w:val="{color}"/>')
    if tracking:
        parts.append(f'<w:spacing w:val="{tracking}"/>')
    if size:
        parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    return f"<w:rPr>{''.join(parts)}</w:rPr>" if parts else ""


def para(*, keep=False, lines=False, pagebreak=False, rule=None, left_rule=None, shade=None, before=None, after=None, line=None,
         left=None, right=None, center=False, outline=None, tab=None) -> str:
    # Element order follows the CT_PPr schema sequence.
    parts = []
    if keep:
        parts.append("<w:keepNext/>")
    if lines:
        parts.append("<w:keepLines/>")
    if pagebreak:
        parts.append("<w:pageBreakBefore/>")
    borders = []
    if left_rule:
        width, space, color = left_rule
        borders.append(f'<w:left w:val="single" w:sz="{width}" w:space="{space}" w:color="{color}"/>')
    if rule == "none":
        borders.append('<w:bottom w:val="nil"/>')
    elif rule:
        width, space, color = rule
        borders.append(f'<w:bottom w:val="single" w:sz="{width}" w:space="{space}" w:color="{color}"/>')
    if borders:
        parts.append(f"<w:pBdr>{''.join(borders)}</w:pBdr>")
    if shade:
        parts.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    if tab:
        parts.append(f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{tab}"/></w:tabs>')
    if before is not None or after is not None or line is not None:
        attrs = ""
        if before is not None:
            attrs += f' w:before="{before}"'
        if after is not None:
            attrs += f' w:after="{after}"'
        if line is not None:
            attrs += f' w:line="{line}" w:lineRule="auto"'
        parts.append(f"<w:spacing{attrs}/>")
    if left is not None or right is not None:
        attrs = ""
        if left is not None:
            attrs += f' w:left="{left}"'
        if right is not None:
            attrs += f' w:right="{right}"'
        parts.append(f"<w:ind{attrs}/>")
    if center:
        parts.append('<w:jc w:val="center"/>')
    if outline is not None:
        parts.append(f'<w:outlineLvl w:val="{outline}"/>')
    return f"<w:pPr>{''.join(parts)}</w:pPr>" if parts else ""


def paragraph_style(style_id, name, based="Normal", follow=None, ppr="", rpr="", custom=False, default=False):
    flags = (' w:default="1"' if default else "") + (' w:customStyle="1"' if custom else "")
    based_xml = f'<w:basedOn w:val="{based}"/>' if based else ""
    next_xml = f'<w:next w:val="{follow}"/>' if follow else ""
    return (
        f'<w:style w:type="paragraph"{flags} w:styleId="{style_id}"><w:name w:val="{name}"/>'
        f"{based_xml}{next_xml}<w:qFormat/>{ppr}{rpr}</w:style>"
    )


def character_style(style_id, name, based="DefaultParagraphFont", rpr="", custom=False):
    flags = ' w:customStyle="1"' if custom else ""
    return (
        f'<w:style w:type="character"{flags} w:styleId="{style_id}"><w:name w:val="{name}"/>'
        f'<w:basedOn w:val="{based}"/>{rpr}</w:style>'
    )


def table_style() -> str:
    root = ET.Element("styles")
    values = {key: value.lstrip("#") for key, value in docx_values().items()}
    for identifier, name in (("Table", "Table"), ("TablePlain", "Table Plain"), ("CalloutBox", "Callout Box")):
        style = ET.SubElement(root, W + "style", {W + "type": "table", W + "styleId": identifier})
        if identifier == "Table":
            style.set(W + "default", "1")
        ET.SubElement(style, W + "name", {W + "val": name})
        ET.SubElement(style, W + "qFormat")
        properties = ET.SubElement(style, W + "tblPr")
        ET.SubElement(properties, W + "tblInd", {W + "w": "0", W + "type": "dxa"})
        borders = ET.SubElement(properties, W + "tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            attrs = {W + "val": "nil"}
            if side == "insideH" and identifier != "CalloutBox":
                attrs = {W + "val": "single", W + "sz": "4", W + "space": "0", W + "color": values["rule"]}
            ET.SubElement(borders, W + side, attrs)
        margins = ET.SubElement(properties, W + "tblCellMar")
        for side, width in (("top", 0), ("left", 60), ("bottom", 0), ("right", 60)):
            ET.SubElement(margins, W + side, {W + "w": str(width), W + "type": "dxa"})
        if identifier == "CalloutBox":
            continue
        first = ET.SubElement(style, W + "tblStylePr", {W + "type": "firstRow"})
        runs = ET.SubElement(first, W + "rPr")
        ET.SubElement(runs, W + "b")
        ET.SubElement(runs, W + "bCs")
        ET.SubElement(runs, W + "color", {W + "val": values["on_solid"]})
        ET.SubElement(ET.SubElement(first, W + "tcPr"), W + "shd", {
            W + "val": "clear", W + "color": "auto", W + "fill": values["accent_solid"]})
        if identifier == "Table":
            for band, color in (("band1Horz", values["canvas"]), ("band2Horz", values["stripe"])):
                conditional = ET.SubElement(style, W + "tblStylePr", {W + "type": band})
                ET.SubElement(ET.SubElement(conditional, W + "tcPr"), W + "shd", {
                    W + "val": "clear", W + "color": "auto", W + "fill": color})
    register_namespaces()
    return "".join(ET.tostring(child, encoding="unicode") for child in root)


def heading_styles() -> list[str]:
    sizes = [
        (0, 160, 40, INK), (240, 80, 30, INK), (200, 60, 24, INK), (160, 40, 21, MUTED),
        (80, 40, 21, MUTED), (40, 0, 21, MUTED), (40, 0, 21, MUTED), (0, 0, 21, MUTED), (0, 0, 21, MUTED),
    ]
    return [
        paragraph_style(
            f"Heading{level}", f"heading {level}", follow="BodyText",
            ppr=para(keep=True, lines=True, pagebreak=(level == 1), before=before, after=after, outline=level - 1),
            rpr=run(font=DISPLAY_FONT if level <= 2 else BODY_FONT, bold=True, color=color, size=size),
        )
        for level, (before, after, size, color) in enumerate(sizes, start=1)
    ]


CALLOUTS = {
    name.title(): (
        values["accent"]["print"].lstrip("#"),
        values["tint"]["print"].lstrip("#"),
    )
    for name, values in _TOKENS["callout"].items()
}


def callout_styles() -> list[str]:
    styles = []
    for name, (accent, tint) in CALLOUTS.items():
        styles.append(paragraph_style(
            f"Callout{name}Title", docx_callout_styles()[name.lower()]["title"], follow=f"Callout{name}Body",
            ppr=para(keep=True, lines=True, before=0, after=0),
            rpr=run(font=DISPLAY_FONT, bold=True, color=accent, size=21), custom=True,
        ))
        styles.append(paragraph_style(
            f"Callout{name}Body", docx_callout_styles()[name.lower()]["body"], based="BodyText", follow="BodyText",
            ppr=para(before=0, after=80),
            rpr=run(color=INK, size=21), custom=True,
        ))
    return styles


def styles_xml() -> str:
    body = run(font=BODY_FONT, color=INK, size=21)
    items = [
        paragraph_style("Normal", "Normal", based=None, default=True,
                        ppr=para(before=0, after=120, line=276), rpr=body),
        paragraph_style("BodyText", "Body Text", ppr=para(before=0, after=160, line=276)),
        paragraph_style("FirstParagraph", "First Paragraph", based="BodyText", follow="BodyText",
                        ppr=para(before=0, after=160), custom=True),
        paragraph_style("Compact", "Compact", based="BodyText",
                        ppr=para(before=40, after=40), rpr=run(size=21), custom=True),
        paragraph_style("Title", "Title", follow="BodyText",
                        ppr=para(keep=True, rule=(12, 10, BLUE), before=2200, after=160, line=240, center=True),
                        rpr=run(font=DISPLAY_FONT, bold=True, color=INK, size=56)),
        paragraph_style("Subtitle", "Subtitle", based="Title", follow="BodyText",
                        ppr=para(rule="none", before=0, after=200, center=True),
                        rpr=run(font=DISPLAY_FONT, bold=False, color=MUTED, size=26)),
        paragraph_style("Author", "Author", based="Title", follow="BodyText",
                        ppr=para(keep=True, rule="none", before=0, after=40, center=True),
                        rpr=run(bold=False, color=MUTED, size=24), custom=True),
        paragraph_style("Date", "Date", based="Title", follow="BodyText",
                        ppr=para(keep=True, rule="none", before=0, after=240, center=True),
                        rpr=run(bold=False, color=MUTED, size=21)),
        paragraph_style("AbstractTitle", "Abstract Title", follow="Abstract",
                        ppr=para(keep=True, lines=True, before=300, after=0, center=True),
                        rpr=run(font=DISPLAY_FONT, bold=True, size=20), custom=True),
        paragraph_style("Abstract", "Abstract", follow="BodyText",
                        ppr=para(keep=True, lines=True, before=100, after=300),
                        rpr=run(size=20), custom=True),
        paragraph_style("Bibliography", "Bibliography", follow="Bibliography"),
        *heading_styles(),
        paragraph_style("BlockText", "Block Text", based="BodyText", follow="BodyText",
                        ppr=para(before=120, after=120, left=360, right=360),
                        rpr=run(italic=True, color=MUTED)),
        paragraph_style("SourceCode", "Source Code", based="Normal", follow="Normal",
                        ppr=para(before=120, after=120, shade=_PRINT["code"].lstrip("#")),
                        rpr=run(font=CODE_FONT, color=INK, size=19), custom=True),
        paragraph_style("FootnoteText", "Footnote Text", follow="FootnoteText"),
        paragraph_style("FootnoteBlockText", "Footnote Block Text", based="FootnoteText", follow="FootnoteText",
                        ppr=para(before=100, after=100, left=480, right=480)),
        paragraph_style("DefinitionTerm", "Definition Term", follow="Definition",
                        ppr=para(keep=True, lines=True, after=0), rpr=run(bold=True), custom=True),
        paragraph_style("Definition", "Definition", custom=True),
        paragraph_style("Caption", "Caption", follow="BodyText", ppr=para(before=60, after=160),
                        rpr=run(italic=True, color=MUTED, size=18)),
        paragraph_style("TableCaption", "Table Caption", based="Caption",
                        ppr=para(lines=True, before=60, after=200, center=True), custom=True),
        paragraph_style("ImageCaption", "Image Caption", based="Caption",
                        ppr=para(before=60, after=200, center=True), custom=True),
        paragraph_style("Figure", "Figure", custom=True),
        paragraph_style("CaptionedFigure", "Captioned Figure", based="Figure", ppr=para(keep=True), custom=True),
        *callout_styles(),
        paragraph_style("TOCHeading", "TOC Heading", based="Heading1", follow="BodyText",
                        ppr=para(keep=True, before=0, after=240, outline=9),
                        rpr=run(font=DISPLAY_FONT, bold=False, color=INK, size=36)),
        paragraph_style("TOC1", "toc 1", follow="Normal", ppr=para(tab=9400, before=40, after=20)),
        paragraph_style("TOC3", "toc 3", based="TOC1", follow="Normal",
                        ppr=para(tab=9400, before=20, after=20, left=480), rpr=run(size=19)),
        paragraph_style("TOC2", "toc 2", based="TOC1", follow="Normal",
                        ppr=para(tab=9400, before=20, after=20, left=240), rpr=run(size=19)),
        paragraph_style("CoverSeries", "Cover Series", follow="BodyText",
                        ppr=para(rule=(6, 8, INK), before=2400, after=120, center=True),
                        rpr=run(bold=True, tracking=40, size=24), custom=True),
        paragraph_style("CoverMeta", "Cover Meta", follow="BodyText",
                        ppr=para(before=0, after=60, center=True), rpr=run(color=MUTED, size=20), custom=True),
        paragraph_style("CoverNote", "Cover Note", follow="BodyText",
                        ppr=para(before=280, after=120, left=720, right=720, center=True),
                        rpr=run(italic=True, color=MUTED, size=18), custom=True),
        '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
        '<w:name w:val="Default Paragraph Font"/></w:style>',
        character_style("BodyTextChar", "Body Text Char", custom=True),
        character_style("VerbatimChar", "Verbatim Char", rpr=run(font=CODE_FONT, color=INK, size=19), custom=True),
        character_style("SectionNumber", "Section Number", based="BodyTextChar", custom=True),
        character_style("FootnoteReference", "Footnote Reference", based="BodyTextChar",
                        rpr='<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'),
        character_style("Hyperlink", "Hyperlink", rpr=f'<w:rPr><w:color w:val="{BLUE}"/><w:u w:val="none"/></w:rPr>'),
        table_style(),
    ]
    defaults = (
        f"<w:docDefaults><w:rPrDefault>{body}</w:rPrDefault>"
        '<w:pPrDefault><w:pPr><w:spacing w:after="200"/></w:pPr></w:pPrDefault></w:docDefaults>'
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{WORD_NS}">{defaults}{"".join(items)}</w:styles>'


def document_xml() -> str:
    sample = "".join(
        f'<w:p><w:pPr><w:pStyle w:val={quoteattr(style)}/></w:pPr><w:r><w:t>{style}</w:t></w:r></w:p>'
        for style in ("Title", "Heading1", "BodyText")
    )
    section = (
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1361" w:right="1247" w:bottom="1361" w:left="1247" '
        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{WORD_NS}"><w:body>{sample}{section}</w:body></w:document>'


PARTS = {
    "[Content_Types].xml": (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    ),
    "_rels/.rels": (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    ),
    "word/_rels/document.xml.rels": (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    ),
}


def write_reference(output: Path) -> None:
    parts = {**PARTS, "word/document.xml": document_xml(), "word/styles.xml": styles_xml()}
    parts["word/fontTable.xml"] = font_table().decode("utf-8")
    content_types = ET.fromstring(parts["[Content_Types].xml"])
    ct = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    ET.SubElement(content_types, ct + "Override", {
        "PartName": "/word/fontTable.xml",
        "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"})
    parts["[Content_Types].xml"] = ET.tostring(content_types, encoding="unicode")
    relationships = ET.fromstring(parts["word/_rels/document.xml.rels"])
    rel = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    ET.SubElement(relationships, rel + "Relationship", {
        "Id": "rIdFonts", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable",
        "Target": "fontTable.xml"})
    parts["word/_rels/document.xml.rels"] = ET.tostring(relationships, encoding="unicode")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(parts):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, parts[name].encode("utf-8"))


if __name__ == "__main__":
    write_reference(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT)
