"""Word callouts are never split across pages; a pitfall and its decision are separate boxes."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from handbook_toolkit.docx_pages import export_pdf, font_environment
from handbook_toolkit.docx_post import _wrap_callout_box
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
