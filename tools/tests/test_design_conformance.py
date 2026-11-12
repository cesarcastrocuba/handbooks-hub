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
        self.assertIn('font-family:"Handbook Mono"', css)
        self.assertNotIn("http", css)

    def test_book_theme_targets_quarto_toggle(self) -> None:
        css = design.book_theme_css()
        self.assertIn("body.quarto-dark", css)
        self.assertIn("prefers-color-scheme:dark", css)
        self.assertIn("../fonts/liberation-sans/LiberationSans-Regular.woff2", css)

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
        self.assertIn('w:ascii="Arial"', styles)
        self.assertIn('w:ascii="JetBrains Mono"', styles)
        for role in ("text", "muted", "accent"):
            colour = self.tokens["color"][role]["print"].lstrip("#")
            with self.subTest(role=role):
                self.assertIn(f'w:val="{colour}"', styles)

    def test_packaged_web_fonts_exist_for_every_face(self) -> None:
        assets = design.font_assets()
        self.assertEqual(len(assets), 7)
        for relative, data in assets.items():
            with self.subTest(font=relative):
                self.assertTrue(data.startswith(b"wOF2"))


if __name__ == "__main__":
    unittest.main()
