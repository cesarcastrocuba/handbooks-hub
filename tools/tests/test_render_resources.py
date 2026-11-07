"""Installed resource distribution and real Quarto filter behavior."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import support
from handbook_toolkit.render_resources import RESOURCE_NAMES, stage_render_resources


class RenderResourceTests(unittest.TestCase):
    def test_stage_is_exclusive_and_cleans_failed_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "resources"
            staged = stage_render_resources(target)
            self.assertEqual(set(staged), set(RESOURCE_NAMES))
            self.assertTrue(all(path.stat().st_size for path in staged.values()))
            with self.assertRaises(FileExistsError):
                stage_render_resources(target)
            failed = Path(folder) / "failed"
            with patch("handbook_toolkit.render_resources.files", side_effect=OSError("read failed")):
                with self.assertRaises(OSError):
                    stage_render_resources(failed)
            self.assertFalse(failed.exists())

    def test_resources_load_from_zip_outside_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "package.zip"
            package = support.SRC / "handbook_toolkit"
            with ZipFile(archive, "w") as bundle:
                for path in sorted(package.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        bundle.write(path, path.relative_to(support.SRC).as_posix())
            output = subprocess.check_output([
                sys.executable, "-c",
                "from pathlib import Path; import handbook_toolkit; "
                "from handbook_toolkit.render_resources import stage_render_resources; "
                "assert '.zip/' in handbook_toolkit.__file__; "
                "print(len(stage_render_resources(Path('staged'))))",
            ], cwd=root, env=dict(os.environ, PYTHONPATH=str(archive)), text=True, timeout=30)
            self.assertEqual(output.strip(), str(len(RESOURCE_NAMES)))

    @unittest.skipUnless(shutil.which("quarto"), "real Quarto boundary requires Quarto")
    def test_table_filter_preserves_labels_and_handles_identical_chapters(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            staged = stage_render_resources(root / "resources")
            table_filter = staged["filters/table-layout.lua"]
            # Identical content in different files must produce distinct labels;
            # a project relocation must not change either label.
            table = "| A | B |\n|---|---|\n| " + "é" * 20 + " | " + "漢" * 20 + " |\n\n: Caption\n\n"
            explicit = table.replace(": Caption", ": Caption {#tbl-kept tbl-colwidths=\"[40,60]\"}")
            script = (
                "quarto={doc={input_file=os.getenv('RENDER_INPUT')},"
                "project={directory=os.getenv('RENDER_PROJECT')}}\n"
                f"dofile({json.dumps(str(table_filter))})\n"
            )
            wrapper = root / "wrapper.lua"
            wrapper.write_text(script)
            identifiers = []
            for project, name in ((root / "a", "one.qmd"), (root / "a", "two.qmd"),
                                  (root / "b", "one.qmd")):
                project.mkdir(exist_ok=True)
                input_file = project / name
                input_file.write_text(table + explicit)
                result = subprocess.check_output([
                    "quarto", "pandoc", str(input_file), "--from", "markdown",
                    "--to", "json", "--lua-filter", str(wrapper),
                ], env=dict(os.environ, RENDER_INPUT=str(input_file), RENDER_PROJECT=str(project)),
                    text=True, timeout=30)
                blocks = json.loads(result)["blocks"]
                tables = [block["c"] for block in blocks if block["t"] == "Table"]
                self.assertEqual(tables[1][0][0], "tbl-kept")
                self.assertIn(["tbl-colwidths", "[40,60]"], tables[1][0][2])
                identifiers.append(tables[0][0][0])
                self.assertIn(["tbl-colwidths", "[50,50]"], tables[0][0][2])
            self.assertNotEqual(identifiers[0], identifiers[1])
            self.assertEqual(identifiers[0], identifiers[2])


if __name__ == "__main__":
    unittest.main()
