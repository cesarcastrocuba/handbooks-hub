"""Template 1.0.0 copy, check and real build regression.

The fast test copies the template outside the hub, replaces its identifiers, installs
nothing from the hub checkout and runs the template's own ``make check``. The build test
additionally runs a real seven-file build when Quarto and ``pdfinfo`` are available.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

TEMPLATE = support.REPO_ROOT / "template/book"
QUARTO = shutil.which("quarto")
PDFINFO = shutil.which("pdfinfo")
PDFTOTEXT = shutil.which("pdftotext")
BUILD_AVAILABLE = QUARTO is not None and PDFINFO is not None

PAYLOADS = {
    "book-html.zip",
    "book.pdf",
    "book.docx",
    "book.md",
    "book-source.zip",
    "publication-manifest.json",
    "SHA256SUMS.txt",
}

REPLACEMENTS = {
    "id: template-book": "id: copied-book",
    "title: Handbook template": "title: Copied Handbook",
    "slug: template-book": "slug: copied-book",
    "summary: Replace this summary before the book is listed in the hub catalog.":
        "summary: A copied template used to prove the book boundary.",
}


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


def _environment() -> dict[str, str]:
    return dict(
        os.environ,
        PYTHONPATH=str(support.SRC),
        TOOLKIT=f"{sys.executable} -m handbook_toolkit",
    )


def _copy_template(root: Path) -> Path:
    book = root / "book"
    shutil.copytree(TEMPLATE, book)
    descriptor = book / "book.yaml"
    text = descriptor.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS.items():
        if old not in text:
            raise AssertionError(f"template descriptor is missing {old!r}")
        text = text.replace(old, new)
    descriptor.write_text(text, encoding="utf-8")
    _git(book, "init", "-q", "-b", "main")
    _git(book, "add", "-A")
    _git(
        book,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        "template copy",
    )
    return book


def _run(command: list[str], book: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=book,
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
    )


class TemplateTests(unittest.TestCase):
    def test_copied_template_passes_its_own_fast_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp))
            self.assertFalse((book / "tools").exists())
            self.assertFalse((book / "schemas").exists())

            result = _run(["make", "check"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("validate-book", result.stdout + result.stderr)
            self.assertIn("OK", result.stdout + result.stderr)

    def test_template_pins_are_exact_and_current(self) -> None:
        descriptor = (TEMPLATE / "book.yaml").read_text(encoding="utf-8")
        self.assertIn('toolkit: "0.6.0"', descriptor)
        self.assertIn('version: "1.0.0"', descriptor)
        for name in ("LICENSE", "LICENSE-CODE", "NOTICE.md", "Makefile", "publishing/_quarto.yml"):
            self.assertTrue((TEMPLATE / name).is_file(), name)

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_copied_template_builds_seven_verified_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book = _copy_template(root)
            output = root / "dist"

            result = _run(["make", "build", f"OUTPUT={output}"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual({path.name for path in output.iterdir()}, PAYLOADS)

            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertEqual(manifest["book"]["commit"], _git(book, "rev-parse", "HEAD"))
            self.assertEqual(manifest["book"]["version"], "0.1.0-preview")
            self.assertEqual(manifest["schema_version"], "1.1")
            self.assertEqual(
                {entry["role"] for entry in manifest["artifacts"]},
                {"html", "pdf", "docx", "markdown", "source"},
            )
            markdown = (output / "book.md").read_text(encoding="utf-8")
            self.assertIn("| Version | 0.1.0-preview |", markdown)
            self.assertIn(f"| Commit | {_git(book, 'rev-parse', 'HEAD')} |", markdown)
            self.assertIn("Example Chapter", markdown)

            if PDFTOTEXT is not None:
                text = subprocess.check_output(
                    [PDFTOTEXT, str(output / "book.pdf"), "-"], text=True
                )
                self.assertIn("Example Chapter", text)


if __name__ == "__main__":
    unittest.main()
