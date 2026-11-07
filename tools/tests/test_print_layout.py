"""Tests for generated print layout, metadata and document control."""

import unittest

from handbook_toolkit.print_layout import (
    DEFAULT_RUNNING_HEADER,
    document_control_table,
    edition_date,
    edition_fields,
    heading_levels,
    inject_document_control,
    license_label,
    toc_depth,
    typst_book_data,
    typst_front,
)


class PrintLayoutTests(unittest.TestCase):
    def test_heading_levels_skips_fences(self) -> None:
        text = """# Heading 1
```markdown
# Not a heading
## Still in code
```
## Heading 2
### Heading 3
"""
        self.assertEqual(heading_levels(text), [1, 2, 3])

    def test_toc_depth_selection(self) -> None:
        self.assertEqual(toc_depth(["# Level 1"]), 1)
        self.assertEqual(toc_depth(["# Level 1\n## Level 2"]), 2)
        # Few level 3 headings choose depth 3
        few = ["# Level 1\n## Level 2\n### Level 3"]
        self.assertEqual(toc_depth(few), 3)
        # Many headings exceeding limit fall back to depth 2
        many = ["# L1\n## L2\n### L3\n" * 50]
        self.assertEqual(toc_depth(many), 2)

    def test_document_control_table_and_injection(self) -> None:
        fields = [
            ("Title", "Sample Handbook"),
            ("Author", "Test Author"),
            ("Status", "Released edition"),
        ]
        table = document_control_table(fields)
        self.assertIn("| Title | Sample Handbook |", table)
        self.assertIn("| Author | Test Author |", table)

        content = "# Document Control {.unnumbered}\n\n#### Version History\n"
        injected = inject_document_control(content, table)
        self.assertIsNotNone(injected)
        self.assertIn(table, injected)
        self.assertTrue(injected.startswith("# Document Control {.unnumbered}\n\n| Field | Value |"))

    def test_inject_document_control_returns_none_when_heading_missing(self) -> None:
        self.assertIsNone(inject_document_control("# Other Heading", "| Table |"))

    def test_typst_book_data_and_front(self) -> None:
        data = typst_book_data(
            title="My Book",
            license_text="CC BY-SA 4.0",
            running_header="Practitioner reference",
        )
        self.assertIn('#let handbook-title = "My Book"', data)
        self.assertIn('#let handbook-license = "CC BY-SA 4.0"', data)

        front = typst_front(
            series_label="TECHNICAL SERIES",
            version_line="Version 1.0, November 2026",
            scope_line="Chapters 1-8",
            author="Author Name",
            license_text="CC BY-SA 4.0",
            disclaimer="Illustrative only.",
            depth=2,
        )
        self.assertIn("#outline(title: [Contents], depth: 2)", front)
        self.assertIn("TECHNICAL SERIES", front)
        self.assertIn("Author Name", front)
        self.assertIn("Illustrative only.", front)


if __name__ == "__main__":
    unittest.main()
