"""Format/container and deterministic archive regressions."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo
import yaml

import support  # noqa: F401
from handbook_toolkit.artifacts import archive_tree, inspect_payload


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def site(self, html):
        source = self.root / "site"
        source.mkdir(exist_ok=True)
        (source / "index.html").write_text(html)
        output = self.root / "site.zip"
        archive_tree(source, output, 1793993016)
        return output

    def test_archives_have_reproducible_bytes_and_normalized_permissions(self):
        one = self.site('<h1 id="intro">Hello</h1><a href="#intro">Read</a>')
        source = self.root / "site"
        (source / "index.html").chmod(0o777)
        two = self.root / "second.zip"
        archive_tree(source, two, 1793993016)
        self.assertEqual(one.read_bytes(), two.read_bytes())
        self.assertFalse(inspect_payload(one, "html"))

    def test_html_missing_fragment_crossfile_and_asset_fail(self):
        for link in ("#absent", "chapter.html", "missing.js", "../escape.html"):
            with self.subTest(link=link):
                output = self.site(f'<h1 id="intro">Hello</h1><a href="{link}">Read</a>')
                self.assertTrue(inspect_payload(output, "html"))
                output.unlink()

    def test_encoded_fragment_and_crossfile_targets_resolve(self):
        source = self.root / "site"
        source.mkdir()
        (source / "index.html").write_text('<a href="chapter.html#some%20id">Read</a>')
        (source / "chapter.html").write_text('<h1 id="some id">Chapter</h1>')
        output = self.root / "site.zip"
        archive_tree(source, output, 1)
        self.assertFalse(inspect_payload(output, "html"))

    def test_unsafe_members_and_symlinks_are_rejected(self):
        for index, name in enumerate(("../outside", "/absolute", "a\\b", "C:drive")):
            output = self.root / f"bad-{index}.zip"
            with ZipFile(output, "w") as archive:
                archive.writestr(name, "data")
            self.assertTrue(inspect_payload(output, "html"))
        output = self.root / "symlink.zip"
        with ZipFile(output, "w") as archive:
            info = ZipInfo("link")
            info.create_system = 3
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "/outside")
        self.assertTrue(inspect_payload(output, "html"))

    def test_docx_requires_word_document_parts_and_text(self):
        output = self.root / "book.docx"
        with ZipFile(output, "w") as archive:
            archive.writestr("word/document.xml", "<not-word/>")
        self.assertTrue(inspect_payload(output, "docx"))
        with ZipFile(output, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("_rels/.rels", "<Relationships/>")
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>')
        self.assertFalse(inspect_payload(output, "docx"))

    def test_source_bundle_requires_expected_commit_and_notices(self):
        output = self.root / "source.zip"
        with ZipFile(output, "w") as archive:
            archive.comment = ("a" * 40).encode()
            for name in ("LICENSE", "LICENSE-CODE", "NOTICE.md", "manuscript/ch01.qmd"):
                archive.writestr(name, "fixture")
            archive.writestr("book.yaml", yaml.safe_dump(support.book_document()))
            archive.writestr("manuscript/book.yml", yaml.safe_dump({"chapters": ["ch01.qmd"]}))
        self.assertFalse(inspect_payload(output, "source", source_commit="a" * 40))
        self.assertTrue(inspect_payload(output, "source", source_commit="b" * 40))
        self.assertTrue(inspect_payload(output, "source"))

    def test_source_missing_reading_order_and_unlisted_chapters_fail(self):
        for entries in ({}, {"chapters": ["missing.qmd"]}):
            output = self.root / "incomplete.zip"
            with ZipFile(output, "w") as archive:
                archive.comment = ("a" * 40).encode()
                for name in ("LICENSE", "LICENSE-CODE", "NOTICE.md", "manuscript/ch01.qmd"):
                    archive.writestr(name, "fixture")
                archive.writestr("book.yaml", yaml.safe_dump(support.book_document()))
                if entries:
                    archive.writestr("manuscript/book.yml", yaml.safe_dump(entries))
            self.assertTrue(inspect_payload(output, "source", source_commit="a" * 40))

    def test_zip_bounds_and_encryption_fail_as_structured_issues(self):
        output = self.site("a sufficiently long HTML fixture")
        with patch("handbook_toolkit.artifacts.MAX_MEMBER_BYTES", 8):
            self.assertTrue(inspect_payload(output, "html"))
        info = ZipInfo("index.html")
        info.flag_bits = 1
        with patch("handbook_toolkit.artifacts.ZipFile.infolist", return_value=[info]):
            issues = inspect_payload(output, "html")
            self.assertTrue(any("encrypted" in issue.message for issue in issues))

    def test_false_pdf_and_non_zip_document_are_rejected(self):
        output = self.root / "fake.pdf"
        output.write_bytes(b"%PDF-1.7\nnot a PDF document")
        self.assertTrue(inspect_payload(output, "pdf"))
        output.write_text("not a ZIP container")
        self.assertTrue(inspect_payload(output, "docx"))

    def test_archive_output_inside_source_and_symlink_inputs_fail(self):
        source = self.root / "source"
        source.mkdir()
        (source / "data.txt").write_text("payload")
        with self.assertRaises(ValueError):
            archive_tree(source, source / "recursive.zip", 1)
        (source / "link").symlink_to(source / "data.txt")
        with self.assertRaises(ValueError):
            archive_tree(source, self.root / "source.zip", 1)


if __name__ == "__main__":
    unittest.main()
