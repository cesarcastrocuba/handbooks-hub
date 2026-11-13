"""Validate portal output against catalog identity and safe HTML construction."""

from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import support
from handbook_toolkit.catalog import ASSET_FILES
from handbook_toolkit.portal import CATEGORIES, FORMATS, SCRIPT, build_portal
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
        for change in ("missing-reading", "draft", "unknown-category", "branch-reading", "query-reading"):
            with self.subTest(change=change):
                document = support.catalog_document()
                book = document["books"][0]
                if change == "missing-reading":
                    del book["reading_url"]
                elif change == "draft":
                    book["status"] = "draft"
                elif change == "branch-reading":
                    book["reading_url"] = "https://github.com/owner/book/tree/main"
                elif change == "query-reading":
                    book["reading_url"] = "https://example.github.io/book/?edition=latest"
                else:
                    book["categories"] = ["uncontrolled-topic"]
                with self.assertRaises(ValueError):
                    self.build(document)
                self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.build({"schema_version": "1.0", "books": []})
        with self.assertRaises(FileExistsError):
            build_portal(self.catalog, self.output)

    def test_write_failure_never_leaves_a_partial_site(self):
        support.write_json(self.catalog, {"schema_version": "1.0", "books": []})
        with patch("handbook_toolkit.portal.Path.write_text", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                build_portal(self.catalog, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".portal-*")), [])

    def with_assets(self):
        document = support.catalog_document()
        document["schema_version"] = "1.1"
        release = document["books"][0]["latest_release"]
        base = release["manifest_url"].rsplit("/", 1)[0] + "/"
        release["assets"] = {role: base + name for role, name in ASSET_FILES.items()}
        return document

    def test_format_buttons_link_only_to_declared_assets(self):
        document = self.with_assets()
        del document["books"][0]["latest_release"]["assets"]["markdown"]
        page = self.build(document)
        parsed = Page(page)
        assets = document["books"][0]["latest_release"]["assets"]
        for url in assets.values():
            self.assertIn(url, parsed.links)
        self.assertFalse(any(str(link).endswith("/book.md") for link in parsed.links))
        self.assertIn(">PDF</a>", page)
        self.assertNotIn(">Markdown</a>", page)

    def test_release_without_assets_has_no_format_buttons(self):
        page = self.build(support.catalog_document())
        self.assertNotIn('class="fmt"', page)
        self.assertIn("Release downloads", page)

    def test_guide_sections_and_navigation_are_present(self):
        for document in (support.catalog_document(), {"schema_version": "1.0", "books": []}):
            with self.subTest(books=len(document["books"])):
                page = self.build(document)
                for anchor in ("library", "how-it-works", "create", "publishing", "contribute", "faq"):
                    self.assertIn(f'<section id="{anchor}"', page)
                for anchor in ("library", "how-it-works", "create", "publishing", "faq"):
                    self.assertIn(f'href="#{anchor}"', page)
                self.assertIn("handbooks-template", page)
                self.assertIn("request-listing.yml", page)
                self.assertIn("request-withdrawal.yml", page)
                self.assertNotIn("<script src", page)
                self.assertNotIn("<link", page)
                shutil.rmtree(self.output)

    def test_llms_txt_links_markdown_edition_or_reading_site(self):
        document = self.with_assets()
        self.build(document)
        book = document["books"][0]
        text = (self.output / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Handbook Hub\n"))
        self.assertIn(f"- [Example Book]({book['latest_release']['assets']['markdown']}):", text)
        shutil.rmtree(self.output)
        self.build(support.catalog_document())
        text = (self.output / "llms.txt").read_text(encoding="utf-8")
        self.assertIn(f"- [Example Book]({book['reading_url']}):", text)
        self.assertNotIn("book.md", text)

    def test_llms_txt_keeps_catalog_prose_on_one_safe_line(self):
        document = support.catalog_document()
        document["books"][0]["title"] = "A [bracketed]\ntitle"
        self.build(document)
        text = (self.output / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("- [A (bracketed) title](", text)

    def test_empty_catalog_writes_an_honest_llms_txt(self):
        self.build({"schema_version": "1.0", "books": []})
        self.assertIn("No handbook is listed yet.", (self.output / "llms.txt").read_text(encoding="utf-8"))

    def test_format_labels_cover_every_asset_role(self):
        self.assertEqual(set(FORMATS), set(ASSET_FILES))

    def test_portal_and_schema_category_vocabulary_agree(self):
        schema = load_packaged_schema("catalog.schema.json")
        vocabulary = schema["properties"]["books"]["items"]["properties"]["categories"]["items"]["enum"]
        self.assertEqual(CATEGORIES, set(vocabulary))


if __name__ == "__main__":
    unittest.main()


class PortalContributionTests(unittest.TestCase):
    """Readers must be able to reach the book source and contribute without guessing."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / "catalog.json"
        self.output = self.root / "site"

    def build(self, document):
        support.write_json(self.catalog, document)
        return build_portal(self.catalog, self.output).read_text()

    def test_card_links_to_the_source_repository(self):
        page = self.build(support.catalog_document())
        self.assertIn("Source and issues", page)
        self.assertIn("https://github.com/example/example-book", page)

    def test_single_book_result_uses_the_singular(self):
        page = self.build(support.catalog_document())
        self.assertIn("Showing 1 of 1 handbook<", page)

    def test_search_normalizes_case_and_accents(self):
        self.assertIn("normalize('NFD')", SCRIPT)
        self.assertIn("u0300", SCRIPT)
        self.assertIn("cards.length===1?'handbook':'handbooks'", SCRIPT)

    def test_fonts_are_published_next_to_the_page(self):
        page = self.build(support.catalog_document())
        fonts = sorted(
            path.relative_to(self.output).as_posix()
            for path in (self.output / "fonts").rglob("*.woff2")
        )
        self.assertEqual(len(fonts), 10)
        self.assertTrue(all(name.startswith("fonts/") for name in fonts))
        licenses = sorted(
            path.relative_to(self.output).as_posix()
            for path in (self.output / "fonts").rglob("OFL.txt")
        )
        self.assertEqual(
            licenses,
            [
                "fonts/jetbrains-mono/OFL.txt",
                "fonts/source-sans3/OFL.txt",
                "fonts/source-serif4/OFL.txt",
            ],
        )
        self.assertIn("fonts/source-sans3/OFL.txt", page)

    def test_theme_carries_the_tokens_and_no_external_host(self):
        page = self.build(support.catalog_document())
        self.assertIn('font-family:"Handbook Sans"', page)
        self.assertIn("--accent-solid:", page)
        self.assertNotIn("fonts.googleapis.com", page)
