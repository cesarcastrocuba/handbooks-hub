"""Installation-boundary tests.

These tests simulate an installed package by copying only ``handbook_toolkit`` (including its bundled
schemas) into an isolated directory, then running the CLI from a book directory that has a decoy
``schemas/`` directory. If schema resolution ever falls back to the book root, the decoy schema makes
the validation fail. The test therefore proves the installed toolkit is self-contained.

A real wheel install is not possible in this environment because pip, ensurepip and wheel are absent;
CI installs the editable package instead. The zip-import case additionally covers a package loaded
from an archive, which is the least filesystem-friendly installation shape.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

PACKAGE_SOURCE = support.TOOLS_ROOT / "src" / "handbook_toolkit"
DECOY_SCHEMAS = ("book.schema.json", "catalog.schema.json", "profile.schema.json")


class InstalledPackageTests(unittest.TestCase):
    def _copy_book(self, root: Path) -> Path:
        book = root / "book"
        shutil.copytree(support.REPO_ROOT / "template/book", book)
        decoy = book / "schemas"
        decoy.mkdir()
        for name in DECOY_SCHEMAS:
            (decoy / name).write_text(
                '{"type": "object", "required": ["this-decoy-must-never-be-used"]}\n',
                encoding="utf-8",
            )
        return book

    def _run(self, package_path: Path, book: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(package_path)
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import handbook_toolkit; print(handbook_toolkit.__file__)",
            ],
            cwd=book,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertIn(str(package_path), probe.stdout)
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "handbook_toolkit",
                "--root",
                str(book),
                "validate-book",
                "book.yaml",
                "--full",
            ],
            cwd=book,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_isolated_package_copy_uses_bundled_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            site = root / "site"
            shutil.copytree(
                PACKAGE_SOURCE,
                site / "handbook_toolkit",
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            self.assertTrue((site / "handbook_toolkit/schemas/book.schema.json").is_file())

            book = self._copy_book(root)
            result = self._run(site, book)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(": OK", result.stdout)

    def test_zip_imported_package_uses_bundled_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "handbook_toolkit.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for path in PACKAGE_SOURCE.rglob("*"):
                    if path.is_file() and "__pycache__" not in path.parts:
                        bundle.write(path, path.relative_to(PACKAGE_SOURCE.parent).as_posix())

            book = self._copy_book(root)
            result = self._run(archive, book)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(": OK", result.stdout)

    def test_pyproject_ships_schemas_as_package_data(self) -> None:
        configuration = tomllib.loads(
            (support.TOOLS_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        package_data = configuration["tool"]["setuptools"]["package-data"]
        self.assertIn("schemas/*.json", package_data["handbook_toolkit"])


if __name__ == "__main__":
    unittest.main()
