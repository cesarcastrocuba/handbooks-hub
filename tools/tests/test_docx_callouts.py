"""Word callouts are never split across pages; a pitfall and its decision are separate boxes."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from handbook_toolkit.docx_pages import export_pdf, font_environment
from handbook_toolkit.docx_post import _wrap_callout_box
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


class CalloutBoxTests(unittest.TestCase):
    def test_a_box_is_one_row_that_never_splits(self):
        body = ET.Element(W + "body")
        title = paragraph(body, "Common Pitfall", "CalloutWarningTitle")
        text = paragraph(body, "A warning.")
        _, box = boxed(body, title, text)
        rows = box.findall(W + "tr")
        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0].find(W + "trPr/" + W + "cantSplit"))


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
