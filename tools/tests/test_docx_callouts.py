"""Word callouts may break across pages; their title and table rows stay whole."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from handbook_toolkit.docx_pages import export_pdf, font_environment
from handbook_toolkit.docx_post import _wrap_callout_box
from handbook_toolkit.docx_tables import candidates, keep_callout_tables, keep_leadins
from handbook_toolkit.docx_xml import W
from test_figure_place import FONTS, _package, paragraph


def styled_table(parent, rows=3, keep=True):
    table = ET.SubElement(parent, W + "tbl")
    properties = ET.SubElement(table, W + "tblPr")
    ET.SubElement(properties, W + "tblStyle", {W + "val": "TablePlain"})
    ET.SubElement(properties, W + "tblLook", {W + "firstRow": "1"})
    for i in range(rows):
        cell = ET.SubElement(ET.SubElement(table, W + "tr"), W + "tc")
        paragraph(cell, f"row {i}", keep=keep)
    return table


def boxed(body, title, *content):
    """Wrap a title paragraph and its content as the post-processor does."""
    document = ET.Element(W + "document")
    document.append(body)
    group = [title, *content]
    children = list(body)
    _wrap_callout_box(document, body, children, children.index(title), group, W, "000000", "FFFFFF")
    return document, next(t for t in body.findall(W + "tbl"))


class CalloutBoxTests(unittest.TestCase):
    def test_the_box_row_may_break_and_its_title_keeps_with_the_next_line(self):
        body = ET.Element(W + "body")
        title = paragraph(body, "Common Pitfall", "CalloutWarningTitle")
        text = paragraph(body, "A warning.")
        _, box = boxed(body, title, text)
        self.assertIsNone(box.find(W + "tr/" + W + "trPr/" + W + "cantSplit"))
        self.assertIsNotNone(title.find(W + "pPr/" + W + "keepNext"))
        self.assertIsNone(text.find(W + "pPr/" + W + "keepNext"))

    def test_a_table_in_a_callout_breaks_only_between_rows(self):
        body = ET.Element(W + "body")
        title = paragraph(body, "Decision & Trade-off", "CalloutImportantTitle")
        inner = styled_table(body, rows=4)
        document, _ = boxed(body, title, inner)
        self.assertEqual(candidates(document), [])  # never measured and kept whole
        self.assertEqual(keep_callout_tables(document), 1)
        rows = inner.findall(W + "tr")
        self.assertTrue(all(r.find(W + "trPr/" + W + "cantSplit") is not None for r in rows))
        kept = [any(p.find(W + "pPr/" + W + "keepNext") is not None for p in r.iter(W + "p")) for r in rows]
        self.assertEqual(kept, [True, False, False, False])

    def test_text_before_a_callout_is_not_chained_to_it(self):
        body = ET.Element(W + "body")
        before = paragraph(body, "End of the example.")
        title = paragraph(body, "Decision & Trade-off", "CalloutImportantTitle")
        inner = styled_table(body, keep=False)
        document, _ = boxed(body, title, inner)
        keep_leadins(document)
        self.assertIsNone(before.find(W + "pPr/" + W + "keepNext"))


@unittest.skipUnless(
    shutil.which("soffice") and shutil.which("pdftotext"),
    "LibreOffice and Poppler are required for the pagination check",
)
class LibreOfficeTests(unittest.TestCase):
    SENTENCE = "Body text that fills the page and keeps the reader moving. " * 9

    def test_a_pitfall_starts_in_the_gap_in_front_of_it(self):
        body = ET.Element(W + "body")
        for _ in range(7):  # leaves about 11 lines for a 30-line pitfall
            paragraph(body, self.SENTENCE)
        title = paragraph(body, "PITFALLTITLE", "CalloutWarningTitle")
        lines = [paragraph(body, f"LINE{i} " + "A warning about a common mistake and its cost. " * 3)
                 for i in range(10)]
        boxed(body, title, *lines)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, body)
            pdf = export_pdf(path, Path(tmp) / "pdf", env=font_environment(FONTS, Path(tmp)))
            pages = subprocess.run(["pdftotext", str(pdf), "-"], check=True, capture_output=True,
                                   text=True).stdout.split("\f")
        self.assertGreater(len([p for p in pages if p.strip()]), 1)  # the box continues
        self.assertIn("PITFALLTITLE", pages[0])
        self.assertIn("LINE0", pages[0])  # the title is not left alone
        self.assertIn("LINE9", pages[1])


if __name__ == "__main__":
    unittest.main()
