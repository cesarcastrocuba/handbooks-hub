"""Word figure placement: deferral and bounded scaling decided from measured pages."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from handbook_toolkit.docx_figure_place import (
    LOOKAHEAD,
    Defer,
    Shrink,
    apply_defer,
    apply_shrink,
    callout_runs,
    caption_bottom,
    decide,
    destination_positions,
    figure_units,
    kept_with_next,
    page_break_styles,
    place_figures,
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
    """Heading, lead-in, bookmarked figure, three blocks, next heading."""
    body = ET.Element(W + "body")
    heading = paragraph(body, "1.1 Heading", "Heading2", keep=True)
    lead = paragraph(body, "Figure 1.1 shows it.", "BodyText", keep=True)
    start = ET.SubElement(body, W + "bookmarkStart", {W + "id": "7", W + "name": "B_fig_1_1"})
    picture = image(body)
    caption = paragraph(body, "Figure 1.1: Caption", "ImageCaption")
    end = ET.SubElement(body, W + "bookmarkEnd", {W + "id": "7"})
    first = paragraph(body, "After the figure.", "BodyText")
    second = paragraph(body, "The table below.", "BodyText", keep=True)
    tbl_start = ET.SubElement(body, W + "bookmarkStart", {W + "id": "8", W + "name": "B_tbl_1_1"})
    data = table(body)
    tbl_end = ET.SubElement(body, W + "bookmarkEnd", {W + "id": "8"})
    following = paragraph(body, "1.2 Next", "Heading2", keep=True)
    return body, dict(
        heading=heading, lead=lead, start=start, picture=picture, caption=caption, end=end,
        first=first, second=second, tbl_start=tbl_start, data=data, tbl_end=tbl_end,
        following=following,
    )


class UnitTests(unittest.TestCase):
    def test_unit_carries_its_bookmark_chain_and_section_blocks(self):
        body, n = figure_section()
        (unit,) = figure_units(body)
        self.assertEqual(unit.nodes, [n["start"], n["picture"], n["caption"], n["end"]])
        self.assertIs(unit.chain, n["heading"])
        self.assertIs(unit.before, n["lead"])
        self.assertEqual(
            unit.blocks,
            [[n["first"]], [n["second"]], [n["tbl_start"], n["data"], n["tbl_end"]]],
        )
        self.assertIs(unit.stop, n["following"])

    def test_a_float_never_lands_inside_a_run_of_callouts(self):
        # Figure, example, pitfall and decision: the figure may stop after the example
        # or after the decision, never between the pitfall and the decision.
        body = ET.Element(W + "body")
        paragraph(body, "1.1 Heading", "Heading2", keep=True)
        image(body)
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        example = paragraph(body, "Example.", "BodyText")
        lone = paragraph(body)  # docx_post puts an empty spacer around each callout
        pitfall = callout(body, "Common Pitfall")
        spacers = [paragraph(body), paragraph(body, keep=True)]
        decision = callout(body, "Decision & Trade-off")
        after = paragraph(body, "Closing text.", "BodyText")
        paragraph(body, "1.2 Next", "Heading2", keep=True)
        (unit,) = figure_units(body)
        self.assertTrue(unit.complete)
        self.assertEqual(
            [block[0] for block in unit.blocks], [example, lone, pitfall, *spacers, decision, after]
        )
        self.assertEqual(
            kept_with_next(unit.blocks), [False, False, True, True, True, False, False]
        )
        self.assertEqual(callout_runs(unit.blocks), [False, False, True, True, True, False, False])
        # A callout followed by text, and a lone callout at the end, hold nothing.
        self.assertEqual(kept_with_next(unit.blocks[:3]), [False, False, False])
        # A lookahead that ends inside a run holds the run to its end.
        self.assertEqual(kept_with_next(unit.blocks[:4], complete=False), [False, False, True, True])

    def test_a_table_nested_in_a_callout_does_not_hold_the_callout(self):
        # The options table of a decision keeps its rows together with keepNext;
        # that does not keep the callout with the block after it.
        body = ET.Element(W + "body")
        decision = callout(body, "Decision & Trade-off")
        cell = decision.find(W + "tr/" + W + "tc")
        table(cell, keep_last=True)
        paragraph(cell)
        self.assertEqual(kept_with_next([[decision]]), [False])
        paragraph(cell, keep=True)
        self.assertEqual(kept_with_next([[decision]]), [True])

    def test_a_lookahead_cut_by_its_length_is_not_complete(self):
        body = ET.Element(W + "body")
        image(body)
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        for i in range(LOOKAHEAD + 1):
            paragraph(body, f"Text {i}.", "BodyText")
        self.assertFalse(figure_units(body)[0].complete)
        body.remove(list(body)[-1])
        self.assertTrue(figure_units(body)[0].complete)

    def test_figure_whose_bookmark_closes_late_is_left_alone(self):
        body, n = figure_section()
        body.remove(n["end"])
        body.insert(list(body).index(n["first"]) + 1, n["end"])
        self.assertEqual(figure_units(body), [])

    def test_lookahead_stops_at_another_figure_and_page_break(self):
        body, n = figure_section()
        second_picture = image(ET.Element(W + "body"))
        body.insert(list(body).index(n["second"]), second_picture)
        unit = figure_units(body)[0]
        self.assertEqual(unit.blocks, [[n["first"]]])
        self.assertIs(unit.stop, second_picture)

    def test_a_paragraph_that_starts_a_page_stops_the_lookahead(self):
        body, n = figure_section()
        ET.SubElement(n["second"].find(W + "pPr"), W + "pageBreakBefore")
        unit = figure_units(body)[0]
        self.assertEqual(unit.blocks, [[n["first"]]])
        self.assertIs(unit.stop, n["second"])

    def test_a_style_that_starts_a_page_stops_the_lookahead(self):
        styles = ET.tostring(ET.fromstring(
            f'<w:styles xmlns:w="{NS["w"]}">'
            '<w:style w:type="paragraph" w:styleId="PartTitle"><w:pPr><w:pageBreakBefore/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="ChapterTitle"><w:basedOn w:val="PartTitle"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="Plain"><w:basedOn w:val="ChapterTitle"/>'
            '<w:pPr><w:pageBreakBefore w:val="0"/></w:pPr></w:style>'
            "</w:styles>"
        ))
        breaking = page_break_styles(styles)
        self.assertEqual(breaking, {"PartTitle", "ChapterTitle"})
        body, n = figure_section()
        n["second"].find(W + "pPr/" + W + "pStyle").set(W + "val", "ChapterTitle")
        self.assertEqual(figure_units(body, breaking)[0].blocks, [[n["first"]]])
        self.assertEqual(len(figure_units(body)[0].blocks), 3)  # without styles it is a plain block

    def test_a_direct_no_break_overrides_a_page_starting_style(self):
        body, n = figure_section()
        properties = n["second"].find(W + "pPr")
        properties.find(W + "pStyle").set(W + "val", "ChapterTitle")
        ET.SubElement(properties, W + "pageBreakBefore", {W + "val": "0"})
        self.assertEqual(len(figure_units(body, frozenset({"ChapterTitle"}))[0].blocks), 3)

    def test_page_break_styles_survive_cycles_long_chains_and_missing_styles(self):
        self.assertEqual(page_break_styles(None), frozenset())
        w = f'xmlns:w="{NS["w"]}"'
        cycle = (
            f'<w:styles {w}>'
            '<w:style w:type="paragraph" w:styleId="A"><w:basedOn w:val="B"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="B"><w:basedOn w:val="A"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="C"><w:basedOn w:val="C"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="D"><w:basedOn w:val="Missing"/></w:style>'
            "</w:styles>"
        )
        self.assertEqual(page_break_styles(cycle.encode()), frozenset())
        chain = "".join(
            f'<w:style w:type="paragraph" w:styleId="S{i}"><w:basedOn w:val="S{i + 1}"/></w:style>'
            for i in range(3000)
        )
        flagged = '<w:style w:type="paragraph" w:styleId="S3000"><w:pPr><w:pageBreakBefore/></w:pPr></w:style>'
        styles = f"<w:styles {w}>{chain}{flagged}</w:styles>".encode()
        self.assertEqual(len(page_break_styles(styles)), 3001)


class TableUnitTests(unittest.TestCase):
    def data_table(self, parent, kept=True):
        t = ET.SubElement(parent, W + "tbl")
        properties = ET.SubElement(t, W + "tblPr")
        ET.SubElement(properties, W + "tblStyle", {W + "val": "Table"})
        ET.SubElement(properties, W + "tblLook", {W + "firstRow": "1"})
        for last in (False, False, True):
            cell = ET.SubElement(ET.SubElement(t, W + "tr"), W + "tc")
            paragraph(cell, "cell", keep=kept and not last)
        return t

    def test_a_kept_table_is_deferred_like_a_figure_but_never_past_a_table(self):
        body = ET.Element(W + "body")
        paragraph(body, "Table 1.1 lists them.", keep=True)
        first = self.data_table(body)
        paragraph(body, "Table 1.1: Caption", "ImageCaption")
        text = paragraph(body, "After the table.")
        second = self.data_table(body)
        paragraph(body, "Table 1.2: Caption", "ImageCaption")
        units = figure_units(body)
        self.assertEqual([u.kind for u in units], ["table", "table"])
        self.assertIs(units[0].image, first)
        self.assertEqual(units[0].blocks, [[text]])
        self.assertIs(units[0].stop, second)

    def test_a_figure_never_passes_a_captioned_table(self):
        body = ET.Element(W + "body")
        paragraph(body, "Figure 1.1 shows it.", keep=True)
        image(body)
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        text = paragraph(body, "After the figure.")
        lead = paragraph(body, "Table 1.1 lists them.", keep=True)
        table = self.data_table(body)
        paragraph(body, "Table 1.1: Caption", "ImageCaption")
        figure = figure_units(body)[0]
        self.assertEqual(figure.kind, "figure")
        self.assertEqual(figure.blocks, [[text], [lead]])  # the lead-in is kept with its table
        self.assertIs(figure.stop, table)

    def test_a_table_that_breaks_across_pages_is_not_a_unit(self):
        body = ET.Element(W + "body")
        self.data_table(body, kept=False)
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
            blocks=[(5, 430.0), (5, 500.0), (5, 560.0), (6, 70.0)],
            bound=[False, True, False],
        )
        values.update(changes)
        return decide(**values)

    def test_deferral_is_preferred_to_scaling(self):
        self.assertEqual(self.decide(), Defer(1))

    def test_a_figure_that_nearly_fits_is_scaled_when_nothing_can_move_up(self):
        action = self.decide(blocks=[(5, 430.0), (6, 70.0)], bound=[False])
        # needs 342 - 300 + 10 = 52 pt less: 0.827 of its height, 0.827 of natural size
        self.assertIsInstance(action, Shrink)
        self.assertAlmostEqual(action.scale, (300 - 52) / 300, places=3)

    def test_scaling_never_goes_below_the_natural_floor(self):
        action = self.decide(natural=0.8)  # 0.8 x 0.827 < 0.75
        self.assertEqual(action, Defer(1))  # block 2 keeps with block 3: stop after block 1

    def test_deferral_moves_whole_unbound_blocks_that_fit(self):
        # Without a raster size there is no scaling; the chain (30 pt) and two blocks
        # (130 pt) fit the 290 pt that remain, the third block is on the next page.
        action = self.decide(natural=None, bound=[False, False, False])
        self.assertEqual(action, Defer(2))

    def test_a_paragraph_that_breaks_across_pages_fills_the_gap(self):
        blocks = [(5, 430.0), (5, 700.0), (6, 70.0)]  # 270 pt block, 280 pt left
        self.assertEqual(
            self.decide(natural=None, blocks=blocks, bound=[False, False], splits=[True, False]),
            Defer(1),
        )
        self.assertIsNone(
            self.decide(natural=None, blocks=blocks, bound=[False, False], splits=[False, False])
        )

    def test_the_last_block_on_the_page_is_measured_to_the_end_of_the_text(self):
        # A callout ends the figure's page; the next block starts page 6. It never
        # breaks across pages, so it ends where the page's text ends.
        blocks = [(5, 430.0), (6, 70.0)]
        fits = dict(natural=None, blocks=blocks, bound=[False], whole=[True])
        self.assertEqual(self.decide(page_end=650.0, **fits), Defer(1))  # 30 + 220 <= 290
        self.assertIsNone(self.decide(page_end=720.0, **fits))  # 30 + 290 > 290
        self.assertIsNone(self.decide(page_end=650.0, **{**fits, "whole": [False]}))
        self.assertIsNone(self.decide(page_end=650.0, **{**fits, "bound": [True]}))

    def test_a_float_stops_in_front_of_a_callout_run_it_cannot_pass(self):
        # Example (60 pt), pitfall (70 pt), decision (300 pt) after a 30 pt chain:
        # the example and the pitfall fit the 290 pt, the decision does not. Held
        # together, the figure stops after the example, not between the callouts.
        blocks = [(5, 430.0), (5, 490.0), (5, 560.0), (6, 70.0)]
        free = dict(natural=None, blocks=blocks, whole=[False, True, True])
        self.assertEqual(self.decide(bound=[False, False, False], **free), Defer(2))
        self.assertEqual(self.decide(bound=[False, True, False], **free), Defer(1))

    def test_a_float_goes_after_a_callout_run_whose_first_callout_fits(self):
        # Same page: the pitfall fits the gap, the decision does not. The figure
        # moves after the decision, which starts the next page; the pitfall fills
        # the gap and stays next to its decision.
        blocks = [(5, 430.0), (5, 490.0), (5, 560.0), (6, 70.0)]
        run = dict(natural=None, blocks=blocks, whole=[False, True, True], page_end=700.0)
        self.assertEqual(self.decide(bound=[False, True, False], runs=[False, True, False], **run),
                         Defer(3))
        # The decision is kept with what follows: the figure stays in front of the run.
        self.assertEqual(self.decide(bound=[False, True, True], runs=[False, True, False], **run),
                         Defer(1))
        # The pitfall does not fit the gap either.
        self.assertEqual(
            self.decide(bound=[False, True, False], runs=[False, True, False],
                        previous_bottom=620.0, **run),
            Defer(1),
        )
        # The decision (210 pt) and a 490 pt figure group exceed the 696 pt left on
        # the next page: the figure stays in front of the run.
        tall = dict(caption=(5, 548.0), caption_end=560.0)
        self.assertEqual(self.decide(bound=[False, True, False], runs=[False, True, False],
                                     **tall, **{**run, "page_end": 770.0}),
                         Defer(1))
        self.assertEqual(self.decide(bound=[False, True, False], runs=[False, True, False],
                                     **{**run, "page_end": 700.0}, **tall),
                         Defer(3))  # a 140 pt decision fits with it
        # The run continues past the lookahead.
        self.assertEqual(self.decide(bound=[False, True, True], runs=[False, True, True], **run),
                         Defer(1))

    def test_small_gaps_and_groups_not_at_the_top_are_left_alone(self):
        self.assertIsNone(self.decide(previous_bottom=700.0))
        self.assertIsNone(self.decide(group=(5, 200.0)))
        self.assertIsNone(self.decide(group=(1, 70.0)))
        self.assertIsNone(self.decide(caption=(6, 70.0)))
        self.assertIsNone(self.decide(previous_bottom=None))

    def test_no_block_fits_and_no_scaling_means_no_action(self):
        self.assertIsNone(self.decide(natural=None, blocks=[(5, 430.0), (6, 70.0)], bound=[False]))
        self.assertIsNone(self.decide(natural=None, bound=[True, True, True]))

    def test_caption_bottom_stops_at_the_paragraph_gap(self):
        words = [(400.0, 412.0), (413.0, 425.0), (440.0, 452.0)]
        self.assertEqual(caption_bottom(words, 400.0), 425.0)
        self.assertIsNone(caption_bottom(words, 600.0))


class ApplyTests(unittest.TestCase):
    def test_deferral_keeps_bookmarks_and_releases_the_lead_in(self):
        body, n = figure_section()
        (unit,) = figure_units(body)
        apply_defer(body, unit, 1)
        order = list(body)
        self.assertEqual(
            order[order.index(n["first"]) + 1 : order.index(n["first"]) + 5],
            [n["start"], n["picture"], n["caption"], n["end"]],
        )
        self.assertIsNone(n["lead"].find(W + "pPr/" + W + "keepNext"))
        self.assertIsNotNone(n["heading"].find(W + "pPr/" + W + "keepNext"))

    def test_deferral_after_a_table_lands_after_its_closing_bookmark(self):
        body, n = figure_section()
        (unit,) = figure_units(body)
        apply_defer(body, unit, 3)
        order = list(body)
        self.assertEqual(order.index(n["start"]), order.index(n["tbl_end"]) + 1)
        self.assertEqual(order.index(n["following"]), order.index(n["end"]) + 1)

    def test_scaling_changes_both_extents(self):
        body = ET.Element(W + "body")
        picture = image(body, 4000000, 3000000)
        extents = [e for e in picture.iter() if e.tag in {WP + "extent", A + "ext"}]
        apply_shrink(extents, 0.5)
        self.assertEqual([(e.get("cx"), e.get("cy")) for e in extents], [("2000000", "1500000")] * 2)


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


def _package(path: Path, body: ET.Element) -> None:
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
        "</Types>"
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


@unittest.skipUnless(
    shutil.which("soffice") and shutil.which("pdfinfo") and shutil.which("pdftotext"),
    "LibreOffice and Poppler are required for the pagination probe",
)
class LibreOfficeTests(unittest.TestCase):
    def test_text_after_a_figure_fills_the_page_it_would_leave_empty(self):
        sentence = "Body text that fills the page and keeps the reader moving. " * 9
        body = ET.Element(W + "body")
        for _ in range(5):  # about 35% of page 1 stays free
            paragraph(body, sentence)
        paragraph(body, "Figure 1.1 shows the flow.", keep=True)
        ET.SubElement(body, W + "bookmarkStart", {W + "id": "7", W + "name": "B_fig_1_1"})
        image(body, cx=5400000, cy=5400000)  # 15 cm square: does not fit the rest of page 1
        paragraph(body, "Figure 1.1: Caption", "ImageCaption")
        ET.SubElement(body, W + "bookmarkEnd", {W + "id": "7"})
        for i in range(4):
            paragraph(body, f"FOLLOW{i} " + "Short paragraph after the figure. " * 4)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.docx"
            _package(path, body)
            report = place_figures(path, FONTS, required=True)
            self.assertIn("0 figures scaled and 1 floats deferred (0 tables)", report["docx_figure_placement"])
            pdf = Path(tmp) / "out"
            subprocess.run(
                ["soffice", f"-env:UserInstallation=file://{tmp}/profile", "--headless",
                 "--convert-to", "pdf", "--outdir", str(pdf), str(path)],
                check=True, capture_output=True,
            )
            pages = subprocess.check_output(
                ["pdftotext", str(pdf / "book.pdf"), "-"], text=True
            ).split("\f")
            first = pages[0]
            self.assertIn("FOLLOW0", first)  # the text after the figure moved up
            self.assertNotIn("Figure 1.1: Caption", first)


if __name__ == "__main__":
    unittest.main()
