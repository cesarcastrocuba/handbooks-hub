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
from handbook_toolkit.build import BuildError, build_book  # noqa: E402
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


def make_book(root: Path, *, include_quarto: bool = True, chapter: bool = False) -> tuple[Path, str]:
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
  version: "0.2.0"
toolkit: "0.3.0"
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
    (repo / "publishing/metadata.yaml").write_text("version: '1.0.0'\n", encoding="utf-8")
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


class BuildTests(unittest.TestCase):
    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_builds_verified_six_file_directory_and_source_comment(self) -> None:
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
                    "book-source.zip",
                    "publication-manifest.json",
                    "SHA256SUMS.txt",
                },
            )
            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertEqual(manifest["book"]["commit"], commit)
            self.assertIn("zlib", manifest["build"]["tool_versions"])
            self.assertIn("typst", manifest["build"]["tool_versions"])
            with zipfile.ZipFile(output / "book-source.zip") as archive:
                self.assertEqual(archive.comment.decode("ascii"), commit)
            self.assertTrue(verify_publication(output).ok)

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
            repo, commit = make_book(root, chapter=True)
            output = root / "dist"
            result = build_book(repo, commit, output, profile=PROFILE)
            self.assertTrue(result.output.is_dir())
            self.assertTrue(verify_publication(output).ok)

    def test_toolkit_pin_mismatch_is_refused_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, commit = make_book(root)
            book = repo / "book.yaml"
            book.write_text(
                book.read_text(encoding="utf-8").replace('toolkit: "0.3.0"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            commit = commit_all(repo, "mismatched toolkit pin")
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
                book.read_text(encoding="utf-8").replace('toolkit: "0.3.0"', 'toolkit: "0.1.0"'),
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
                book.read_text(encoding="utf-8").replace('toolkit: "0.3.0"', 'toolkit: "0.1.0"'),
                encoding="utf-8",
            )
            _git(repo, "update-index", "--assume-unchanged", "book.yaml")
            output = root / "dist"
            result = build_book(repo, commit, output, profile=PROFILE, mode="section-pilot")
            self.assertTrue(result.output.is_dir())


if __name__ == "__main__":
    unittest.main()
