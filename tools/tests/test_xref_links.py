"""Synthetic opt-in navigation fixtures; no reference manuscript is copied here."""

from pathlib import Path
import tempfile
import unittest
import yaml
import support
from handbook_toolkit.books import validate_book
from handbook_toolkit.validation import load_document
from handbook_toolkit.build_types import BuildError
from handbook_toolkit.xref_links import (
    heading_id,
    link_references,
    stage_cross_references,
    rewrite_html_links,
)


def targets(*sections: str):
    return (
        {x: x for x in sections},
        {"fig-2-1": "fig-chart"},
        {"tbl-1-1": "tbl-summary"},
    )


class CrossReferenceTests(unittest.TestCase):
    def test_descriptor_option_is_boolean_and_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = support.make_book_tree(root)
            self.assertTrue(
                validate_book(
                    descriptor,
                    load_document(
                        support.REPO_ROOT
                        / "tools/src/handbook_toolkit/schemas/book.schema.json"
                    ),
                ).ok
            )
            data = yaml.safe_load(descriptor.read_text())
            for value in (True, False):
                data["publication"]["cross_reference_links"] = value
                descriptor.write_text(yaml.safe_dump(data))
                self.assertTrue(
                    validate_book(
                        descriptor,
                        load_document(
                            support.REPO_ROOT
                            / "tools/src/handbook_toolkit/schemas/book.schema.json"
                        ),
                    ).ok
                )
            data["publication"]["cross_reference_links"] = "true"
            descriptor.write_text(yaml.safe_dump(data))
            self.assertFalse(
                validate_book(
                    descriptor,
                    load_document(
                        support.REPO_ROOT
                        / "tools/src/handbook_toolkit/schemas/book.schema.json"
                    ),
                ).ok
            )

    def test_named_references_ranges_and_existing_ids(self):
        registry = targets(
            "sec_ch_1", "sec_ch_2", "sec_app_a", "sec_app_z", "sec_z_1", "sec_2_3"
        )
        text = "Chapter 2; Chapters 1–2; Appendix Z; Appendices A and Z; Section 2.3; Figure 2.1; Table 1.1."
        linked = link_references(text, registry)
        for part in (
            "[Chapter 2](#sec_ch_2)",
            "[1](#sec_ch_1)–[2](#sec_ch_2)",
            "[Appendix Z](#sec_app_z)",
            "[Section 2.3](#sec_2_3)",
            "[Figure 2.1](#fig-chart)",
            "[Table 1.1](#tbl-summary)",
        ):
            self.assertIn(part, linked.replace("{.handbook-xref}", ""))
        self.assertEqual(link_references(linked, registry), linked)
        self.assertEqual(
            link_references("Chapter 99 and Section 99.9.", registry),
            "Chapter 99 and Section 99.9.",
        )

    def test_cues_reference_groups_and_lists(self):
        registry = targets("sec_1_2", "sec_2_3", "sec_4_5_6")
        for text in (
            "See 1.2.",
            "(1.2, 2.3)",
            "defined in 4.5.6",
            "(method, 2.3)",
            "See 1.2 and 2.3.",
        ):
            self.assertIn(".handbook-xref", link_references(text, registry), text)
        self.assertNotIn(
            ".handbook-xref", link_references("An unexplained 1.2.", registry)
        )

    def test_values_versions_dates_and_standard_clauses_stay_plain(self):
        registry = targets(
            "sec_1_2", "sec_1_3", "sec_2_2", "sec_2_3", "sec_4_5", "sec_9_9"
        )
        for text in (
            "TLS 1.2 minimum, 1.3 preferred.",
            "Use [TLS](https://example.org/a(b)) 1.2 and 1.3.",
            "WCAG 2.2",
            "clause 2.3",
            "about 4.5",
            "a rate of 4.5",
            "a total of 9.9 out of 10",
            "from 1.2 to 2.3",
            "2.3 million",
            "1.2 seconds",
            "99.9%",
            "2026.01.02",
            "| Version | Where used |\n| --- | --- |\n| 1.2 | TLS 1.3 |",
        ):
            self.assertEqual(link_references(text, registry), text)

    def test_markdown_and_bibliographies_are_protected(self):
        registry = targets("sec_ch_2", "sec_1_2")
        text = """---
title: Chapter 2
---
# Chapter 2

````python
See 1.2
```
Chapter 2
````
    See 1.2
`Chapter 2` and ``code ` See 1.2``.
[Chapter 2](https://example.org/a(b)) and [See 1.2][source].
[Chapter 2]
[source]: https://example.org
![Chapter 2](image.png)
<!-- Chapter 2
See 1.2 -->
## Further Reading
See Section 1.2 and Chapter 2.
### Subsection
See 1.2.
# References {.unnumbered}
See Chapter 2 and Section 1.2.
"""
        self.assertEqual(link_references(text, registry), text)
        self.assertIn(
            "[Chapter 2]", link_references(text + "\n# Next\nChapter 2", registry)
        )

    def test_multiline_inline_code_and_link_labels_stay_plain(self):
        registry = targets("sec_ch_2", "sec_1_2")
        for text in (
            "`example\nChapter 2 and See 1.2\ncode`",
            "[See 1.2\nChapter 2](https://example.org)",
        ):
            self.assertEqual(link_references(text, registry), text)

    def test_reference_columns_preserve_escaped_and_code_pipes(self):
        registry = targets("sec_ch_1", "sec_ch_2", "sec_1_2")
        text = "| Subject | See |\n| --- | --- |\n| Value \\| name | 1, 2; 1.2 |\n| `a|b` | Section 1.2 |"
        linked = link_references(text, registry)
        self.assertIn("Value \\| name", linked)
        self.assertIn("`a|b`", linked)
        self.assertIn(
            "[1](#sec_ch_1), [2](#sec_ch_2)", linked.replace("{.handbook-xref}", "")
        )
        self.assertIn("[1.2](#sec_1_2)", linked)

    def test_partial_named_tokens_and_html_code_are_not_linked(self):
        registry = targets("sec_ch_2", "sec_1_2", "sec_app_a")
        for text in (
            "Chapter 2x",
            "Section 1.2a",
            "Figure 2.1a",
            "Table 1.1.9",
            "Appendix A.9x",
            "Example <code>Chapter 2</code> stays code.",
            "<pre>\nSee 1.2\n</pre>",
        ):
            self.assertEqual(link_references(text, registry), text)

    def test_reference_columns_do_not_link_integer_measurements(self):
        registry = targets("sec_ch_1", "sec_ch_2")
        text = "| Subject | See |\n| --- | --- |\n| A | 2% and 1 hour |"
        self.assertEqual(link_references(text, registry), text)

    def test_number_anchors_ignore_prose_and_keep_deep_sections(self):
        self.assertEqual(heading_id(1, "7. Renamed Chapter"), "sec_ch_7")
        self.assertEqual(heading_id(1, "Appendix Z — Guide"), "sec_app_z")
        self.assertEqual(heading_id(4, "7.2.3.4 Deep section"), "sec_7_2_3_4")

    def test_registry_cross_page_links_preserve_explicit_ids_and_attributes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chapters").mkdir()
            (root / "index.qmd").write_text(
                "# 1. Start\n\nSee Chapter 2 and Section 2.1 and Table 2.1.\n"
            )
            other = root / "chapters/two.qmd"
            other.write_text(
                "# 2. Destination {.unnumbered}\n\n## 2.1 Choice {#custom-choice .unlisted}\n\n| A | B |\n| --- | --- |\n| C | D |\n\n: Summary\n\nSee Chapter 1.\n"
            )
            entries = ["./index.qmd", "chapters/two.qmd"]
            registry = stage_cross_references(root, entries)
            self.assertIn("{#custom-choice .unlisted}", other.read_text())
            self.assertIn("{.unnumbered #sec_ch_2}", other.read_text())
            self.assertIn("{#tbl-2-1}", other.read_text())
            self.assertIn("](#custom-choice)", (root / "index.qmd").read_text())
            (root / "handbook-source-index.qmd").write_text(
                (root / "index.qmd").read_text()
            )
            rewrite_html_links(
                root,
                ["handbook-source-index.qmd", "chapters/two.qmd"],
                registry,
                "handbook-source-index.qmd",
            )
            self.assertIn(
                "](chapters/two.qmd#custom-choice)",
                (root / "handbook-source-index.qmd").read_text(),
            )
            self.assertIn("](../handbook-source-index.qmd#sec_ch_1)", other.read_text())

    def test_unnumbered_caption_ids_do_not_collide_with_numbered_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            table = "\n| A | B |\n| --- | --- |\n| C | D |\n\n: Summary\n"
            (root / "front.qmd").write_text("# Introduction {.unnumbered}\n" + table)
            (root / "chapter.qmd").write_text("# 1. Chapter\n" + table)
            registry = stage_cross_references(root, ["front.qmd", "chapter.qmd"])
            self.assertIn("tbl-1-1", registry.pages)
            self.assertEqual(len(registry.targets[2]), 2)
            self.assertTrue(
                all(len(identity) <= 40 for identity in registry.targets[2].values())
            )

    def test_duplicate_anchors_fail_before_linking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a.qmd", "b.qmd"):
                (root / name).write_text("# 1. Duplicate\n")
            with self.assertRaisesRegex(BuildError, "duplicate navigation anchor"):
                stage_cross_references(root, ["a.qmd", "b.qmd"])
