"""Regression tests for Standard Profile 1.1.0 enhancements (Change 0050).

Covers:
1. Qualified callout titles (G3): prefix words allowed before title on word boundaries under 1.1.0.
2. Dedicated appendix rule (G2): single H1, non-empty body, no chapter anatomy required.
3. Unit relaxations:
   (a) Multiple closing elements of the same kind.
   (b) Block body (e.g. bullet list) following label paragraph.
   (c) Unit scanner ignores text inside table cells.
4. Backwards compatibility: Profile 1.0.0 preserves prior strict enforcement.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import support
from handbook_toolkit.manuscript import validate_manuscript
from handbook_toolkit.profile_resources import load_profile


SYNTHETIC_SECTION = """\
## 1.1 Core Concept

**Definition.** A synthetic definition for unit testing.

**Purpose.** Demonstrates structural compliance with the editorial profile.

**What it includes.** Synthetic attributes and test parameters.

**Why it is needed.** Necessary for automated verification.

**Example.** Illustrative example of the core concept.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
A synthetic common pitfall warning.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
A synthetic decision and trade-off table.
:::
"""

SYNTHETIC_CHAPTER = """\
# 1. Synthetic Chapter

Introductory remarks.

::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}
- Testing profile 1.1.0 rules.
:::

::: {.callout-tip appearance="simple" icon=false title="Key Takeaway"}
Synthetic test chapters isolate structural behavior.
:::

## 1.1 First Section

**Definition.** A test definition.

**Purpose.** A test purpose.

**What it includes.** Test items.

**Why it is needed.** Test rationale.

**Example.** Test example.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Test pitfall.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
Test trade-off.
:::

## 1.2 Worked Example — Synthetic Case

A concrete walkthrough of the synthetic case.

::: {.callout-important appearance="simple" icon=false title="Architecture Review Checklist — Domain"}
- Synthetic checklist item.
:::

## 1.3 Further Reading

- Synthetic reference item.
"""


class Profile110Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.profile_110 = load_profile("standard", "1.1.0")
        self.profile_100 = load_profile("standard", "1.0.0")
        self.profile_020 = load_profile("standard", "0.2.0")

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _check(self, text: str, profile: dict, mode: str, name: str = "doc.qmd"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return validate_manuscript(path, profile, mode)

    # 1. Qualified titles (G3)
    def test_accepts_qualified_checklist_title_under_110(self) -> None:
        result = self._check(SYNTHETIC_CHAPTER, self.profile_110, "chapter")
        self.assertTrue(result.ok, [str(i) for i in result.issues])

    def test_rejects_qualified_checklist_title_under_100(self) -> None:
        result = self._check(SYNTHETIC_CHAPTER, self.profile_100, "chapter")
        self.assertFalse(result.ok)
        self.assertTrue(any("missing chapter element" in i.message and "Review Checklist" in i.message for i in result.issues))

    def test_accepts_various_separators_with_qualification_under_110(self) -> None:
        for title in (
            "Review Checklist",
            "Review Checklist — Domain",
            "Architecture Review Checklist — Domain",
            "Architecture Review Checklist: Domain",
            "Enterprise Architecture Review Checklist - Domain",
            "Architecture Review Checklist",
        ):
            with self.subTest(title=title):
                text = SYNTHETIC_CHAPTER.replace(
                    'title="Architecture Review Checklist — Domain"',
                    f'title="{title}"',
                )
                result = self._check(text, self.profile_110, "chapter")
                self.assertTrue(result.ok, f"Failed for title {title!r}: {[str(i) for i in result.issues]}")

    def test_word_boundary_rejects_accidental_prefix_under_110(self) -> None:
        for bad_title in (
            "Pre-Review Checklist",
            "Pre-Review Checklist — Domain",
            "Architecture Review Checklist Extra",
        ):
            with self.subTest(bad_title=bad_title):
                text = SYNTHETIC_CHAPTER.replace(
                    'title="Architecture Review Checklist — Domain"',
                    f'title="{bad_title}"',
                )
                result = self._check(text, self.profile_110, "chapter")
                self.assertFalse(result.ok)
                self.assertTrue(any("Review Checklist" in i.message for i in result.issues))

    # 2. Appendix rule (G2)
    def test_appendix_rule_accepts_single_h1_and_body_under_110(self) -> None:
        appendix_text = """\
# Appendix A — Reference Tables

This is non-empty body text describing the appendix.

| Key | Description |
| :--- | :--- |
| Val1 | Explanatory note |
"""
        result = self._check(appendix_text, self.profile_110, "appendix")
        self.assertTrue(result.ok, [str(i) for i in result.issues])

    def test_appendix_in_chapter_mode_detected_and_accepted_under_110(self) -> None:
        appendix_text = """\
# Appendix B — Catalog

Catalog items and reference material.
"""
        result = self._check(appendix_text, self.profile_110, "chapter", name="appendices/appendix-b.qmd")
        self.assertTrue(result.ok, [str(i) for i in result.issues])

    def test_appendix_rejects_missing_h1_under_110(self) -> None:
        appendix_text = "Just plain body text without an H1 heading."
        result = self._check(appendix_text, self.profile_110, "appendix")
        self.assertFalse(result.ok)
        self.assertTrue(any("appendix must start with an H1 heading" in i.message for i in result.issues))

    def test_appendix_rejects_multiple_h1_under_110(self) -> None:
        appendix_text = """\
# Appendix A — First

Content.

# Appendix B — Second

Content.
"""
        result = self._check(appendix_text, self.profile_110, "appendix")
        self.assertFalse(result.ok)
        self.assertTrue(any("appendix must contain exactly one H1 heading" in i.message for i in result.issues))

    def test_appendix_rejects_empty_body_under_110(self) -> None:
        appendix_text = "# Appendix A — Blank Heading\n"
        result = self._check(appendix_text, self.profile_110, "appendix")
        self.assertFalse(result.ok)
        self.assertTrue(any("appendix body must not be empty" in i.message for i in result.issues))

    def test_appendix_with_chapter_anatomy_passes_under_both_100_and_110(self) -> None:
        appendix_with_anatomy = """\
# Appendix A — Structured Appendix {.unnumbered}

Overview narrative.

::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}
- When testing structured appendix.
:::

::: {.callout-tip appearance="simple" icon=false title="Key Takeaway"}
Structured appendix takeaway.
:::

## A.1 Unit One

**Definition.** Structured definition.

**Purpose.** Structured purpose.

**What it includes.** Structured scope.

**Why it is needed.** Structured rationale.

**Example.** Structured example.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Structured pitfall.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
Structured decision.
:::

## A.2 Worked Example — Demonstration

Demonstration text.

::: {.callout-important appearance="simple" icon=false title="Review Checklist"}
- Item.
:::

## A.3 Further Reading

- Reading item.
"""
        res_100 = self._check(appendix_with_anatomy, self.profile_100, "chapter")
        self.assertTrue(res_100.ok, [str(i) for i in res_100.issues])

        res_110 = self._check(appendix_with_anatomy, self.profile_110, "appendix")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    # 3. Unit relaxations
    def test_multiple_closing_elements_of_same_kind_under_110(self) -> None:
        # Two **Example.** paragraphs in the section closing
        double_example = SYNTHETIC_SECTION.replace(
            "**Example.** Illustrative example of the core concept.",
            "**Example.** First illustrative example.\n\n**Example.** Second illustrative example.",
        )
        res_110 = self._check(double_example, self.profile_110, "section-pilot")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

        res_100 = self._check(double_example, self.profile_100, "section-pilot")
        self.assertFalse(res_100.ok)
        self.assertTrue(any("duplicate closing element" in i.message for i in res_100.issues))

    def test_block_list_body_following_label_under_110(self) -> None:
        # **What it includes.** followed by a blank line and bullet points
        block_body = SYNTHETIC_SECTION.replace(
            "**What it includes.** Synthetic attributes and test parameters.",
            "**What it includes.**\n\n- First synthetic bullet point.\n- Second synthetic bullet point.\n- Third synthetic bullet point.",
        )
        res_110 = self._check(block_body, self.profile_110, "section-pilot")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

        res_100 = self._check(block_body, self.profile_100, "section-pilot")
        self.assertFalse(res_100.ok)
        self.assertTrue(any("must include non-empty body text" in i.message for i in res_100.issues))

    def test_table_cell_text_ignored_by_unit_scanner_under_110(self) -> None:
        # Table contains cell text matching "Example"
        section_with_table = SYNTHETIC_SECTION.replace(
            "**What it includes.** Synthetic attributes and test parameters.",
            "**What it includes.** Synthetic attributes and test parameters.\n\n"
            "| Header 1 | Header 2 |\n"
            "| :--- | :--- |\n"
            "| Example | Table cell value explaining an example |\n"
            "| Purpose | Table cell value explaining purpose |\n",
        )
        res_110 = self._check(section_with_table, self.profile_110, "section-pilot")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    def test_worked_example_body_may_contain_bold_label_under_110(self) -> None:
        chapter_with_worked_example_label = SYNTHETIC_CHAPTER.replace(
            "A concrete walkthrough of the synthetic case.",
            "A concrete walkthrough of the synthetic case.\n\n"
            "**Worked example.** Specific synthetic scenario narrative.",
        )
        res_110 = self._check(chapter_with_worked_example_label, self.profile_110, "chapter")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    def test_worked_example_body_with_bold_label_fails_under_100_and_020(self) -> None:
        chapter_with_worked_example_label = SYNTHETIC_CHAPTER.replace(
            "A concrete walkthrough of the synthetic case.",
            "A concrete walkthrough of the synthetic case.\n\n"
            "**Worked example.** Specific synthetic scenario narrative.",
        ).replace(
            'title="Architecture Review Checklist — Domain"',
            'title="Review Checklist"',
        )
        res_100 = self._check(chapter_with_worked_example_label, self.profile_100, "chapter")
        self.assertFalse(res_100.ok)
        self.assertTrue(
            any("found a bold paragraph instead of a heading" in i.message for i in res_100.issues),
            f"Expected wrong-form heading finding in: {[str(i) for i in res_100.issues]}",
        )

        res_020 = self._check(chapter_with_worked_example_label, self.profile_020, "chapter")
        self.assertFalse(res_020.ok)
        self.assertTrue(
            any("found a bold paragraph instead of a heading" in i.message for i in res_020.issues),
            f"Expected wrong-form heading finding in: {[str(i) for i in res_020.issues]}",
        )

    def test_untitled_container_reports_malformed_under_100_and_020(self) -> None:
        untitled_container = SYNTHETIC_CHAPTER.replace(
            "## 1.1 First Section",
            "::: {.custom-container}\nCustom content inside container.\n:::\n\n## 1.1 First Section",
        ).replace(
            'title="Architecture Review Checklist — Domain"',
            'title="Review Checklist"',
        )
        for prof in (self.profile_020, self.profile_100):
            with self.subTest(profile_version=prof["version"]):
                res = self._check(untitled_container, prof, "chapter")
                self.assertFalse(res.ok)
                self.assertTrue(
                    any('callout "untitled" has no callout-* class' in i.message for i in res.issues),
                    f"Expected malformed container diagnostic in {[str(i) for i in res.issues]}",
                )

        # Under 1.1.0, untitled generic divs are permitted, but titled non-callout containers fail
        res_110_untitled = self._check(
            untitled_container.replace('title="Review Checklist"', 'title="Architecture Review Checklist — Domain"'),
            self.profile_110,
            "chapter",
        )
        self.assertTrue(res_110_untitled.ok, [str(i) for i in res_110_untitled.issues])

        titled_container = untitled_container.replace(
            "::: {.custom-container}",
            '::: {title="Missing Callout Class"}',
        )
        res_110_titled = self._check(titled_container, self.profile_110, "chapter")
        self.assertFalse(res_110_titled.ok)
        self.assertTrue(
            any('callout "Missing Callout Class" has no callout-* class' in i.message for i in res_110_titled.issues),
            f"Expected malformed container diagnostic in {[str(i) for i in res_110_titled.issues]}",
        )

    def test_appendix_mode_dispatch_rejected_under_100_and_020(self) -> None:
        appendix_text = "# Appendix A — Data Catalog\n\nSome body text.\n"
        for prof in (self.profile_020, self.profile_100):
            with self.subTest(profile_version=prof["version"]):
                res = self._check(appendix_text, prof, "appendix")
                self.assertFalse(res.ok)
                self.assertTrue(
                    any('unsupported mode "appendix"' in i.message for i in res.issues),
                    f"Expected unsupported mode in {[str(i) for i in res.issues]}",
                )

        res_110 = self._check(appendix_text, self.profile_110, "appendix")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    def test_callout_with_only_table_body_passes_under_both_100_and_110(self) -> None:
        # A Decision & Trade-off callout whose body consists solely of a markdown table
        section_with_table_callout = SYNTHETIC_SECTION.replace(
            "::: {.callout-important appearance=\"simple\" icon=false title=\"Decision & Trade-off\"}\nA synthetic decision and trade-off table.\n:::",
            "::: {.callout-important appearance=\"simple\" icon=false title=\"Decision & Trade-off\"}\n"
            "| Option | Pro | Con |\n"
            "| :--- | :--- | :--- |\n"
            "| Monolith | Simple transactions | Scaling limits |\n"
            "| Services | Independent deployment | Network complexity |\n"
            ":::",
        )
        res_100 = self._check(section_with_table_callout, self.profile_100, "section-pilot")
        self.assertTrue(res_100.ok, [str(i) for i in res_100.issues])

        res_110 = self._check(section_with_table_callout, self.profile_110, "section-pilot")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    def test_appendix_with_only_data_table_passes_under_110(self) -> None:
        appendix_with_table = """\
# Appendix A — Data Catalog

| Column | Type | Description |
| :--- | :--- | :--- |
| id | uuid | Primary key |
| status | string | Order lifecycle state |
"""
        res_110 = self._check(appendix_with_table, self.profile_110, "appendix")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])

    def test_appendix_with_empty_subheading_fails_under_110(self) -> None:
        # Appendix with one H1 plus an empty H2 must fail as having no substantive body
        appendix_empty_subheading = """\
# Appendix A — Empty Subheading Appendix

## A.1 Subheading Without Body
"""
        res_110 = self._check(appendix_empty_subheading, self.profile_110, "appendix")
        self.assertFalse(res_110.ok)
        self.assertTrue(
            any("appendix body must not be empty" in i.message for i in res_110.issues),
            f"Expected empty body finding in: {[str(i) for i in res_110.issues]}",
        )

    def test_appendix_with_fenced_code_body_passes_under_110(self) -> None:
        appendix_with_code = """\
# Appendix A — Code Snippets

```python
def example():
    return True
```
"""
        res_110 = self._check(appendix_with_code, self.profile_110, "appendix")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])


    def test_callout_with_only_fenced_code_fails_under_100_and_020_but_passes_under_110(self) -> None:
        code_callout = SYNTHETIC_SECTION.replace(
            "::: {.callout-important appearance=\"simple\" icon=false title=\"Decision & Trade-off\"}\nA synthetic decision and trade-off table.\n:::",
            "::: {.callout-important appearance=\"simple\" icon=false title=\"Decision & Trade-off\"}\n"
            "```text\n"
            "An example value.\n"
            "```\n"
            ":::",
        )
        for prof in (self.profile_020, self.profile_100):
            with self.subTest(profile_version=prof["version"]):
                res = self._check(code_callout, prof, "section-pilot")
                self.assertFalse(res.ok)
                self.assertTrue(
                    any('closing element "Decision & Trade-off" must include non-empty body text' in i.message for i in res.issues),
                    f"Expected non-empty body text finding in {[str(i) for i in res.issues]}",
                )

        res_110 = self._check(code_callout, self.profile_110, "section-pilot")
        self.assertTrue(res_110.ok, [str(i) for i in res_110.issues])


if __name__ == "__main__":
    unittest.main()
