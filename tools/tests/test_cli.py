"""CLI smoke and exit-code tests."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
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
        self.assertIn("handbook-toolkit 0.1.0", stdout)

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
        code, stdout, stderr = self.run_cli("--root", str(support.REPO_ROOT), "validate-book", "--full")
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


if __name__ == "__main__":
    unittest.main()
