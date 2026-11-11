"""Issue-form regression.

Both catalog request forms are GitHub issue forms. GitHub rejects a form that does not parse as YAML
or that omits a required top-level field, so the tests load both forms and assert the fields the
author journey depends on.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

FORMS = support.REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
CATEGORIES = {
    "architecture",
    "authoring",
    "cloud",
    "data",
    "engineering",
    "governance",
    "publishing",
    "security",
}


def _load(name: str) -> dict:
    return yaml.safe_load((FORMS / name).read_text(encoding="utf-8"))


def _fields(document: dict) -> dict[str, dict]:
    return {
        entry["id"]: entry
        for entry in document["body"]
        if isinstance(entry, dict) and "id" in entry
    }


def _required(entry: dict) -> bool:
    return entry.get("validations", {}).get("required") is True


class IssueFormTests(unittest.TestCase):
    def _common(self, document: dict) -> None:
        self.assertIsInstance(document, dict)
        for key in ("name", "description", "body"):
            self.assertIn(key, document)
        self.assertIsInstance(document["body"], list)
        self.assertTrue(document["body"])

    def test_listing_form_is_a_valid_issue_form(self) -> None:
        document = _load("request-listing.yml")
        self._common(document)
        fields = _fields(document)

        for identifier in (
            "repository",
            "release-tag",
            "release-url",
            "reading-site",
            "summary",
            "categories",
        ):
            self.assertIn(identifier, fields, identifier)
            if identifier != "summary":
                self.assertTrue(_required(fields[identifier]), identifier)

        summary = fields["summary"]
        self.assertEqual(summary["type"], "textarea")
        self.assertIn("280", summary["attributes"]["label"])
        self.assertTrue(_required(summary))

        categories = fields["categories"]
        self.assertEqual(categories["type"], "dropdown")
        self.assertTrue(categories["attributes"].get("multiple") is True)
        self.assertEqual(set(categories["attributes"]["options"]), CATEGORIES)
        self.assertTrue(_required(categories))

        checks = fields["confirmations"]
        self.assertEqual(checks["type"], "checkboxes")
        options = checks["attributes"]["options"]
        self.assertGreaterEqual(len(options), 3)
        self.assertTrue(all(option.get("required") is True for option in options))

    def test_withdrawal_form_is_a_valid_issue_form(self) -> None:
        document = _load("request-withdrawal.yml")
        self._common(document)
        fields = _fields(document)

        for identifier in ("book-slug", "version", "reason", "details", "keep-tag"):
            self.assertIn(identifier, fields, identifier)

        self.assertTrue(_required(fields["book-slug"]))
        self.assertTrue(_required(fields["version"]))
        self.assertTrue(_required(fields["details"]))

        reason = fields["reason"]
        self.assertEqual(reason["type"], "dropdown")
        self.assertEqual(
            set(reason["attributes"]["options"]),
            {"defect", "licensing or rights", "author request", "superseded"},
        )
        self.assertTrue(_required(reason))

        keep_tag = fields["keep-tag"]
        self.assertEqual(keep_tag["type"], "checkboxes")
        self.assertTrue(all(option.get("required") is True for option in keep_tag["attributes"]["options"]))

    def test_blank_issues_are_enabled(self) -> None:
        config = _load("config.yml")
        self.assertIs(config["blank_issues_enabled"], True)


if __name__ == "__main__":
    unittest.main()
