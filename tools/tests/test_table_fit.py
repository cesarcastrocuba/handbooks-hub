"""Native Typst measurement and Word keep chains."""

from pathlib import Path
import json, re, shutil, subprocess, tempfile, unittest
import xml.etree.ElementTree as ET
from handbook_toolkit.docx_tables import keep_rows, keep_leadins
from handbook_toolkit.docx_xml import W


class TableFitTests(unittest.TestCase):
    def test_word_short_rows_and_caption_chain(self):
        t = ET.Element(W + "tbl")
        for i in range(3):
            r = ET.SubElement(t, W + "tr")
            c = ET.SubElement(r, W + "tc")
            ET.SubElement(c, W + "p")
        caption = ET.Element(W + "p")
        keep_rows(t, caption, True)
        self.assertTrue(
            all(r.find(W + "trPr/" + W + "cantSplit") is not None for r in t)
        )
        self.assertTrue(
            all(
                p.find(W + "pPr/" + W + "keepNext") is not None for p in t.iter(W + "p")
            )
        )

    @unittest.skipUnless(shutil.which("quarto"), "Quarto Typst required")
    def test_measured_short_moves_whole_and_tall_breaks_with_its_caption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = (
                Path(__file__).resolve().parents[1]
                / "src/handbook_toolkit/render_data/typst/table-fit.typ"
            )
            script = """#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))
#set table(inset:6pt)
#import "HELPER": handbook-fit-table, handbook-fit-float
#show table: it => handbook-fit-table(it, 2pt)
#show figure.where(kind:table): set block(breakable:true)
#show figure.where(kind:table): handbook-fit-float
#v(23cm)
#figure(table(columns:1,table.header[SHORTHEADER],[SHORTFIRST],[SHORTLAST]),caption:[SHORTCAPTION]) <short>
#pagebreak()
#figure(table(columns:1,table.header[LONGHEADER],..range(100).map(i=>[LONGROW#i])),caption:[LONGCAPTION]) <long>
""".replace("HELPER", helper.as_posix())
            path = root / "test.typ"
            path.write_text(script)
            compiled = subprocess.run(
                [
                    "quarto",
                    "typst",
                    "compile",
                    str(path),
                    str(root / "test.pdf"),
                    "--root",
                    "/",
                ],
                check=True,
                capture_output=True,
            )
            self.assertNotIn(b"did not converge", compiled.stdout + compiled.stderr)
            result = subprocess.run(
                [
                    "quarto",
                    "typst",
                    "query",
                    str(path),
                    "<handbook-table-fit>",
                    "--field",
                    "value",
                    "--root",
                    "/",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            values = json.loads(
                next(
                    line
                    for line in (result.stdout + "\n" + result.stderr).splitlines()
                    if line.startswith("[")
                )
            )
            for name, fit in [("short", True), ("long", False)]:
                events = [e for e in values if e["name"] == name]
                self.assertEqual(events[0]["height"] <= events[0]["body"], fit)
                self.assertEqual(events[0]["page"] == events[-1]["page"], fit)
            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(root / "test.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda s: [i for i, p in enumerate(pages) if s in p]
            self.assertEqual(containing("SHORTFIRST"), containing("SHORTCAPTION"))
            self.assertEqual(containing("LONGROW99"), containing("LONGCAPTION"))
            self.assertGreater(len(containing("LONGHEADER")), 1)

    @unittest.skipUnless(
        shutil.which("quarto") and shutil.which("pdftotext"),
        "native pagination tools required",
    )
    def test_heading_and_caption_stay_with_boundary_height_tables(self):
        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        source = f"""#set page(width:160mm,height:120mm,margin:10mm)
#set table(inset:6pt)
#import "{helper}": handbook-fit-table, handbook-fit-float, handbook-float-group
#show table: it=>handbook-fit-table(it,2pt)
#show figure.where(kind:table):set block(breakable:true)
#show figure.where(kind:table):handbook-fit-float
"""
        for n in range(10, 46):
            source += f"""#pagebreak(weak:true)
#handbook-float-group(lead:[#heading(level:2)[HEADING{n}X]],body:[#figure(table(columns:1,table.header[HEADER{n}X],..range({n}).map(i=>[ROW{n}X#i#sym.zws])),caption:figure.caption(position:bottom)[CAP{n}X]) <case{n}>])
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "boundary.typ"
            path.write_text(source)
            compiled = subprocess.run(
                ["quarto", "typst", "compile", str(path), "--root", "/"],
                check=True,
                capture_output=True,
            )
            self.assertNotIn(b"did not converge", compiled.stdout + compiled.stderr)
            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(path.with_suffix(".pdf")), "-"], text=True
            ).split("\f")
            containing = lambda token: [
                i for i, page in enumerate(pages) if token in page
            ]
            for n in range(10, 46):
                with self.subTest(rows=n):
                    self.assertEqual(
                        containing(f"HEADING{n}X"), containing(f"ROW{n}X0")
                    )
                    self.assertEqual(
                        containing(f"ROW{n}X{n-1}"), containing(f"CAP{n}X")
                    )

    def test_word_leadin_crosses_bookmarks_and_keeps_heading_with_table_or_image(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        heading = ET.SubElement(body, W + "p")
        pp = ET.SubElement(heading, W + "pPr")
        ET.SubElement(pp, W + "pStyle", {W + "val": "Heading2"})
        ET.SubElement(pp, W + "keepNext", {W + "val": "0"})
        ET.SubElement(ET.SubElement(heading, W + "r"), W + "t").text = "Heading"
        intro = ET.SubElement(body, W + "p")
        ET.SubElement(ET.SubElement(intro, W + "r"), W + "t").text = (
            "A short introduction."
        )
        ET.SubElement(body, W + "bookmarkEnd")
        table = ET.SubElement(body, W + "tbl")
        ET.SubElement(
            ET.SubElement(table, W + "tblPr"), W + "tblLook", {W + "firstRow": "1"}
        )
        self.assertEqual(keep_leadins(root), 2)
        for p in [heading, intro]:
            self.assertEqual(p.find(W + "pPr/" + W + "keepNext").get(W + "val"), "1")
        body.remove(table)
        picture = ET.SubElement(body, W + "p")
        ET.SubElement(ET.SubElement(picture, W + "r"), W + "drawing")
        self.assertEqual(keep_leadins(root), 2)

    def test_word_does_not_chain_long_body_paragraphs_to_floats(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        p = ET.SubElement(body, W + "p")
        ET.SubElement(ET.SubElement(p, W + "r"), W + "t").text = "word " * 81
        table = ET.SubElement(body, W + "tbl")
        ET.SubElement(
            ET.SubElement(table, W + "tblPr"), W + "tblLook", {W + "firstRow": "1"}
        )
        self.assertEqual(keep_leadins(root), 0)
        self.assertIsNone(p.find(W + "pPr/" + W + "keepNext"))
