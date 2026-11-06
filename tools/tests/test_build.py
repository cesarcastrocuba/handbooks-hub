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


def make_book(root: Path, *, include_quarto: bool = True) -> tuple[Path, str]:
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
    (repo / "manuscript/chapters/pilot.qmd").write_text(PILOT, encoding="utf-8")
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
            result = build_book(repo, commit, output, profile=PROFILE)
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


if __name__ == "__main__":
    unittest.main()
