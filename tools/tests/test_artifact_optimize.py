"""Tests for lossless artifact optimization (change 0055, PDF in change 0062)."""

import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile
import zlib

import support
from handbook_toolkit.artifact_optimize import (
    PNG_SIGNATURE,
    QPDF_MINIMUM_MAJOR,
    _chunk,
    optimize_pdf,
    optimize_png_file,
    optimize_staged_pngs,
    png_pixels,
    png_recompress,
    qpdf_path,
    qpdf_version,
)
from handbook_toolkit.artifacts import archive_tree
from handbook_toolkit.build import build_book
from handbook_toolkit.build_types import BuildError
from test_build import BUILD_AVAILABLE, PROFILE, make_book


def _make_test_png(width: int = 16, height: int = 16, compress_level: int = 1) -> bytes:
    """Generate a valid test PNG with suboptimal compression."""
    # 8-bit RGBA (color_type 6, bit_depth 8)
    ihdr_payload = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw_rows = []
    for y in range(height):
        # Filter method 1 (Sub) for test variety
        row = bytearray(width * 4)
        for x in range(width):
            row[x * 4] = (x * 16) & 0xFF
            row[x * 4 + 1] = (y * 16) & 0xFF
            row[x * 4 + 2] = 128
            row[x * 4 + 3] = 255
        raw_rows.append(b"\x00" + bytes(row))
    raw_scanlines = b"".join(raw_rows)
    idat_payload = zlib.compress(raw_scanlines, compress_level)

    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr_payload)
        + _chunk(b"IDAT", idat_payload)
        + _chunk(b"IEND", b"")
    )


def _make_test_pdf(padding: int = 1) -> bytes:
    """A well-formed one-page PDF whose content stream is not compressed."""
    content = b"BT 20 100 Td (" + b"A" * padding + b") Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % index + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def _pdf_pages(path: Path) -> int:
    tool = qpdf_path()
    return int(subprocess.run([tool, "--show-npages", str(path)],
                              capture_output=True, text=True, check=True).stdout)


QPDF = qpdf_path()


class ArtifactOptimizeTests(unittest.TestCase):
    def test_png_recompress_smaller_identical_pixels(self) -> None:
        # Create an uncompressed/suboptimally compressed PNG
        suboptimal = _make_test_png(width=32, height=32, compress_level=0)
        recompressed = png_recompress(suboptimal)

        self.assertLess(len(recompressed), len(suboptimal))
        self.assertEqual(png_pixels(recompressed), png_pixels(suboptimal))

    def test_png_recompress_preserves_already_optimal(self) -> None:
        data = _make_test_png(width=8, height=8, compress_level=9)
        recompressed = png_recompress(data)
        # Should return same bytes or smaller, never larger
        self.assertLessEqual(len(recompressed), len(data))
        self.assertEqual(png_pixels(recompressed), png_pixels(data))

    def test_png_pixels_decodes_palette_and_grayscale(self) -> None:
        # Grayscale (color_type 0, bit_depth 8)
        ihdr = struct.pack(">IIBBBBB", 4, 4, 8, 0, 0, 0, 0)
        scanlines = b"".join(b"\x00\x10\x20\x30\x40" for _ in range(4))
        gray_png = PNG_SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(scanlines, 9)) + _chunk(b"IEND", b"")
        pixels = png_pixels(gray_png)
        self.assertEqual(len(pixels), 4 * 4)

    def test_png_recompress_corrupt_signature_fails(self) -> None:
        with self.assertRaises(BuildError) as ctx:
            png_recompress(b"not a png")
        self.assertIn("missing PNG signature", str(ctx.exception))

    def test_png_recompress_truncated_chunk_fails(self) -> None:
        truncated = PNG_SIGNATURE + struct.pack(">I4s", 100, b"IHDR") + b"short"
        with self.assertRaises(BuildError) as ctx:
            png_recompress(truncated)
        self.assertIn("truncated PNG chunk", str(ctx.exception))

    def test_png_recompress_crc_error_fails(self) -> None:
        ihdr_payload = struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 0)
        corrupt_crc_chunk = struct.pack(">I", len(ihdr_payload)) + b"IHDR" + ihdr_payload + struct.pack(">I", 0x12345678)
        corrupt = PNG_SIGNATURE + corrupt_crc_chunk + _chunk(b"IEND", b"")
        with self.assertRaises(BuildError) as ctx:
            png_recompress(corrupt)
        self.assertIn("bad CRC", str(ctx.exception))

    def test_png_recompress_corrupt_idat_fails(self) -> None:
        ihdr_payload = struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 0)
        corrupt_idat = PNG_SIGNATURE + _chunk(b"IHDR", ihdr_payload) + _chunk(b"IDAT", b"garbage-idat") + _chunk(b"IEND", b"")
        with self.assertRaises(BuildError) as ctx:
            png_recompress(corrupt_idat)
        self.assertIn("PNG IDAT decompression failed", str(ctx.exception))

    def test_optimize_png_file_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            png_path = Path(temp) / "test.png"
            suboptimal = _make_test_png(width=20, height=20, compress_level=0)
            png_path.write_bytes(suboptimal)

            res = optimize_png_file(png_path)
            self.assertGreater(res["saved"], 0)
            self.assertEqual(res["before"], len(suboptimal))
            self.assertEqual(res["after"], png_path.stat().st_size)
            self.assertEqual(png_pixels(png_path.read_bytes()), png_pixels(suboptimal))

    def test_optimize_staged_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "img1.png").write_bytes(_make_test_png(width=16, height=16, compress_level=0))
            (root / "sub").mkdir()
            (root / "sub/img2.png").write_bytes(_make_test_png(width=16, height=16, compress_level=0))
            (root / "sub/readme.txt").write_text("not an image")

            stats = optimize_staged_pngs(root)
            self.assertEqual(stats["files"], 2)
            self.assertGreater(stats["saved"], 0)

    def test_archive_tree_compresslevel(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "src"
            src.mkdir()
            # 100k of repetitive data compresses differently at level 6 vs level 9
            (src / "data.txt").write_bytes(b"pattern12345678" * 10000)
            zip_default = Path(temp) / "default.zip"
            zip_nine = Path(temp) / "nine.zip"
            archive_tree(src, zip_default, 1, compresslevel=None)
            archive_tree(src, zip_nine, 1, compresslevel=9)
            self.assertTrue(zip_default.is_file())
            self.assertTrue(zip_nine.is_file())
            self.assertLessEqual(zip_nine.stat().st_size, zip_default.stat().st_size)

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for full build test")
    def test_build_book_reproducible_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            out1 = root / "dist1"
            out2 = root / "dist2"
            build_book(repo, commit, out1, profile=PROFILE, mode="section-pilot")
            build_book(repo, commit, out2, profile=PROFILE, mode="section-pilot")

            files1 = sorted([p.name for p in out1.iterdir()])
            files2 = sorted([p.name for p in out2.iterdir()])
            self.assertEqual(files1, files2)
            for name in files1:
                b1 = (out1 / name).read_bytes()
                b2 = (out2 / name).read_bytes()
                self.assertEqual(
                    hashlib.sha256(b1).hexdigest(),
                    hashlib.sha256(b2).hexdigest(),
                    f"Mismatch in artifact bytes for {name}",
                )

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for full build test")
    def test_build_book_no_optimize_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            out_opt = root / "dist_opt"
            out_no_opt = root / "dist_no_opt"
            build_book(repo, commit, out_opt, profile=PROFILE, mode="section-pilot", optimize=True)
            build_book(repo, commit, out_no_opt, profile=PROFILE, mode="section-pilot", optimize=False)

            self.assertTrue((out_opt / "book.docx").is_file())
            self.assertTrue((out_no_opt / "book.docx").is_file())
            self.assertTrue((out_opt / "book-html.zip").is_file())
            self.assertTrue((out_no_opt / "book-html.zip").is_file())


class PdfOptimizeTests(unittest.TestCase):
    def test_missing_qpdf_fails_a_release_build_and_skips_a_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "book.pdf"
            data = _make_test_pdf(padding=2048)
            path.write_bytes(data)
            with mock.patch.dict(os.environ, {"QPDF": str(root / "no-such-qpdf")}):
                self.assertIsNone(qpdf_path())
                with self.assertRaises(BuildError) as ctx:
                    optimize_pdf(path, required=True)
                self.assertIn("qpdf", str(ctx.exception))
                result = optimize_pdf(path, required=False)
            self.assertEqual(result["status"], "skipped: qpdf not found")
            self.assertEqual(result["before"], len(data))
            self.assertEqual(result["after"], len(data))
            self.assertEqual(result["saved"], 0)
            self.assertEqual(path.read_bytes(), data)

    @unittest.skipUnless(QPDF, "qpdf is not installed")
    def test_qpdf_version_is_parsed(self) -> None:
        version = qpdf_version(QPDF)
        self.assertGreaterEqual(int(version.split(".")[0]), QPDF_MINIMUM_MAJOR)

    @unittest.skipUnless(QPDF, "qpdf is not installed")
    def test_optimize_pdf_is_lossless_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "book.pdf"
            path.write_bytes(_make_test_pdf(padding=200_000))
            original_size = path.stat().st_size
            pages = _pdf_pages(path)
            result = optimize_pdf(path, required=True)
            self.assertEqual(result["status"], "optimized")
            self.assertEqual(result["tool"], "qpdf")
            self.assertEqual(result["before"], original_size)
            self.assertLess(result["after"], result["before"])
            self.assertEqual(result["saved"], result["before"] - result["after"])
            self.assertEqual(path.stat().st_size, result["after"])
            self.assertEqual(_pdf_pages(path), pages)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            again = optimize_pdf(path, required=True)
            self.assertEqual(again["status"], "kept: no gain")
            self.assertEqual(again["saved"], 0)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    @unittest.skipUnless(QPDF, "qpdf is not installed")
    def test_optimize_pdf_rejects_changed_page_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "book.pdf"
            path.write_bytes(_make_test_pdf(padding=2048))
            from handbook_toolkit import artifact_optimize

            original = artifact_optimize._pdf_pages
            calls = {"count": 0}

            def changing(tool: str, target: Path) -> int:
                calls["count"] += 1
                return original(tool, target) + (1 if calls["count"] == 1 else 0)

            with mock.patch.object(artifact_optimize, "_pdf_pages", changing):
                with self.assertRaises(BuildError) as ctx:
                    optimize_pdf(path, required=True)
            self.assertIn("page count", str(ctx.exception))

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for full build test")
    def test_build_book_records_the_pdf_optimization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            out = root / "dist"
            build_book(repo, commit, out, profile=PROFILE, mode="section-pilot", preview=True)
            manifest = json.loads((out / "publication-manifest.json").read_text(encoding="utf-8"))
            record = manifest["build"]["optimization"]["pdf"]
            self.assertEqual(record["tool"], "qpdf")
            self.assertEqual(record["saved"], record["before"] - record["after"])
            self.assertGreaterEqual(record["before"], record["after"])
            self.assertEqual((out / "book.pdf").stat().st_size, record["after"])
            if QPDF:
                self.assertIn(record["status"], ("optimized", "kept: no gain"))
                self.assertIn("qpdf", manifest["build"]["tool_versions"])
            else:
                self.assertEqual(record["status"], "skipped: qpdf not found")

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for full build test")
    def test_no_optimize_skips_pdf_compaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            out = root / "dist"
            build_book(repo, commit, out, profile=PROFILE, mode="section-pilot",
                       preview=True, optimize=False)
            manifest = json.loads((out / "publication-manifest.json").read_text(encoding="utf-8"))
            record = manifest["build"]["optimization"]["pdf"]
            self.assertEqual(record["status"], "skipped: --no-optimize")
            self.assertEqual(record["saved"], 0)
            self.assertEqual((out / "book.pdf").stat().st_size, record["after"])


if __name__ == "__main__":
    unittest.main()
