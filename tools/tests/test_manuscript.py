"""Structural manuscript validation tests.

These tests prove deterministic structure only. They do not assert prose quality, factual accuracy or
visual usefulness.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.manuscript import validate_manuscript  # noqa: E402

SECTION = """\
## 2.2 The Brief as a Decision Record

**Definition.** A brief is a bounded decision record for a handbook.

**Purpose.** It lets a reviewer reject out-of-scope work without asking the author.

**What it includes.** Audience, promise, scope, non-goals and evidence.

**Why it is needed.** Without it, scope grows and review becomes opinion.

**Example.** An illustrative brief names one audience and one excluded topic.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Writing a brief as a wish list rather than a set of boundaries.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
How much scope should the brief fix? Fix enough to reject work; leave room for discovery.
:::
"""

CHAPTER = """\
# 1. Why Handbooks Fail

A chapter about failure modes.

::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}
- A handbook has no owner.
:::

::: {.callout-tip appearance="simple" icon=false title="Key Takeaway"}
Ownership and boundaries matter more than tooling.
:::

## 1.1 What a Handbook Is For

**Definition.** A handbook is a maintained decision record for a body of work.

**Purpose.** It gives a reader a reliable starting point.

**What it includes.** Audience, scope, examples and references.

**Why it is needed.** Without it, knowledge stays in individuals and repeated explanations.

**Example.** An illustrative handbook for one team names its owner and exclusions.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Writing pages without an owner or a maintenance trigger.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
How broad should the handbook be? Narrow enough to maintain; broad enough to answer the reader's
decision.
:::

## 1.2 Worked Example — A Failure

The illustrative failure and its correction.

::: {.callout-important appearance="simple" icon=false title="Review Checklist — Why handbooks fail"}
- Name the owner.
- Name the excluded scope.
:::

## 1.3 Further Reading

- A checkable source.
"""


class SectionPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.profile = support.profile_document()

    def tearDown(self) -> None:
        self._temp.cleanup()

    def check(self, text: str):
        path = self.root / "pilot.qmd"
        path.write_text(text, encoding="utf-8")
        return validate_manuscript(path, self.profile, "section-pilot")

    def test_accepts_valid_section_without_visuals(self) -> None:
        result = self.check(SECTION)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_rejects_missing_required_label(self) -> None:
        result = self.check(
            SECTION.replace(
                "**Purpose.** It lets a reviewer reject out-of-scope work without asking the author.\n\n",
                "",
            )
        )
        self.assertFalse(result.ok)
        self.assertTrue(any('missing required label "Purpose."' in issue.message for issue in result.issues))

    def test_rejects_plain_text_instead_of_bold_label(self) -> None:
        result = self.check(
            SECTION.replace(
                "**Purpose.** It lets a reviewer reject out-of-scope work without asking the author.",
                "Purpose. It lets a reviewer reject out-of-scope work without asking the author.",
            )
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("bold paragraph" in issue.message for issue in result.issues))

    def test_rejects_duplicate_required_label(self) -> None:
        result = self.check(SECTION.replace("**Purpose.**", "**Purpose.** First.\n\n**Purpose.** Second."))
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate required label" in issue.message for issue in result.issues))

    def test_rejects_misordered_labels(self) -> None:
        text = SECTION.replace(
            "**Purpose.** It lets a reviewer reject out-of-scope work without asking the author.\n\n"
            "**What it includes.** Audience, promise, scope, non-goals and evidence.",
            "**What it includes.** Audience, promise, scope, non-goals and evidence.\n\n"
            "**Purpose.** It lets a reviewer reject out-of-scope work without asking the author.",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("misordered" in issue.message for issue in result.issues))

    def test_rejects_heading_instead_of_bold_label(self) -> None:
        result = self.check(SECTION.replace("**Definition.** A brief", "### Definition. A brief"))
        self.assertFalse(result.ok)
        self.assertTrue(any("bold paragraph" in issue.message for issue in result.issues))

    def test_rejects_example_as_callout(self) -> None:
        text = SECTION.replace(
            "**Example.** An illustrative brief names one audience and one excluded topic.",
            '::: {.callout-note title="Example"}\nAn illustrative brief.\n:::',
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("Example" in issue.message and "bold paragraph" in issue.message for issue in result.issues))

    def test_rejects_common_pitfall_as_paragraph(self) -> None:
        text = SECTION.replace(
            '::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}\n'
            "Writing a brief as a wish list rather than a set of boundaries.\n"
            ":::",
            "**Common Pitfall.** Writing a brief as a wish list rather than a set of boundaries.",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("Common Pitfall" in issue.message and "callout" in issue.message for issue in result.issues))

    def test_rejects_misordered_closing_elements(self) -> None:
        common = (
            '::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}\n'
            "Writing a brief as a wish list rather than a set of boundaries.\n"
            ":::"
        )
        decision = (
            '::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}\n'
            "How much scope should the brief fix? Fix enough to reject work; leave room for discovery.\n"
            ":::"
        )
        text = SECTION.replace(common + "\n\n" + decision, decision + "\n\n" + common)
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("closing elements are misordered" in issue.message for issue in result.issues))

    def test_ignores_required_material_inside_fenced_code(self) -> None:
        text = """\
## 2.2 A Section

```markdown
**Definition.** Not real.
**Purpose.** Not real.
**What it includes.** Not real.
**Why it is needed.** Not real.
**Example.** Not real.
::: {.callout-warning title="Common Pitfall"}
Not real.
:::
::: {.callout-important title="Decision & Trade-off"}
Not real.
:::
```
"""
        result = self.check(text)
        self.assertFalse(result.ok)
        messages = " ".join(issue.message for issue in result.issues)
        self.assertIn("missing required label", messages)
        self.assertIn("missing closing element", messages)

    def test_rejects_empty_required_bodies(self) -> None:
        text = """\
## 2.2 An Empty Section

**Definition.**

**Purpose.**

**What it includes.**

**Why it is needed.**

**Example.**

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
:::
"""
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("non-empty body text" in issue.message for issue in result.issues))

    def test_rejects_callout_without_callout_class(self) -> None:
        text = SECTION.replace(
            '::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}\n'
            "Writing a brief as a wish list rather than a set of boundaries.\n"
            ":::",
            '::: {title="Common Pitfall"}\n'
            "Writing a brief as a wish list rather than a set of boundaries.\n"
            ":::",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("callout" in issue.message for issue in result.issues))

    def test_four_backtick_fence_does_not_close_at_three(self) -> None:
        text = """\
## 2.2 A Section

````markdown
```
**Definition.** Fake.
**Purpose.** Fake.
**What it includes.** Fake.
**Why it is needed.** Fake.
**Example.** Fake.
::: {.callout-warning title="Common Pitfall"}
Fake.
:::
::: {.callout-important title="Decision & Trade-off"}
Fake.
:::
```
````
"""
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("missing required label" in issue.message for issue in result.issues))

    def test_rejects_unclosed_callout(self) -> None:
        common = (
            '::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}\n'
            "Writing a brief as a wish list rather than a set of boundaries.\n"
            ":::"
        )
        text = SECTION.replace(common, common.rsplit("\n:::", 1)[0])
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("unclosed callout" in issue.message for issue in result.issues))

    def test_rejects_heading_without_a_meaningful_title(self) -> None:
        result = self.check(SECTION.replace("## 2.2 The Brief as a Decision Record", "## 2.2"))
        self.assertFalse(result.ok)
        self.assertTrue(any("meaningful title" in issue.message for issue in result.issues))

    def test_rejects_missing_section_heading(self) -> None:
        result = self.check(SECTION.replace("## 2.2 The Brief as a Decision Record", ""))
        self.assertFalse(result.ok)
        self.assertTrue(any("missing section pilot heading" in issue.message for issue in result.issues))


class ChapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.profile = support.profile_document()

    def tearDown(self) -> None:
        self._temp.cleanup()

    def check(self, text: str):
        path = self.root / "chapter.qmd"
        path.write_text(text, encoding="utf-8")
        return validate_manuscript(path, self.profile, "chapter")

    def test_accepts_valid_chapter_without_visuals(self) -> None:
        result = self.check(CHAPTER)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_rejects_content_section_missing_unit_labels(self) -> None:
        text = CHAPTER.replace(
            "**Purpose.** It gives a reader a reliable starting point.\n\n", ""
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any('missing required label "Purpose."' in issue.message for issue in result.issues))

    def test_rejects_content_section_missing_closing_element(self) -> None:
        decision = (
            '::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}\n'
            "How broad should the handbook be? Narrow enough to maintain; broad enough to answer the reader's\n"
            "decision.\n"
            ":::"
        )
        text = CHAPTER.replace(decision, "")
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any('missing closing element "Decision & Trade-off"' in issue.message for issue in result.issues))

    def test_rejects_content_section_with_single_subsection(self) -> None:
        text = CHAPTER.replace(
            "## 1.1 What a Handbook Is For\n\n**Definition.**",
            "## 1.1 What a Handbook Is For\n\n### 1.1.1 Only Unit\n\n**Definition.**",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("single subsection" in issue.message for issue in result.issues))

    def test_rejects_missing_when_to_use(self) -> None:
        text = CHAPTER.replace(
            '::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}\n'
            "- A handbook has no owner.\n"
            ":::",
            "",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("missing chapter element" in issue.message for issue in result.issues))

    def test_rejects_when_to_use_after_first_section(self) -> None:
        callout = (
            '::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}\n'
            "- A handbook has no owner.\n"
            ":::"
        )
        text = CHAPTER.replace(callout + "\n\n", "", 1)
        text = text.replace("## 1.1 What a Handbook Is For\n\n", "## 1.1 What a Handbook Is For\n\n" + callout + "\n\n")
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("before the first numbered section" in issue.message for issue in result.issues))

    def test_rejects_misordered_opening_callouts(self) -> None:
        when = (
            '::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}\n'
            "- A handbook has no owner.\n"
            ":::"
        )
        key = (
            '::: {.callout-tip appearance="simple" icon=false title="Key Takeaway"}\n'
            "Ownership and boundaries matter more than tooling.\n"
            ":::"
        )
        text = CHAPTER.replace(when + "\n\n" + key, key + "\n\n" + when)
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("misordered" in issue.message for issue in result.issues))

    def test_rejects_review_checklist_outside_worked_example(self) -> None:
        checklist = (
            '::: {.callout-important appearance="simple" icon=false title="Review Checklist — Why handbooks fail"}\n'
            "- Name the owner.\n"
            "- Name the excluded scope.\n"
            ":::"
        )
        text = CHAPTER.replace(checklist + "\n\n", "", 1)
        text = text.replace(
            "## 1.1 What a Handbook Is For\n\n",
            "## 1.1 What a Handbook Is For\n\n" + checklist + "\n\n",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("inside the worked-example section" in issue.message for issue in result.issues))

    def test_rejects_worked_example_that_is_not_last_content_section(self) -> None:
        text = CHAPTER.replace(
            "## 1.3 Further Reading",
            "## 1.3 Another Section\n\nMore prose.\n\n## 1.4 Further Reading",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("last section before Further Reading" in issue.message for issue in result.issues))

    def test_rejects_further_reading_that_is_not_last(self) -> None:
        text = CHAPTER + "\n## 1.4 Appendix\n\nExtra prose.\n"
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("last numbered section" in issue.message for issue in result.issues))

    def test_rejects_wrong_form_for_opening_callout(self) -> None:
        text = CHAPTER.replace(
            '::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}\n'
            "- A handbook has no owner.\n"
            ":::",
            "**When to Use This Chapter.** A handbook has no owner.",
        )
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("When to Use This Chapter" in issue.message and "callout" in issue.message for issue in result.issues))

    def test_rejects_duplicate_opening_callout(self) -> None:
        callout = (
            '::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}\n'
            "- A handbook has no owner.\n"
            ":::"
        )
        text = CHAPTER.replace(callout, callout + "\n\n" + callout, 1)
        result = self.check(text)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate" in issue.message for issue in result.issues))

    def test_ignores_callouts_inside_fenced_code(self) -> None:
        text = """\
# 1. A Chapter

```markdown
::: {.callout-note title="When to Use This Chapter"}
Not real.
:::
::: {.callout-tip title="Key Takeaway"}
Not real.
:::
```

## 1.1 First

## 1.2 Worked Example

::: {.callout-important title="Review Checklist — Topic"}
- Real checklist.
:::

## 1.3 Further Reading
"""
        result = self.check(text)
        self.assertFalse(result.ok)
        messages = " ".join(issue.message for issue in result.issues)
        self.assertIn("missing chapter element", messages)


if __name__ == "__main__":
    unittest.main()
