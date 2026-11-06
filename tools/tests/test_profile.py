"""Profile validation tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.profiles import validate_profile  # noqa: E402
from handbook_toolkit.validation import load_schema  # noqa: E402


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.schema = load_schema(support.SCHEMAS / "profile.schema.json")

    def tearDown(self) -> None:
        self._temp.cleanup()

    def check(self, document: dict):
        path = support.write_yaml(self.root / "profile.yaml", document)
        return validate_profile(path, self.schema)

    def test_repository_profile_is_valid(self) -> None:
        result = validate_profile(support.REPO_ROOT / "profiles/standard/profile.yaml", self.schema)
        self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_duplicate_chapter_element_id_is_rejected(self) -> None:
        document = support.profile_document()
        document["chapter"]["required_elements"].append(
            support.copy_document(document["chapter"]["required_elements"][0])
        )
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate element id" in issue.message for issue in result.issues))

    def test_duplicate_chapter_title_is_rejected(self) -> None:
        document = support.profile_document()
        duplicate = support.copy_document(document["chapter"]["required_elements"][0])
        duplicate["id"] = "duplicate-title"
        document["chapter"]["required_elements"].append(duplicate)
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate element title" in issue.message for issue in result.issues))

    def test_closing_order_must_match_section_elements(self) -> None:
        document = support.profile_document()
        document["section"]["closing_order"] = ["example", "common-pitfall"]
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("closing_order" in issue.message for issue in result.issues))

    def test_word_range_must_be_ordered(self) -> None:
        document = support.profile_document()
        document["unit"]["min_words"] = 400
        document["unit"]["max_words"] = 100
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("min_words" in issue.message for issue in result.issues))

    def test_labels_must_end_with_period(self) -> None:
        document = support.profile_document()
        document["unit"]["required_labels"][0] = "Definition"
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("must end with a period" in issue.message for issue in result.issues))

    def test_standard_profile_is_topic_neutral_and_visuals_are_optional(self) -> None:
        document = support.profile_document()
        chapter = {element["id"]: element for element in document["chapter"]["required_elements"]}

        self.assertIn("review-checklist", chapter)
        self.assertNotIn("architecture-review-checklist", chapter)
        self.assertEqual(chapter["review-checklist"]["title"], "Review Checklist")
        self.assertFalse(
            any("architecture" in element["title"].lower() for element in chapter.values())
        )

        for required in ("when-to-use", "key-takeaway", "worked-example", "further-reading"):
            self.assertIn(required, chapter)
        self.assertEqual(
            document["unit"]["required_labels"],
            ["Definition.", "Purpose.", "What it includes.", "Why it is needed."],
        )

        self.assertFalse(document["figure"]["required"])
        self.assertEqual(document["figure"]["min_per_section"], 0)
        self.assertFalse(document["table"]["required"])
        self.assertEqual(document["table"]["min_per_section"], 0)
        section_ids = {element["id"] for element in document["section"]["required_elements"]}
        self.assertNotIn("figure", section_ids)
        self.assertNotIn("table", section_ids)
        self.assertTrue({"example", "common-pitfall", "decision-trade-off"} <= section_ids)

        self.assertTrue(document["exceptions"]["allowed"])
        self.assertTrue(document["exceptions"]["requires_owner_approval"])

    def test_required_figure_needs_a_minimum(self) -> None:
        document = support.profile_document()
        document["figure"]["required"] = True
        document["figure"]["min_per_section"] = 0
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("figure is required" in issue.message for issue in result.issues))

    def test_optional_figure_cannot_have_a_minimum(self) -> None:
        document = support.profile_document()
        document["figure"]["min_per_section"] = 1
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("figure is optional but min_per_section" in issue.message for issue in result.issues)
        )

    def test_required_table_needs_a_minimum(self) -> None:
        document = support.profile_document()
        document["table"]["required"] = True
        document["table"]["min_per_section"] = 0
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("table is required" in issue.message for issue in result.issues))

    def test_optional_table_cannot_have_a_minimum(self) -> None:
        document = support.profile_document()
        document["table"]["min_per_section"] = 1
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("table is optional but min_per_section" in issue.message for issue in result.issues)
        )

    def test_upscaling_is_rejected(self) -> None:
        document = support.profile_document()
        document["figure"]["upscale"] = True
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("upscaling" in issue.message for issue in result.issues))

    def test_profile_1_rules_have_complete_classifications(self) -> None:
        document = support.profile_document()
        self.assertEqual(document["version"], "1.0.0")
        rules = document["validation"]["rules"]
        self.assertEqual(len({rule["id"] for rule in rules}), len(rules))
        self.assertEqual({rule["classification"] for rule in rules} - {"automated", "assisted", "manual"}, set())

    def test_profile_1_requires_validation_rules(self) -> None:
        document = support.profile_document()
        document.pop("validation")
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("requires rule classifications" in issue.message for issue in result.issues))

    def test_duplicate_rule_ids_are_rejected(self) -> None:
        document = support.profile_document()
        document["validation"]["rules"].append(support.copy_document(document["validation"]["rules"][0]))
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate rule id" in issue.message for issue in result.issues))

    def test_unknown_field_is_rejected_by_schema(self) -> None:
        document = support.profile_document()
        document["chapter"]["unknown"] = True
        result = self.check(document)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
