"""Synthetic glossary/Index fixtures; no reference manuscript content."""

from pathlib import Path
import tempfile
import unittest
import yaml
import support
from handbook_toolkit.build_types import BuildError
from handbook_toolkit.glossary_index import (
    glossary_terms,
    index_terms,
    glossary_matches,
    stage_glossary_index,
    rewrite_glossary_links,
    word_glossary_sources,
)
from handbook_toolkit.xref_links import stage_cross_references, rewrite_html_links
from handbook_toolkit.validation import schema_issues, load_packaged_schema
from handbook_toolkit.docx_fields import bookmark_name

LONG = "A deliberately long glossary entry whose identifier exceeds the Word bookmark limit"
GLOSSARY = f"# Appendix A — Terms\n\n| Term | Meaning | Defined in |\n| --- | --- | --- |\n| Latency | Waiting time. | 1.1 |\n| IT | Information technology. | 1.1 |\n| {LONG} | A synthetic term. | 1.1 |\n"


class GlossaryIndexTests(unittest.TestCase):
    def fixture(self, root):
        (root / "m").mkdir()
        (root / "m/ch.qmd").write_text(
            "# 1. Concepts\n\n## 1.1 Delay {#author_id}\n\nLatency and IT matter; it is prose.\n\nSee [latency](#gl-latency).\n\n## Further Reading\nLatency citation.\n"
        )
        (root / "m/terms.qmd").write_text(GLOSSARY)
        book = {"manuscript": {"root": "m", "glossary": "terms.qmd"}, "publication": {}}
        groups = {
            "front": [],
            "chapters": ["m/ch.qmd"],
            "back": [],
            "appendices": ["m/terms.qmd"],
            "references": [],
        }
        entries = [e for v in groups.values() for e in v]
        texts = {e: (root / e).read_text() for e in entries}
        nav = stage_cross_references(root, entries, groups=groups, link_prose=False)
        return book, groups, entries, texts, nav

    def test_anchors_pointers_index_and_no_automatic_term_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            b, g, entries, texts, nav = self.fixture(w)
            name = stage_glossary_index(w, b, g, nav, texts)
            index = (w / name).read_text()
            self.assertIn("[Latency](#gl-latency)", index)
            self.assertIn("**[1.1](#author_id){.handbook-xref}**", index)
            self.assertIn(
                "[1.1](#author_id){.handbook-xref}", (w / "m/terms.qmd").read_text()
            )
            self.assertEqual((w / "m/ch.qmd").read_text().count("](#gl-"), 1)
            self.assertIn(
                "Latency and IT matter; it is prose.", (w / "m/ch.qmd").read_text()
            )
            entries.append(name)
            rewrite_glossary_links(w, entries, nav)
            rewrite_html_links(w, entries, nav)
            self.assertIn("](terms.qmd#gl-latency)", (w / "m/ch.qmd").read_text())
            self.assertIn("](m/terms.qmd#gl-latency)", (w / name).read_text())
            self.assertIn("](m/ch.qmd#author_id)", (w / name).read_text())

    def test_longest_alias_acronym_and_proper_names(self):
        terms = [
            {"slug": "a", "aliases": ["Event"]},
            {"slug": "b", "aliases": ["Event stream"]},
            {"slug": "it", "aliases": ["IT"]},
        ]
        matches = glossary_matches("event stream and it and IT", terms, True)
        self.assertEqual([m[2]["slug"] for m in matches], ["b", "it"])

    def test_vocabulary_aliases_and_see_rows(self):
        g = glossary_terms(GLOSSARY)
        result = index_terms(
            g,
            {
                "terms": [
                    {"term": "Wait", "see": "Latency"},
                    {"term": "Queue", "aliases": ["Backlog"], "defined": "1.1"},
                ]
            },
        )
        self.assertIn("Wait", result[0]["aliases"])
        self.assertTrue(any(e.get("see") == "Latency" for e in result))
        self.assertTrue(any("Backlog" in e["aliases"] for e in result))
        with self.assertRaises(BuildError):
            index_terms(g, {"terms": [{"term": "Wait", "see": "Missing"}]})

    def test_book_keys_are_optional_and_vocabulary_requires_glossary(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = support.make_book_tree(Path(tmp))
            book = yaml.safe_load(descriptor.read_text())
            schema = load_packaged_schema("book.schema.json")
            self.assertFalse(schema_issues(book, schema, "book"))
            book["publication"]["index_vocabulary"] = "publishing/terms.yaml"
            self.assertTrue(schema_issues(book, schema, "book"))
            book["manuscript"]["glossary"] = "terms.qmd"
            self.assertFalse(schema_issues(book, schema, "book"))
            for bad in ("../escape.qmd", "/absolute.qmd", 3):
                book["manuscript"]["glossary"] = bad
                self.assertTrue(schema_issues(book, schema, "book"))

    def test_duplicate_glossary_slugs_rejected(self):
        with self.assertRaises(BuildError):
            glossary_terms(GLOSSARY + "| latency | Repeated. | 1.1 |\n")

    def test_vocabulary_schema_rejects_wrong_types_and_unknown_fields(self):
        schema = load_packaged_schema("index-vocabulary.schema.json")
        for value in (
            {"terms": "bad"},
            {"terms": [{"term": "x", "aliases": [3]}]},
            {"terms": [{"term": "x", "surprise": 1}]},
            {"terms": [{"term": "x", "see": "y", "defined": "1.1"}]},
        ):
            self.assertTrue(schema_issues(value, schema, "vocabulary"))
        self.assertFalse(
            schema_issues(
                {"terms": [{"term": "x", "aliases": ["Y"]}]}, schema, "vocabulary"
            )
        )

    def test_missing_glossary_link_and_generated_collision_rejected(self):
        for collision in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                w = Path(tmp)
                b, g, entries, texts, nav = self.fixture(w)
                if collision:
                    (w / "analytic-index.qmd").write_text("author file")
                else:
                    texts["m/ch.qmd"] += "\n[Missing](#gl-missing)\n"
                with self.assertRaises(BuildError):
                    stage_glossary_index(w, b, g, nav, texts)

    def test_word_encodes_long_ids_before_pandoc_and_can_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            b, g, entries, texts, nav = self.fixture(w)
            name = stage_glossary_index(w, b, g, nav, texts)
            entries.append(name)
            (w / "index.qmd").write_text("# Home\n")
            originals = word_glossary_sources(w, entries, nav)
            slug = "gl-" + LONG.lower().replace(" ", "-")
            encoded = bookmark_name(slug)
            self.assertLessEqual(len(encoded), 40)
            self.assertIn("{#" + encoded + "}", (w / "m/terms.qmd").read_text())
            self.assertIn("](#" + encoded + ")", (w / name).read_text())
            for p, text in originals.items():
                p.write_text(text)
            self.assertIn("{#" + slug + "}", (w / "m/terms.qmd").read_text())

    def test_word_and_html_leave_glossary_code_examples_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            b, g, entries, texts, nav = self.fixture(w)
            name = stage_glossary_index(w, b, g, nav, texts)
            entries.append(name)
            (w / "index.qmd").write_text("# Home\n")
            code = "`[Latency](#gl-latency)`\n\n````md\n[Latency](#gl-latency)\n```\n[Latency](#gl-latency)\n````\n"
            source = w / "m/ch.qmd"
            source.write_text(source.read_text() + "\n" + code)
            word_glossary_sources(w, entries, nav)
            self.assertIn(code, source.read_text())
            rewrite_glossary_links(w, entries, nav)
            self.assertIn(code, source.read_text())

    def test_glossary_root_alias_rebases_author_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            b, g, entries, texts, nav = self.fixture(w)
            nav.pages["gl-latency"] = "./index.qmd"
            rewrite_glossary_links(w, ["m/ch.qmd"], nav, "handbook-source-index.qmd")
            self.assertIn(
                "../handbook-source-index.qmd#gl-latency", (w / "m/ch.qmd").read_text()
            )

    def test_code_is_excluded_and_front_back_are_not_index_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            b, g, entries, texts, nav = self.fixture(w)
            texts["m/ch.qmd"] = (
                "# 1. Concepts\n\n## 1.1 Delay {#author_id}\n\n````\nLatency\n```\nLatency\n````\n`Latency`\n## Further Reading\nLatency\n### Nested\nLatency\n"
            )
            name = stage_glossary_index(w, b, g, nav, texts)
            # Only the definition remains, not a prose location.
            self.assertNotIn("Ch. 1:", (w / name).read_text())


if __name__ == "__main__":
    unittest.main()
