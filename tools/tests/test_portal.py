"""Portal contracts checked through parsed structure and real, deterministic Quarto output."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import support
from html_support import Document
from handbook_toolkit import design
from handbook_toolkit.catalog import ASSET_FILES
from handbook_toolkit.portal import CATEGORIES, FORMATS, build_portal
from handbook_toolkit.portal_catalog import read_catalog
from handbook_toolkit.portal_quarto import stage_site
from handbook_toolkit.validation import load_packaged_schema


def document_with_assets():
    document=support.catalog_document()
    document['schema_version']='1.1'
    release=document['books'][0]['latest_release']
    base=release['manifest_url'].rsplit('/',1)[0]+'/'
    release['assets']={role:base+name for role,name in ASSET_FILES.items()}
    return document


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.catalog=self.root/'catalog.json'
        self.output=self.root/'site'

    def build(self,document):
        support.write_json(self.catalog,document)
        return Document(build_portal(self.catalog,self.output).read_text()).root

    def test_empty_catalog_has_no_book_or_release_link(self):
        page=self.build({'schema_version':'1.0','books':[]})
        self.assertIn('The first handbook is being prepared',page.text())
        self.assertIn('Planned topics',page.text())
        self.assertFalse(page.find('article'))
        self.assertFalse(any('/releases/' in (n.attrs.get('href') or '') for n in page.find('a')))

    def test_exact_catalog_links_and_accessible_controls(self):
        document=document_with_assets()
        page=self.build(document)
        book=document['books'][0];release=book['latest_release']
        links={n.attrs.get('href') for n in page.find('a')}
        self.assertEqual(len(page.find('article')),1)
        self.assertTrue({book['reading_url'],release['url'],release['manifest_url'],release['checksums_url'],*release['assets'].values()} <= links)
        self.assertEqual(page.find('p',id='results')[0].attrs['aria-live'],'polite')
        group=page.find('div',role='group')[0]
        self.assertEqual(group.attrs['aria-label'],'Filter by topic')
        self.assertEqual(group.find('button')[0].attrs['aria-pressed'],'true')
        self.assertEqual(page.find('label',**{'for':'search'})[0].find('input')[0].attrs['id'],'search')
        self.assertEqual(page.find('p',id='results')[0].text(),'Showing 1 of 1 handbook')

    def test_untrusted_catalog_prose_is_text(self):
        document=support.catalog_document()
        document['books'][0]['title']='<script>alert("x")</script>'
        document['books'][0]['summary']='<img src=x onerror="bad()">'
        page=self.build(document)
        article=page.find('article')[0]
        self.assertFalse(article.find('script'))
        self.assertFalse(article.find('img'))
        self.assertEqual(article.find('h3')[0].text(),document['books'][0]['title'])

    def test_invalid_catalog_never_creates_output(self):
        for change in ('missing-reading','draft','unknown-category','branch-reading','query-reading'):
            with self.subTest(change=change):
                document=support.catalog_document();book=document['books'][0]
                if change=='missing-reading':del book['reading_url']
                elif change=='draft':book['status']='draft'
                elif change=='branch-reading':book['reading_url']='https://github.com/owner/book/tree/main'
                elif change=='query-reading':book['reading_url']='https://example.github.io/book/?edition=latest'
                else:book['categories']=['uncontrolled-topic']
                support.write_json(self.catalog,document)
                for engine in ('legacy','quarto'):
                    with self.assertRaises(ValueError):build_portal(self.catalog,self.output,engine=engine)
                self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.build({'schema_version':'1.0','books':[]})
        for engine in ('legacy','quarto'):
            with self.assertRaises(FileExistsError):build_portal(self.catalog,self.output,engine=engine)

    def test_write_failure_cleans_private_staging(self):
        support.write_json(self.catalog,{'schema_version':'1.0','books':[]})
        with patch('handbook_toolkit.portal.Path.write_text',side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):build_portal(self.catalog,self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.portal-*')))

    def test_only_declared_editions_have_buttons(self):
        document=document_with_assets();del document['books'][0]['latest_release']['assets']['markdown']
        page=self.build(document)
        formats=[n for n in page.find('a') if n.attrs.get('class')=='fmt']
        self.assertEqual({n.text() for n in formats},set(FORMATS.values())-{'Markdown'})
        self.assertEqual({n.attrs['href'] for n in formats},set(document['books'][0]['latest_release']['assets'].values()))

    def test_guides_and_contribution_links_exist(self):
        page=self.build(support.catalog_document())
        for anchor in ('library','how-it-works','create','publishing','contribute','faq'):
            self.assertEqual(len(page.find('section',id=anchor)),1)
        links={n.attrs.get('href') for n in page.find('a')}
        self.assertIn('https://github.com/example/example-book',links)
        self.assertTrue(any('request-listing.yml' in (url or '') for url in links))
        self.assertTrue(any('request-withdrawal.yml' in (url or '') for url in links))
        self.assertTrue(all(not n.attrs.get('src') for n in page.find('script')))

    def test_llms_uses_declared_markdown_else_reading_url(self):
        document=document_with_assets();self.build(document)
        book=document['books'][0]
        self.assertIn(f"- [Example Book]({book['latest_release']['assets']['markdown']}):",(self.output/'llms.txt').read_text())
        shutil.rmtree(self.output);self.build(support.catalog_document())
        self.assertIn(f"- [Example Book]({book['reading_url']}):",(self.output/'llms.txt').read_text())

    def test_llms_one_safe_line_and_empty_catalog(self):
        document=support.catalog_document();document['books'][0]['title']='A [bracketed]\ntitle'
        self.build(document)
        self.assertIn('- [A (bracketed) title](',(self.output/'llms.txt').read_text())
        shutil.rmtree(self.output);self.build({'schema_version':'1.0','books':[]})
        self.assertIn('No handbook is listed yet.',(self.output/'llms.txt').read_text())

    def test_fonts_and_notices_are_packaged_and_linked(self):
        page=self.build(support.catalog_document());links={n.attrs.get('href') for n in page.find('a')}
        self.assertEqual(len(list((self.output/'fonts').rglob('*.woff2'))),10)
        for relative,data in design.font_licenses().items():
            self.assertEqual((self.output/'fonts'/relative).read_bytes(),data)
            self.assertIn('fonts/'+relative,links)
        self.assertEqual(set(FORMATS),set(ASSET_FILES))
        schema=load_packaged_schema('catalog.schema.json')
        self.assertEqual(CATEGORIES,set(schema['properties']['books']['items']['properties']['categories']['items']['enum']))

    def test_default_generator_remains_legacy_until_weight_parity(self):
        with patch('handbook_toolkit.portal_quarto.build_quarto_portal',side_effect=AssertionError('candidate deployed')):
            self.assertTrue(self.build(support.catalog_document()).find('article'))

    def test_failed_quarto_render_cleans_staging_without_output(self):
        support.write_json(self.catalog,support.catalog_document())
        with patch('handbook_toolkit.portal_quarto._run',side_effect=['1.11.9',ValueError('renderer failed')]):
            with self.assertRaisesRegex(ValueError,'renderer failed'):
                build_portal(self.catalog,self.output,engine='quarto')
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.portal-*')))

    def test_staged_configuration_has_shared_theme_and_native_metadata(self):
        import yaml
        site=self.root/'staging'
        support.write_json(self.catalog,document_with_assets())
        stage_site(site,read_catalog(self.catalog))
        config=yaml.safe_load((site/'_quarto.yml').read_text())
        self.assertEqual(config['project']['type'],'website')
        self.assertEqual(config['format']['html']['theme'],{'light':['cosmo','handbook-light.scss'],'dark':['cosmo','handbook-dark.scss']})
        for scheme in ('light','dark'):
            self.assertEqual((site/f'handbook-{scheme}.scss').read_text(),design.book_scss(scheme))
        self.assertTrue(config['format']['html']['canonical-url'])
        variables=dict(line[1:].rstrip(';').split(': ',1) for line in design.book_scss('light').splitlines() if line.startswith('$'))
        self.assertEqual(variables['web-font-path'],'false')
        self.assertTrue(config['website']['open-graph'])
        self.assertEqual((site/'.handbook-render/html/handbook.css').read_text(),design.book_layout_css())
        self.assertFalse(config['execute']['enabled'])


@unittest.skipUnless(shutil.which('quarto'),'Quarto is required for portal rendering')
class QuartoPortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.root=Path(cls.temp.name);cls.catalog=cls.root/'catalog.json'
        cls.document=document_with_assets()
        cls.document['books'][0]['title']='<script>bad()</script> Café\n```\nTitle'
        support.write_json(cls.catalog,cls.document)
        cls.site=build_portal(cls.catalog,cls.root/'site',engine='quarto').parent

    def test_rendered_catalog_is_text_and_links_are_exact(self):
        page=Document((self.site/'index.html').read_text()).root
        article=page.find('article')[0]
        self.assertEqual(article.find('h2')[0].text(),self.document['books'][0]['title'])
        self.assertFalse(article.find('script'))
        links={node.attrs.get('href') for node in article.find('a')}
        self.assertTrue(set(self.document['books'][0]['latest_release']['assets'].values()) <= links)
        self.assertEqual(len(page.find('input',id='search')),1)
        self.assertTrue(page.find('a',id='quarto-skip-link'))
        self.assertTrue(page.find('link',rel='canonical'))
        self.assertEqual((self.site/'llms.txt').read_bytes(),self._legacy_llms())

    def _legacy_llms(self):
        return (build_portal(self.catalog,self.root/'legacy').parent/'llms.txt').read_bytes()

    def test_repeat_render_is_byte_identical(self):
        second=build_portal(self.catalog,self.root/'second',engine='quarto').parent
        first={p.relative_to(self.site):p.read_bytes() for p in self.site.rglob('*') if p.is_file()}
        repeated={p.relative_to(second):p.read_bytes() for p in second.rglob('*') if p.is_file()}
        self.assertEqual(first.keys(),repeated.keys())
        self.assertEqual([str(name) for name in first if first[name]!=repeated[name]],[])

    def test_design_page_contains_token_rows_and_every_role(self):
        tree=Document((self.site/'design.html').read_text()).root
        tables=tree.find('table')
        roles={row.find('td')[0].text().strip() for row in tables[0].find('tr') if row.find('td')}
        self.assertEqual(roles,set(design.load_tokens()['color']))
        self.assertEqual(len(tree.find('span',**{'class':'style-swatch'})),len(roles)*3)
        self.assertTrue(any('Note' in node.text() for node in tree.find('div')))
        self.assertFalse(list(self.root.glob('.portal-*')))
