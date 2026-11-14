"""Native list collection and generated theme structure."""
from pathlib import Path
import re
import tempfile
import unittest

import support
from handbook_toolkit import design
from handbook_toolkit.web_lists import caption_references, generate_list_pages
from handbook_toolkit.build import BuildError


class NativeWebTests(unittest.TestCase):
    def test_registry_lists_are_nonempty_and_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.qmd').write_text('# Title\n\n: Routes {#tbl-routes}\n\n![Alt](image.svg){#fig-flow}\n\n```{#lst-demo .python lst-cap="Demo"}\n# code {#tbl-false}\n```\n')
            self.assertEqual(generate_list_pages(root, ['index.qmd']), ['tables.qmd', 'figures.qmd', 'listings.qmd'])
            self.assertEqual(caption_references((root / 'index.qmd').read_text()), [('tbl-routes', 'Routes'), ('fig-flow', 'Alt'), ('lst-demo', 'Demo')])
            with self.assertRaises(BuildError):
                generate_list_pages(root, ['index.qmd'])

    def test_empty_lists_are_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.qmd').write_text('# Title\nNo captions.\n')
            self.assertEqual(generate_list_pages(root, ['index.qmd']), [])

    def test_sass_defaults_derive_from_each_scheme(self):
        tokens = design.load_tokens()
        for scheme in ('light', 'dark'):
            declarations = dict(re.findall(r'^\$([\w-]+):\s*(.*);$', design.book_scss(scheme), re.M))
            self.assertEqual(declarations['body-bg'], tokens['color']['canvas'][scheme])
            self.assertEqual(declarations['navbar-bg'], declarations['body-bg'])
            self.assertEqual(declarations['sidebar-bg'], declarations['body-bg'])
            self.assertEqual(declarations['link-color'], tokens['color']['accent'][scheme])
            self.assertEqual(declarations['callout-color-note'], tokens['callout']['note']['accent'][scheme])

    def test_book_styles_have_no_important_or_unexpanded_dimensions(self):
        css = design.book_layout_css() + design.book_theme_css()
        self.assertNotIn('!important', css)
        self.assertNotIn('{{book-metric-', css)
