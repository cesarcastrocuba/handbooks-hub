"""Native reading-site configuration, metadata and accessible CSS behavior."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import tinycss2
import yaml
import support
from handbook_toolkit import design
from handbook_toolkit.build import BuildError
from handbook_toolkit.reading_site import prepare_reading_site, release_links, site_url


def motion_violations(css):
    violations = []
    def walk(rules, allowed=False):
        for rule in rules:
            if rule.type == 'at-rule':
                condition = tinycss2.serialize(rule.prelude).strip()
                nested = allowed or (rule.at_keyword == 'media' and condition == '(prefers-reduced-motion: no-preference)')
                if rule.at_keyword in {'view-transition', 'keyframes'} and not allowed:
                    violations.append(rule.at_keyword)
                if rule.content and rule.at_keyword in {'media', 'supports', 'keyframes'}:
                    walk(tinycss2.parse_rule_list(rule.content), nested)
            elif rule.type == 'qualified-rule':
                for declaration in tinycss2.parse_declaration_list(rule.content):
                    if declaration.type == 'declaration' and declaration.name.startswith(('animation', 'transition')) and not allowed:
                        violations.append(declaration.name)
    walk(tinycss2.parse_stylesheet(css))
    return violations


def rule_declarations(css, selector):
    """Declarations of the first rule with this selector, at any nesting depth."""
    def walk(rules):
        for rule in rules:
            if rule.type == 'qualified-rule' and tinycss2.serialize(rule.prelude).strip() == selector:
                return {declaration.name: tinycss2.serialize(declaration.value).strip()
                        for declaration in tinycss2.parse_declaration_list(rule.content)
                        if declaration.type == 'declaration'}
            if rule.type == 'at-rule' and rule.content:
                found = walk(tinycss2.parse_rule_list(rule.content))
                if found is not None:
                    return found
        return None
    found = walk(tinycss2.parse_stylesheet(css))
    if found is None:
        raise AssertionError(f'no rule for {selector}')
    return found


class ReadingSiteTests(unittest.TestCase):
    def test_cover_parts_footer_and_native_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.handbook-render/html').mkdir(parents=True)
            (root / 'chapter.qmd').write_text('# Example\n')
            book = {'title': 'Handbook \\T', 'status':'draft', 'catalog':{'summary':'A <script> is text.'},
                    'license':{'content':'CC-BY-SA-4.0'},
                    'repository':{'url':'https://github.com/example/handbook'}}
            groups = {'front':[], 'chapters':['chapter.qmd'], 'back':[], 'appendices':[], 'references':[]}
            config = {'book':{}, 'format':{'html':{}}}
            result = prepare_reading_site(root, config, book, {'subtitle':'An edition'}, groups,
                        ['figures.qmd'], [('Version','1.0.0')], 'An Author',
                        '1.0.0', 'November 2026', False)
            chapters = result['book']['chapters']
            self.assertEqual(chapters, ['index.qmd', {'part':'Front matter','chapters':['document-control.qmd','figures.qmd']},
                                      'chapter.qmd'])
            front = yaml.safe_load((root/'index.qmd').read_text().split('---',2)[1])
            self.assertEqual(front['title'], '# Handbook \\T {.unnumbered}')
            self.assertFalse(front['numbered'])
            self.assertIn('&lt;script&gt;', (root/'index.qmd').read_text())
            self.assertNotIn('edition_urls', (root/'index.qmd').read_text())
            self.assertIn('chapter.html', (root/'index.qmd').read_text())
            self.assertEqual(result['book']['site-url'], 'https://example.github.io/handbook/')
            self.assertTrue(result['format']['html']['canonical-url'])
            self.assertEqual(result['book']['description'], book['catalog']['summary'])
            self.assertTrue(result['book']['open-graph'])
            self.assertEqual(result['book']['twitter-card']['card-style'], 'summary')
            self.assertIn('1.0.0', result['book']['page-footer']['center'])
            self.assertTrue((root / result['book']['favicon']).is_file())

    def _prepare(self, root, summary, subtitle, groups):
        (root / '.handbook-render/html').mkdir(parents=True)
        for files in groups.values():
            for name in files:
                (root / name).write_text('# ' + name + '\n')
        book = {'title': 'Handbook', 'status': 'draft', 'catalog': {'summary': summary},
                'license': {'content': 'CC-BY-SA-4.0'}, 'repository': {'url': None}}
        config = {'book': {}, 'format': {'html': {}}}
        return prepare_reading_site(root, config, book, {'subtitle': subtitle}, groups, [],
                                    [('Version', '1.0.0')], 'An Author', '1.0.0', 'November 2026', False)

    def test_a_group_is_a_part_only_when_it_has_several_pages(self):
        groups = {'front': ['intro.qmd'], 'chapters': ['one.qmd', 'two.qmd'], 'back': ['notices.qmd'],
                  'appendices': ['a.qmd', 'b.qmd'], 'references': ['references.qmd']}
        with tempfile.TemporaryDirectory() as folder:
            result = self._prepare(Path(folder), 'A summary.', 'A subtitle', groups)
        self.assertEqual(result['book']['chapters'], [
            'index.qmd',
            {'part': 'Front matter', 'chapters': ['document-control.qmd', 'intro.qmd']},
            {'part': 'Chapters', 'chapters': ['one.qmd', 'two.qmd']},
            'notices.qmd',
            {'part': 'Appendices', 'chapters': ['a.qmd', 'b.qmd']},
            'references.qmd',
        ])

    def test_the_cover_states_the_summary_once(self):
        groups = {'front': [], 'chapters': ['one.qmd'], 'back': [], 'appendices': [], 'references': []}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._prepare(root, 'A practical guide.', 'a practical guide', groups)
            repeated = (root / 'index.qmd').read_text().split('---', 2)[2]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._prepare(root, 'What the book promises.', 'A practical guide', groups)
            distinct = (root / 'index.qmd').read_text().split('---', 2)[2]
        self.assertNotIn('practical guide', repeated.casefold())
        self.assertIn('What the book promises.', distinct)

    def test_the_cover_keeps_the_page_grid_of_the_other_pages(self):
        groups = {'front': [], 'chapters': ['one.qmd'], 'back': [], 'appendices': [], 'references': []}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._prepare(root, 'A summary.', 'A subtitle', groups)
            front = yaml.safe_load((root / 'index.qmd').read_text().split('---', 2)[1])
        self.assertNotIn('toc', front)

    def test_the_progress_bar_is_hidden_until_the_scroll_timeline_drives_it(self):
        css = (support.SRC / 'handbook_toolkit/render_data/html/reading.css').read_text()
        declarations = rule_declarations(css, 'body::before')
        self.assertEqual(declarations['transform'], 'scaleX(0)')
        self.assertEqual(declarations['animation-timeline'], 'scroll()')

    def test_release_urls_are_explicit_and_omitted_in_preview(self):
        metadata={'release_url':'https://example.org/releases/v1', 'edition_urls':{'pdf':'https://example.org/book.pdf'}}
        self.assertEqual(release_links({}, False), (None, {}))
        self.assertEqual(release_links(metadata, True), (None, {}))
        self.assertEqual(release_links(metadata, False), (metadata['release_url'], metadata['edition_urls']))
        for value in ['javascript:alert(1)', 'https://user:secret@example.org/book', 'https://example.org/a b']:
            with self.subTest(url=value), self.assertRaises(BuildError):
                release_links({'release_url':value}, False)
        with self.assertRaises(BuildError):
            release_links({'edition_urls':{'unknown':'https://example.org/book'}},False)

    def test_unknown_repository_has_no_guessed_canonical(self):
        for repo in [None, 'https://github.com/OWNER/REPOSITORY', 'https://example.org/repo']:
            self.assertIsNone(site_url({'repository':{'url':repo}}, {}, {}))
        self.assertEqual(site_url({}, {'site_url':'https://books.example.org/'}, {}),'https://books.example.org/')

    def test_motion_is_guarded_by_reduced_motion_query(self):
        self.assertEqual(motion_violations(design.reading_css()), [])
        self.assertEqual(motion_violations(design.book_layout_css()), [])
        self.assertEqual(motion_violations('a {transition: color 1s}'), ['transition'])
        self.assertEqual(motion_violations('@view-transition {navigation:auto}'), ['view-transition'])

    def test_generated_svg_sources_are_deterministic_and_token_derived(self):
        root=ET.fromstring(design.favicon_svg())
        colors=design.load_tokens()['color']
        self.assertEqual(root.get('viewBox'), design.READING_METRICS['favicon-viewbox'])
        fills={node.get('fill') for node in root if node.get('fill')}
        self.assertEqual(fills,{colors['accent_solid']['light'],colors['on_solid']['light']})
        illustration=support.REPO_ROOT/'template/book/manuscript/images/section-structure.svg'
        self.assertEqual(illustration.read_text(),design.example_figure_svg())
        ET.fromstring(illustration.read_text())

    def test_real_component_contrast_in_each_scheme(self):
        tokens=design.load_tokens()
        for scheme in ('light','dark'):
            colors=tokens['color']
            for name,role in tokens['callout'].items():
                with self.subTest(scheme=scheme,callout=name):
                    self.assertGreaterEqual(design.contrast_ratio(role['accent'][scheme],role['tint'][scheme]),4.5)
            for foreground,background in [('accent','canvas'),('accent','table_stripe'),('on_solid','accent_solid'),('muted','canvas')]:
                with self.subTest(scheme=scheme,foreground=foreground,background=background):
                    self.assertGreaterEqual(design.contrast_ratio(colors[foreground][scheme],colors[background][scheme]),4.5)
