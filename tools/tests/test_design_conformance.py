"""Generated surfaces must carry the packaged tokens, not private copies."""

from __future__ import annotations

import re
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit import design  # noqa: E402

RENDER = support.SRC / "handbook_toolkit" / "render_data"
HEX = re.compile(r"#[0-9A-Fa-f]{6}")


class GeneratedSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tokens = design.load_tokens()

    def test_portal_theme_contains_every_token_and_font(self) -> None:
        css = design.portal_theme_css()
        for role, values in self.tokens["color"].items():
            with self.subTest(role=role):
                self.assertIn(values["light"], css)
                self.assertIn(values["dark"], css)
        self.assertIn('font-family:"Handbook Sans"', css)
        self.assertIn('font-family:"Handbook Serif"', css)
        self.assertIn('font-family:"Handbook Mono"', css)
        self.assertNotIn("http", css)

    def test_book_theme_targets_quarto_toggle(self) -> None:
        css = design.book_theme_css()
        self.assertIn("body.quarto-dark", css)
        self.assertIn("prefers-color-scheme:dark", css)
        self.assertIn("../fonts/source-sans3/HandbookSans-Regular.woff2", css)

    def test_book_layout_has_no_private_palette(self) -> None:
        css = (RENDER / "html" / "handbook.css").read_text(encoding="utf-8")
        self.assertEqual(HEX.findall(css), [])
        self.assertIn("var(--accent-solid)", css)
        self.assertIn("var(--font-sans)", css)

    def test_typst_theme_uses_generated_constants(self) -> None:
        theme = (RENDER / "typst" / "handbook-typst.typ").read_text(encoding="utf-8")
        self.assertIn("hb-font", theme)
        self.assertIn("hb-text", theme)
        self.assertIn("hb-accent", theme)
        for retired in ("#161616", "#605E5C", "#0065b3", "Selawik"):
            with self.subTest(value=retired):
                self.assertNotIn(retired, theme)

    def test_print_layout_uses_generated_constants(self) -> None:
        layout = (support.SRC / "handbook_toolkit" / "print_layout.py").read_text(encoding="utf-8")
        self.assertNotIn("#E1DFDD", layout)
        self.assertNotIn("#605E5C", layout)
        self.assertIn("hb-border", layout)
        self.assertIn("hb-muted", layout)

    def test_docx_reference_uses_tokens(self) -> None:
        reference = RENDER / "docx" / "reference.docx"
        with zipfile.ZipFile(reference) as archive:
            styles = archive.read("word/styles.xml").decode("utf-8")
        self.assertIn('w:ascii="Source Sans 3"', styles)
        self.assertIn('w:ascii="Source Serif 4"', styles)
        self.assertIn('w:ascii="JetBrains Mono"', styles)
        self.assertIn('w:pageBreakBefore', styles)
        self.assertIn('w:tblStylePr w:type="firstRow"', styles)
        self.assertIn('CalloutNoteTitle', styles)
        for role in ("text", "muted", "accent"):
            colour = self.tokens["color"][role]["print"].lstrip("#")
            with self.subTest(role=role):
                self.assertIn(f'w:val="{colour}"', styles)

    def test_packaged_web_fonts_exist_for_every_face(self) -> None:
        assets = design.font_assets()
        self.assertEqual(len(assets), 10)
        for relative, data in assets.items():
            with self.subTest(font=relative):
                self.assertTrue(data.startswith(b"wOF2"))

    def test_license_files_travel_with_the_web_fonts(self) -> None:
        licenses = design.font_licenses()
        self.assertEqual(
            set(licenses),
            {"source-sans3/OFL.txt", "source-serif4/OFL.txt", "jetbrains-mono/OFL.txt"},
        )
        for relative, data in licenses.items():
            with self.subTest(license=relative):
                self.assertIn(b"SIL OPEN FONT LICENSE", data.upper())

    def test_font_face_output_names_the_license(self) -> None:
        css = design.font_face_css("fonts/")
        self.assertIn("fonts/source-sans3/OFL.txt", css)
        self.assertIn("fonts/source-serif4/OFL.txt", css)
        self.assertIn("fonts/jetbrains-mono/OFL.txt", css)

    def test_portal_filled_controls_use_the_solid_role(self) -> None:
        from handbook_toolkit.portal import STYLE_LAYOUT

        self.assertIn(
            "button[aria-pressed=true]{background:var(--accent-solid);color:var(--on-solid)",
            STYLE_LAYOUT,
        )
        self.assertIn(
            ".btn.primary{background:var(--accent-solid);color:var(--on-solid)}",
            STYLE_LAYOUT,
        )
        self.assertNotIn("background:var(--accent);color:var(--accent-ink)", STYLE_LAYOUT)


if __name__ == "__main__":
    unittest.main()
