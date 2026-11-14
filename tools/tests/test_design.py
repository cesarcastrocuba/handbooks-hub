"""The packaged design tokens must stay complete, contrast-safe and shipped."""

from __future__ import annotations

import copy
from pathlib import Path
import io
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

    def test_pdf_canvas_is_cream_and_callouts_cover_every_scheme(self) -> None:
        self.assertEqual(self.tokens["color"]["canvas"]["print"], "#F6F1E7")
        self.assertEqual(
            set(self.tokens["callout"]),
            {"note", "tip", "warning", "important", "review"},
        )
        for name, values in self.tokens["callout"].items():
            with self.subTest(callout=name):
                self.assertEqual(sorted(values), ["accent", "tint"])
                for part in values.values():
                    self.assertEqual(sorted(part), sorted(design.SCHEMES))

    def test_book_chrome_shares_width_callouts_and_code_surfaces(self) -> None:
        chrome = design.book_layout_css()
        self.assertIn("max-width: 1300px", chrome)
        self.assertIn("div.callout.review", chrome)
        self.assertIn("#quarto-document-content pre.text", chrome)
        self.assertIn("background: var(--code)", chrome)
        self.assertIn("tbody tr:nth-child(even)", chrome)
        self.assertIn("--callout-review-accent", design.css_variables("light"))

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
        self.assertIn("render_data/fonts/*/*.woff2", package_data)

    def test_brand_typeface_is_shared_across_media(self) -> None:
        brand = self.tokens["type"]["brand"]
        self.assertEqual(self.tokens["type"]["body"]["print_family"], brand["text_family"])
        self.assertEqual(self.tokens["type"]["display"]["print_family"], brand["display_family"])
        self.assertIn(brand["web_text_name"], self.tokens["type"]["body"]["web_family"])
        self.assertIn(brand["web_display_name"], self.tokens["type"]["display"]["web_family"])
        self.assertEqual(self.tokens["type"]["code"]["print_family"], "JetBrains Mono")

    def test_web_font_assets_are_packaged_woff2(self) -> None:
        assets = design.font_assets()
        expected = {relative for _family, relative, _weight, _style in design.WEB_FONTS}
        self.assertEqual(set(assets), expected)
        for relative, data in assets.items():
            with self.subTest(font=relative):
                self.assertTrue(data.startswith(b"wOF2"))
                self.assertGreater(len(data), 10_000)

    def test_font_faces_are_same_origin(self) -> None:
        css = design.font_face_css("fonts/")
        self.assertIn("@font-face", css)
        self.assertNotIn("http", css)
        self.assertIn("fonts/source-sans3/HandbookSans-Regular.woff2", css)

    def test_book_theme_covers_quarto_dark_and_media(self) -> None:
        css = design.book_theme_css()
        self.assertIn("body.quarto-dark", css)
        self.assertIn("prefers-color-scheme:dark", css)
        for role, values in self.tokens["color"].items():
            with self.subTest(role=role):
                self.assertIn(values["light"], css)
                self.assertIn(values["dark"], css)

    def test_portal_theme_uses_brand_font_and_both_schemes(self) -> None:
        css = design.portal_theme_css()
        self.assertIn('font-family:"Handbook Sans"', css)
        self.assertIn('font-family:"Handbook Serif"', css)
        self.assertIn("--paper: var(--canvas);", css)
        self.assertIn("prefers-color-scheme:dark", css)

    def test_typst_preamble_uses_brand_fonts(self) -> None:
        typst = design.typst_preamble()
        self.assertIn('#let hb-font = ("Handbook Sans",)', typst)
        self.assertIn('#let hb-display-font = ("Handbook Serif",)', typst)
        self.assertIn('#let hb-code-font = ("JetBrains Mono",)', typst)

    def test_docx_values_name_the_compatible_family(self) -> None:
        values = design.docx_values()
        self.assertEqual(values["body_font"], "Source Sans 3")
        self.assertEqual(values["display_font"], "Source Serif 4")
        self.assertEqual(values["code_font"], "JetBrains Mono")
        self.assertEqual(values["ink"], self.tokens["color"]["text"]["print"])


    def test_web_fonts_are_renamed_and_carry_the_license(self) -> None:
        from fontTools.ttLib import TTFont

        for relative, data in design.font_assets().items():
            with self.subTest(font=relative):
                font = TTFont(io.BytesIO(data))
                name = font["name"]
                family = name.getDebugName(1) or ""
                postscript = name.getDebugName(6) or ""
                self.assertIn(family, ("Handbook Sans", "Handbook Serif", "Handbook Mono"))
                self.assertTrue(
                    postscript.startswith(("HandbookSans-", "HandbookSerif-", "HandbookMono-")), postscript
                )
                self.assertNotIn("SourceSans", postscript)
                self.assertIn("SIL Open Font License", name.getDebugName(13) or "")
                self.assertIn("openfontlicense.org", name.getDebugName(14) or "")


if __name__ == "__main__":
    unittest.main()
