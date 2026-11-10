"""Template export regression.

The export script copies exactly the tracked files of ``template/book/`` into a new directory. The
tests prove that the exported tree equals the template file-for-file, that dotfiles are included, that
nothing else is added, and that unsafe output directories are refused.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

SCRIPT = support.REPO_ROOT / "tools" / "scripts" / "export_template.py"
TEMPLATE = support.REPO_ROOT / "template" / "book"
PREFIX = "template/book"


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(support.REPO_ROOT), "ls-files", "-z", "--", PREFIX],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(
        Path(entry).relative_to(PREFIX) for entry in result.stdout.split("\0") if entry
    )


def _export(output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=support.REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExportTemplateTests(unittest.TestCase):
    def test_export_equals_the_tracked_template_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "export"
            result = _export(output)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            expected = _tracked_files()
            actual = sorted(
                path.relative_to(output) for path in output.rglob("*") if path.is_file()
            )
            self.assertEqual(actual, expected)
            for relative in expected:
                self.assertEqual(
                    (output / relative).read_bytes(),
                    (TEMPLATE / relative).read_bytes(),
                    str(relative),
                )

            self.assertTrue((output / ".gitignore").is_file())
            self.assertTrue((output / ".github/workflows/ci.yml").is_file())
            self.assertTrue((output / ".github/scripts/initialize_book.py").is_file())
            self.assertFalse((output / ".git").exists())

    def test_export_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            self.assertEqual(_export(first).returncode, 0)
            self.assertEqual(_export(second).returncode, 0)

            def snapshot(root: Path) -> dict[str, str]:
                return {
                    path.relative_to(root).as_posix(): _digest(path)
                    for path in sorted(root.rglob("*"))
                    if path.is_file()
                }

            self.assertEqual(snapshot(first), snapshot(second))

    def test_refuses_an_existing_non_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "export"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")

            result = _export(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not empty", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["keep.txt"])

    def test_allows_an_existing_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "export"
            output.mkdir()
            result = _export(output)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((output / "README.md").is_file())

    def test_refuses_an_output_inside_the_template(self) -> None:
        output = TEMPLATE / "dist" / "export"
        self.assertFalse(output.exists())
        result = _export(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside template/book", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
