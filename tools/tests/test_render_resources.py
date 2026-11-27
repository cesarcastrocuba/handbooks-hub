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

    def test_embedded_inter_widths_match_the_font(self):
        result = subprocess.run(
            [sys.executable, str(support.TOOLS_ROOT / "scripts/table_font_widths.py"), "--check"],
            cwd=support.REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("quarto"), "real Quarto boundary requires Quarto")
    def test_table_floors_fit_inter_bold_words(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            staged = stage_render_resources(root / "resources")
            table_filter = staged["filters/table-layout.lua"]
            wrapper = root / "wrapper.lua"
            wrapper.write_text(
                "quarto={doc={input_file=os.getenv('RENDER_INPUT')},"
                "project={directory=os.getenv('RENDER_PROJECT')}}\n"
                f"dofile({json.dumps(str(table_filter))})\n"
            )
            source = root / "tables.md"
            source.write_text(
                "| Version | Date | Summary |\n"
                "|---|---|---|\n"
                "| 0.6.0 | November 2026 | A very long summary that makes the third column dominate the "
                "content weight, so the date column is squeezed below its floor unless the filter takes "
                "room from several columns. |\n"
                "| 0.6.1 | November 2026 | Another very long summary that keeps the third column dominant "
                "across rows, because the width shares are computed from average text length. |\n\n"
                ": Version history\n\n"
                "| Component | Configuration | Owner | Evidence | Notes |\n"
                "|---|---|---|---|---|\n"
                "| configuration | PAYMENT_PENDING configuration here | Penetration evidence text | "
                "Technique evidence | scanning notes |\n\n"
                ": Appendix F shaped\n\n"
                "| Component | Owner | Evidence | Notes |\n"
                "|---|---|---|---|\n"
                "| PAYMENT_PENDING | Platform team evidence | A long evidence sentence for this row | "
                "A long note sentence for this row |\n\n"
                ": Four columns\n"
            )
            result = subprocess.check_output(
                [
                    "quarto", "pandoc", str(source), "--from", "markdown", "--to", "json",
                    "--lua-filter", str(wrapper),
                ],
                env=dict(os.environ, RENDER_INPUT=str(source), RENDER_PROJECT=str(root)),
                text=True,
                timeout=30,
            )
            tables = [
                dict(block["c"][0][2]).get("tbl-colwidths")
                for block in json.loads(result)["blocks"]
                if block["t"] == "Table"
            ]
            widths = [[int(value) for value in table.strip("[]").split(",")] for table in tables]
            # Inter Bold 'November' is 5.1167 em: ceil((5.1167 * 10.5 + 8) / 440 * 100) = 15.
            self.assertGreaterEqual(widths[0][1], 15)
            # Inter Bold 'configuration' is 6.6084 em: ceil((6.6084 * 10.5 + 8) / 440 * 100) = 18.
            self.assertGreaterEqual(widths[1][0], 18)
            # Inter Bold 'PAYMENT_PENDING' is 10.1035 em: ceil(...)=26, above the 20 % cap.
            # The uncapped floors fit the page, so the cap must not apply.
            self.assertGreaterEqual(widths[2][0], 26)

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

@unittest.skipUnless(shutil.which('quarto') and shutil.which('pdftotext'),
                     'Quarto and Poppler are required for the long-table probe')
class RoundedTableTests(unittest.TestCase):
    def test_rounded_print_table_keeps_all_rows_and_repeated_headers(self):
        from handbook_toolkit import design
        theme = (support.SRC / 'handbook_toolkit/render_data/typst/handbook-typst.typ').read_text()
        with tempfile.TemporaryDirectory() as folder:
            stage_render_resources(Path(folder) / 'handbook-render')
            source = Path(folder) / 'long-table.typ'
            source.write_text(design.typst_preamble() + theme + '''
#set page(width: 160mm, height: 120mm, margin: 10mm, header: none, footer: none)
#table(columns: (1fr, 3fr), table.header([Row], [Evidence]),
  ..range(100).map(n => ([#n], [A repeated row that must split across pages.])).flatten())
''')
            result = subprocess.run(['quarto', 'typst', 'compile', '--font-path',
                                     str(support.SRC / 'handbook_toolkit/render_data/fonts'), str(source)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['pdftotext', '-layout', str(source.with_suffix('.pdf')), '-'],
                                    capture_output=True, text=True, check=True)
            import re
            rows = re.findall(r'^\s*(\d+)\s+A repeated row', result.stdout, re.MULTILINE)
            self.assertEqual(rows, list(map(str, range(100))))
            pages = result.stdout.count('\f')
            self.assertGreater(pages, 1)
            self.assertEqual(result.stdout.count('Evidence'), pages)


if __name__ == "__main__":
    unittest.main()
