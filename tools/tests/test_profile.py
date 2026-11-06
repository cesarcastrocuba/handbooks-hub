"""Profile validation tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.profiles import validate_profile  # noqa: E402


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.schema = support.SCHEMAS / "profile.schema.json"

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

    def test_required_figure_needs_a_minimum(self) -> None:
        document = support.profile_document()
        document["figure"]["min_per_section"] = 0
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("figure is required" in issue.message for issue in result.issues))

    def test_upscaling_is_rejected(self) -> None:
        document = support.profile_document()
        document["figure"]["upscale"] = True
        result = self.check(document)
        self.assertFalse(result.ok)
        self.assertTrue(any("upscaling" in issue.message for issue in result.issues))

    def test_unknown_field_is_rejected_by_schema(self) -> None:
        document = support.profile_document()
        document["chapter"]["unknown"] = True
        result = self.check(document)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
