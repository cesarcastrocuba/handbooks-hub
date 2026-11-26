"""Transparent print copies: colour-to-alpha round trip, determinism and staging."""

from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from handbook_toolkit.artifact_optimize import PNG_SIGNATURE, _chunk, _chunks, _ihdr, png_pixels
from handbook_toolkit.figure_layout import png_size
from handbook_toolkit.print_figures import (
    PRINT_FIGURES,
    stage_print_figures,
    transparent_png,
)


def png(width, height, channels, pixels, phys=True):
    color = {1: 0, 2: 4, 3: 2, 4: 6}[channels]
    rows = b"".join(
        b"\x00" + bytes(pixels[offset : offset + width * channels])
        for offset in range(0, len(pixels), width * channels)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0))
        + (_chunk(b"pHYs", struct.pack(">IIB", 7874, 7874, 1)) if phys else b"")
        + _chunk(b"IDAT", zlib.compress(rows, 9))
        + _chunk(b"IEND", b"")
    )


def white_border(width, height, channels, fill=(20, 40, 60)):
    pixels = bytearray([255] * (width * height * channels))
    if channels == 4:
        for index in range(0, len(pixels), 4):
            pixels[index + 3] = 255
    for y in range(height // 4, 3 * height // 4):
        for x in range(width // 4, 3 * width // 4):
            offset = (y * width + x) * channels
            for channel in range(3):
                pixels[offset + channel] = fill[channel]
    return bytes(pixels)


def reference(data):
    """Straightforward per-pixel colour-to-alpha; the fast path must match its bytes."""
    width, height, _, color_type, *_ , interlace = _ihdr(data)
    assert not interlace
    pixels = png_pixels(data)
    channels = 3 if color_type == 2 else 4
    rgba = bytearray(width * height * 4)
    for index in range(width * height):
        source = index * channels
        alpha_in = pixels[source + 3] if channels == 4 else 255
        over = [
            (pixels[source + channel] * alpha_in + 255 * (255 - alpha_in) + 127) // 255
            for channel in range(3)
        ]
        alpha = max(255 - value for value in over)
        if alpha == 0:
            continue
        target = index * 4
        for channel in range(3):
            value = ((over[channel] - 255 + alpha) * 255 + alpha // 2) // alpha
            rgba[target + channel] = min(255, max(0, value))
        rgba[target + 3] = alpha
    row = width * 4
    filtered = b"".join(
        b"\x00" + rgba[offset : offset + row] for offset in range(0, len(rgba), row)
    )
    compressed = zlib.compress(filtered, 9)
    out = [PNG_SIGNATURE]
    for kind, payload in _chunks(data):
        if kind == b"IHDR":
            out.append(_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        elif kind == b"IDAT":
            continue
        elif kind == b"IEND":
            out.append(_chunk(b"IDAT", compressed))
            out.append(_chunk(b"IEND", payload))
        elif kind not in {b"tRNS", b"PLTE", b"bKGD", b"hIST"}:
            out.append(_chunk(kind, payload))
    return b"".join(out)


def over_white(pixels, index, channels):
    alpha = pixels[index * channels + 3] / 255 if channels == 4 else 1.0
    return [
        round(pixels[index * channels + channel] * alpha + 255 * (1 - alpha))
        for channel in range(3)
    ]


class ColourToAlphaTests(unittest.TestCase):
    def test_rgb_round_trip_over_white(self):
        width = height = 24
        source = png(width, height, 3, white_border(width, height, 3))
        result = transparent_png(source)
        self.assertIsNotNone(result)
        self.assertEqual(_ihdr(result)[3], 6)
        pixels = png_pixels(result)
        original = white_border(width, height, 3)
        for index in range(width * height):
            expected = over_white(original, index, 3)
            actual = over_white(pixels, index, 4)
            self.assertLessEqual(
                max(abs(a - b) for a, b in zip(actual, expected)), 1, index
            )
        self.assertEqual(pixels[3], 0)
        size = self._write(result)
        self.assertEqual((size.width, size.height), (width, height))

    def _write(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "figure.png"
            path.write_bytes(data)
            return png_size(path)

    def test_rgba_existing_alpha_round_trip(self):
        width = height = 24
        pixels = bytearray(white_border(width, height, 4))
        for y in range(8, 16):
            for x in range(8, 16):
                offset = (y * width + x) * 4
                pixels[offset : offset + 4] = bytes((200, 30, 80, 128))
        source = png(width, height, 4, pixels)
        result = transparent_png(source)
        self.assertIsNotNone(result)
        converted = png_pixels(result)
        for index in range(width * height):
            self.assertLessEqual(
                max(
                    abs(a - b)
                    for a, b in zip(
                        over_white(converted, index, 4), over_white(pixels, index, 4)
                    )
                ),
                1,
                index,
            )

    def test_fast_path_matches_reference_bytes(self):
        colours = [(20, 40, 60), (0, 0, 0), (242, 242, 242), (255, 254, 252), (12, 200, 99)]
        pixels = bytearray(white_border(24, 24, 3))
        for index in range(24 * 24):
            if pixels[index * 3] != 255:
                pixels[index * 3 : index * 3 + 3] = bytes(colours[index % len(colours)])
        source = png(24, 24, 3, pixels)
        self.assertEqual(transparent_png(source), reference(source))

    def test_fast_path_matches_reference_for_existing_alpha(self):
        pixels = bytearray(white_border(24, 24, 4))
        for index in range(24 * 24):
            pixels[index * 4 + 3] = (0, 64, 128, 255)[index % 4]
        source = png(24, 24, 4, pixels)
        self.assertEqual(transparent_png(source), reference(source))

    def test_deterministic_output(self):
        source = png(24, 24, 3, white_border(24, 24, 3))
        self.assertEqual(transparent_png(source), transparent_png(source))

    def test_non_white_border_is_skipped(self):
        pixels = bytes([12, 34, 56] * (24 * 24))
        self.assertIsNone(transparent_png(png(24, 24, 3, pixels)))

    def test_palette_png_is_skipped(self):
        source = png(24, 24, 1, bytes([0] * (24 * 24)))
        self.assertIsNone(transparent_png(source))


class StagingTests(unittest.TestCase):
    def test_png_references_move_to_the_print_copy_and_are_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            images = workspace / "manuscript/images"
            images.mkdir(parents=True)
            source = png(24, 24, 3, white_border(24, 24, 3))
            (images / "figure.png").write_bytes(source)
            (images / "photo.jpg").write_bytes(b"not a png")
            (images / "vector.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
            chapter = workspace / "manuscript/chapter.qmd"
            original = (
                "![A figure](images/figure.png){#fig-a width=\"80%\"}\n\n"
                "![A photo](images/photo.jpg){#fig-b}\n\n"
                "![A vector](images/vector.svg){#fig-c}\n"
            )
            chapter.write_text(original)
            figures = stage_print_figures(workspace, ["manuscript/chapter.qmd"])
            staged = chapter.read_text()
            print_path = workspace / PRINT_FIGURES / "manuscript/images/figure.png"
            self.assertTrue(print_path.is_file())
            self.assertIn("handbook-render/print-figures/manuscript/images/figure.png", staged)
            self.assertIn("images/photo.jpg", staged)
            self.assertIn("images/vector.svg", staged)
            self.assertEqual(_ihdr(print_path.read_bytes())[3], 6)
            self.assertEqual(png_size(print_path), png_size(images / "figure.png"))
            figures.restore(workspace)
            self.assertEqual(chapter.read_text(), original)
            self.assertEqual((images / "figure.png").read_bytes(), source)

    def test_code_examples_are_not_referenced(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "images").mkdir()
            (workspace / "images/figure.png").write_bytes(
                png(24, 24, 3, white_border(24, 24, 3))
            )
            chapter = workspace / "chapter.qmd"
            original = "`![inline](images/figure.png)`\n"
            chapter.write_text(original)
            figures = stage_print_figures(workspace, ["chapter.qmd"])
            self.assertEqual(chapter.read_text(), original)
            figures.restore(workspace)


if __name__ == "__main__":
    unittest.main()
