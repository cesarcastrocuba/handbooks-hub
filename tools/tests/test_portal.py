"""Validate portal output against catalog identity and safe HTML construction."""

from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

import support
from handbook_toolkit.portal import CATEGORIES, SCRIPT, build_portal
from handbook_toolkit.validation import load_packaged_schema


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.cards = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs.get("href"))
        if tag == "article" and attrs.get("class") == "book":
            self.cards.append(attrs)


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / "catalog.json"
        self.output = self.root / "site"

    def build(self, document):
        support.write_json(self.catalog, document)
        return build_portal(self.catalog, self.output).read_text()

    def test_empty_catalog_is_honest_and_has_no_book_or_release_link(self):
        page = self.build({"schema_version": "1.0", "books": []})
        self.assertIn("The first handbook is being prepared", page)
        self.assertIn("Planned topics", page)
        self.assertEqual(Page(page).cards, [])
        self.assertFalse(any("/releases/" in link for link in Page(page).links))

    def test_card_retains_exact_reading_and_immutable_download_links(self):
        document = support.catalog_document()
        page = self.build(document)
        book = document["books"][0]
        parsed = Page(page)
        self.assertEqual(len(parsed.cards), 1)
        self.assertIn(book["reading_url"], parsed.links)
        for key in ("url", "manifest_url", "checksums_url"):
            self.assertIn(book["latest_release"][key], parsed.links)
        self.assertIn('aria-live="polite"', page)
        self.assertIn('aria-label="Filter by topic"', page)
        self.assertIn('data-filter="authoring"', page)

    def test_catalog_prose_is_escaped_not_executable(self):
        document = support.catalog_document()
        document["books"][0]["title"] = '<script>alert("x")</script>'
        document["books"][0]["summary"] = '<img src=x onerror="bad()">'
        page = self.build(document)
        self.assertNotIn('<script>alert(', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn("&lt;script&gt;", page)

    def test_invalid_catalog_never_creates_output(self):
        for change in ("missing-reading", "draft", "unknown-category"):
            with self.subTest(change=change):
                document = support.catalog_document()
                book = document["books"][0]
                if change == "missing-reading":
                    del book["reading_url"]
                elif change == "draft":
                    book["status"] = "draft"
                else:
                    book["categories"] = ["uncontrolled-topic"]
                with self.assertRaises(ValueError):
                    self.build(document)
                self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.build({"schema_version": "1.0", "books": []})
        with self.assertRaises(FileExistsError):
            build_portal(self.catalog, self.output)

    def test_portal_and_schema_category_vocabulary_agree(self):
        schema = load_packaged_schema("catalog.schema.json")
        vocabulary = schema["properties"]["books"]["items"]["properties"]["categories"]["items"]["enum"]
        self.assertEqual(CATEGORIES, set(vocabulary))


if __name__ == "__main__":
    unittest.main()
