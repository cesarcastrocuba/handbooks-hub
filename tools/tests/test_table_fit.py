"""Native Typst measurement and Word keep chains."""

from pathlib import Path
import json, re, shutil, subprocess, tempfile, unittest
import xml.etree.ElementTree as ET
from handbook_toolkit.docx_tables import candidates, keep_rows, keep_leadins
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

    def test_word_layout_cell_caption_is_found_and_kept(self):
        # Quarto wraps a table float in a one-cell layout table and styles its
        # caption ImageCaption; only the caption style differs from a figure.
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        layout = ET.SubElement(body, W + "tbl")
        row = ET.SubElement(layout, W + "tr")
        cell = ET.SubElement(row, W + "tc")
        table = ET.SubElement(cell, W + "tbl")
        properties = ET.SubElement(table, W + "tblPr")
        ET.SubElement(properties, W + "tblStyle", {W + "val": "Table"})
        ET.SubElement(properties, W + "tblLook", {W + "firstRow": "1"})
        for i in range(2):
            data_row = ET.SubElement(table, W + "tr")
            data_cell = ET.SubElement(data_row, W + "tc")
            ET.SubElement(data_cell, W + "p")
        caption = ET.SubElement(cell, W + "p")
        caption_properties = ET.SubElement(caption, W + "pPr")
        ET.SubElement(caption_properties, W + "pStyle", {W + "val": "ImageCaption"})
        found = candidates(root)
        self.assertEqual([(value[0], value[1], value[2]) for value in found], [(table, caption, True)])
        keep_rows(table, caption, True, row)
        final = table.findall(W + "tr")[-1]
        self.assertTrue(
            all(p.find(W + "pPr/" + W + "keepNext") is not None for p in final.iter(W + "p"))
        )
        self.assertIsNotNone(row.find(W + "trPr/" + W + "cantSplit"))

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

    @unittest.skipUnless(shutil.which("quarto"), "Quarto pandoc required")
    def test_lead_group_is_not_wrapped_in_a_breakable_div(self):
        # A Div renders as a breakable #block[ and Typst then shrinks an image to
        # the remaining space instead of moving it to the next page.
        leadins = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/filters/float-leadins.lua"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "lead.md"
            source.write_text(
                '### Heading Two\n\nA short introduction.\n\n'
                '![Caption](img.png){#fig-x width="60%"}\n'
            )
            result = subprocess.run(
                [
                    "quarto",
                    "pandoc",
                    "-f",
                    "markdown",
                    "-t",
                    "typst",
                    "--lua-filter",
                    str(leadins),
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(result.stdout.startswith("#handbook-float-group("))
            self.assertNotIn("#block[", result.stdout)
            self.assertIn("#figure(", result.stdout)

    @unittest.skipUnless(
        shutil.which("quarto") and shutil.which("pdfimages"),
        "native pagination tools required",
    )
    def test_figure_in_lead_group_keeps_its_stated_width(self):
        # A breakable wrapper around the group scaled images down to the remaining
        # space instead of moving them to the next page.
        from test_figure_layout import png as fixture

        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "tall.png"
            image.write_bytes(fixture(1000, 1200))
            source = root / "figure.typ"
            source.write_text(
                f"""#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))
#import "{helper}": handbook-float-group
#v(20cm)
#handbook-float-group(lead:[LEADTEXT], body:[#figure(image("{image}", width: 60%), caption: [CAPTIONTEXT])])
"""
            )
            subprocess.run(
                ["quarto", "typst", "compile", str(source), "--root", "/"],
                check=True,
                capture_output=True,
            )
            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(root / "figure.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda token: [i for i, page in enumerate(pages) if token in page]
            self.assertEqual(containing("LEADTEXT"), containing("CAPTIONTEXT"))
            listing = subprocess.check_output(
                ["pdfimages", "-list", str(root / "figure.pdf")], text=True
            )
            columns = next(
                line.split()
                for line in listing.splitlines()
                if line.split()[:1] and line.split()[0].isdigit()
            )
            ppi = float(columns[-4])
            body = (21.0 - 2 * 2.2) / 2.54 * 72
            self.assertAlmostEqual(ppi, 1000 / (0.6 * body / 72), delta=2)

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
