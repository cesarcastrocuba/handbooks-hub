"""CLI smoke and exit-code tests."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.cli import main  # noqa: E402


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_version(self) -> None:
        code, stdout, _ = self.run_cli("version")
        self.assertEqual(code, 0)
        self.assertIn("handbook-toolkit 0.9.1", stdout)

    def test_verify_fast(self) -> None:
        code, stdout, stderr = self.run_cli("--root", str(support.REPO_ROOT), "verify")
        self.assertEqual(code, 0, stderr)
        self.assertIn("VERIFY:", stdout)
        self.assertIn("0 problem(s)", stdout)

    def test_verify_full(self) -> None:
        code, stdout, stderr = self.run_cli("--root", str(support.REPO_ROOT), "verify", "--full")
        self.assertEqual(code, 0, stderr)
        self.assertIn("VERIFY (full):", stdout)

    def test_validate_book_default(self) -> None:
        code, stdout, stderr = self.run_cli(
            "--root", str(support.REPO_ROOT / "template/book"), "validate-book", "--full"
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn(": OK", stdout)

    def test_schema_directory_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            schemas = Path(temp) / "schemas"
            shutil.copytree(support.SCHEMAS, schemas)
            code, stdout, stderr = self.run_cli(
                "--root",
                str(support.REPO_ROOT),
                "--schemas",
                str(schemas),
                "validate-book",
                "template/book/book.yaml",
                "--full",
            )
            self.assertEqual(code, 0, stderr)
            self.assertIn(": OK", stdout)

    def test_invalid_catalog_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = support.write_json(
                Path(temp) / "catalog.json",
                {"schema_version": "1.0", "books": [{"id": "bad"}]},
            )
            code, stdout, stderr = self.run_cli(
                "--root", str(support.REPO_ROOT), "validate-catalog", str(path)
            )
            self.assertEqual(code, 1)
            self.assertIn("problem(s)", stdout)
            self.assertTrue(stderr)

    def test_missing_document_returns_one(self) -> None:
        code, _, stderr = self.run_cli(
            "--root", str(support.REPO_ROOT), "validate-profile", "does-not-exist.yaml"
        )
        self.assertEqual(code, 1)
        self.assertIn("cannot read", stderr)

    def test_validate_manuscript_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pilot.qmd"
            path.write_text(
                "## 2.2 A Pilot\n\n"
                "**Definition.** A thing.\n\n"
                "**Purpose.** A decision.\n\n"
                "**What it includes.** Fields.\n\n"
                "**Why it is needed.** Evidence.\n\n"
                "**Example.** A labeled case.\n\n"
                '::: {.callout-warning title="Common Pitfall"}\nA mistake.\n:::\n\n'
                '::: {.callout-important title="Decision & Trade-off"}\nA choice.\n:::\n',
                encoding="utf-8",
            )
            code, stdout, stderr = self.run_cli(
                "--root",
                temp,
                "validate-manuscript",
                "pilot.qmd",
                "--mode",
                "section-pilot",
                "--profile",
                str(support.REPO_ROOT / "profiles/standard/profile.yaml"),
            )
            self.assertEqual(code, 0, stderr)
            self.assertIn(": OK", stdout)

    def test_validate_manuscript_missing_profile_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pilot.qmd"
            path.write_text("## 2.2 A Pilot\n", encoding="utf-8")
            code, _, stderr = self.run_cli(
                "--root",
                temp,
                "validate-manuscript",
                "pilot.qmd",
                "--mode",
                "section-pilot",
                "--profile",
                "missing-profile.yaml",
            )
            self.assertEqual(code, 1)
            self.assertIn("cannot read", stderr)


if __name__ == "__main__":
    unittest.main()
