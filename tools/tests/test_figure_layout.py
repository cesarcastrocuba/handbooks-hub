"""Synthetic raster metadata and staging protections."""

from pathlib import Path
import struct, tempfile, unittest, zlib
from handbook_toolkit.figure_layout import (
    RasterSize,
    figure_width,
    png_size,
    stage_figures,
)
from handbook_toolkit.page_geometry import text_width_inches


def png(width=904, height=893, phys=True):
    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + (chunk(b"pHYs", struct.pack(">IIB", 7874, 7874, 1)) if phys else b"")
        + chunk(b"IDAT", zlib.compress((b"\0" + b"\xff" * (width * 3)) * height))
        + chunk(b"IEND", b"")
    )


class FigureLayoutTests(unittest.TestCase):
    def test_natural_and_tall_caps_and_stated_maximum(self):
        column = text_width_inches({})
        self.assertAlmostEqual(column, 16.6 / 2.54)
        self.assertEqual(figure_width(RasterSize(904, 893, 199.9996), column), 69)
        self.assertEqual(figure_width(RasterSize(1059, 1046, 199.9996), column), 81)
        self.assertEqual(figure_width(RasterSize(1000, 3000, 200), column), 41)
        self.assertEqual(figure_width(RasterSize(904, 893, 200), column, 50), 50)
        self.assertEqual(figure_width(RasterSize(1, 1, 200), column), 0)

    def test_custom_geometry_is_shared(self):
        self.assertAlmostEqual(
            text_width_inches({"format": {"typst": {"margin": {"x": "1cm"}}}}),
            19 / 2.54,
        )

    def test_stages_attributes_not_pixels_or_code_or_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            data = png()
            (w / "figure.png").write_bytes(data)
            (w / "plain.png").write_bytes(png(3, 3, False))
            (w / "vector.svg").write_text("<svg/>")
            text = '![A](figure.png){#fig-a width="100%"}\n![B](plain.png){#fig-b width="80%"}\n![C](vector.svg){#fig-c width="90%"}\n`![A](figure.png)`\n````\n![A](figure.png)\n```\n![A](figure.png)\n````\n'
            (w / "chapter.qmd").write_text(text)
            records = stage_figures(w, ["chapter.qmd"], {})
            result = (w / "chapter.qmd").read_text()
            self.assertIn('width="69%"', result)
            self.assertIn('![C](vector.svg){#fig-c width="90%"}', result)
            self.assertIn('width="80%"', result)
            self.assertEqual(result.count(".handbook-raster"), 2)
            self.assertEqual((w / "figure.png").read_bytes(), data)
            self.assertEqual(len(records), 2)
            self.assertEqual(png_size(w / "figure.png"), RasterSize(904, 893, 199.9996))
            self.assertIsNone(png_size(w / "plain.png"))

    def test_remote_raster_receives_blend_class_without_fetching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "test.qmd"
            path.write_text(
                '![Remote](https://example.invalid/figure.png){width="70%"}'
            )
            records = stage_figures(root, ["test.qmd"], {})
            self.assertIn('width="70%"', path.read_text())
            self.assertIn(".handbook-raster", path.read_text())
            self.assertIsNone(records[0]["size"])
