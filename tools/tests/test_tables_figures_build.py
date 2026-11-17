"""Real multi-page tables, physical raster widths and SVG regression."""

from pathlib import Path
import json, posixpath, re, subprocess, tempfile, unittest, xml.etree.ElementTree as ET
from zipfile import ZipFile
from test_build import make_book, commit_all, build_book, BUILD_AVAILABLE
from test_figure_layout import png
from html_support import Document
from handbook_toolkit.docx_xml import W


@unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo required")
class TablesFiguresBuildTests(unittest.TestCase):
    def test_short_tall_tables_and_raster_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _ = make_book(root, chapter=True)
            image = repo / "manuscript/images"
            (image / "natural.png").write_bytes(png())
            (image / "tall.png").write_bytes(png(1000, 3000))
            (image / "vector.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"><rect width="200" height="100" fill="white"/></svg>'
            )
            chapter = repo / "manuscript/chapters/pilot.qmd"
            extra = "\n\n```{=typst}\n#v(16cm)\n```\n\n### SHORTHEADING\n\nSHORTINTRO A short introduction.\n\n| SHORTKEY | Value |\n| --- | --- |\n| SHORTFIRST | A |\n| SHORTLAST | B |\n\n: Page-sized fixture. {#tbl-short}\n\n"
            extra += (
                "### LONGHEADING\n\nLONGINTRO A short introduction.\n\n| LONGKEY | Value |\n| --- | --- |\n"
                + "".join(
                    f"| LONGROW{i:03d} | A long table entry. |\n" for i in range(100)
                )
                + "\n: Tall table fixture. {#tbl-long}\n\n"
            )
            extra += '### IMAGEHEADING\n\nIMAGEINTRO A short introduction.\n\n![Natural fixture.](../images/natural.png){#fig-natural width="100%"}\n\n![Tall fixture.](../images/tall.png){#fig-tall width="100%"}\n\n![Vector fixture.](../images/vector.svg){#fig-vector width="60%"}\n'
            marker = '::: {.callout-important appearance="simple" icon=false title="Review Checklist'
            original = chapter.read_text()
            self.assertIn(marker, original)
            chapter.write_text(original.replace(marker, extra + marker))
            out = root / "dist"
            build_book(
                repo, commit_all(repo), out, mode="chapter", require_page_numbers=True
            )
            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(out / "book.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda token: [i for i, p in enumerate(pages) if token in p]
            for heading, intro, first in [
                ("SHORTHEADING", "SHORTINTRO", "SHORTFIRST"),
                ("LONGHEADING", "LONGINTRO", "LONGROW000"),
                ("IMAGEHEADING", "IMAGEINTRO", "Natural fixture."),
            ]:
                self.assertEqual(containing(heading)[-1], containing(first)[-1])
                self.assertEqual(containing(intro)[-1], containing(first)[-1])
            self.assertEqual(containing("SHORTFIRST"), containing("SHORTLAST"))
            self.assertEqual(
                containing("SHORTLAST")[-1], containing("Page-sized fixture.")[-1]
            )
            self.assertNotEqual(containing("LONGROW000"), containing("LONGROW099"))
            self.assertEqual(
                containing("LONGROW099")[-1], containing("Tall table fixture.")[-1]
            )
            for i in range(
                containing("LONGROW000")[0], containing("LONGROW099")[0] + 1
            ):
                self.assertIn("LONGKEY", pages[i])
            with ZipFile(out / "book-html.zip") as z:
                doc = Document(z.read("manuscript/chapters/pilot.html").decode()).root
                images = [
                    n
                    for n in doc.find("img")
                    if "/natural.png" in n.attrs.get("src", "")
                ]
                self.assertEqual(len(images), 1)
                self.assertRegex(str(images[0].attrs), r"69(?:\.0)?%")
                vector = [
                    n
                    for n in doc.find("img")
                    if "/vector.svg" in n.attrs.get("src", "")
                ][0]
                self.assertNotIn("handbook-raster", vector.attrs.get("class", ""))
            with ZipFile(out / "book.docx") as z:
                doc = ET.fromstring(z.read("word/document.xml"))
            for token in [
                "SHORTHEADING",
                "SHORTINTRO",
                "LONGHEADING",
                "LONGINTRO",
                "IMAGEHEADING",
                "IMAGEINTRO",
            ]:
                paragraphs = [
                    p
                    for p in doc.iter(W + "p")
                    if token in "".join(t.text or "" for t in p.iter(W + "t"))
                ]
                paragraphs = [
                    p
                    for p in paragraphs
                    if (style := p.find(W + "pPr/" + W + "pStyle")) is None
                    or not style.get(W + "val", "").startswith("TOC")
                ]
                self.assertEqual(len(paragraphs), 1, token)
                keep = paragraphs[0].find(W + "pPr/" + W + "keepNext")
                self.assertIsNotNone(keep, token)
                self.assertNotEqual(keep.get(W + "val"), "0", token)
            tables = [t for t in doc.iter(W + "tbl") if len(t.findall(W + "tr")) > 1]
            short = next(
                t
                for t in tables
                if any(n.text == "SHORTFIRST" for n in t.iter(W + "t"))
            )
            long = next(
                t
                for t in tables
                if any(n.text == "LONGROW099" for n in t.iter(W + "t"))
            )
            self.assertTrue(
                any(
                    p.find(W + "pPr/" + W + "keepNext") is not None
                    for p in short.findall(W + "tr")[1].iter(W + "p")
                )
            )
            self.assertFalse(
                any(
                    p.find(W + "pPr/" + W + "keepNext") is not None
                    for p in long.findall(W + "tr")[1].iter(W + "p")
                )
            )
