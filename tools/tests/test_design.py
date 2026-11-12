"""The packaged design tokens must stay complete, contrast-safe and shipped."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit import design  # noqa: E402


class DesignTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tokens = design.load_tokens()

    def test_packaged_tokens_validate(self) -> None:
        self.assertEqual(design.validate_tokens(self.tokens), [])

    def test_every_colour_role_covers_every_scheme(self) -> None:
        for role, values in self.tokens["color"].items():
            with self.subTest(role=role):
                self.assertEqual(sorted(values), sorted(design.SCHEMES))
                for scheme, value in values.items():
                    self.assertRegex(value, r"^#[0-9A-F]{6}$", f"{role}.{scheme}")

    def test_contrast_pairs_cover_every_scheme(self) -> None:
        covered = {scheme for pair in self.tokens["contrast"] for scheme in pair["schemes"]}
        self.assertEqual(covered, set(design.SCHEMES))

    def test_contrast_pairs_reference_declared_roles(self) -> None:
        roles = set(self.tokens["color"])
        for pair in self.tokens["contrast"]:
            with self.subTest(pair=pair["name"]):
                self.assertIn(pair["foreground"], roles)
                self.assertIn(pair["background"], roles)

    def test_low_contrast_is_reported(self) -> None:
        tokens = copy.deepcopy(self.tokens)
        tokens["color"]["muted"]["light"] = "#EDE6D8"
        issues = design.validate_tokens(tokens)
        self.assertTrue(
            any("below the required" in issue.message for issue in issues),
            [str(issue) for issue in issues],
        )

    def test_missing_scheme_is_reported(self) -> None:
        tokens = copy.deepcopy(self.tokens)
        del tokens["color"]["accent"]["dark"]
        issues = design.validate_tokens(tokens)
        self.assertTrue(
            any("color.accent" in issue.location for issue in issues),
            [str(issue) for issue in issues],
        )

    def test_declared_contrast_floor_cannot_be_lowered(self) -> None:
        tokens = copy.deepcopy(self.tokens)
        tokens["contrast"][0]["minimum"] = 3.0
        issues = design.validate_tokens(tokens)
        self.assertTrue(
            any("text floor" in issue.message for issue in issues),
            [str(issue) for issue in issues],
        )

    def test_unknown_colour_role_is_reported(self) -> None:
        tokens = copy.deepcopy(self.tokens)
        tokens["contrast"][0]["foreground"] = "ink"
        issues = design.validate_tokens(tokens)
        self.assertTrue(
            any("unknown colour role" in issue.message for issue in issues),
            [str(issue) for issue in issues],
        )

    def test_contrast_math_matches_wcag_definitions(self) -> None:
        self.assertAlmostEqual(design.contrast_ratio("#000000", "#FFFFFF"), 21.0, places=6)
        self.assertAlmostEqual(design.contrast_ratio("#FFFFFF", "#FFFFFF"), 1.0, places=6)
        with self.assertRaises(ValueError):
            design.relative_luminance("#FFF")

    def test_pyproject_ships_design_tokens(self) -> None:
        pyproject = tomllib.loads(
            (support.TOOLS_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        package_data = pyproject["tool"]["setuptools"]["package-data"]["handbook_toolkit"]
        self.assertIn("design/*.json", package_data)


if __name__ == "__main__":
    unittest.main()
