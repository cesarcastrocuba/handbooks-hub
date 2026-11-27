"""Native Typst measurement and Word keep chains."""

from pathlib import Path
import json, re, shutil, subprocess, tempfile, unittest
import xml.etree.ElementTree as ET
from handbook_toolkit import design
from handbook_toolkit.docx_tables import (
    candidates,
    keep_rows,
    keep_leadins,
    keep_section_intros,
    unwrap_float_layouts,
)
from handbook_toolkit.docx_xml import W
from test_figure_layout import png


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
    def test_a_figure_is_grouped_with_its_lead_in_and_opens_images_from_the_document(self):
        leadins = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/filters/float-leadins.lua"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "lead.md"
            source.write_text(
                '### Heading Two\n\nFigure 1 shows it.\n\n'
                '![Caption](img.png){#fig-x width="60%"}\n\n'
                '::: {.callout-warning}\nPITFALL\n:::\n\n::: {.callout-important}\nDECISION\n:::\n'
            )
            result = subprocess.run(
                ["quarto", "pandoc", "-f", "markdown", "-t", "typst",
                 "--lua-filter", str(leadins), str(source)],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertTrue(result.startswith(
                '#handbook-figure-group(open: p => image(p, alt: "handbook-natural"), lead: ['))
            self.assertLess(result.index("Figure 1 shows it."), result.index("#figure("))
            self.assertNotIn("place.flush", result)
            self.assertNotIn("placement", result)

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftotext") and shutil.which("pdfimages"),
                         "native pagination tools required")
    def test_a_figure_stays_in_place_and_is_scaled_only_when_it_nearly_fits(self):
        from test_figure_layout import png as fixture

        template = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/handbook-typst.typ"
        ).read_text()
        self.assertNotIn("placement: auto", template)
        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 500 x 400 px at 200 ppi is 180 pt wide: at 60% of the text block it prints
            # at 1.57 of its natural size; 1000 x 800 px prints at 0.78 and cannot shrink.
            (root / "small.png").write_bytes(fixture(500, 400))
            (root / "big.png").write_bytes(fixture(1000, 800))

            def layout(space, picture):
                source = root / "figure.typ"
                source.write_text(
                    f'''#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))
#import "{helper}": handbook-figure-group
#v({space})
LEADTEXT
#handbook-figure-group(open: p => image(p, alt: "handbook-natural"), lead:[INTRO shows it.], body:[#figure(image("{picture}", width: 60%), caption: [CAPTIONTEXT])])
AFTERTEXT
'''
                )
                subprocess.run(["quarto", "typst", "compile", str(source), "--root", "/"],
                               check=True, capture_output=True)
                pages = subprocess.check_output(
                    ["pdftotext", str(root / "figure.pdf"), "-"], text=True).split("\f")
                listing = subprocess.check_output(
                    ["pdfimages", "-list", str(root / "figure.pdf")], text=True).splitlines()
                ppi = float(listing[2].split()[-4])
                where = {k: next(i for i, page in enumerate(pages) if k in page)
                         for k in ("LEADTEXT", "INTRO", "CAPTIONTEXT", "AFTERTEXT")}
                return where, ppi

            body = (21.0 - 2 * 2.2) / 2.54  # inches
            unscaled = 500 / (0.6 * body)
            big = 1000 / (0.6 * body)
            where, ppi = layout("2cm", "small.png")  # fits: printed at the print scale
            self.assertEqual(where["CAPTIONTEXT"], 0)
            self.assertAlmostEqual(ppi, unscaled / 0.85, delta=2)
            where, ppi = layout("17cm", "small.png")  # nearly fits: scaled further and stays
            self.assertEqual(where["CAPTIONTEXT"], 0)
            self.assertGreater(ppi, unscaled / 0.85 + 5)
            where, ppi = layout("19cm", "small.png")  # would cross the natural floor: moves
            self.assertEqual((where["LEADTEXT"], where["INTRO"], where["CAPTIONTEXT"]), (0, 1, 1))
            self.assertAlmostEqual(ppi, unscaled / 0.85, delta=2)
            where, ppi = layout("2cm", "big.png")  # at 0.78 of natural size: only to the floor
            self.assertAlmostEqual(ppi, big / (0.75 / 0.78), delta=3)

    def test_a_checklist_on_decisions_keeps_the_checklist_colour(self):
        # This only reads the template: it needs neither Quarto nor Poppler.
        template = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/handbook-typst.typ"
        ).read_text()
        callout = template[template.index("#let callout("):]
        # "Architecture Review Checklist — Decisions" contains both words.
        self.assertLess(callout.index('"Review Checklist" in label'), callout.index('"Decision" in label'))

    def test_a_callout_is_never_split(self):
        # Source assertion only: it needs neither Quarto nor Poppler.
        template = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/handbook-typst.typ"
        ).read_text()
        callout = template[template.index("#let callout("):]
        self.assertIn("breakable: false", callout[: callout.index("fill: tint")])

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftocairo"),
                         "native pagination tools required")
    def test_a_checklist_on_decisions_prints_the_checklist_tint(self):
        # A real compile, not only the source order: the checklist title also
        # contains "Decision", so the wrong branch paints the important tint.
        package = Path(__file__).resolve().parents[1] / "src/handbook_toolkit/render_data"
        fonts = package / "fonts"
        tokens = design.load_tokens()["callout"]

        def tint(name):
            value = tokens[name]["tint"]["print"].lstrip("#")
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

        def near(colour, expected):
            return max(abs(a - b) for a, b in zip(colour, expected)) <= 1

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handbook-render/typst").mkdir(parents=True)
            (root / "handbook-render/typst/table-fit.typ").write_bytes(
                (package / "typst/table-fit.typ").read_bytes()
            )
            source = root / "checklist.typ"
            source.write_text(
                design.typst_preamble()
                + "\n"
                + (package / "typst/handbook-typst.typ").read_text()
                + '\n#callout(title: "Architecture Review Checklist — Decisions", body: [BODYTEXT])\n'
            )
            subprocess.run(
                [
                    "quarto", "typst", "compile", str(source), "--root", str(root),
                    "--font-path", str(fonts / "inter"),
                    "--font-path", str(fonts / "jetbrains-mono"),
                ],
                check=True,
                capture_output=True,
            )
            svg = root / "checklist.svg"
            subprocess.run(
                ["pdftocairo", "-svg", str(root / "checklist.pdf"), str(svg)],
                check=True, capture_output=True,
            )
            markup = svg.read_text()
        rendered = [
            tuple(round(float(value) / 100 * 255) for value in match.groups())
            for match in re.finditer(
                r"rgb\(([\d.]+)%, ([\d.]+)%, ([\d.]+)%\)", markup
            )
        ]
        self.assertTrue(
            any(near(colour, tint("review")) for colour in rendered), rendered
        )
        self.assertFalse(
            any(near(colour, tint("important")) for colour in rendered), rendered
        )

    @unittest.skipUnless(shutil.which("quarto"), "Quarto Typst required")
    def test_the_gap_gate_and_safety_margin_are_pinned(self):
        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gaps.typ"
            path.write_text(
                f'#import "{helper}": handbook-gap-admits, handbook-gap-fit\n'
                "#assert(handbook-gap-admits(110.0pt, 706.0pt, 200.0pt))\n"
                # 90 pt is below 15% of a 706 pt body: only the gate rejects it.
                "#assert(not handbook-gap-admits(90.0pt, 706.0pt, 105.0pt))\n"
                # (105 - 95 + 10) pt of a 100 pt figure: fit = 0.8 exactly,
                # which is the 10 pt safety margin in the formula.
                "#assert(calc.abs(handbook-gap-fit(105.0pt, 95.0pt, 100.0pt) - 0.8) < 0.00001)\n"
            )
            subprocess.run(
                ["quarto", "typst", "compile", str(path), "--root", "/"],
                check=True,
                capture_output=True,
            )

    @unittest.skipUnless(shutil.which("quarto"), "Quarto Typst required")
    def test_the_print_scale_rounds_to_one_before_scaling(self):
        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scale.typ"
            path.write_text(
                f'#import "{helper}": handbook-print-factor\n'
                "#assert(calc.abs(handbook-print-factor(1.2pt, 1pt, 1.0) - 0.9) < 0.000001)\n"
                # 0.75 x 1.33332 is 0.99999, which must round to a 1.0 no-op.
                "#assert(handbook-print-factor(1.33332pt, 1pt, 1.0) == 1.0)\n"
            )
            subprocess.run(
                ["quarto", "typst", "compile", str(path), "--root", "/"],
                check=True,
                capture_output=True,
            )

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftotext"),
                         "native pagination tools required")
    def test_a_group_taller_than_a_page_is_not_wrapped(self):
        helper = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tall.png").write_bytes(png(1000, 3000))
            source = root / "tall.typ"
            source.write_text(
                f'''#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))
#import "{helper}": handbook-figure-group
#v(2cm)
LEADTEXT
#handbook-figure-group(open: p => image(p, alt: "handbook-natural"), lead:[INTRO shows it.], body:[#figure(image("tall.png", width: 60%), caption: [CAPTIONTEXT])])
'''
            )
            compiled = subprocess.run(
                ["quarto", "typst", "compile", str(source), "--root", "/"],
                check=True,
                capture_output=True,
            )
            # An unbreakable group taller than the page would drag the lead-in
            # to the caption's page (or overflow).
            self.assertNotIn(b"overflow", compiled.stdout + compiled.stderr)
            pages = subprocess.check_output(
                ["pdftotext", str(root / "tall.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda token: [
                i for i, page in enumerate(pages) if token in page
            ]
            self.assertEqual(containing("LEADTEXT"), containing("INTRO"))
            self.assertNotEqual(containing("INTRO"), containing("CAPTIONTEXT"))

    @unittest.skipUnless(shutil.which("quarto") and shutil.which("pdftotext"),
                         "native pagination tools required")
    def test_a_long_callout_stays_whole(self):
        # The real template's callout, not a grep: a long box is unbreakable, so
        # its first and last lines share a page even when it has to move whole.
        package = Path(__file__).resolve().parents[1] / "src/handbook_toolkit/render_data"
        fonts = package / "fonts"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handbook-render/typst").mkdir(parents=True)
            (root / "handbook-render/typst/table-fit.typ").write_bytes(
                (package / "typst/table-fit.typ").read_bytes()
            )
            tokens = design.typst_preamble()
            template = (package / "typst/handbook-typst.typ").read_text()
            source = root / "callout.typ"
            source.write_text(
                tokens
                + "\n"
                + template
                + '\n#v(14cm)\n#callout(title: "Common Pitfall", body: [CALLSTART #lorem(600) CALLLAST])\n'
            )
            subprocess.run(
                [
                    "quarto", "typst", "compile", str(source), "--root", str(root),
                    "--font-path", str(fonts / "inter"),
                    "--font-path", str(fonts / "jetbrains-mono"),
                ],
                check=True,
                capture_output=True,
            )
            pages = subprocess.check_output(
                ["pdftotext", str(root / "callout.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda token: [
                i for i, page in enumerate(pages) if token in page
            ]
            self.assertEqual(containing("CALLSTART"), containing("CALLLAST"))

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
