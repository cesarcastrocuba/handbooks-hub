"""Tests for appendices and book-owned Document Control (0060)."""

import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from handbook_toolkit.build import build_book
from handbook_toolkit.build_staging import _transform_chapter
from handbook_toolkit.build_identity import PREVIEW_SUFFIX, validation_version
from handbook_toolkit.build_types import BuildError
from handbook_toolkit.print_layout import (
    extract_document_control_version,
    has_document_control_table,
    inject_document_control,
    validate_document_control_version,
)

from test_build import PROFILE, commit_all, make_book

QUARTO = shutil.which("quarto")
PDFINFO = shutil.which("pdfinfo")
PDFTOTEXT = shutil.which("pdftotext")
BUILD_AVAILABLE = QUARTO is not None and PDFINFO is not None


class AppendicesDocumentControlUnitTests(unittest.TestCase):
    def test_has_document_control_table(self) -> None:
        text_without_table = "# Document Control {.unnumbered}\n\nSome introductory text.\n"
        self.assertFalse(has_document_control_table(text_without_table))

        text_with_table = (
            "# Document Control {.unnumbered .unlisted}\n\n"
            "| Field | Value |\n"
            "| :--- | :--- |\n"
            "| Title | Sample Book |\n"
            "| Version | 3.1.0 |\n\n"
            "#### History\n"
        )
        self.assertTrue(has_document_control_table(text_with_table))

        # Case-insensitive heading match
        text_case_insensitive = (
            "# Document control\n\n"
            "| Field | Value |\n"
            "| :--- | :--- |\n"
            "| Version | 1.0 |\n"
        )
        self.assertTrue(has_document_control_table(text_case_insensitive))

    def test_extract_document_control_version(self) -> None:
        text = (
            "# Document Control {.unnumbered}\n\n"
            "| Field | Value |\n"
            "| :--- | :--- |\n"
            "| Title | Sample Book |\n"
            "| Version | 3.1 (pre-release 3.1.0-rc.1) |\n"
            "| Date | November 2026 |\n"
        )
        self.assertEqual(
            extract_document_control_version(text),
            "3.1 (pre-release 3.1.0-rc.1)",
        )

        no_ver = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| :--- | :--- |\n"
            "| Title | Sample Book |\n"
        )
        self.assertIsNone(extract_document_control_version(no_ver))

    def test_validate_document_control_version(self) -> None:
        # Pre-release exact match inside description
        text_rc = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| Version | 3.1 (pre-release 3.1.0-rc.1) |\n"
        )
        validate_document_control_version(text_rc, "3.1.0-rc.1")

        # Final release x.y.0 matched by x.y
        text_final = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| Version | 3.1 |\n"
        )
        validate_document_control_version(text_final, "3.1.0")

        # Exact match of full semantic version
        text_exact = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| Version | 3.1.0 |\n"
        )
        validate_document_control_version(text_exact, "3.1.0")

        # Mismatch raises BuildError
        with self.assertRaises(BuildError) as ctx:
            validate_document_control_version(text_final, "3.2.0")
        self.assertIn("does not match edition version '3.2.0'", str(ctx.exception))

        # Missing version row raises BuildError
        text_missing = "# Document Control\n\n| Field | Value |\n| Title | Test |\n"
        with self.assertRaises(BuildError) as ctx:
            validate_document_control_version(text_missing, "1.0.0")
        self.assertIn("has no Version row to validate", str(ctx.exception))

    def test_validation_version_strips_only_a_preview_suffix(self) -> None:
        self.assertEqual(PREVIEW_SUFFIX, "-preview")
        self.assertEqual(validation_version("3.1.0-preview", True), "3.1.0")
        self.assertEqual(validation_version("3.1.0", True), "3.1.0")
        self.assertEqual(validation_version("3.1.0-rc.1", True), "3.1.0-rc.1")
        self.assertEqual(validation_version("3.1.0-preview", False), "3.1.0-preview")

    def test_preview_previews_the_release_version_it_describes(self) -> None:
        text_final = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| Version | 3.1 |\n"
        )
        text_rc = (
            "# Document Control\n\n"
            "| Field | Value |\n"
            "| Version | 3.1 (pre-release 3.1.0-rc.1) |\n"
        )
        # A preview of the final book validates against 3.1.0, and an rc preview keeps its rc.
        validate_document_control_version(text_final, validation_version("3.1.0-preview", True))
        validate_document_control_version(text_rc, validation_version("3.1.0-rc.1", True))
        # Release builds stay strict: the preview identity never matches, and a wrong
        # release version still fails.
        with self.assertRaises(BuildError):
            validate_document_control_version(text_final, validation_version("3.1.0-preview", False))
        with self.assertRaises(BuildError):
            validate_document_control_version(text_final, "3.0.0")
        with self.assertRaises(BuildError):
            validate_document_control_version(text_rc, "3.2.0-rc.1")

    def test_inject_document_control_preserves_existing_table_and_validates(self) -> None:
        existing = (
            "# Document Control {.unnumbered}\n\n"
            "| Field | Value |\n"
            "| :--- | :--- |\n"
            "| Version | 2.5 |\n"
        )
        generated_table = "| Field | Value |\n| :--- | :--- |\n| Version | 2.5.0 |\n"

        # Valid version: existing text is unchanged
        result = inject_document_control(existing, generated_table, version="2.5.0")
        self.assertEqual(result, existing)

        # Mismatched version: raises BuildError
        with self.assertRaises(BuildError):
            inject_document_control(existing, generated_table, version="2.6.0")

        # Heading without existing table: injected
        empty_section = "# Document Control {.unnumbered}\n\nProse text.\n"
        injected = inject_document_control(empty_section, generated_table, version="2.5.0")
        self.assertIsNotNone(injected)
        assert injected is not None
        self.assertIn(generated_table, injected)

    def test_transform_chapter_appendix_l1_and_l2_formatting(self) -> None:
        # The literal "Appendix X — Title" label belongs to the staged heading and the
        # heading is unnumbered, so every edition shows the same text.
        text_a = """\
# Appendix A — Architecture Principles

Some intro.

## A.1 Principle One

Details.

## Principle Two

More details.
"""
        staged_a = _transform_chapter(text_a, "A", is_appendix=True)
        lines = staged_a.splitlines()
        self.assertEqual(lines[0], "# Appendix A — Architecture Principles {.unnumbered}")
        self.assertIn("## A.1 Principle One {.unnumbered}", lines)
        # A section without a source number gets the next one, never the renderer's.
        self.assertIn("## A.2 Principle Two {.unnumbered}", lines)

        staged_md = _transform_chapter(text_a, "A", is_appendix=True, strip_heading_numbers=False)
        self.assertTrue(staged_md.startswith("# Appendix A — Architecture Principles {.unnumbered}"))
        self.assertIn("## A.2 Principle Two {.unnumbered}", staged_md.splitlines())

        # A colon instead of an em dash and authored attributes are normalized, not lost.
        text_b = """\
# Appendix B: Reference Checklists {#sec_checklists .unnumbered}

## B.1 Release Gate Checklist {#sec_b1}

Checklist items.
"""
        staged_b = _transform_chapter(text_b, "B", is_appendix=True)
        self.assertTrue(
            staged_b.startswith("# Appendix B — Reference Checklists {#sec_checklists .unnumbered}")
        )
        self.assertIn("## B.1 Release Gate Checklist {#sec_b1 .unnumbered}", staged_b)

        # Headings inside a fenced code block are content, not sections.
        text_c = """\
# Appendix C — Templates

```
# Not a heading
## Not a section
```

## C.1 Real Section
"""
        staged_c = _transform_chapter(text_c, "C", is_appendix=True)
        self.assertIn("# Not a heading", staged_c)
        self.assertIn("## Not a section", staged_c)
        self.assertIn("## C.1 Real Section {.unnumbered}", staged_c)


class AppendicesDocumentControlIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdf tools required")
    def test_preview_of_a_final_book_validates_its_release_document_control(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _ = make_book(root, chapter=True, version="1.0.0")
            control = repo / "manuscript/front-matter/document-control.qmd"
            control.parent.mkdir(parents=True)
            control.write_text(
                "# Document Control {.unnumbered}\n\n"
                "| Field | Value |\n"
                "| :--- | :--- |\n"
                "| Title | Synthetic Handbook |\n"
                "| Version | 1.0 |\n"
                "| Status | Released |\n",
                encoding="utf-8",
            )
            (repo / "manuscript/book.yml").write_text(
                "front:\n"
                "  - front-matter/document-control.qmd\n"
                "chapters:\n"
                "  - chapters/pilot.qmd\n"
                "back: []\n"
                "appendices: []\n"
                "references: []\n",
                encoding="utf-8",
            )
            commit = commit_all(repo, "document control for a final version")
            build_book(repo, commit, root / "release", profile=PROFILE, mode="chapter")
            build_book(
                repo,
                commit,
                root / "preview",
                profile=PROFILE,
                mode="chapter",
                version="1.0.0-preview",
                preview=True,
            )

    @unittest.skipUnless(BUILD_AVAILABLE and PDFTOTEXT, "Quarto and pdf tools required")
    def test_end_to_end_synthetic_book_with_appendices_and_document_control(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _ = make_book(root, chapter=True, version="1.0.0-rc.1")

            # Front matter: document control and introduction
            doc_ctrl = repo / "manuscript/front-matter/document-control.qmd"
            doc_ctrl.parent.mkdir(parents=True, exist_ok=True)
            doc_ctrl.write_text(
                "# Document Control {.unnumbered}\n\n"
                "| Field | Value |\n"
                "| :--- | :--- |\n"
                "| Title | Synthetic Handbook |\n"
                "| Version | 1.0 (pre-release 1.0.0-rc.1) |\n"
                "| Status | Pre-release |\n",
                encoding="utf-8",
            )
            intro = repo / "manuscript/front-matter/intro.qmd"
            intro.write_text("# Introduction {.unnumbered}\n\nIntro prose.\n", encoding="utf-8")

            # Appendix A: not .unnumbered in source
            app_a = repo / "manuscript/appendices/app-a.qmd"
            app_a.parent.mkdir(parents=True, exist_ok=True)
            app_a.write_text(
                "# Appendix A — Worked Architecture Cases\n\n"
                "Appendix A overview.\n\n"
                "## A.1 First Worked Example\n\n"
                "| Scenario | Result |\n|---|---|\n| Failover | 2s |\n\n"
                ": Failover Results {#tbl-a-1}\n\n"
                "![Appendix Diagram](../images/fixture.png){#fig-a-1}\n",
                encoding="utf-8",
            )

            # Appendix B: .unnumbered in source
            app_b = repo / "manuscript/appendices/app-b.qmd"
            app_b.write_text(
                "# Appendix B — Operational Checklists {.unnumbered}\n\n"
                "Appendix B overview.\n\n"
                "## B.1 Readiness Checklist\n\n"
                "| Item | Status |\n|---|---|\n| Gate | Pass |\n\n"
                ": Gate Status {#tbl-b-1}\n",
                encoding="utf-8",
            )

            # References
            refs = repo / "manuscript/back-matter/references.qmd"
            refs.parent.mkdir(parents=True, exist_ok=True)
            refs.write_text(
                "# References {.unnumbered}\n\nReference items.\n",
                encoding="utf-8",
            )

            (repo / "manuscript/book.yml").write_text(
                "front:\n"
                "  - front-matter/document-control.qmd\n"
                "  - front-matter/intro.qmd\n"
                "chapters:\n"
                "  - chapters/pilot.qmd\n"
                "back: []\n"
                "appendices:\n"
                "  - appendices/app-a.qmd\n"
                "  - appendices/app-b.qmd\n"
                "references:\n"
                "  - back-matter/references.qmd\n",
                encoding="utf-8",
            )

            commit = commit_all(repo, "configure appendices and document control")
            output = root / "dist"

            # 1. Build succeeds with matching Document Control version
            build_book(repo, commit, output, profile=PROFILE, mode="chapter")

            # Verify HTML
            with zipfile.ZipFile(output / "book-html.zip") as z:
                app_a_html = z.read("manuscript/appendices/app-a.html").decode("utf-8")
                self.assertIn("Appendix A — Worked Architecture Cases", app_a_html)
                self.assertIn("First Worked Example", app_a_html)
                self.assertIn("A.1 First Worked Example", app_a_html)
                self.assertNotIn("Appendix A —  Worked", app_a_html)

                app_b_html = z.read("manuscript/appendices/app-b.html").decode("utf-8")
                self.assertIn("Appendix B — Operational Checklists", app_b_html)
                self.assertIn("B.1 Readiness Checklist", app_b_html)

                # The reading site keeps the appendices in one part and References at
                # the top level after it; the sidebar entries carry the literal labels.
                sidebar_m = re.search(r'<nav id="quarto-sidebar"[^>]*>(.*?)</nav>', app_a_html, re.DOTALL)
                self.assertIsNotNone(sidebar_m)
                assert sidebar_m is not None
                sidebar = sidebar_m.group(1)
                self.assertIn("Appendices", sidebar)
                self.assertIn("References", sidebar)
                self.assertIn("Appendix A — Worked Architecture Cases", sidebar)
                self.assertIn("Appendix B — Operational Checklists", sidebar)
                part_m = re.search(
                    r'<span class="menu-text" id="[^"]*">Appendices</span>.*?(<ul [^>]*>.*?</ul>)',
                    sidebar,
                    re.DOTALL,
                )
                self.assertIsNotNone(part_m)
                assert part_m is not None
                part_html = part_m.group(1)
                self.assertIn("app-a.html", part_html)
                self.assertIn("app-b.html", part_html)
                self.assertNotIn("references.html", part_html)
                self.assertIsNone(re.search(r'chapter-number">[^<]*</span>\s*<span class="chapter-title">Appendix', sidebar))

                # The References breadcrumb is top level, not "Appendices › References".
                refs_html = z.read("manuscript/back-matter/references.html").decode("utf-8")
                bread_m = re.search(
                    r'<nav class="quarto-page-breadcrumbs[^"]*"[^>]*>(.*?)</nav>', refs_html, re.DOTALL
                )
                self.assertIsNotNone(bread_m)
                assert bread_m is not None
                self.assertNotIn("Appendices", bread_m.group(1))
                self.assertIn("References", bread_m.group(1))

            # Verify PDF
            pdf_path = output / "book.pdf"
            self.assertTrue(pdf_path.exists())
            pdf_text = subprocess.check_output(["pdftotext", "-layout", str(pdf_path), "-"]).decode()

            # No standalone "Appendices" page: "Appendices" must not appear alone on a page
            pages = pdf_text.split("\x0c")
            for idx, page in enumerate(pages):
                lines = [l.strip() for l in page.splitlines() if l.strip()]
                content_lines = [l for l in lines if not l.startswith("Licensed under") and not l.startswith("Page ")]
                self.assertNotEqual(
                    content_lines,
                    ["Appendices"],
                    f"Found standalone Appendices page at page {idx + 1}",
                )

            # PDF Contents outline lists Appendix A and Appendix B, with one space
            self.assertIn("Appendix A — Worked Architecture Cases", pdf_text)
            self.assertIn("Appendix B — Operational Checklists", pdf_text)
            self.assertNotIn("Appendix A —  Worked", pdf_text)
            self.assertIn("A.1 First Worked Example", pdf_text)
            self.assertIn("B.1 Readiness Checklist", pdf_text)
            # Table and figure captions
            self.assertIn("Table A.1: Failover Results", pdf_text)
            self.assertIn("Figure A.1: Appendix Diagram", pdf_text)
            self.assertIn("Table B.1: Gate Status", pdf_text)

            # Verify DOCX
            docx_path = output / "book.docx"
            self.assertTrue(docx_path.exists())
            with zipfile.ZipFile(docx_path) as z:
                xml_content = z.read("word/document.xml")
                root_elem = ET.fromstring(xml_content)
            docx_headings = []
            for p in root_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                pPr = p.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr")
                if pPr is not None:
                    pStyle = pPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle")
                    if pStyle is not None and "Heading" in pStyle.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", ""):
                        docx_headings.append("".join(p.itertext()))

            self.assertIn("Appendix A — Worked Architecture Cases", docx_headings)
            self.assertIn("A.1 First Worked Example", docx_headings)
            self.assertIn("Appendix B — Operational Checklists", docx_headings)
            self.assertIn("B.1 Readiness Checklist", docx_headings)

            # Verify Markdown
            md_path = output / "book.md"
            self.assertTrue(md_path.exists())
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Appendix A — Worked Architecture Cases", md_text)
            self.assertIn("Appendix B — Operational Checklists", md_text)

            # 2. Build fails when Document Control version is mismatched
            doc_ctrl.write_text(
                "# Document Control {.unnumbered}\n\n"
                "| Field | Value |\n"
                "| :--- | :--- |\n"
                "| Version | 2.0 (mismatched) |\n",
                encoding="utf-8",
            )
            commit2 = commit_all(repo, "mismatched document control version")
            out_fail = root / "dist-fail"
            with self.assertRaises(BuildError) as ctx:
                build_book(repo, commit2, out_fail, profile=PROFILE, mode="chapter")
            self.assertIn("does not match edition version", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
