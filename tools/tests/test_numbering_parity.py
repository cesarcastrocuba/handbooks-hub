"""Regression and parity tests for figure, table and appendix numbering (0051)."""
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from handbook_toolkit.build_staging import (
    _appendix_letter,
    _count_tables,
    _is_unnumbered,
    _prepare_render,
    _render_config,
    _strip_heading_number,
    _transform_chapter,
)
from handbook_toolkit.build_types import BuildError

QUARTO = shutil.which("quarto")
PDFINFO = shutil.which("pdfinfo")
PDFTOTEXT = shutil.which("pdftotext")
BUILD_AVAILABLE = QUARTO is not None and PDFINFO is not None


class NumberingParityUnitTests(unittest.TestCase):
    def test_appendix_letter(self) -> None:
        self.assertEqual(_appendix_letter(1), "A")
        self.assertEqual(_appendix_letter(2), "B")
        self.assertEqual(_appendix_letter(26), "Z")
        self.assertEqual(_appendix_letter(27), "AA")

    def test_strip_heading_number(self) -> None:
        self.assertEqual(_strip_heading_number("1. Chapter One"), "Chapter One")
        self.assertEqual(_strip_heading_number("1.2 Section Two"), "Section Two")
        self.assertEqual(_strip_heading_number("Appendix A — Worked Cases"), "Worked Cases")
        self.assertEqual(_strip_heading_number("Appendix B: Reference Checklists"), "Reference Checklists")
        self.assertEqual(_strip_heading_number("A.1 First Case"), "First Case")
        self.assertEqual(_strip_heading_number("Introduction {.unnumbered}"), "Introduction {.unnumbered}")

    def test_figure_caption_prefix_stripped_when_matching(self) -> None:
        text = """\
# Chapter 1

![Figure 1.1 — First Figure](diagram1.png){#fig-1-1 width="100%"}

![Figure 1.2: Second Figure](diagram2.png){#fig-1-2}
"""
        transformed = _transform_chapter(text, "1")
        self.assertIn("![First Figure](diagram1.png){#fig-1-1 width=\"100%\"}", transformed)
        self.assertIn("![Second Figure](diagram2.png){#fig-1-2}", transformed)
        self.assertNotIn("Figure 1.1 —", transformed)
        self.assertNotIn("Figure 1.2:", transformed)

    def test_figure_caption_without_prefix_retained(self) -> None:
        text = """\
# Chapter 1

![Unprefixed Figure Caption](diagram.png){#fig-1-1 width="90%"}
"""
        transformed = _transform_chapter(text, "1")
        self.assertIn("![Unprefixed Figure Caption](diagram.png){#fig-1-1 width=\"90%\"}", transformed)

    def test_figure_caption_mismatch_raises_build_error(self) -> None:
        # Second figure labeled 1.3 instead of 1.2
        text = """\
# Chapter 1

![Figure 1.1 — First Figure](diagram1.png){#fig-1-1}

![Figure 1.3 — Mislabeled Figure](diagram2.png){#fig-1-2}
"""
        with self.assertRaises(BuildError) as ctx:
            _transform_chapter(text, "1", path="ch01.qmd")
        self.assertIn("figure caption label '1.3' does not match expected number '1.2'", str(ctx.exception))

    def test_figure_caption_class_first_stripped_when_matching(self) -> None:
        text = """\
# Chapter 1

![Figure 1.1 — Section Architecture](diagram1.png){.wide #fig-section-structure}
"""
        transformed = _transform_chapter(text, "1")
        self.assertIn("![Section Architecture](diagram1.png){.wide #fig-section-structure}", transformed)
        self.assertNotIn("Figure 1.1 —", transformed)

    def test_figure_caption_class_first_mismatch_raises_build_error(self) -> None:
        text = """\
# Chapter 1

![Figure 9.9 — Wrong label](diagram1.png){.wide #fig-section-structure}
"""
        with self.assertRaises(BuildError) as ctx:
            _transform_chapter(text, "1", path="ch01.qmd")
        self.assertIn("figure caption label '9.9' does not match expected number '1.1'", str(ctx.exception))

    def test_appendix_figure_prefix_stripped_and_validated(self) -> None:
        text = """\
# Worked Architecture Cases

![Figure A.1 — Reference Checkout Flow](checkout.png){#fig-a-1}
"""
        transformed = _transform_chapter(text, "A")
        self.assertIn("![Reference Checkout Flow](checkout.png){#fig-a-1}", transformed)
        self.assertNotIn("Figure A.1 —", transformed)

    def test_appendix_figure_mismatch_raises_build_error(self) -> None:
        text = """\
# Worked Architecture Cases

![Figure B.1 — Wrong Appendix Letter](checkout.png){#fig-a-1}
"""
        with self.assertRaises(BuildError) as ctx:
            _transform_chapter(text, "A")
        self.assertIn("figure caption label 'B.1' does not match expected number 'A.1'", str(ctx.exception))

    def test_table_caption_prefix_stripped_when_matching(self) -> None:
        text = """\
# Chapter 1

| A | B |
|---|---|
| 1 | 2 |

: Table 1.1 — Functional Categories
"""
        transformed = _transform_chapter(text, "1")
        self.assertIn(": Functional Categories {#tbl-1-1}", transformed)
        self.assertNotIn("Table 1.1 —", transformed)

    def test_table_caption_mismatch_raises_build_error(self) -> None:
        text = """\
# Chapter 1

| A | B |
|---|---|
| 1 | 2 |

: Table 1.2 — Wrong Number
"""
        with self.assertRaises(BuildError) as ctx:
            _transform_chapter(text, "1")
        self.assertIn("table caption label '1.2' does not match expected number '1.1'", str(ctx.exception))

    def test_positional_table_numbering_for_chapters_and_appendices(self) -> None:
        # Front matter with tables
        intro_text = """\
# Introduction {.unnumbered}

| A | B |
|---|---|
| 1 | 2 |

: Intro Table One

| C | D |
|---|---|
| 3 | 4 |

: Intro Table Two
"""
        role_text = """\
# The Role {.unnumbered}

| E | F |
|---|---|
| 5 | 6 |

: Role Table One
"""
        # Chapter 1 tables
        ch1_text = """\
# 1. Architecture Requirements

| G | H |
|---|---|
| 7 | 8 |

: Chapter 1 Table One
"""
        # Appendix A tables
        app_text = """\
# Appendix A — Reference Catalog

| I | J |
|---|---|
| 9 | 10 |

: Appendix Table One
"""
        with tempfile.TemporaryDirectory() as temp:
            ws = Path(temp)
            (ws / "intro.qmd").write_text(intro_text, encoding="utf-8")
            (ws / "role.qmd").write_text(role_text, encoding="utf-8")
            (ws / "ch01.qmd").write_text(ch1_text, encoding="utf-8")
            (ws / "app-a.qmd").write_text(app_text, encoding="utf-8")

            entries = ["intro.qmd", "role.qmd", "ch01.qmd", "app-a.qmd"]
            rendered = _prepare_render(ws, entries, appendices=["app-a.qmd"])

            # Intro tables get tbl-0-1, tbl-0-2
            intro_transformed = (ws / "intro.qmd").read_text(encoding="utf-8")
            self.assertIn("{#tbl-0-1}", intro_transformed)
            self.assertIn("{#tbl-0-2}", intro_transformed)

            # Role table gets tbl-0-3 (running front-matter count)
            role_transformed = (ws / "role.qmd").read_text(encoding="utf-8")
            self.assertIn("{#tbl-0-3}", role_transformed)

            # Chapter 1 table starts at tbl-1-1 (front matter does not count)
            ch1_transformed = (ws / "ch01.qmd").read_text(encoding="utf-8")
            self.assertIn("{#tbl-1-1}", ch1_transformed)

            # Appendix A table gets tbl-a-1
            app_transformed = (ws / "app-a.qmd").read_text(encoding="utf-8")
            self.assertIn("{#tbl-a-1}", app_transformed)

            self.assertEqual(rendered.appendix_start, 2)

    def test_render_config_preserves_reading_order_with_appendices_and_references(self) -> None:
        entries = ["intro.qmd", "ch01.qmd", "conclusions.qmd", "app-a.qmd", "references.qmd"]
        book = {"title": "Test"}
        config: dict = {"project": {"type": "book"}}
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            resources = {
                "filters/table-layout.lua": workspace / "handbook-render/filters/table-layout.lua",
                "filters/task-checkbox.lua": workspace / "handbook-render/filters/task-checkbox.lua",
                "filters/docx-callouts.lua": workspace / "handbook-render/filters/docx-callouts.lua",
                "filters/front-crossrefs.lua": workspace / "handbook-render/filters/front-crossrefs.lua",
                "typst/callout-breakable.typ": workspace / "handbook-render/typst/callout-breakable.typ",
                "typst/handbook-typst.typ": workspace / "handbook-render/typst/handbook-typst.typ",
                "typst/typst-show.typ": workspace / "handbook-render/typst/typst-show.typ",
                "docx/reference.docx": workspace / "handbook-render/docx/reference.docx",
                "html/handbook.css": workspace / "handbook-render/html/handbook.css",
                "fonts/source-sans3/HandbookSans-Regular.ttf": workspace / "handbook-render/fonts/source-sans3/HandbookSans-Regular.ttf",
                "fonts/source-serif4/HandbookSerif-Regular.ttf": workspace / "handbook-render/fonts/source-serif4/HandbookSerif-Regular.ttf",
                "fonts/jetbrains-mono/JetBrainsMono-Regular.ttf": workspace / "handbook-render/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
            }
            for path in resources.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            rendered = _render_config(
                book,
                config,
                entries,
                resources,
                workspace,
                appendices=["app-a.qmd"],
            )
            self.assertEqual(rendered["book"]["chapters"], ["intro.qmd", "ch01.qmd", "conclusions.qmd"])
            self.assertEqual(rendered["book"]["appendices"], ["app-a.qmd", "references.qmd"])

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_negative_build_mismatched_class_first_figure(self) -> None:
        import subprocess
        from test_build import make_book, build_book, PROFILE
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, chapter=True)
            ch_file = repo / "manuscript/chapters/pilot.qmd"
            content = ch_file.read_text(encoding="utf-8")
            content += "\n![Figure 9.9 — Wrong label](../images/fixture.png){.wide #fig-section-structure}\n"
            ch_file.write_text(content, encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "commit", "-am", "mismatch"], check=True, capture_output=True)
            new_commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).decode().strip()
            with self.assertRaises(BuildError) as ctx:
                build_book(repo, new_commit, root / "dist", profile=PROFILE, mode="chapter")
            self.assertIn("figure caption label '9.9' does not match expected number '1.1'", str(ctx.exception))

    @unittest.skipUnless(BUILD_AVAILABLE and PDFTOTEXT, "Quarto, pdfinfo, and pdftotext are required for the PDF build test")
    def test_pdf_appendix_letter_numbering(self) -> None:
        import subprocess
        from test_build import make_book, build_book, PROFILE
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, chapter=True)
            # Add an appendix with figure and table
            app_path = repo / "manuscript/appendices/app-a.qmd"
            app_path.parent.mkdir(parents=True, exist_ok=True)
            app_path.write_text(
                "# Worked Cases\n\n"
                "| A | B |\n|---|---|\n| 1 | 2 |\n\n: Appendix Table {#tbl-a-1}\n\n"
                "![Appendix Figure](../images/fixture.png){#fig-a-1}\n",
                encoding="utf-8",
            )
            # Update book.yml to list appendix
            (repo / "manuscript/book.yml").write_text(
                "front: []\nchapters:\n  - chapters/pilot.qmd\nback: []\nappendices:\n  - appendices/app-a.qmd\nreferences: []\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "add appendix"], check=True, capture_output=True)
            new_commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).decode().strip()
            output = root / "dist"
            build_book(repo, new_commit, output, profile=PROFILE, mode="chapter")
            pdf_path = output / "book.pdf"
            self.assertTrue(pdf_path.exists())
            pdf_text = subprocess.check_output(["pdftotext", "-layout", str(pdf_path), "-"]).decode()
            self.assertIn("Figure A.1: Appendix Figure", pdf_text)
            self.assertIn("Table A.1: Appendix Table", pdf_text)


if __name__ == "__main__":
    unittest.main()
