"""Real publication-build tests.

The primary test performs an actual Quarto HTML/Typst/DOCX render of a small
pilot book in a temporary repository. It is skipped only when Quarto or
``pdfinfo`` is unavailable; the CI build job installs both.

No release, upload or deployment is performed.
"""

from __future__ import annotations

import json
import struct
import zlib
import os
import re
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from html_support import Document
from handbook_toolkit.build import (  # noqa: E402
    BuildError,
    _clean_markdown,
    _markdown_header,
    _markdown_sources,
    _reject_local_paths,
    _render_config,
    build_book,
)
from handbook_toolkit.build_staging import _prepare_render, _rebase_images
from handbook_toolkit.docx_post import _reflow_license_paragraph
from handbook_toolkit.docx_xml import W, fields, text_of
from handbook_toolkit.docx_validation import validate_docx
from handbook_toolkit.publication import verify_publication  # noqa: E402

QUARTO = shutil.which("quarto")
PDFINFO = shutil.which("pdfinfo")
BUILD_AVAILABLE = QUARTO is not None and PDFINFO is not None
PROFILE = support.REPO_ROOT / "profiles/standard/profile.yaml"

PILOT = """\
## 1.1 A Pilot Section

**Definition.** A pilot section is a structural test of the editorial contract.

**Purpose.** It proves the renderer and validator path before a full chapter.

**What it includes.** A heading, required labels, an example and closing callouts.

**Why it is needed.** Without it, build failures appear too late in the publication.

**Example.** An illustrative handbook names its reader and its excluded scope.

| Field | Detail |
| :--- | :--- |
| Reader | A technical reader |
| Promise | A bounded outcome |

: Fixture table caption.

![An original fixture diagram.](../images/fixture.png){#fig-fixture}

```{#lst-fixture .python lst-cap="Fixture listing"}
print("fixture")
```

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Treating a successful render as editorial approval.

| Signal | Verdict |
| :--- | :--- |
| Render succeeds | Not enough |
| Review approves | Enough |
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
Should the pilot include a diagram? Only if the relationship needs one; this fixture does not.
:::

::: {.callout-note .review appearance="simple" icon=false title="Review Checklist"}
- Does the review box use the neutral role?
- Is every checklist item inside the box?
:::
"""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


CHAPTER = """\
# 1. A Build Chapter

::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}
- A structural build is required.
:::

::: {.callout-tip appearance="simple" icon=false title="Key Takeaway"}
Structure and identity are separate gates.
:::

## 1.1 A Content Section

**Definition.** A content section is an ordinary chapter section.

**Purpose.** It carries the argument.

**What it includes.** Labels, an example and closing elements.

**Why it is needed.** Without it, the chapter has no reviewed shape.

**Example.** A labeled example.

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Skipping the section gate.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
How much structure is enough? Enough to review the argument.
:::

## 1.2 Worked Example — Build Identity

An illustrative worked example.

::: {.callout-important appearance="simple" icon=false title="Review Checklist — Build identity"}
- Check the source commit.
- Check every payload.
:::

## 1.3 Further Reading

- A checkable source.
"""

def commit_all(repo: Path, message: str = "fixture update") -> str:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def make_book(root: Path, *, include_quarto: bool = True, chapter: bool = False, version: str = "1.0.0-preview") -> tuple[Path, str]:
    repo = root / "book"
    repo.mkdir()
    image = repo / "manuscript/images/fixture.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress((b"\x00" + b"\x20\x80\x60" * 2) * 2)) + chunk(b"IEND", b""))
    (repo / "book.yaml").write_text(
        """\
schema_version: "1.0"
id: build-fixture
title: Build Fixture
status: draft
profile:
  id: standard
  version: "1.0.0"
toolkit: "0.10.1"
license:
  content: CC-BY-SA-4.0
  code: MIT
manuscript:
  root: manuscript
  reading_order: manuscript/book.yml
publication:
  formats: [html, pdf, docx]
  manifest: publication-manifest.json
catalog:
  slug: build-fixture
  categories: [authoring]
  summary: A build fixture with no external content dependency.
repository:
  url: null
  default_branch: main
""",
        encoding="utf-8",
    )
    (repo / "manuscript/chapters").mkdir(parents=True)
    (repo / "manuscript/book.yml").write_text(
        "front: []\nchapters:\n  - chapters/pilot.qmd\nback: []\nappendices: []\nreferences: []\n",
        encoding="utf-8",
    )
    (repo / "manuscript/chapters/pilot.qmd").write_text(CHAPTER if chapter else PILOT, encoding="utf-8")
    (repo / "publishing").mkdir()
    (repo / "publishing/metadata.yaml").write_text(f"version: '{version}'\n", encoding="utf-8")
    if include_quarto:
        (repo / "publishing/_quarto.yml").write_text(
            """\
project:
  type: book
  output-dir: _output
book:
  title: Build Fixture
  author: Fixture Author
format:
  html: {}
  typst:
    papersize: a4
  docx: {}
""",
            encoding="utf-8",
        )
    (repo / "LICENSE").write_text("fixture content license\n", encoding="utf-8")
    (repo / "LICENSE-CODE").write_text("fixture code license\n", encoding="utf-8")
    (repo / "NOTICE.md").write_text("# Notice\nFixture.\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        "fixture",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


class FirstPageStagingTests(unittest.TestCase):
    """The first page is staged at the project root; its images must still be found."""

    def rebase(self, text: str, directory: str = "manuscript/front-matter") -> str:
        return _rebase_images(text, PurePosixPath(directory))

    def test_relative_images_point_at_the_source_directory(self) -> None:
        self.assertEqual(
            self.rebase("Text ![Alt text](../images/a.svg){#fig-a width=80%} and ![](b.png)."),
            "Text ![Alt text](manuscript/images/a.svg){#fig-a width=80%} and "
            "![](manuscript/front-matter/b.png).",
        )
        self.assertEqual(self.rebase("![A](<../images/a b.svg>)"), "![A](<manuscript/images/a b.svg>)")

    def test_remote_absolute_and_anchor_targets_are_kept(self) -> None:
        for target in ("https://example.org/a.png", "/abs/a.png", "data:image/png;base64,AAAA", "#fig-a"):
            with self.subTest(target=target):
                self.assertEqual(self.rebase(f"![A]({target})"), f"![A]({target})")

    def test_code_is_not_rewritten(self) -> None:
        text = "\n".join(
            [
                "Write `![A](a.png)` for an image.",
                "```markdown",
                "![A](a.png)",
                "```",
                "~~~~",
                "![B](b.png)",
                "~~~",
                "![C](c.png)",
                "~~~~",
                "![D](d.png)",
            ]
        )
        expected = text.replace("![D](d.png)", "![D](manuscript/front-matter/d.png)")
        self.assertEqual(self.rebase(text), expected)

    def test_a_first_page_at_the_root_is_unchanged(self) -> None:
        text = "![A](images/a.png)"
        self.assertEqual(self.rebase(text, "."), text)

    def test_only_the_staged_index_is_rebased(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            for name in ("manuscript/front-matter/intro.qmd", "manuscript/chapters/one.qmd"):
                path = workspace / name
                path.parent.mkdir(parents=True)
                path.write_text("# Page\n\n![A](../images/a.png)\n", encoding="utf-8")
            rendered = _prepare_render(
                workspace, ["manuscript/front-matter/intro.qmd", "manuscript/chapters/one.qmd"]
            )
            self.assertEqual(rendered, ["index.qmd", "manuscript/chapters/one.qmd"])
            self.assertIn("![A](manuscript/images/a.png)", (workspace / "index.qmd").read_text())
            for name in ("manuscript/front-matter/intro.qmd", "manuscript/chapters/one.qmd"):
                self.assertIn("![A](../images/a.png)", (workspace / name).read_text())
            self.assertEqual(
                sorted(path.name for path in workspace.iterdir()), ["index.qmd", "manuscript"]
            )


class RenderConfigTests(unittest.TestCase):
    def test_staged_resources_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            resources = {
                "filters/table-layout.lua": workspace / ".handbook-render/filters/table-layout.lua",
                "filters/task-checkbox.lua": workspace / ".handbook-render/filters/task-checkbox.lua",
                "filters/docx-callouts.lua": workspace / ".handbook-render/filters/docx-callouts.lua",
                "typst/callout-breakable.typ": workspace / ".handbook-render/typst/callout-breakable.typ",
                "typst/handbook-typst.typ": workspace / ".handbook-render/typst/handbook-typst.typ",
                "typst/typst-show.typ": workspace / ".handbook-render/typst/typst-show.typ",
                "docx/reference.docx": workspace / ".handbook-render/docx/reference.docx",
                "html/handbook.css": workspace / ".handbook-render/html/handbook.css",
                "fonts/source-sans3/HandbookSans-Regular.ttf": workspace / ".handbook-render/fonts/source-sans3/HandbookSans-Regular.ttf",
                "fonts/source-serif4/HandbookSerif-Regular.ttf": workspace / ".handbook-render/fonts/source-serif4/HandbookSerif-Regular.ttf",
                "fonts/jetbrains-mono/JetBrainsMono-Regular.ttf": workspace / ".handbook-render/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
            }
            for path in resources.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            config = _render_config(
                {"title": "Fixture"},
                {"project": {"type": "book"}, "book": {}, "format": {}},
                ["index.qmd"],
                resources,
                workspace,
            )
            self.assertEqual(
                [entry["path"] for entry in config["filters"]],
                [
                    ".handbook-render/filters/table-layout.lua",
                    ".handbook-render/filters/task-checkbox.lua",
                    ".handbook-render/filters/docx-callouts.lua",
                ],
            )
            self.assertEqual(
                config["format"]["typst"]["mainfont"],
                "Handbook Sans",
            )
            self.assertEqual(
                config["format"]["typst"]["monofont"],
                "JetBrains Mono",
            )
            self.assertEqual(
                config["format"]["typst"]["font-paths"],
                [
                    ".handbook-render/fonts/source-sans3",
                    ".handbook-render/fonts/source-serif4",
                    ".handbook-render/fonts/jetbrains-mono",
                ],
            )
            self.assertEqual(
                config["format"]["typst"]["include-before-body"],
                ".handbook-render/typst/handbook-typst.typ",
            )
            self.assertEqual(
                config["format"]["typst"]["template-partials"],
                [".handbook-render/typst/typst-show.typ"],
            )
            self.assertEqual(
                config["format"]["docx"]["reference-doc"],
                ".handbook-render/docx/reference.docx",
            )
            self.assertEqual(
                config["format"]["html"]["css"],
                [
                    ".handbook-render/html/design-tokens.css",
                    ".handbook-render/html/handbook.css",
                ],
            )


class MarkdownEditionTests(unittest.TestCase):
    """The Markdown edition is assembled from the reading order without Quarto."""

    def test_sources_follow_reading_order_without_front_matter(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "manuscript/front").mkdir(parents=True)
            (workspace / "manuscript/chapters").mkdir(parents=True)
            (workspace / "manuscript/front/title.qmd").write_text(
                "---\ntitle: Book\n---\n\n# Document Control\n\nText.\n", encoding="utf-8"
            )
            (workspace / "manuscript/chapters/ch01.qmd").write_text(
                "---\ntitle: 1. Chapter\nprofile: standard\n---\n\n"
                "# 1. Chapter\n\n{{< include _parts/section.qmd >}}\n",
                encoding="utf-8",
            )
            source = _markdown_sources(
                workspace, ["manuscript/front/title.qmd", "manuscript/chapters/ch01.qmd"]
            )
            self.assertTrue(source.startswith("# Document Control"))
            self.assertIn("# 1. Chapter", source)
            self.assertNotIn("profile: standard", source)
            self.assertIn("{{< include manuscript/chapters/_parts/section.qmd >}}", source)

    def test_clean_markdown_keeps_text_and_drops_rendered_html(self):
        rendered = (
            'See <a href="#sec-x" class="quarto-xref">Section 2</a>.\n\n'
            '<div id="fig-a">\n\n![](images/a.png)\n\nFigure 1: A caption\n\n</div>\n\n'
            '<div id="tbl-b">\n\nTable 1: A table\n\n| A | B |\n| :- | :- |\n| 1 | 2 |\n\n</div>\n\n'
            "![](images/b.png)\n"
        )
        cleaned = _clean_markdown(rendered)
        self.assertIn("See Section 2.", cleaned)
        self.assertIn("*Figure 1: A caption*", cleaned)
        self.assertIn("| A | B |", cleaned)
        self.assertNotIn("<div", cleaned)
        self.assertNotIn("![", cleaned)
        self.assertIn("*(figure image not included in the Markdown edition)*", cleaned)
        self.assertFalse(cleaned.startswith("\n"))

    def test_local_path_guard_rejects_this_build_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / ".handbook-build-fixture" / "work"
            _reject_local_paths("The demo writes to /tmp/demo and file:///srv/book.", [workspace])
            with self.assertRaises(BuildError):
                _reject_local_paths(f"See {workspace}/manuscript/ch01.qmd.", [workspace])
            with self.assertRaises(BuildError):
                _reject_local_paths(f"Home is {Path.home()}.", [Path.home()])

    def test_local_path_guard_sees_markdown_escaped_paths(self):
        for raw, escaped in (
            ("/tmp/leak_guard/work", "/tmp/leak\\_guard/work"),
            ("/tmp/leak*guard/work", "/tmp/leak\\*guard/work"),
            ("/tmp/leak[1]/work", "/tmp/leak\\[1\\]/work"),
        ):
            with self.subTest(path=raw):
                needle = Path(raw)
                with self.assertRaises(BuildError):
                    _reject_local_paths(f"See {raw}/manuscript.", [needle])
                with self.assertRaises(BuildError):
                    _reject_local_paths(f"See {escaped}/manuscript.", [needle])
        _reject_local_paths(
            "Unrelated content: /tmp/demo, /home/reader/project and file:///srv/book.",
            [Path(raw)],
        )

    def test_local_path_guard_ignores_short_system_directories(self):
        for value in ("/tmp", "/home", "/var", "/opt"):
            with self.subTest(path=value):
                _reject_local_paths("The demo writes to /tmp/demo.", [Path(value)])
        self.assertEqual(len(Path("/tmp").parts), 2)
        self.assertEqual(len(Path("/home").parts), 2)

    def test_header_carries_document_control_fields_and_commit(self):
        fields = [("Title", "Fixture"), ("Version", "1.0.0"),
                  ("Content license", "CC BY-SA 4.0")]
        header = _markdown_header({"title": "Fixture"}, fields, "a" * 40)
        self.assertTrue(header.startswith("# Fixture\n\n| Field | Value |\n"))
        self.assertIn("| Version | 1.0.0 |", header)
        self.assertIn("| Commit | " + "a" * 40 + " |", header)
        self.assertIn("| Content license | CC BY-SA 4.0 |", header)


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % WORD_NS


class DocxHelperTests(unittest.TestCase):
    def test_license_paragraph_reflows_hard_lines_and_keeps_blank_lines(self) -> None:
        paragraph = ET.Element(f"{W}p")
        for text in ("The MIT License (MIT)", "Copyright (c) The Authors", "", "Permission is granted"):
            run = ET.SubElement(paragraph, f"{W}r")
            ET.SubElement(run, f"{W}t").text = text
            ET.SubElement(run, f"{W}br")
        _reflow_license_paragraph(paragraph, W)
        text = "".join(node.text or "" for node in paragraph.iter(f"{W}t"))
        self.assertIn("The MIT License (MIT) Copyright (c) The Authors", text)
        self.assertNotIn("(MIT)Copyright", text)
        self.assertIn("Permission is granted", text)
        self.assertEqual(len(list(paragraph.iter(f"{W}br"))), 2)


@unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
class BuildTests(unittest.TestCase):
    def test_builds_verified_seven_file_directory_and_source_comment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            output = root / "dist"
            result = build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertEqual(result.commit, commit)
            self.assertFalse(output.is_symlink())
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {
                    "book-html.zip",
                    "book.pdf",
                    "book.docx",
                    "book.md",
                    "book-source.zip",
                    "publication-manifest.json",
                    "SHA256SUMS.txt",
                },
            )
            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertEqual(manifest["book"]["commit"], commit)
            self.assertEqual(manifest["schema_version"], "1.1")
            self.assertIn("--mode section-pilot", manifest["build"]["command"])
            self.assertIn("zlib", manifest["build"]["tool_versions"])
            self.assertIn("typst", manifest["build"]["tool_versions"])
            with zipfile.ZipFile(output / "book-source.zip") as archive:
                self.assertEqual(archive.comment.decode("ascii"), commit)
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                site = archive.read("manuscript/chapters/pilot.html").decode("utf-8")
            with zipfile.ZipFile(output / "book.docx") as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
                settings_xml = archive.read("word/settings.xml").decode("utf-8")
            document = ET.fromstring(document_xml)
            settings = ET.fromstring(settings_xml)
            self.assertIsNotNone(document.find(W + "background"))
            self.assertIsNotNone(settings.find(W + "updateFields"))
            self.assertIsNotNone(settings.find(W + "displayBackgroundShape"))
            with zipfile.ZipFile(output / "book.docx") as archive:
                validate_docx(archive)
                styles = ET.fromstring(archive.read("word/styles.xml"))
            ids = [style.get(W + "styleId") for style in styles.findall(W + "style")]
            self.assertEqual(len(ids), len(set(ids)))
            instructions = [item.instruction for item in fields(document)]
            self.assertTrue(any(value.startswith("TOC ") and "\\o" in value for value in instructions))
            for letter in ("T", "F", "L"):
                self.assertTrue(any(value == f"TOC \\h \\z \\f {letter}" for value in instructions))
            self.assertTrue(any(value.startswith("TC ") for value in instructions))
            self.assertFalse(any(value.startswith("PAGEREF") for value in instructions))
            self.assertTrue(document.findall(".//" + W + "tblHeader"))
            self.assertFalse(document.findall(".//" + W + "trPr/" + W + "shd"))
            callout = styles.find(f"{W}style[@{W}styleId='CalloutReviewTitle']")
            self.assertIsNotNone(callout.find(W + "rPr/" + W + "b"))
            self.assertTrue(document.findall(".//" + W + "cantSplit"))
            self.assertFalse(document.findall(".//" + W + "pBdr"))
            self.assertIn("Table&nbsp;1.1", site)
            self.assertIn('class="review callout', site)
            root = ET.fromstring(document_xml)
            for box in root.iter(f"{W}tbl"):
                style = box.find(f"./{W}tblPr/{W}tblStyle")
                if style is None or style.get(f"{W}val") != "CalloutBox":
                    continue
                for nested in box.iter(f"{W}tbl"):
                    if nested is box:
                        continue
                    nested_style = nested.find(f"./{W}tblPr/{W}tblStyle")
                    self.assertEqual(nested_style.get(f"{W}val"), "TablePlain")
                    for row in nested.findall(f"{W}tr"):
                        properties = row.find(f"./{W}trPr")
                        if properties is not None:
                            self.assertIsNone(properties.find(f"./{W}shd"))
            for cell in root.iter(f"{W}tc"):
                for paragraph in cell.findall(f"./{W}p"):
                    properties = paragraph.findall(f"./{W}pPr")
                    self.assertLessEqual(len(properties), 1)
                    if properties:
                        self.assertLessEqual(
                            len(properties[0].findall(f"./{W}jc")), 1
                        )
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                tables_page = archive.read("tables.html").decode("utf-8")
                index_page = archive.read("index.html").decode("utf-8")
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                for name, label in (("figures.html", "fig-fixture"), ("listings.html", "lst-fixture")):
                    page = archive.read(name).decode()
                    self.assertIn('manuscript/chapters/pilot.html#' + label, page)
                    self.assertIn('quarto-sidebar', page)
                    self.assertIn('quarto-xref', page)
            tree = Document(tables_page).root
            links = tree.find("a")
            target_links = [link for link in links if "quarto-xref" in (link.attrs.get("class") or "").split()]
            self.assertEqual(len(target_links), 1)
            self.assertEqual(target_links[0].text().replace(chr(160), " "), "Table 1.1")
            self.assertTrue(target_links[0].attrs["href"].startswith("manuscript/chapters/pilot.html#tbl-"))
            self.assertEqual(tree.find("main")[0].find("h1")[0].text().strip(), "List of Tables")
            self.assertIn("List of Tables", tables_page)
            self.assertIn('href="manuscript/chapters/pilot.html#tbl-', tables_page)
            self.assertIn('menu-text">List of Tables</span>', tables_page)
            self.assertIn('menu-text">List of Tables</span>', index_page)
            self.assertIn('class="sidebar-item-text sidebar-link"', index_page)
            cover = Document(index_page).root
            self.assertEqual(len([a for a in cover.find("a") if a.text().strip() == "Start reading"]),1)
            self.assertTrue(cover.find("a", id="quarto-skip-link"))
            for script in cover.find("script"):
                source = script.attrs.get("src")
                if source:
                    self.assertTrue(source.lstrip("./").startswith("site_libs/"), source)
                elif script.attrs.get("id"):
                    self.assertIn(script.attrs["id"], {"quarto-search-options", "quarto-html-before-body", "quarto-html-after-body"})
                else:
                    self.assertTrue(script.text().strip().startswith("window.quartoScrollableRegionsLabels ="))
            footer = cover.find("footer")[0]
            self.assertIn("1.0.0-preview", footer.text())
            self.assertIn("A Pilot Section", site)
            markdown = (output / "book.md").read_text(encoding="utf-8")
            self.assertTrue(markdown.startswith("# Build Fixture\n"))
            self.assertIn(f"| Commit | {commit} |", markdown)
            self.assertIn("| Version | 1.0.0-preview |", markdown)
            self.assertIn("A Pilot Section", markdown)
            self.assertNotIn("<a href=", markdown)
            self.assertTrue(verify_publication(output).ok)
            self.assertIn("**Definition.**", (repo / "manuscript/chapters/pilot.qmd").read_text())

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdftotext"),
                         "LibreOffice and pdftotext are required for the smoke conversion")
    def test_libreoffice_displays_cached_contents_tables_and_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            output = root / "dist"
            build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            converted = root / "converted"
            converted.mkdir()
            subprocess.run([
                shutil.which("soffice"),
                "-env:UserInstallation=" + (root / "lo-profile").as_uri(),
                "--headless", "--convert-to", "pdf", "--outdir", str(converted),
                str(output / "book.docx")], check=True, capture_output=True, text=True, timeout=90)
            text = subprocess.check_output(
                ["pdftotext", "-layout", str(converted / "book.pdf"), "-"],
                text=True, timeout=30)
            pages = [" ".join(page.split()) for page in text.split("\f")]
            for title, entry in (("Contents", "A Pilot Section"),
                                 ("List of Tables", "Fixture table caption"),
                                 ("List of Figures", "An original fixture diagram")):
                matching = [page for page in pages if page.startswith(title)]
                self.assertEqual(len(matching), 1, pages)
                self.assertIn(entry, matching[0])
            for page in text.split("\f"):
                lines = [line.strip() for line in page.splitlines() if line.strip()]
                if lines and lines[0] in {"Contents", "List of Tables", "List of Figures"}:
                    for line in lines[1:]:
                        self.assertIsNone(
                            re.search(r"(?:[.·]\s*){2,}$|…\s*$", line),
                            f"Cached entry has a dangling leader without a page number: {line}",
                        )
            pdf = subprocess.check_output(["pdftotext", str(output / "book.pdf"), "-"], text=True)
            self.assertIn("List of Figures", pdf)
            self.assertIn("An original fixture diagram", pdf)
            with zipfile.ZipFile(output / "book.docx") as archive:
                self.assertTrue(any(name.startswith("word/media/") for name in archive.namelist()))
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                self.assertTrue(any(name.endswith("/fixture.png") for name in archive.namelist()))

    def test_local_path_in_the_markdown_fails_the_build(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            # The escaped case proves the guard under a real Quarto render: the gfm writer
            # escapes the underscore, so a raw comparison alone would miss the leak.
            for name, escaped in (("plain", False), ("under_score", True)):
                with self.subTest(directory=name):
                    root = base / name
                    root.mkdir()
                    repo, commit = make_book(root)
                    self.assertEqual("_" in root.name, escaped)
                    if escaped:
                        self.assertIn("_", str(repo))
                    pilot = repo / "manuscript/chapters/pilot.qmd"
                    pilot.write_text(
                        pilot.read_text(encoding="utf-8").replace(
                            "**Example.** An illustrative handbook names its reader and its excluded scope.",
                            f"**Example.** An illustrative handbook lives at {repo}/manuscript.",
                        ),
                        encoding="utf-8",
                    )
                    self.assertIn(f"{repo}/manuscript", pilot.read_text(encoding="utf-8"))
                    commit = commit_all(repo, f"local path in the manuscript ({name})")
                    output = root / "dist"
                    with self.assertRaises(
                        BuildError, msg=f"a local path must fail the build: {repo}"
                    ):
                        build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
                    self.assertFalse(output.exists())

    def test_existing_output_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            output = root / "dist"
            output.mkdir()
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE)
            self.assertEqual(list(output.iterdir()), [])

    def test_dirty_source_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE)
            self.assertFalse(output.exists())

    def test_failed_build_leaves_no_final_or_private_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, include_quarto=False)
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE)
            self.assertFalse(output.exists())
            self.assertEqual(
                [path for path in root.iterdir() if path.name.startswith(".handbook-build-")],
                [],
            )


    def test_default_chapter_mode_builds_a_full_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, chapter=True, version="1.0.0")
            output = root / "dist"
            result = build_book(repo, commit, output)
            self.assertTrue(result.output.is_dir())
            self.assertTrue(verify_publication(output).ok)
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                self.assertFalse({"tables.html", "figures.html", "listings.html"} & set(archive.namelist()))


    def test_figures_outside_the_first_page_directory_build_in_every_edition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _ = make_book(root)
            front = repo / "manuscript/front-matter"
            front.mkdir()
            (front / "introduction.qmd").write_text(
                "# Introduction {.unnumbered}\n\nAn opening page.\n\n"
                "![A figure on the first page.](../images/fixture.png){#fig-first}\n",
                encoding="utf-8",
            )
            (repo / "manuscript/book.yml").write_text(
                "front:\n  - front-matter/introduction.qmd\nchapters:\n  - chapters/pilot.qmd\n"
                "back: []\nappendices: []\nreferences: []\n",
                encoding="utf-8",
            )
            commit = commit_all(repo)
            output = root / "dist"
            build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")

            pdf = subprocess.check_output(["pdftotext", str(output / "book.pdf"), "-"], text=True)
            for caption in ("A figure on the first page.", "An original fixture diagram."):
                self.assertIn(caption, pdf)
            with zipfile.ZipFile(output / "book.docx") as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
            self.assertEqual(len(document.findall(".//" + W + "drawing")), 2)
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                names = set(archive.namelist())
                for page in ("manuscript/front-matter/introduction.html", "manuscript/chapters/pilot.html"):
                    sources = [image.attrs["src"] for image in Document(archive.read(page).decode()).root.find("img")]
                    self.assertEqual(len(sources), 1, page)
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(page), sources[0]))
                    self.assertIn(resolved, names)

    def test_canonical_root_index_survives_generated_web_cover(self) -> None:
        import yaml
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            repo,_=make_book(root)
            source=repo/"manuscript/chapters/pilot.qmd"
            (repo/"index.qmd").write_text(source.read_text().replace("../images/fixture.png","manuscript/images/fixture.png") + "\n[Back to this section](index.qmd#fig-fixture)\n")
            source.unlink()
            book=yaml.safe_load((repo/"book.yaml").read_text())
            book["manuscript"]["root"]="."
            (repo/"book.yaml").write_text(yaml.safe_dump(book))
            (repo/"manuscript/book.yml").write_text("chapters: [index.qmd]\n")
            commit=commit_all(repo)
            build_book(repo,commit,root/"dist",profile=PROFILE,mode="section-pilot")
            with zipfile.ZipFile(root/"dist/book-html.zip") as archive:
                chapter=Document(archive.read("handbook-source-index.html").decode()).root
                self.assertIn("A Pilot Section",chapter.text())
                self.assertTrue(any(link.attrs.get("href","").endswith("handbook-source-index.html#fig-fixture") for link in chapter.find("a")))
                cover=Document(archive.read("index.html").decode()).root
                self.assertTrue(any(link.attrs.get("href","").endswith("handbook-source-index.html") for link in cover.find("a") if link.text()=="Start reading"))

    def test_toolkit_pin_mismatch_is_refused_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            book = repo / "book.yaml"
            book.write_text(
                book.read_text(encoding="utf-8").replace('toolkit: "0.10.1"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            commit = commit_all(repo, "mismatched toolkit pin")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertFalse(output.exists())

    def test_section_pilot_requires_a_prerelease_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, version="1.0.0")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertFalse(output.exists())

    def test_chapter_mode_validates_appendices(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root, chapter=True, version="1.0.0")
            appendix = repo / "manuscript/appendices/appendix-a.qmd"
            appendix.parent.mkdir(exist_ok=True)
            appendix.write_text("## Appendix A\n\nNo chapter structure.\n", encoding="utf-8")
            reading = repo / "manuscript/book.yml"
            reading.write_text(
                reading.read_text(encoding="utf-8").replace(
                    "appendices: []", "appendices:\n  - appendices/appendix-a.qmd"
                ),
                encoding="utf-8",
            )
            commit = commit_all(repo, "invalid appendix")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE)
            self.assertFalse(output.exists())

    def test_invalid_reference_is_refused_before_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            pilot = repo / "manuscript/chapters/pilot.qmd"
            pilot.write_text(
                pilot.read_text(encoding="utf-8").replace(
                    "**Example.**",
                    "See @tbl-missing.\n\n**Example.**",
                ),
                encoding="utf-8",
            )
            commit = commit_all(repo, "invalid reference")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertFalse(output.exists())

    def test_preview_mode_is_explicit_and_non_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            book = repo / "book.yaml"
            book.write_text(
                book.read_text(encoding="utf-8").replace('toolkit: "0.10.1"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            commit = commit_all(repo, "preview toolkit pin")
            output = root / "dist"
            result = build_book(
                repo, commit, output, profile=PROFILE, mode="section-pilot", preview=True
            )
            self.assertTrue(result.output.is_dir())
            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertIn("--preview", manifest["build"]["command"])

    def test_invalid_manuscript_structure_is_refused_before_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            pilot = repo / "manuscript/chapters/pilot.qmd"
            pilot.write_text(
                pilot.read_text(encoding="utf-8").replace(
                    "**Purpose.** It proves the renderer and validator path before a full chapter.\n\n",
                    "",
                ),
                encoding="utf-8",
            )
            commit = commit_all(repo, "invalid pilot structure")
            output = root / "dist"
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertFalse(output.exists())
            self.assertEqual(
                [path for path in root.iterdir() if path.name.startswith(".handbook-build-")],
                [],
            )

    def test_dangling_output_symlink_is_refused_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            output = root / "dist"
            target = root / "missing-target"
            output.symlink_to(target)
            with self.assertRaises(BuildError):
                build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertFalse(target.exists())
            self.assertTrue(output.is_symlink())

    def test_build_reads_book_and_reading_order_from_the_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            book = repo / "book.yaml"
            book.write_text(
                book.read_text(encoding="utf-8").replace('toolkit: "0.10.1"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            _git(repo, "update-index", "--assume-unchanged", "book.yaml")
            output = root / "dist"
            result = build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertTrue(result.output.is_dir())


if __name__ == "__main__":
    unittest.main()
