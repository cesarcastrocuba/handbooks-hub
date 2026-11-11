"""Real publication-build tests.

The primary test performs an actual Quarto HTML/Typst/DOCX render of a small
pilot book in a temporary repository. It is skipped only when Quarto or
``pdfinfo`` is unavailable; the CI build job installs both.

No release, upload or deployment is performed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.build import (  # noqa: E402
    BuildError,
    _clean_markdown,
    _markdown_header,
    _markdown_sources,
    _reject_local_paths,
    _render_config,
    build_book,
)
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

::: {.callout-warning appearance="simple" icon=false title="Common Pitfall"}
Treating a successful render as editorial approval.
:::

::: {.callout-important appearance="simple" icon=false title="Decision & Trade-off"}
Should the pilot include a diagram? Only if the relationship needs one; this fixture does not.
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
    (repo / "book.yaml").write_text(
        """\
schema_version: "1.0"
id: build-fixture
title: Build Fixture
status: draft
profile:
  id: standard
  version: "1.0.0"
toolkit: "0.6.0"
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


class RenderConfigTests(unittest.TestCase):
    def test_staged_resources_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            resources = {
                "filters/table-layout.lua": workspace / ".handbook-render/filters/table-layout.lua",
                "filters/task-checkbox.lua": workspace / ".handbook-render/filters/task-checkbox.lua",
                "typst/callout-breakable.typ": workspace / ".handbook-render/typst/callout-breakable.typ",
                "typst/handbook-typst.typ": workspace / ".handbook-render/typst/handbook-typst.typ",
                "typst/typst-show.typ": workspace / ".handbook-render/typst/typst-show.typ",
                "docx/reference.docx": workspace / ".handbook-render/docx/reference.docx",
                "html/handbook.css": workspace / ".handbook-render/html/handbook.css",
                "fonts/selawik/selawk.ttf": workspace / ".handbook-render/fonts/selawik/selawk.ttf",
                "fonts/jetbrains-mono/JetBrainsMono-Regular.ttf": workspace / ".handbook-render/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
                "fonts/liberation-sans/LiberationSans-Regular.ttf": workspace / ".handbook-render/fonts/liberation-sans/LiberationSans-Regular.ttf",
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
                [".handbook-render/filters/table-layout.lua", ".handbook-render/filters/task-checkbox.lua"],
            )
            self.assertEqual(
                config["format"]["typst"]["mainfont"],
                "Selawik",
            )
            self.assertEqual(
                config["format"]["typst"]["monofont"],
                "JetBrains Mono",
            )
            self.assertEqual(
                config["format"]["typst"]["font-paths"],
                [
                    ".handbook-render/fonts/selawik",
                    ".handbook-render/fonts/jetbrains-mono",
                    ".handbook-render/fonts/liberation-sans",
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
                [".handbook-render/html/handbook.css"],
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
                site = archive.read("index.html").decode("utf-8")
            self.assertIn("Table 1.1 —", site)
            self.assertIn("A Pilot Section", site)
            markdown = (output / "book.md").read_text(encoding="utf-8")
            self.assertTrue(markdown.startswith("# Build Fixture\n"))
            self.assertIn(f"| Commit | {commit} |", markdown)
            self.assertIn("| Version | 1.0.0-preview |", markdown)
            self.assertIn("A Pilot Section", markdown)
            self.assertNotIn("<a href=", markdown)
            self.assertTrue(verify_publication(output).ok)
            self.assertIn("**Definition.**", (repo / "manuscript/chapters/pilot.qmd").read_text())

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

    def test_toolkit_pin_mismatch_is_refused_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            book = repo / "book.yaml"
            book.write_text(
                book.read_text(encoding="utf-8").replace('toolkit: "0.6.0"', 'toolkit: "0.1.0"'),
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
                book.read_text(encoding="utf-8").replace('toolkit: "0.6.0"', 'toolkit: "0.1.0"'),
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
                book.read_text(encoding="utf-8").replace('toolkit: "0.6.0"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            _git(repo, "update-index", "--assume-unchanged", "book.yaml")
            output = root / "dist"
            result = build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertTrue(result.output.is_dir())


if __name__ == "__main__":
    unittest.main()
