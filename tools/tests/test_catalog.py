"""Catalog validation tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.catalog import validate_catalog  # noqa: E402
from handbook_toolkit.validation import load_schema  # noqa: E402


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.schema = load_schema(support.SCHEMAS / "catalog.schema.json")

    def tearDown(self) -> None:
        self._temp.cleanup()

    def check(self, document: dict):
        path = support.write_json(self.root / "catalog.json", document)
        return validate_catalog(path, self.schema)

    def test_repository_catalog_is_valid(self) -> None:
        result = validate_catalog(support.REPO_ROOT / "catalog/catalog.json", self.schema)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_valid_catalog_entry(self) -> None:
        result = self.check(support.catalog_document())
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_duplicate_slug_is_rejected(self) -> None:
        document = support.catalog_document()
        document["books"].append(support.copy_document(document["books"][0]))
        document["books"][1]["id"] = "another-book"
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate slug" in issue.message for issue in result.issues))

    def test_duplicate_id_is_rejected(self) -> None:
        document = support.catalog_document()
        document["books"].append(support.copy_document(document["books"][0]))
        document["books"][1]["slug"] = "another-book"
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate book id" in issue.message for issue in result.issues))

    def test_tag_must_match_version(self) -> None:
        document = support.catalog_document()
        document["books"][0]["latest_release"]["tag"] = "v1.0.1"
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("must be 'v1.0.0'" in issue.message for issue in result.issues))

    def test_manifest_url_must_contain_tag(self) -> None:
        document = support.catalog_document()
        document["books"][0]["latest_release"]["manifest_url"] = (
            "https://github.com/example/example-book/releases/download/latest/publication-manifest.json"
        )
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("immutable tag segment" in issue.message for issue in result.issues))

    def test_release_url_must_end_with_tag(self) -> None:
        document = support.catalog_document()
        document["books"][0]["latest_release"]["url"] = (
            "https://github.com/example/example-book/releases/latest"
        )
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("must end with" in issue.message for issue in result.issues))

    def test_invalid_date_is_rejected(self) -> None:
        document = support.catalog_document()
        document["books"][0]["latest_release"]["published_at"] = "2026-02-31"
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("real ISO date" in issue.message for issue in result.issues))

    def test_books_must_be_sorted_by_slug(self) -> None:
        document = support.catalog_document()
        second = support.copy_document(document["books"][0])
        second["id"] = "aaa-book"
        second["slug"] = "aaa-book"
        second["latest_release"]["url"] = "https://github.com/example/aaa-book/releases/tag/v1.0.0"
        second["latest_release"]["manifest_url"] = (
            "https://github.com/example/aaa-book/releases/download/v1.0.0/publication-manifest.json"
        )
        second["latest_release"]["checksums_url"] = (
            "https://github.com/example/aaa-book/releases/download/v1.0.0/SHA256SUMS.txt"
        )
        document["books"].append(second)
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("sorted by slug" in issue.message for issue in result.issues))

    def test_duplicate_release_url_is_rejected(self) -> None:
        document = support.catalog_document()
        second = support.copy_document(document["books"][0])
        second["id"] = "example-book-two"
        second["slug"] = "example-book-two"
        document["books"].append(second)
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate release URL" in issue.message for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
