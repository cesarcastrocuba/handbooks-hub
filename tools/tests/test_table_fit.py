"""Native Typst measurement and Word keep chains."""

from pathlib import Path
import json, re, shutil, subprocess, tempfile, unittest
import xml.etree.ElementTree as ET
from handbook_toolkit.docx_tables import (
    candidates,
    keep_rows,
    keep_leadins,
    keep_section_intros,
    unwrap_float_layouts,
)
from handbook_toolkit.docx_xml import W


def _paragraph(parent, text="", style=None):
    p = ET.SubElement(parent, W + "p")
    if style:
        ET.SubElement(ET.SubElement(p, W + "pPr"), W + "pStyle", {W + "val": style})
    if text:
        ET.SubElement(ET.SubElement(p, W + "r"), W + "t").text = text
    return p


def _layout(body, inner):
    """A Quarto float layout table: one row, one cell, the float and its caption."""
    layout = ET.SubElement(body, W + "tbl")
    cell = ET.SubElement(ET.SubElement(layout, W + "tr"), W + "tc")
    ET.SubElement(cell, W + "tcPr")
    ET.SubElement(cell, W + "bookmarkStart", {W + "name": "float"})
    inner(cell)
    caption = _paragraph(cell, "Caption", "ImageCaption")
    ET.SubElement(cell, W + "bookmarkEnd")
    return layout, caption


class FloatLayoutTests(unittest.TestCase):
    def test_table_and_figure_layouts_are_unwrapped_in_place(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        heading = _paragraph(body, "B.10 Control and Evidence Matrix", "Heading2")
        holder = {}

        def data(cell):
            table = ET.SubElement(cell, W + "tbl")
            props = ET.SubElement(table, W + "tblPr")
            ET.SubElement(props, W + "tblStyle", {W + "val": "Table"})
            ET.SubElement(props, W + "tblLook", {W + "firstRow": "1"})
            for _ in range(2):
                _paragraph(ET.SubElement(ET.SubElement(table, W + "tr"), W + "tc"), "x")
            holder["table"] = table

        def image(cell):
            p = _paragraph(cell, style="Compact")
            ET.SubElement(ET.SubElement(p, W + "r"), W + "drawing")
            holder["image"] = p

        _, table_caption = _layout(body, data)
        _paragraph(body, "A sentence between the floats.", "BodyText")
        _, figure_caption = _layout(body, image)
        ET.SubElement(body, W + "sectPr")
        self.assertEqual(unwrap_float_layouts(root), (1, 1))
        tags = [child.tag.replace(W, "") for child in body]
        self.assertEqual(
            tags,
            ["p", "bookmarkStart", "tbl", "p", "bookmarkEnd", "p",
             "bookmarkStart", "p", "p", "bookmarkEnd", "sectPr"],
        )
        self.assertIs(body[2], holder["table"])
        self.assertIs(body[3], table_caption)
        self.assertIs(body[8], figure_caption)
        self.assertIsNotNone(holder["image"].find(W + "pPr/" + W + "keepNext"))
        self.assertIs(body[0], heading)
        # The unwrapped data table is found with its caption after it, as Word needs.
        self.assertEqual(
            [(t, c, after) for t, c, after in candidates(root)],
            [(holder["table"], table_caption, True)],
        )
        # The heading now reaches the table directly, and the sentence between the
        # floats leads into the figure; the table's caption does not chain onward.
        self.assertEqual(keep_leadins(root), 2)
        self.assertIsNotNone(heading.find(W + "pPr/" + W + "keepNext"))
        self.assertIsNone(table_caption.find(W + "pPr/" + W + "keepNext"))

    def test_callouts_and_uncaptioned_one_cell_tables_stay_wrapped(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        callout = ET.SubElement(body, W + "tbl")
        cell = ET.SubElement(ET.SubElement(callout, W + "tr"), W + "tc")
        _paragraph(cell, "Decision & Trade-off")
        ET.SubElement(cell, W + "tbl")
        _paragraph(cell)
        self.assertEqual(unwrap_float_layouts(root), (0, 0))
        self.assertIs(body[0], callout)

    def test_section_introduction_keeps_with_the_next_heading(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        _paragraph(body, "9.3 Responsibilities and Team Interactions", "Heading2")
        intro = _paragraph(
            body,
            "A platform moves work from many teams to one. The architecture must state "
            "which work moved, which did not, and how the teams interact around the boundary.",
            "FirstParagraph",
        )
        ET.SubElement(body, W + "bookmarkEnd")
        ET.SubElement(body, W + "bookmarkStart")
        _paragraph(body, "9.3.1 The Platform Responsibility Model", "Heading3")
        body_text = _paragraph(body, "Definition. A long paragraph.", "FirstParagraph")
        _paragraph(body, "9.3.2 Next", "Heading3")
        long_intro_heading = _paragraph(body, "9.4 Long", "Heading2")
        long_intro = _paragraph(body, "word " * 81, "FirstParagraph")
        _paragraph(body, "9.4.1 Next", "Heading3")
        self.assertEqual(keep_section_intros(root), 2)
        self.assertEqual(intro.find(W + "pPr/" + W + "keepNext").get(W + "val"), "1")
        # A unit's first paragraph between two headings counts too: it is that heading's
        # only text and moves with the next heading rather than stand alone.
        self.assertIsNotNone(body_text.find(W + "pPr/" + W + "keepNext"))
        self.assertIsNone(long_intro.find(W + "pPr/" + W + "keepNext"))
        self.assertIsNotNone(long_intro_heading)


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
                '| A | B |\n|---|---|\n| 1 | 2 |\n\n: Caption {#tbl-x}\n'
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

    @unittest.skipUnless(shutil.which("quarto"), "Quarto pandoc required")
    def test_figures_are_not_grouped_because_they_float(self):
        # A grouped figure moved to the next page with its lead-in and left the
        # page part empty; a floating figure lets the following text fill it.
        leadins = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/filters/float-leadins.lua"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "lead.md"
            source.write_text(
                '### Heading Two\n\nFigure 1 shows it.\n\n'
                '![Caption](img.png){#fig-x width="60%"}\n'
            )
            result = subprocess.run(
                ["quarto", "pandoc", "-f", "markdown", "-t", "typst",
                 "--lua-filter", str(leadins), str(source)],
                capture_output=True, text=True, check=True,
            )
            self.assertNotIn("#handbook-float-group(", result.stdout)
            self.assertIn("#figure(", result.stdout)

    @unittest.skipUnless(shutil.which("quarto"), "Quarto pandoc required")
    def test_pending_floats_are_placed_before_a_run_of_callouts(self):
        leadins = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/filters/float-leadins.lua"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "callouts.md"
            source.write_text(
                "::: {.callout-warning title=\"Common Pitfall\"}\nPITFALL\n:::\n\n"
                "::: {.callout-important title=\"Decision\"}\nDECISION\n:::\n\n"
                "Closing text.\n\n"
                "::: {.callout-tip title=\"Key Takeaway\"}\nLONE\n:::\n"
            )
            result = subprocess.run(
                ["quarto", "pandoc", "-f", "markdown", "-t", "typst",
                 "--lua-filter", str(leadins), str(source)],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertEqual(result.count("#place.flush()"), 1)  # not before the lone callout
            self.assertLess(result.index("#place.flush()"), result.index("#handbook-run-start"))
            self.assertLess(result.index("#handbook-run-start"), result.index("PITFALL"))
            self.assertEqual(result.count("#handbook-run-continue"), 1)
            self.assertLess(result.index("PITFALL"), result.index("#handbook-run-continue"))
            self.assertLess(result.index("#handbook-run-continue"), result.index("DECISION"))

    @unittest.skipUnless(shutil.which("quarto"), "Quarto pandoc required")
    def test_each_figure_is_placed_knowing_whether_its_section_ends_in_callouts(self):
        leadins = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/filters/float-leadins.lua"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "top.md"
            source.write_text(
                "## One\n\n![FIRSTFIG](a.png){#fig-a}\n\nText.\n\n"
                "::: {.callout-warning}\nP\n:::\n\n::: {.callout-important}\nD\n:::\n\n"
                "## Two\n\n![SECONDFIG](b.png){#fig-b}\n\nText.\n\n"
                "::: {.callout-tip}\nLONE\n:::\n"
            )
            result = subprocess.run(
                ["quarto", "pandoc", "-f", "markdown", "-t", "typst",
                 "--lua-filter", str(leadins), str(source)],
                capture_output=True, text=True, check=True,
            ).stdout
            first = result.index("#handbook-placed-figure(before-run: true)[")
            second = result.index("#handbook-placed-figure(before-run: false)[")
            self.assertLess(first, result.index("FIRSTFIG"))
            self.assertLess(result.index("FIRSTFIG"), second)
            self.assertLess(second, result.index("SECONDFIG"))

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftotext"),
                         "native pagination tools required")
    def test_a_floating_figure_never_lands_between_the_callouts_of_a_run(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/handbook-typst.typ"
        ).read_text()
        start = template.index("// A figure never floats between the callouts of a run")
        helpers = template[start:template.index("\n}\n", template.index("#let handbook-placed-figure")) + 3]
        rules = "\n".join(line for line in template.splitlines() if "set figure(placement: auto)" in line)

        def positions(body):
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "run.typ"
                source.write_text(
                    "#set page(height: 400pt, width: 300pt, margin: 20pt)\n#set text(size: 9pt)\n"
                    + rules + "\n" + helpers + "\n"
                    "#let box(body) = block(breakable: false, fill: luma(230), width: 100%, inset: 6pt, body)\n"
                    "#let fig(before, label) = handbook-placed-figure(before-run: before)["
                    "#figure(rect(height: 100pt, width: 80%), kind: \"quarto-float-fig\", "
                    "supplement: [Figure], caption: label)]\n" + body
                )
                subprocess.run(["quarto", "typst", "compile", str(source)], check=True,
                               capture_output=True)
                text = subprocess.check_output(
                    ["pdftotext", "-bbox", str(Path(tmp) / "run.pdf"), "-"], text=True
                )
            found = {}
            for number, page in enumerate(text.split("<page ")[1:], 1):
                for top, word in re.findall(r'yMin="([\d.]+)"[^>]*>([A-Z]{4,})<', page):
                    found.setdefault(word, (number, float(top)))
            return found

        run = ("#place.flush()\n#handbook-run-start\n#box[PITFALL #lorem(20)]\n"
               "#handbook-run-continue\n#box[DECISION #lorem(50)]\n")
        cases = {
            # the section's figure would float to the foot of the page under the pitfall
            "own figure": "#lorem(110)\n#fig(true, [OWNFIG])\n#lorem(10)\n" + run + "= Next\n#lorem(20)\n",
            # the next section's figure (its section also ends in a run) would float to
            # the top of the page, above the decision that starts it
            "next figure": "#lorem(230)\n" + run + "= Next\n#lorem(20)\n#fig(true, [NEXTFIG])\n"
                           "#lorem(60)\n" + run.replace("PITFALL", "LATERP").replace("DECISION", "LATERD"),
            # a figure still pending when the run starts
            "pending": "#lorem(100)\n#fig(true, [PENDFIG])\n#lorem(30)\n" + run,
        }
        for name, body in cases.items():
            with self.subTest(name):
                found = positions(body)
                pitfall, decision = found["PITFALL"], found["DECISION"]
                figure = next(value for key, value in found.items() if key.endswith("FIG"))
                self.assertFalse(pitfall < figure < decision, found)

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftotext"),
                         "native pagination tools required")
    def test_template_floats_figures_and_lets_text_fill_the_page(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/handbook-typst.typ"
        ).read_text()
        rules = [line for line in template.splitlines() if "set figure(placement: auto)" in line]
        self.assertEqual(len(rules), 2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "float.typ"
            source.write_text(
                '#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))\n'
                + "\n".join(rules)
                + "\n#v(15cm)\nLEADTEXT\n\n"
                + '#figure(rect(width:10cm,height:12cm), kind:"quarto-float-fig", supplement:[Figure], caption:[CAPTIONTEXT])\n\n'
                + "AFTERTEXT\n"
            )
            subprocess.run(["quarto", "typst", "compile", str(source)], check=True,
                           capture_output=True)
            pages = subprocess.check_output(
                ["pdftotext", str(root / "float.pdf"), "-"], text=True
            ).split("\f")
            self.assertIn("LEADTEXT", pages[0])
            self.assertIn("AFTERTEXT", pages[0])  # the text after the figure fills page 1
            self.assertIn("CAPTIONTEXT", pages[1])

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
