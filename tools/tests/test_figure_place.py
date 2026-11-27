"""Word figure placement: bounded scaling decided from measured pages; nothing moves."""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from handbook_toolkit.docx_figure_place import (
    MIN_GAP,
    MIN_NATURAL,
    PRINT_SCALE,
    SAFETY,
    Shrink,
    apply_shrink,
    caption_bottom,
    decide,
    destination_positions,
    figure_units,
    place_figures,
    print_scale,
)
from handbook_toolkit.build_types import BuildError
from handbook_toolkit.docx_xml import NS, W
from test_figure_layout import png

WP = "{" + NS["wp"] + "}"
A = "{" + NS["a"] + "}"
R = "{" + NS["r"] + "}"
FONTS = Path(__file__).resolve().parents[1] / "src/handbook_toolkit/render_data/fonts"


def paragraph(parent, text="", style=None, keep=False):
    p = ET.SubElement(parent, W + "p")
    if style or keep:
        properties = ET.SubElement(p, W + "pPr")
        if style:
            ET.SubElement(properties, W + "pStyle", {W + "val": style})
        if keep:
            ET.SubElement(properties, W + "keepNext", {W + "val": "1"})
    if text:
        ET.SubElement(ET.SubElement(p, W + "r"), W + "t").text = text
    return p


def image(parent, cx=4000000, cy=3000000, rid="rId9"):
    p = paragraph(parent, keep=True)
    drawing = ET.SubElement(ET.SubElement(p, W + "r"), W + "drawing")
    inline = ET.SubElement(drawing, WP + "inline")
    ET.SubElement(inline, WP + "extent", {"cx": str(cx), "cy": str(cy)})
    ET.SubElement(inline, WP + "docPr", {"id": "1", "name": "Picture"})
    graphic = ET.SubElement(ET.SubElement(inline, A + "graphic"), A + "graphicData")
    pic = ET.SubElement(graphic, "{" + NS["pic"] + "}pic")
    ET.SubElement(ET.SubElement(pic, "{" + NS["pic"] + "}blipFill"), A + "blip", {R + "embed": rid})
    xfrm = ET.SubElement(ET.SubElement(pic, "{" + NS["pic"] + "}spPr"), A + "xfrm")
    ET.SubElement(xfrm, A + "ext", {"cx": str(cx), "cy": str(cy)})
    return p


def table(parent, keep_last=False):
    t = ET.SubElement(parent, W + "tbl")
    for last in (False, True):
        row = ET.SubElement(t, W + "tr")
        cell = ET.SubElement(row, W + "tc")
        paragraph(cell, "cell", keep=(not last) or keep_last)
    return t


def callout(parent, text):
    t = ET.SubElement(parent, W + "tbl")
    ET.SubElement(ET.SubElement(t, W + "tblPr"), W + "tblStyle", {W + "val": "CalloutBox"})
    row = ET.SubElement(t, W + "tr")
    ET.SubElement(ET.SubElement(row, W + "trPr"), W + "cantSplit")
    paragraph(ET.SubElement(row, W + "tc"), text)
    return t


def figure_section():
    """Heading, lead-in, bookmarked figure, caption, text, next heading."""
    body = ET.Element(W + "body")
    heading = paragraph(body, "1.1 Heading", "Heading2", keep=True)
    lead = paragraph(body, "Figure 1.1 shows it.", "BodyText", keep=True)
    ET.SubElement(body, W + "bookmarkStart", {W + "id": "7", W + "name": "B_fig_1_1"})
    picture = image(body)
    caption = paragraph(body, "Figure 1.1: Caption", "ImageCaption")
    ET.SubElement(body, W + "bookmarkEnd", {W + "id": "7"})
    paragraph(body, "After the figure.", "BodyText")
    paragraph(body, "1.2 Next", "Heading2", keep=True)
    return body, dict(heading=heading, lead=lead, picture=picture, caption=caption)


def body_order(path: Path) -> list[str]:
    """Text of every body block, with FIGURE for an image paragraph."""
    with ZipFile(path) as package:
        body = ET.fromstring(package.read("word/document.xml")).find(W + "body")
    return [
        "FIGURE" if node.find(".//" + W + "drawing") is not None
        else "".join(t.text or "" for t in node.iter(W + "t"))
        for node in body if node.tag in {W + "p", W + "tbl"}
    ]


class UnitTests(unittest.TestCase):
    def test_unit_carries_its_caption_and_keep_chain(self):
        body, n = figure_section()
        (unit,) = figure_units(body)
        self.assertIs(unit.image, n["picture"])
        self.assertIs(unit.caption, n["caption"])
        self.assertIs(unit.chain, n["heading"])  # heading and lead-in are kept with it

    def test_an_image_without_a_caption_is_not_a_unit(self):
        body = ET.Element(W + "body")
        image(body)
        paragraph(body, "Plain text.", "BodyText")
        self.assertEqual(figure_units(body), [])

    def test_tables_are_never_units(self):
        body = ET.Element(W + "body")
        table(body)
        paragraph(body, "Table 1.1: Caption", "ImageCaption")
        self.assertEqual(figure_units(body), [])


class DecisionTests(unittest.TestCase):
    TOP, BOTTOM = 68.0, 774.0  # A4 with 2.4 cm margins, points from the top

    def decide(self, **changes):
        values = dict(
            top=self.TOP,
            bottom=self.BOTTOM,
            group=(5, 70.0),
            image=(5, 100.0),
            caption=(5, 400.0),
            caption_end=412.0,
            previous_bottom=474.0,  # 300 pt free on page 4
            figure_height=300.0,
            natural=1.0,
        )
        values.update(changes)
        return decide(**values)

    def test_a_figure_that_nearly_fits_is_scaled(self):
        action = self.decide()
        # needs 342 - 300 + 10 = 52 pt less: 0.827 of its height, 0.827 of natural size
        self.assertIsInstance(action, Shrink)
        self.assertAlmostEqual(action.scale, (300 - 52) / 300, places=3)

    def test_scaling_never_goes_below_the_natural_floor(self):
        self.assertIsNone(self.decide(natural=0.8))  # 0.8 x 0.827 < 0.75
        self.assertIsNone(self.decide(natural=None))  # no raster size, no scaling

    def test_a_figure_that_fits_or_cannot_shrink_enough_is_left_alone(self):
        self.assertIsNone(self.decide(caption_end=300.0))  # already fits the gap
        self.assertIsNone(self.decide(previous_bottom=700.0, figure_height=60.0))
        self.assertIsNone(self.decide(figure_height=40.0))  # needs 52 pt of a 40 pt figure
        self.assertIsNone(self.decide(caption_end=360.0001))  # 0.0001 pt short: scale rounds to 1

    def test_small_gaps_and_groups_not_at_the_top_are_left_alone(self):
        self.assertIsNone(self.decide(previous_bottom=700.0))
        self.assertIsNone(self.decide(group=(5, 200.0)))
        self.assertIsNone(self.decide(group=(1, 70.0)))
        self.assertIsNone(self.decide(caption=(6, 70.0)))
        self.assertIsNone(self.decide(image=(6, 100.0)))
        self.assertIsNone(self.decide(previous_bottom=None))

    def test_the_gap_threshold_rejects_a_gap_the_floor_would_allow(self):
        # 90 pt of room is below 15% of the 706 pt body, but the fit would be
        # 0.75 of a 100 pt figure, exactly at the natural floor: only the gate
        # rejects it. Setting MIN_GAP to 0 makes this case scale.
        self.assertIsNone(
            self.decide(previous_bottom=684.0, caption_end=175.0, figure_height=100.0)
        )
        # The same geometry with 110 pt of room (above the gate) scales.
        self.assertIsInstance(
            self.decide(previous_bottom=664.0, caption_end=175.0, figure_height=100.0),
            Shrink,
        )

    def test_caption_bottom_stops_at_the_paragraph_gap(self):
        words = [(400.0, 412.0), (413.0, 425.0), (440.0, 452.0)]
        self.assertEqual(caption_bottom(words, 400.0), 425.0)
        self.assertIsNone(caption_bottom(words, 600.0))


class ApplyTests(unittest.TestCase):
    def test_scaling_changes_both_extents(self):
        body = ET.Element(W + "body")
        picture = image(body, 4000000, 3000000)
        extents = [e for e in picture.iter() if e.tag in {WP + "extent", A + "ext"}]
        apply_shrink(extents, 0.5)
        self.assertEqual([(e.get("cx"), e.get("cy")) for e in extents], [("2000000", "1500000")] * 2)


class PrintScaleTests(unittest.TestCase):
    def scaled(self, cx, natural_px):
        """A figure printed `cx` EMU wide from a PNG `natural_px` wide at `ppi`."""
        body = ET.Element(W + "body")
        picture = image(body, cx, cx // 2)
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        members = {"word/media/a.png": png(natural_px, natural_px // 2)}
        count = print_scale(body, members, {"rId9": "media/a.png"})
        extent = picture.find(".//" + WP + "extent")
        return count, int(extent.get("cx")) / cx

    def test_every_figure_prints_at_the_print_scale(self):
        natural = 4 * 914400  # 800 px at 200 ppi is 4 in
        count, factor = self.scaled(natural, 800)
        self.assertEqual(count, 1)
        self.assertAlmostEqual(factor, PRINT_SCALE, places=3)

    def test_the_natural_floor_limits_the_print_scale(self):
        natural = 4 * 914400
        _, factor = self.scaled(int(natural * 0.8), 800)  # already at 0.8 of natural size
        self.assertAlmostEqual(factor, 0.75 / 0.8, places=3)
        count, factor = self.scaled(int(natural * 0.7), 800)  # below the floor: untouched
        self.assertEqual((count, factor), (0, 1.0))

    def test_a_factor_that_rounds_to_one_is_not_counted(self):
        # 0.7500075 of the natural size gives 0.99999, which rounds to a 1.0
        # no-op: the extent is unchanged, so neither the count nor the report
        # may call it scaled.
        natural = 4 * 914400
        count, factor = self.scaled(int(natural * 0.7500075), 800)
        self.assertEqual((count, factor), (0, 1.0))


class ConstantParityTests(unittest.TestCase):
    def test_word_and_typst_share_the_gap_constants(self):
        # docs/publication-build.md says the two sets change together; a
        # one-sided edit must fail here instead of drifting the editions.
        typst = (
            Path(__file__).resolve().parents[1]
            / "src/handbook_toolkit/render_data/typst/table-fit.typ"
        ).read_text()

        def value(name):
            match = re.search(rf"^#let {name} = ([\d.]+)", typst, re.MULTILINE)
            self.assertIsNotNone(match, name)
            return float(match[1])

        self.assertEqual(value("handbook-print-scale"), PRINT_SCALE)
        self.assertEqual(value("handbook-min-gap"), MIN_GAP)
        self.assertEqual(value("handbook-min-natural"), MIN_NATURAL)
        self.assertEqual(value("handbook-gap-safety"), SAFETY)


class MeasurementTests(unittest.TestCase):
    def test_destinations_carry_page_and_height(self):
        listing = (
            "Page  Destination                 Name\n"
            '  48 [ XYZ   62  241 null      ] "FigPlaceG0"\n'
            '  49 [ XYZ   62  702.5 null      ] "FigPlaceC0"\n'
        )
        with patch("handbook_toolkit.docx_pages._run", return_value=listing):
            found = destination_positions(Path("x.pdf"), {"FigPlaceG0", "FigPlaceC0", "Missing"})
        self.assertEqual(found, {"FigPlaceG0": (48, 241.0), "FigPlaceC0": (49, 702.5)})

    def test_missing_tools_leave_the_document_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            path.write_bytes(b"untouched")
            with patch("handbook_toolkit.docx_figure_place.shutil.which", return_value=None):
                report = place_figures(path, FONTS, required=False)
                self.assertIn("not measured", report["docx_figure_placement"])
                with self.assertRaises(BuildError):
                    place_figures(path, FONTS, required=True)
            self.assertEqual(path.read_bytes(), b"untouched")

    def test_a_failed_measurement_leaves_the_document_unchanged(self):
        body, _ = figure_section()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, body)
            before = path.read_bytes()
            with patch("handbook_toolkit.docx_figure_place.shutil.which", return_value="/usr/bin/x"), \
                    patch("handbook_toolkit.docx_pages._run", side_effect=BuildError("probe timed out")):
                report = place_figures(path, FONTS, required=False)
                self.assertIn("not applied", report["docx_figure_placement"])
                self.assertEqual(path.read_bytes(), before)
                with self.assertRaises(BuildError):
                    place_figures(path, FONTS, required=True)
            self.assertEqual(path.read_bytes(), before)


def _package(path: Path, body: ET.Element, styles: str | None = None) -> None:
    document = ET.Element(W + "document")
    document.append(body)
    section = ET.SubElement(body, W + "sectPr")
    ET.SubElement(section, W + "pgSz", {W + "w": "11906", W + "h": "16838"})
    ET.SubElement(
        section,
        W + "pgMar",
        {W + "top": "1361", W + "bottom": "1361", W + "left": "1247", W + "right": "1247",
         W + "header": "708", W + "footer": "708", W + "gutter": "0"},
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        + (
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            if styles is not None
            else ""
        )
        + "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure.png"/>'
        "</Relationships>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/_rels/document.xml.rels", document_rels)
        archive.writestr("word/media/figure.png", png(1200, 900))
        archive.writestr("word/document.xml", ET.tostring(document))
        if styles is not None:
            archive.writestr("word/styles.xml", styles)


@unittest.skipUnless(
    shutil.which("soffice") and shutil.which("pdfinfo") and shutil.which("pdftotext"),
    "LibreOffice and Poppler are required for the pagination probe",
)
class LibreOfficeTests(unittest.TestCase):
    SENTENCE = "Body text that fills the page and keeps the reader moving. " * 9

    def section(self, cx, cy, fill=5):
        """Text that fills part of page 1, a lead-in, a figure, then a pitfall and its decision."""
        body = ET.Element(W + "body")
        for _ in range(fill):
            paragraph(body, self.SENTENCE)
        paragraph(body, "Figure 1.1 shows the flow.", keep=True)
        ET.SubElement(body, W + "bookmarkStart", {W + "id": "7", W + "name": "B_fig_1_1"})
        image(body, cx=cx, cy=cy)
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        ET.SubElement(body, W + "bookmarkEnd", {W + "id": "7"})
        for i in range(2):
            paragraph(body, f"FOLLOW{i} " + "Short paragraph after the figure. " * 4)
        paragraph(body)
        callout(body, "PITFALL " + "A warning about a common mistake and its cost. " * 10)
        paragraph(body)
        paragraph(body, keep=True)
        decision = callout(body, "DECISION Which option? " + "Each option has a cost. " * 14)
        table(decision.find(W + "tr").find(W + "tc"), keep_last=True)
        paragraph(body)
        paragraph(body, "1.2 Next", "Heading2", keep=True)
        return body

    def test_nothing_moves_in_front_of_a_figure_that_does_not_fit(self):
        # A 15 cm square figure cannot be scaled into the gap: the page stays part
        # empty and every block keeps the author's order.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, self.section(5400000, 5400000))
            before = body_order(path)
            report = place_figures(path, FONTS, required=True)
            self.assertIn("figures scaled to fit page gaps: 0", report["docx_figure_placement"])
            self.assertIn("no figure or table moved", report["docx_figure_placement"])
            self.assertEqual(body_order(path), before)

    def test_a_figure_that_nearly_fits_is_scaled_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, self.section(NEAR_CX, NEAR_CY, fill=NEAR_FILL))
            before = body_order(path)
            # The gap rule on its own: the print scale is tested separately.
            with patch("handbook_toolkit.docx_figure_place.PRINT_SCALE", 1.0):
                report = place_figures(path, FONTS, required=True)
            self.assertIn("figures scaled to fit page gaps: 1", report["docx_figure_placement"])
            self.assertEqual(body_order(path), before)
            with ZipFile(path) as package:
                extent = ET.fromstring(package.read("word/document.xml")).find(".//" + WP + "extent")
            self.assertLess(int(extent.get("cy")), NEAR_CY)

    def test_the_print_scale_runs_before_the_gap_pass(self):
        # At 85% this figure fits and the gap pass leaves it alone; at its full
        # size it nearly fits and the gap pass scales it. If print_scale ran
        # after the pass, this page would report a gap fit and the final extent
        # would be the printed size of a shrunk figure.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, self.section(ORDER_CX, ORDER_CY, fill=ORDER_FILL))
            before = body_order(path)
            report = place_figures(path, FONTS, required=True)
            self.assertEqual(body_order(path), before)
            with ZipFile(path) as package:
                extent = ET.fromstring(package.read("word/document.xml")).find(
                    ".//" + WP + "extent"
                )
            self.assertEqual(int(extent.get("cy")), int(ORDER_CY * PRINT_SCALE))
        self.assertIn(
            "figures at print scale: 1; figures scaled to fit page gaps: 0",
            report["docx_figure_placement"],
        )


# Natural width, 299 pt tall. With the packaged Inter metrics the gap rule scaled this figure in
# a probe of heights 3650000-4100000 EMU (3900000 was the one exception, where it was left alone).
NEAR_CX, NEAR_CY, NEAR_FILL = 5486400, 3800000, 5

# At the full size this figure nearly fits its page and the gap pass shrinks it; at the 85% print
# scale it fits, so the unpatched pass reports no gap fit. Measured with the packaged Inter metrics.
ORDER_CX, ORDER_CY, ORDER_FILL = 5486400, 3600000, 5


if __name__ == "__main__":
    unittest.main()
