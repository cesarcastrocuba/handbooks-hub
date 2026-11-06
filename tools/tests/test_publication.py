"""Publication integrity regressions; fixtures are bytes, not valid rendered formats."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import support  # noqa: F401 -- establishes the toolkit source path
from handbook_toolkit.publication import CHECKSUMS, MANIFEST, verify_publication, write_manifest


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifacts = {"html": "site.zip", "pdf": "book.pdf", "docx": "book.docx", "source": "source.zip"}
        for role, name in self.artifacts.items():
            (self.root / name).write_bytes((role + " fixture").encode())
        self.metadata = {
            "book": {"id": "test-book", "version": "1.0.0", "commit": "a" * 40},
            "toolkit": "0.2.0", "profile": {"id": "standard", "version": "0.2.0"},
            "build": {"command": "fixture build", "source_date_epoch": 1,
                      "tool_versions": {"quarto": "1.11.9", "pandoc": "3.10", "typst": "0.15.1", "python": "3.12"}},
        }

    def publish(self):
        return write_manifest(self.root, self.metadata, self.artifacts)

    def test_manifest_identity_and_exact_checksum_membership(self):
        manifest = json.loads(self.publish().read_text())
        self.assertEqual(manifest["book"]["commit"], "a" * 40)
        self.assertNotIn("artifacts", self.metadata)
        lines = (self.root / CHECKSUMS).read_text().splitlines()
        self.assertEqual(len(lines), 5)
        self.assertTrue(verify_publication(self.root).ok)

    def test_same_length_corruption_is_rejected(self):
        self.publish()
        path = self.root / self.artifacts["pdf"]
        path.write_bytes(b"x" * path.stat().st_size)
        result = verify_publication(self.root)
        self.assertFalse(result.ok)
        self.assertTrue(any("SHA-256" in issue.message for issue in result.issues))

    def test_manifest_tampering_is_detected_by_checksums(self):
        path = self.publish()
        path.write_text(path.read_text().replace('"commit": "a', '"commit": "b'))
        self.assertFalse(verify_publication(self.root).ok)

    def test_missing_or_duplicate_checksum_entries_fail(self):
        self.publish()
        path = self.root / CHECKSUMS
        original = path.read_text()
        path.write_text(original.splitlines()[0] + "\n")
        self.assertFalse(verify_publication(self.root).ok)
        path.write_text(original + original.splitlines()[0] + "\n")
        self.assertFalse(verify_publication(self.root).ok)

    def test_duplicate_roles_fail_even_when_manifest_hash_is_updated(self):
        path = self.publish()
        data = json.loads(path.read_text())
        data["artifacts"][0]["role"] = data["artifacts"][1]["role"]
        path.write_text(json.dumps(data))
        sums = self.root / CHECKSUMS
        lines = sums.read_text().splitlines()
        sums.write_text("\n".join(
            hashlib.sha256(path.read_bytes()).hexdigest() + "  " + MANIFEST
            if line.endswith("  " + MANIFEST) else line for line in lines
        ) + "\n")
        self.assertFalse(verify_publication(self.root).ok)

    def test_extra_payloads_and_missing_files_fail(self):
        self.publish()
        extra = self.root / "unverified.txt"
        extra.write_text("not part of the approved release")
        self.assertFalse(verify_publication(self.root).ok)
        extra.unlink()
        (self.root / self.artifacts["source"]).unlink()
        self.assertFalse(verify_publication(self.root).ok)

    def test_unsafe_path_or_symlink_cannot_be_published(self):
        bad = dict(self.artifacts, pdf="../outside.pdf")
        with self.assertRaises(ValueError):
            write_manifest(self.root, self.metadata, bad)
        pdf = self.root / self.artifacts["pdf"]
        pdf.unlink()
        pdf.symlink_to(self.root / self.artifacts["docx"])
        with self.assertRaises(ValueError):
            self.publish()
        self.assertFalse((self.root / MANIFEST).exists())

    def test_existing_identity_cannot_be_replaced(self):
        self.publish()
        original = (self.root / MANIFEST).read_bytes()
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual((self.root / MANIFEST).read_bytes(), original)

    def test_invalid_provenance_fails_before_writing_identity(self):
        self.metadata["book"]["commit"] = "main"
        with self.assertRaises(ValueError):
            self.publish()
        self.assertFalse((self.root / MANIFEST).exists())

    def test_failed_pair_commit_cleans_identity_and_allows_retry(self):
        link = os.link

        def fail_checksum(source, destination):
            if Path(destination).name == CHECKSUMS:
                raise OSError("simulated filesystem failure")
            return link(source, destination)

        with patch("handbook_toolkit.publication.os.link", side_effect=fail_checksum):
            with self.assertRaises(OSError):
                self.publish()
        self.assertEqual({path.name for path in self.root.iterdir()}, set(self.artifacts.values()))
        self.publish()
        self.assertTrue(verify_publication(self.root).ok)

    def test_writer_rejects_dirty_directory_wrong_extensions_and_missing_typst(self):
        extra = self.root / "unrelated.txt"
        extra.write_text("not an asset")
        with self.assertRaises(ValueError):
            self.publish()
        extra.unlink()
        (self.root / "book.pdf").rename(self.root / "book.bin")
        self.artifacts["pdf"] = "book.bin"
        with self.assertRaises(ValueError):
            self.publish()
        (self.root / "book.bin").rename(self.root / "book.pdf")
        self.artifacts["pdf"] = "book.pdf"
        del self.metadata["build"]["tool_versions"]["typst"]
        with self.assertRaises(ValueError):
            self.publish()
        self.assertFalse((self.root / MANIFEST).exists())


if __name__ == "__main__":
    unittest.main()
