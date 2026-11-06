"""Book descriptor and reading-order tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.books import validate_book  # noqa: E402


class BookTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.schema = support.SCHEMAS / "book.schema.json"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def check(self, path: Path, full: bool = True):
        return validate_book(path, self.schema, full=full)

    def test_repository_template_is_valid(self) -> None:
        result = self.check(support.REPO_ROOT / "template/book/book.yaml", full=True)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_valid_fixture_book(self) -> None:
        path = support.make_book_tree(self.root)
        result = self.check(path, full=True)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_toolkit_must_be_an_exact_version(self) -> None:
        path = support.make_book_tree(self.root)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["toolkit"] = "0.1"
        support.write_yaml(path, document)
        result = self.check(path, full=False)
        self.assertFalse(result.ok)

    def test_missing_reading_order_is_rejected(self) -> None:
        path = support.make_book_tree(self.root)
        (self.root / "manuscript/book.yml").unlink()
        result = self.check(path, full=False)
        self.assertFalse(result.ok)
        self.assertTrue(any("reading order" in issue.message for issue in result.issues))

    def test_missing_chapter_file_is_rejected(self) -> None:
        path = support.make_book_tree(self.root)
        (self.root / "manuscript/chapters/01-example.qmd").unlink()
        result = self.check(path, full=False)
        self.assertFalse(result.ok)
        self.assertTrue(any("does not exist" in issue.message for issue in result.issues))

    def test_full_mode_detects_unlisted_manuscript(self) -> None:
        path = support.make_book_tree(self.root)
        extra = self.root / "manuscript/chapters/02-extra.qmd"
        extra.write_text("# 2. Extra\n", encoding="utf-8")
        result = self.check(path, full=True)
        self.assertFalse(result.ok)
        self.assertTrue(any("is not listed" in issue.message for issue in result.issues))

    def test_duplicate_reading_order_entry_is_rejected(self) -> None:
        path = support.make_book_tree(self.root)
        reading_order = yaml.safe_load((self.root / "manuscript/book.yml").read_text(encoding="utf-8"))
        reading_order["chapters"].append("chapters/01-example.qmd")
        support.write_yaml(self.root / "manuscript/book.yml", reading_order)
        result = self.check(path, full=False)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate reading-order entry" in issue.message for issue in result.issues))

    def test_non_qmd_entry_is_rejected(self) -> None:
        path = support.make_book_tree(self.root)
        notes = self.root / "manuscript/chapters/notes.txt"
        notes.write_text("notes\n", encoding="utf-8")
        reading_order = yaml.safe_load((self.root / "manuscript/book.yml").read_text(encoding="utf-8"))
        reading_order["chapters"].append("chapters/notes.txt")
        support.write_yaml(self.root / "manuscript/book.yml", reading_order)
        result = self.check(path, full=False)
        self.assertFalse(result.ok)
        self.assertTrue(any("must end with .qmd" in issue.message for issue in result.issues))

    def test_path_traversal_is_rejected_by_schema(self) -> None:
        path = support.make_book_tree(self.root)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["manuscript"]["root"] = "../outside"
        support.write_yaml(path, document)
        result = self.check(path, full=False)
        self.assertFalse(result.ok)

    def test_active_book_must_publish_all_formats(self) -> None:
        path = support.make_book_tree(self.root)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["status"] = "active"
        document["publication"]["formats"] = ["html"]
        support.write_yaml(path, document)
        result = self.check(path, full=True)
        self.assertFalse(result.ok)
        self.assertTrue(any("must publish" in issue.message for issue in result.issues))

    def test_unknown_reading_order_group_is_rejected(self) -> None:
        path = support.make_book_tree(self.root)
        reading_order = yaml.safe_load((self.root / "manuscript/book.yml").read_text(encoding="utf-8"))
        reading_order["draft"] = []
        support.write_yaml(self.root / "manuscript/book.yml", reading_order)
        result = self.check(path, full=False)
        self.assertFalse(result.ok)
        self.assertTrue(any("unknown reading-order groups" in issue.message for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
