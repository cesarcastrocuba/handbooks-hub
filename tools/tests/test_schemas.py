"""The published schemas must themselves be valid Draft 2020-12 schemas."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402


class SchemaTests(unittest.TestCase):
    def test_all_schemas_are_valid(self) -> None:
        paths = sorted(support.SCHEMAS.glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(schema=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(document)

    def test_schema_versions_are_declared(self) -> None:
        for path in sorted(support.SCHEMAS.glob("*.json")):
            with self.subTest(schema=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
