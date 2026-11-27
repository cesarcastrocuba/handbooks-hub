"""Word callouts are never split across pages; a pitfall and its decision are separate boxes."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from handbook_toolkit.docx_pages import export_pdf, font_environment
from handbook_toolkit.docx_post import CALLOUT_STYLE, _wrap_callout_box
from handbook_toolkit.docx_tables import keep_fitting_tables, keep_leadins, release_callout_keeps
from unittest.mock import patch
import zipfile
from handbook_toolkit.docx_xml import W
from test_figure_place import FONTS, _package, paragraph


def boxed(body, title, *content):
    """Wrap a title paragraph and its content as the post-processor does."""
    document = ET.Element(W + "document")
    document.append(body)
    group = [title, *content]
    children = list(body)
    _wrap_callout_box(document, body, children, children.index(title), group, W, "000000", "FFFFFF")
    boxes = [t for t in body.findall(W + "tbl")]
    return document, boxes[-1]


def _keep(paragraph, value="1"):
    properties = paragraph.find(W + "pPr")
    if properties is None:
        properties = ET.Element(W + "pPr")
        paragraph.insert(0, properties)
    ET.SubElement(properties, W + "keepNext", {W + "val": value})
    return paragraph


def data_table(parent, style="Table", keep_first=False):
    table = ET.SubElement(parent, W + "tbl")
    properties = ET.SubElement(table, W + "tblPr")
    ET.SubElement(properties, W + "tblStyle", {W + "val": style})
    ET.SubElement(properties, W + "tblLook", {W + "firstRow": "1"})
    for i in range(2):
        cell = ET.SubElement(ET.SubElement(table, W + "tr"), W + "tc")
        paragraph_ = paragraph(cell, f"CELL{i}")
        if i == 0 and keep_first:
            _keep(paragraph_)
    return table


def callout_table(parent):
    table = ET.SubElement(parent, W + "tbl")
    properties = ET.SubElement(table, W + "tblPr")
    ET.SubElement(properties, W + "tblStyle", {W + "val": CALLOUT_STYLE})
    row = ET.SubElement(table, W + "tr")
    ET.SubElement(ET.SubElement(row, W + "trPr"), W + "cantSplit")
    return ET.SubElement(row, W + "tc")


class CalloutBoxTests(unittest.TestCase):
    def test_a_box_is_one_row_that_never_splits(self):
        body = ET.Element(W + "body")
        title = paragraph(body, "Common Pitfall", "CalloutWarningTitle")
        text = paragraph(body, "A warning.")
        _, box = boxed(body, title, text)
        rows = box.findall(W + "tr")
        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0].find(W + "trPr/" + W + "cantSplit"))


    def test_no_paragraph_in_a_box_keeps_with_what_follows(self):
        # Desktop Word keeps a row with the next paragraph when a paragraph in the
        # row keeps with next; the callout title styles carry keepNext, so a pitfall
        # was dragged to the next page with its decision (Owner check 2026-11-25).
        body = ET.Element(W + "body")
        title = paragraph(body, "Common Pitfall", "CalloutWarningTitle")
        text = paragraph(body, "A warning.")
        ET.SubElement(text.find(W + "pPr") if text.find(W + "pPr") is not None
                      else ET.SubElement(text, W + "pPr"), W + "keepNext")
        document, box = boxed(body, title, text)
        self.assertEqual(release_callout_keeps(document), 1)
        for p in box.iter(W + "p"):
            keep = p.find(W + "pPr/" + W + "keepNext")
            self.assertIsNotNone(keep, "an explicit off value is needed to override the style")
            self.assertEqual(keep.get(W + "val"), "0")


    def test_nothing_before_a_box_is_kept_with_it(self):
        # A decision holds a table with a header row; keep_leadins took the box for
        # a float and chained the spacers (and a short paragraph) to it, so they
        # moved with it and left an empty line at the top of the page (Owner Word
        # check 2026-11-25: after Table 1.5 and Figure 2.1).
        body = ET.Element(W + "body")
        text = paragraph(body, "A short paragraph before the decision.")
        title = paragraph(body, "Decision & Trade-off", "CalloutImportantTitle")
        inner = ET.SubElement(body, W + "tbl")
        ET.SubElement(ET.SubElement(inner, W + "tblPr"), W + "tblLook", {W + "firstRow": "1"})
        ET.SubElement(ET.SubElement(ET.SubElement(inner, W + "tr"), W + "tc"), W + "p")
        document, box = boxed(body, title, inner)
        keep_leadins(document)
        for p in body.findall(W + "p"):
            self.assertIsNone(p.find(W + "pPr/" + W + "keepNext"),
                              "".join(t.text or "" for t in p.iter(W + "t")) or "spacer")


    def test_the_box_lands_where_the_callout_was(self):
        body = ET.Element(W + "body")
        paragraph(body, "BEFORE")
        title = paragraph(body, "TITLE", "CalloutWarningTitle")
        text = paragraph(body, "CONTENT")
        paragraph(body, "AFTER")
        document = ET.Element(W + "document")
        document.append(body)
        children = list(body)
        _wrap_callout_box(
            document, body, children, children.index(title), [title, text],
            W, "000000", "FFFFFF",
        )
        self.assertEqual(
            [node.tag.replace(W, "") for node in body],
            ["p", "p", "tbl", "p", "p"],
        )
        self.assertEqual(
            ["".join(t.text or "" for t in node.iter(W + "t")) for node in body],
            ["BEFORE", "", "TITLECONTENT", "", "AFTER"],
        )
        self.assertEqual(
            "".join(t.text or "" for t in body.find(W + "tbl").iter(W + "t")),
            "TITLECONTENT",
        )

    def test_a_data_table_inside_a_box_does_not_chain_the_box(self):
        # keep_leadins treated the box's cell as an ordinary container, so a
        # nested data table made it keep the box's title with the float. That
        # keep was then cleared by release_callout_keeps, but it was counted as
        # a float lead-in and could drag the box before the release ran.
        body = ET.Element(W + "body")
        cell = callout_table(body)
        paragraph(cell, "Decision & Trade-off", "CalloutImportantTitle")
        lead_in = paragraph(cell, "Each option has a cost.")
        data_table(cell, "TablePlain")
        document = ET.Element(W + "document")
        document.append(body)
        self.assertEqual(keep_leadins(document), 0)
        self.assertIsNone(lead_in.find(W + "pPr/" + W + "keepNext"))

    @unittest.skipUnless(
        shutil.which("soffice") and shutil.which("pdfinfo"),
        "LibreOffice and Poppler are required for the table measurement",
    )
    def test_the_measured_path_releases_the_box_including_a_nested_table(self):
        styles = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:style w:type="paragraph" w:styleId="CalloutWarningTitle">'
            '<w:name w:val="Callout Warning Title"/><w:pPr><w:keepNext/></w:pPr>'
            "</w:style></w:styles>"
        )
        body = ET.Element(W + "body")
        data_table(body)  # a candidate, so the normal measured path runs
        cell = callout_table(body)
        title = paragraph(cell, "Common Pitfall", "CalloutWarningTitle")
        body_text = paragraph(cell, "A warning.")
        data_table(cell, "TablePlain", keep_first=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, body, styles=styles)
            report = keep_fitting_tables(path, FONTS, required=True)
            root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
        self.assertEqual(
            report["docx_callout_keeps"],
            "callout boxes released from keep-with-next: 1",
        )
        self.assertEqual(
            report["docx_float_leadins"],
            "0 heading/lead-in paragraphs kept with floats",
        )
        self.assertIn("isolated LibreOffice measurement", report["docx_table_fit"])
        box = next(
            table
            for table in root.iter(W + "tbl")
            if (style := table.find(W + "tblPr/" + W + "tblStyle")) is not None
            and style.get(W + "val") == CALLOUT_STYLE
        )

        def paragraph_with(text):
            return next(
                p
                for p in root.iter(W + "p")
                if text in "".join(t.text or "" for t in p.iter(W + "t"))
            )

        for text in ("Common Pitfall", "A warning."):
            keep = paragraph_with(text).find(W + "pPr/" + W + "keepNext")
            self.assertIsNotNone(keep)
            self.assertEqual(keep.get(W + "val"), "0")
        # A nested header row is still a paragraph of the outer box row; Word
        # would chain the box through it, so it is released too.
        inner = next(table for table in box.iter(W + "tbl") if table is not box)
        keep = inner.find(W + "tr/" + W + "tc/" + W + "p/" + W + "pPr/" + W + "keepNext")
        self.assertIsNotNone(keep)
        self.assertEqual(keep.get(W + "val"), "0")

    def test_the_build_step_releases_the_keeps(self):
        # The pipeline, not only the function: both paths of keep_fitting_tables.
        def built(**options):
            body = ET.Element(W + "body")
            title = paragraph(body, "Common Pitfall", "CalloutWarningTitle")
            boxed(body, title, paragraph(body, "A warning."))
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "book.docx"
                _package(path, body)
                with patch("handbook_toolkit.docx_tables.shutil.which", return_value=None):
                    report = keep_fitting_tables(path, FONTS, required=False, **options)
                root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
            return report, root
        report, root = built()
        self.assertEqual(report["docx_callout_keeps"], "callout boxes released from keep-with-next: 1")
        keeps = [p.find(W + "pPr/" + W + "keepNext") for t in root.iter(W + "tbl") for p in t.iter(W + "p")]
        self.assertTrue(keeps and all(k is not None and k.get(W + "val") == "0" for k in keeps))


@unittest.skipUnless(
    shutil.which("soffice") and shutil.which("pdftotext"),
    "LibreOffice and Poppler are required for the pagination check",
)
class LibreOfficeTests(unittest.TestCase):
    SENTENCE = "Body text that fills the page and keeps the reader moving. " * 9

    def pages(self, body):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, body)
            pdf = export_pdf(path, Path(tmp) / "pdf", env=font_environment(FONTS, Path(tmp)))
            return subprocess.run(["pdftotext", str(pdf), "-"], check=True, capture_output=True,
                                  text=True).stdout.split("\f")

    def test_a_box_that_does_not_fit_moves_whole(self):
        body = ET.Element(W + "body")
        for _ in range(7):  # leaves about 11 lines for a 30-line pitfall
            paragraph(body, self.SENTENCE)
        title = paragraph(body, "PITFALLTITLE", "CalloutWarningTitle")
        lines = [paragraph(body, f"LINE{i} " + "A warning about a common mistake and its cost. " * 3)
                 for i in range(10)]
        boxed(body, title, *lines)
        pages = self.pages(body)
        self.assertNotIn("PITFALLTITLE", pages[0])
        self.assertIn("LINE0", pages[1])
        self.assertIn("LINE9", pages[1])

    def test_a_pitfall_that_fits_stays_when_its_decision_moves(self):
        body = ET.Element(W + "body")
        for _ in range(6):
            paragraph(body, self.SENTENCE)
        title = paragraph(body, "PITFALLTITLE", "CalloutWarningTitle")
        boxed(body, title, paragraph(body, "A short warning. " * 6))
        decision = paragraph(body, "DECISIONTITLE", "CalloutImportantTitle")
        lines = [paragraph(body, f"OPTION{i} " + "Each option has a cost and a consequence. " * 3)
                 for i in range(8)]
        boxed(body, decision, *lines)
        pages = self.pages(body)
        self.assertIn("PITFALLTITLE", pages[0])
        self.assertNotIn("DECISIONTITLE", pages[0])
        self.assertIn("OPTION7", pages[1])


if __name__ == "__main__":
    unittest.main()
