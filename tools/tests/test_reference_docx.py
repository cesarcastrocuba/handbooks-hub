"""The packaged DOCX reference must match its generator."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
SCRIPT = TOOLS / "scripts/generate_reference_docx.py"
PACKAGED = TOOLS / "src/handbook_toolkit/render_data/docx/reference.docx"


class ReferenceDocxTests(unittest.TestCase):
    def test_normal_table_text_is_10_5_points(self) -> None:
        word = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with ZipFile(PACKAGED) as archive:
            styles = ET.fromstring(archive.read('word/styles.xml'))
        normal = styles.find(f"{word}style[@{word}styleId='Normal']")
        self.assertIsNotNone(normal)
        size = normal.find(f"{word}rPr/{word}sz")
        self.assertEqual(size.get(f"{word}val"), "21")

    def test_reference_has_no_conditional_banding_or_update_request(self) -> None:
        word = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with ZipFile(PACKAGED) as archive:
            for name in archive.namelist():
                if name.endswith('.xml'):
                    root = ET.fromstring(archive.read(name))
                    self.assertFalse(list(root.iter(word + 'updateFields')))
                    self.assertFalse(any(node.get(word + 'type') in {'band1Horz', 'band2Horz'}
                                         for node in root.iter(word + 'tblStylePr')))

    def test_packaged_file_matches_generator(self) -> None:
        spec = importlib.util.spec_from_file_location("generate_reference_docx", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "reference.docx"
            module.write_reference(output)
            self.assertEqual(output.read_bytes(), PACKAGED.read_bytes())


if __name__ == "__main__":
    unittest.main()
