"""The packaged DOCX reference must match its generator."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
SCRIPT = TOOLS / "scripts/generate_reference_docx.py"
PACKAGED = TOOLS / "src/handbook_toolkit/render_data/docx/reference.docx"


class ReferenceDocxTests(unittest.TestCase):
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
