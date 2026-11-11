"""The published schemas must themselves be valid Draft 2020-12 schemas."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402


def manifest_document(version: str, roles: tuple[str, ...]) -> dict:
    names = {"html": "book-html.zip", "pdf": "book.pdf", "docx": "book.docx",
             "markdown": "book.md", "source": "book-source.zip"}
    return {
        "schema_version": version,
        "book": {"id": "test-book", "version": "1.0.0", "commit": "a" * 40},
        "toolkit": "0.6.0",
        "profile": {"id": "standard", "version": "1.0.0"},
        "build": {
            "command": "fixture build",
            "source_date_epoch": 1,
            "tool_versions": {"quarto": "1.11.9", "pandoc": "3.10", "typst": "0.15.1",
                              "python": "3.12", "zlib": "1.3.1"},
        },
        "artifacts": [
            {"role": role, "path": names[role], "sha256": "b" * 64,
             "bytes": 1, "media_type": "application/octet-stream"}
            for role in roles
        ],
    }


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


class PublicationManifestSchemaTests(unittest.TestCase):
    """Schema 1.0 keeps four payloads valid; schema 1.1 requires the fifth."""

    def setUp(self) -> None:
        schema = json.loads(
            (support.SCHEMAS / "publication-manifest.schema.json").read_text(encoding="utf-8")
        )
        self.validator = Draft202012Validator(schema)

    def test_legacy_and_current_payload_sets_are_valid(self) -> None:
        self.assertTrue(
            self.validator.is_valid(manifest_document("1.0", ("html", "pdf", "docx", "source")))
        )
        self.assertTrue(
            self.validator.is_valid(
                manifest_document("1.1", ("html", "pdf", "docx", "markdown", "source"))
            )
        )

    def test_mismatched_version_and_payload_set_is_invalid(self) -> None:
        self.assertFalse(
            self.validator.is_valid(
                manifest_document("1.0", ("html", "pdf", "docx", "markdown", "source"))
            )
        )
        self.assertFalse(
            self.validator.is_valid(manifest_document("1.1", ("html", "pdf", "docx", "source")))
        )

    def test_duplicate_role_cannot_replace_a_required_payload(self) -> None:
        document = manifest_document("1.1", ("html", "pdf", "docx", "markdown", "source"))
        duplicate = copy.deepcopy(document)
        duplicate["artifacts"][4]["role"] = "markdown"
        duplicate["artifacts"][4]["path"] = "second.md"
        self.assertFalse(self.validator.is_valid(duplicate))

    def test_unknown_schema_version_is_invalid(self) -> None:
        document = manifest_document("2.0", ("html", "pdf", "docx", "markdown", "source"))
        self.assertFalse(self.validator.is_valid(document))


if __name__ == "__main__":
    unittest.main()
