"""Cross-reference and local-asset validation tests across a canonical reading order."""

from pathlib import Path
import tempfile
import unittest

import support
from handbook_toolkit.references import validate_references
from handbook_toolkit.validation import load_packaged_schema


class ReferenceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manuscript = self.root / "manuscript"
        (self.manuscript / "front").mkdir(parents=True)
        (self.manuscript / "chapters").mkdir()
        (self.manuscript / "back").mkdir()
        (self.root / "assets").mkdir()
        (self.root / "assets" / "pic.png").write_bytes(b"image")
        self.book = self.root / "book.yaml"
        self.schema = load_packaged_schema("book.schema.json")

    def write_book(self, one: str, two: str | None = None, preface: str = "# Preface {#sec-preface .unnumbered}\n") -> None:
        (self.manuscript / "front/preface.qmd").write_text(preface, encoding="utf-8")
        (self.manuscript / "chapters/one.qmd").write_text(one, encoding="utf-8")
        (self.manuscript / "chapters/two.qmd").write_text(
            two if two is not None else "# 2. Two {#sec-two}\n\nSee @fig-one and @sec-preface.\n",
            encoding="utf-8",
        )
        (self.manuscript / "back/references.qmd").write_text(
            "# References {.unnumbered}\n", encoding="utf-8"
        )
        support.write_yaml(
            self.manuscript / "book.yml",
            {
                "front": ["front/preface.qmd"],
                "chapters": ["chapters/one.qmd", "chapters/two.qmd"],
                "back": ["back/references.qmd"],
                "appendices": [],
                "references": [],
            },
        )
        document = support.book_document()
        document["id"] = "reference-book"
        document["catalog"]["slug"] = "reference-book"
        support.write_yaml(self.book, document)

    def check(self, one: str, two: str | None = None):
        self.write_book(one, two)
        return validate_references(self.book, self.schema)

    def test_valid_cross_file_labels_images_and_external_links(self) -> None:
        one = """\
# 1. One {#sec-one}

![A local figure](../../assets/pic.png){#fig-one}

See @fig-one, @sec-preface, [local](#fig-one) and [external](https://example.com/page).
"""
        result = self.check(one)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_duplicate_labels_across_files_fail_even_in_special_matter(self) -> None:
        one = "# 1. One {#sec-one}\n\n![A local figure](../../assets/pic.png){#fig-one}\n"
        two = "# 2. Two {#sec-two}\n\n![Another](../../assets/pic.png){#fig-one}\n"
        result = self.check(one, two)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate explicit label #fig-one" in issue.message for issue in result.issues))

    def test_unresolved_at_and_local_anchor_fail(self) -> None:
        one = "# 1. One {#sec-one}\n\nSee @fig-missing and [local](#tbl-missing).\n"
        result = self.check(one, "# 2. Two {#sec-two}\n")
        self.assertFalse(result.ok)
        messages = " ".join(issue.message for issue in result.issues)
        self.assertIn("unresolved explicit cross-reference @fig-missing", messages)
        self.assertIn("unresolved local cross-reference #tbl-missing", messages)

    def test_missing_unsafe_and_symlinked_images_fail(self) -> None:
        one = """\
# 1. One {#sec-one}

![Missing](../../assets/missing.png)
![Outside](../../../outside.png)
![Remote](https://example.com/pic.png)
![Absolute](/etc/passwd)
"""
        result = self.check(one)
        self.assertFalse(result.ok)
        messages = " ".join(issue.message for issue in result.issues)
        self.assertIn("referenced image is missing", messages)
        self.assertIn("image path escapes the book repository", messages)
        self.assertIn("image path must be relative", messages)

        (self.root / "assets/link.png").symlink_to(self.root / "assets/pic.png")
        one = "# 1. One {#sec-one}\n\n![Link](../../assets/link.png)\n"
        result = self.check(one)
        self.assertFalse(result.ok)
        self.assertTrue(any("uses a symlink" in issue.message for issue in result.issues))

    def test_multiline_comments_and_exact_backtick_spans_are_ignored(self) -> None:
        one = """# 1. One {#sec-one}

![Figure](../../assets/pic.png){#fig-one}

<!--
@fig-comment
{#fig-comment}
![comment](../../assets/missing.png)
-->

Use ``@fig-inline`` and `{#fig-inline-code}` here, then see @fig-one and [local](#fig-one).
"""
        two = "# 2. Two {#sec-two}\n"
        result = self.check(one, two)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_cross_file_local_explicit_links_resolve_and_auto_anchors_are_ignored(self) -> None:
        one = "# 1. One {#sec-one}\n\nSee [target](two.qmd#fig-two) and [auto](#Some-Heading).\n"
        two = "# 2. Two {#sec-two}\n\n![Figure](../../assets/pic.png){#fig-two}\n"
        result = self.check(one, two)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

        one = "# 1. One {#sec-one}\n\nSee [target](two.qmd#fig-missing).\n"
        result = self.check(one, two)
        self.assertFalse(result.ok)
        self.assertTrue(any("unresolved local cross-reference" in issue.message for issue in result.issues))

    def test_external_links_and_fragments_are_preserved(self) -> None:
        one = "# 1. One {#sec-one}\n\n[external](https://example.com/page#fig-missing).\n"
        result = self.check(one, "# 2. Two {#sec-two}\n")
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_parent_symlink_image_is_rejected(self) -> None:
        (self.root / "assets/linkdir").symlink_to(self.root / "assets")
        one = "# 1. One {#sec-one}\n\n![Link](../../assets/linkdir/pic.png)\n"
        result = self.check(one)
        self.assertFalse(result.ok)
        self.assertTrue(any("uses a symlink" in issue.message for issue in result.issues))

    def test_code_fences_do_not_define_labels_or_references(self) -> None:
        one = """\
# 1. One {#sec-one}

```markdown
{#fig-code}
@fig-missing
![Missing](../../assets/missing.png)
```
"""
        result = self.check(one)
        self.assertFalse(result.ok)
        self.assertTrue(any("@fig-one" in issue.message for issue in result.issues))

    def test_front_and_back_matter_are_checked_without_profile_shape_rules(self) -> None:
        result = self.check(
            "# 1. One {#sec-one}\n\nSee @sec-preface.\n",
            "# 2. Two {#sec-two}\n\nSee @sec-back.\n",
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("@sec-back" in issue.message for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
