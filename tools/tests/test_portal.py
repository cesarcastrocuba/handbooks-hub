"""Portal contracts checked through parsed structure and real, deterministic Quarto output."""
from pathlib import Path
import posixpath
import shutil
import tempfile
import unittest
from unittest.mock import patch

import support
from html_support import Document
from handbook_toolkit import design
from handbook_toolkit.artifacts import hidden_site_paths
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

    def test_quarto_portal_loads_the_shared_guarded_motion_layer(self):
        from test_reading_site import motion_violations
        stage_site(self.root / 'staged', [])
        reading = next((self.root / 'staged').rglob('reading.css')).read_text()
        self.assertEqual(reading, design.reading_css())
        self.assertEqual(motion_violations(reading), [])
        import yaml
        config=yaml.safe_load((self.root / 'staged/_quarto.yml').read_text())
        self.assertNotIn('blocking',str(config['format']['html']))

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

    def with_authors(self, authors, second_authors=None):
        document = document_with_assets()
        document['schema_version'] = '1.2'
        document['books'][0]['authors'] = authors
        if second_authors is not None:
            second = support.copy_document(document['books'][0])
            second['id'] = second['slug'] = 'second-book'
            second['title'] = 'Second Book'
            second['reading_url'] = 'https://example.github.io/second-book/'
            second['authors'] = second_authors
            release = second['latest_release']
            for field in ('url', 'manifest_url', 'checksums_url'):
                release[field] = release[field].replace('example/example-book', 'example/second-book')
            release['assets'] = {role: url.replace('example/example-book', 'example/second-book')
                                 for role, url in release['assets'].items()}
            document['books'].append(second)
        return document

    def test_card_and_cover_show_the_authors_and_the_publisher(self):
        page = self.build(self.with_authors(['Franz César Castro Cuba', 'Second <Author>']))
        article = page.find('article')[0]
        self.assertEqual(article.find('p', **{'class': 'authors'})[0].text(),
                         'By Franz César Castro Cuba and Second <Author>')
        cover = article.find('div', **{'class': 'cover'})[0]
        self.assertEqual(cover.find('span', **{'class': 'cover-author'})[0].text(),
                         'Franz César Castro Cuba and Second <Author>')
        self.assertEqual(cover.find('span', **{'class': 'cover-foot'})[0].text(),
                         'Handbooks Hub · v1.0.0')
        self.assertEqual(article.attrs['data-authors'], 'Franz César Castro Cuba | Second <Author>')
        self.assertFalse(article.find('script'))
        self.assertIn('Handbooks Hub — an independent publisher of open handbooks', page.text())

    def test_author_select_lists_each_distinct_author_once(self):
        document = self.with_authors(['Zoe Author', 'Álvaro Author'], ['Zoe Author'])
        page = self.build(document)
        select = page.find('select', id='author')[0]
        options = [option.text() for option in select.find('option')]
        self.assertEqual(options[0], 'All authors')
        self.assertEqual(sorted(options[1:]), sorted(['Zoe Author', 'Álvaro Author']))
        self.assertEqual(len(options), 3)
        self.assertEqual(select.find('option')[0].attrs['value'], 'all')
        label = page.find('label', **{'for': 'author'})[0]
        self.assertEqual(label.text().split()[0], 'Author')

    def test_a_catalog_without_authors_keeps_the_card_clean(self):
        page = self.build(document_with_assets())
        article = page.find('article')[0]
        self.assertFalse(article.find('p', **{'class': 'authors'}))
        self.assertFalse(article.find('span', **{'class': 'cover-author'}))
        self.assertEqual(article.attrs['data-authors'], '')

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
        self.assertEqual(len(list((self.output/'fonts').rglob('*.woff2'))),7)
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
        self.assertEqual((site/'handbook-render/html/handbook.css').read_text(),design.book_layout_css())
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
        self.assertIn('Handbooks Hub — an independent publisher of open handbooks',page.text())
        self.assertEqual((self.site/'llms.txt').read_bytes(),self._legacy_llms())

    def test_every_local_asset_of_every_page_is_publishable(self):
        files={path.relative_to(self.site).as_posix() for path in self.site.rglob('*') if path.is_file()}
        self.assertEqual(hidden_site_paths(files),[])
        pages=sorted(name for name in files if name.endswith('.html'))
        self.assertIn('design.html',pages)

        css=next(self.site.rglob('reading.css')).read_text()
        self.assertEqual(css,design.reading_css())
        self.assertNotIn("view-transition", css)
        for name in pages:
            markup=(self.site/name).read_text()

            page=Document(markup).root
            self.assertEqual(len(page.find('script',id='quarto-html-after-body')),1)
            ready=page.find('link',rel='expect')
            self.assertEqual(len(ready), 0)
            targets=[node.attrs.get('href') for node in page.find('link')]
            targets+=[node.attrs.get('src') for tag in ('script','img') for node in page.find(tag)]
            local=[posixpath.normpath(posixpath.join(posixpath.dirname(name),target.split('#')[0].split('?')[0]))
                   for target in targets
                   if target and '://' not in target and not target.startswith(('data:','#','mailto:'))]
            self.assertTrue(any(target.endswith('portal.css') for target in local),name)
            for target in local:
                with self.subTest(page=name,target=target):
                    self.assertIn(target,files)

    def test_home_guides_are_whole_card_links(self):
        page = Document((self.site / 'index.html').read_text()).root
        guides = page.find('nav', **{'aria-label': 'Platform guides'})[0]
        cards = guides.find('a', **{'class': 'guide-card'})
        self.assertEqual(len(cards), 5)
        self.assertEqual({card.attrs['href'] for card in cards},
                         {name + '.html' for name in ('how-it-works', 'create', 'publishing', 'contribute', 'faq')})
        for card in cards:
            self.assertEqual(len(card.find('a')), 1)  # the card itself; no nested links
            self.assertTrue(card.find('span', **{'class': 'guide-title'})[0].text())
            self.assertTrue(card.find('span', **{'class': 'guide-description'})[0].text())
            self.assertEqual(card.find('span', **{'class': 'guide-arrow'})[0].attrs['aria-hidden'], 'true')

    def test_browser_scale_targets_focus_and_uniform_scrollable_tables(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest('Playwright is installed by the edition-preview job')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for width in (1280, 390):
                for scheme in ('light', 'dark'):
                    context = browser.new_context(viewport={'width': width, 'height': 1000},
                                                  color_scheme=scheme, reduced_motion='reduce')
                    try:
                        page = context.new_page()
                        page.goto((self.site / 'index.html').as_uri())
                        page.evaluate('document.fonts.ready')
                        computed = lambda selector, prop: page.locator(selector).first.evaluate(
                            '(e,p)=>getComputedStyle(e)[p]', prop)
                        accent = design.load_tokens()['color']['accent'][scheme].lstrip('#')
                        expected_accent = 'rgb(' + ', '.join(str(int(accent[i:i+2], 16)) for i in (0, 2, 4)) + ')'
                        self.assertEqual(computed('.links a', 'color'), expected_accent)
                        self.assertEqual(computed('body', 'fontSize'), '15px')
                        self.assertEqual(computed('body', 'lineHeight'), '23.25px')
                        self.assertEqual(computed('h1', 'fontSize'), '40px' if width == 1280 else '28px')
                        self.assertEqual(computed('h1', 'fontWeight'), '700')
                        self.assertEqual(computed('.planned', 'fontSize'), '13px')
                        self.assertEqual(computed('.planned', 'marginTop'), '20px')
                        gap = page.evaluate('document.querySelector(".planned").getBoundingClientRect().top - document.querySelector("#book-grid").getBoundingClientRect().bottom')
                        self.assertGreaterEqual(gap, 20)
                        self.assertEqual(computed('.btn', 'fontSize'), '14px')
                        self.assertEqual(computed('.btn', 'borderRadius'), '6px')
                        self.assertEqual(computed('.btn', 'padding'), '10px 16px')
                        self.assertEqual(computed('.tag', 'fontSize'), '11px')
                        self.assertEqual(computed('.fmt', 'fontSize'), '12px')
                        self.assertEqual(computed('.book', 'borderRadius'), '8px')
                        for selector in ('.btn', '.fmt', '[data-filter]', '#search', '#sort'):
                            for target in page.locator(selector).all():
                                self.assertGreaterEqual(target.bounding_box()['height'], 24)
                        page.locator('.guide-card').first.focus()
                        self.assertEqual(computed('.guide-card', 'outlineStyle'), 'solid')
                        self.assertEqual(computed('.guide-card', 'outlineWidth'), '3px')
                        self.assertEqual(page.locator('link[rel="expect"]').count(), 0)
                        page.goto((self.site / 'design.html').as_uri())
                        self.assertEqual(computed('h1', 'fontSize'), '48px' if width == 1280 else '32px')
                        cells = page.locator('main table').first.locator('tbody td').all()
                        colors = {cell.evaluate('e=>getComputedStyle(e).backgroundColor') for cell in cells}
                        expected = 'rgb(255, 253, 248)' if scheme == 'light' else 'rgb(28, 37, 38)'
                        self.assertEqual(colors, {expected})
                        # At phone width the table itself remains a scroll container.
                        if width == 390:
                            table = page.locator('main table').first
                            dimensions = table.evaluate('e=>({scroll:e.scrollWidth,client:e.clientWidth})')
                            self.assertGreater(dimensions['scroll'], dimensions['client'])
                            table.evaluate('e=>e.scrollLeft=100')
                            self.assertGreater(table.evaluate('e=>e.scrollLeft'), 0)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                    finally:
                        context.close()
            browser.close()

    def test_author_filter_and_search_work_in_the_browser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest('Playwright is installed by the edition-preview job')
        document = support.catalog_document()
        document['schema_version'] = '1.2'
        book = document['books'][0]
        book['authors'] = ['Zoe Author']
        second = support.copy_document(book)
        second['id'] = second['slug'] = 'second-book'
        second['title'] = 'Second Book'
        second['reading_url'] = 'https://example.github.io/second-book/'
        second['authors'] = ['Álvaro <Author>']
        release = second['latest_release']
        for field in ('url', 'manifest_url', 'checksums_url'):
            release[field] = release[field].replace('example/example-book', 'example/second-book')
        document['books'].append(second)
        catalog = self.root / 'authors.json'
        support.write_json(catalog, document)
        site = build_portal(catalog, self.root / 'authors-site', engine='quarto').parent
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto((site / 'index.html').as_uri())
                visible = lambda: page.locator('.book:not([hidden])').count()
                self.assertEqual(visible(), 2)
                self.assertEqual(page.locator('#results').inner_text(), 'Showing 2 of 2 handbooks')
                page.select_option('#author', 'Álvaro <Author>')
                self.assertEqual(visible(), 1)
                self.assertEqual(page.locator('#results').inner_text(), 'Showing 1 of 2 handbooks')
                page.select_option('#author', 'all')
                self.assertEqual(visible(), 2)
                page.fill('#search', 'Álvaro')
                self.assertEqual(visible(), 1)
                page.fill('#search', 'zoe')
                self.assertEqual(visible(), 1)
            finally:
                browser.close()

    def _legacy_llms(self):
        return (build_portal(self.catalog,self.root/'legacy').parent/'llms.txt').read_bytes()

    def test_cover_opens_the_reading_site_and_star_links_the_repository(self):
        book=self.document['books'][0]
        page=Document((self.site/'index.html').read_text()).root
        article=page.find('article')[0]
        cover=article.find('a',**{'class':'cover-link'})[0]
        self.assertEqual(cover.attrs['href'],book['reading_url'])
        # A pointer shortcut only: the visible "Read handbook" link stays the single tab stop.
        self.assertEqual(cover.attrs['tabindex'],'-1')
        self.assertEqual(cover.attrs['aria-hidden'],'true')
        self.assertTrue(cover.find('div',**{'class':'cover'}))
        star=article.find('a',**{'class':'star'})[0]
        repository=book['latest_release']['url'].split('/releases/')[0]
        self.assertEqual(star.attrs['href'],repository)
        # Built without HANDBOOK_STARS=fetch: no number, never a failure.
        self.assertTrue(star.attrs['aria-label'].startswith('Star '))
        self.assertFalse(star.find('span',**{'class':'star-count'}))
        navbar=[node for node in page.find('a',**{'class':'nav-link'}) if 'Star' in node.text()]
        self.assertEqual([node.attrs['href'] for node in navbar],['https://github.com/cesarcastrocuba/handbooks-hub'])
        for path in self.site.rglob('*.html'):
            self.assertNotIn('api.github.com',path.read_text(),path.name)

    def test_guide_pages_show_actions_steps_and_features(self):
        expected={'how-it-works':('edition-strip','feature-grid','owner-grid','pipeline'),
                  'create':('pipeline','feature-grid','file-tree'),
                  'publishing':('pipeline',),'contribute':('pipeline',)}
        for name,classes in expected.items():
            with self.subTest(page=name):
                markup=(self.site/f'{name}.html').read_text()
                page=Document(markup).root
                actions=page.find('p',**{'class':'actions'})
                self.assertTrue(actions)
                for group in actions:
                    self.assertGreaterEqual(len(group.find('a')),1)
                for css in classes:
                    self.assertIn(f'class="{css}"',markup)
                self.assertNotIn('{{icon:',markup)
        create=(self.site/'create.html').read_text()
        self.assertIn('https://github.com/cesarcastrocuba/handbooks-template',create)

    def test_buttons_never_touch_and_the_cover_navigates_in_the_browser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest('Playwright is installed by the edition-preview job')
        gaps_script=("()=>{const r=[];document.querySelectorAll('#quarto-document-content p:has(> .btn), .actions')"
                     ".forEach(g=>{const b=[...g.querySelectorAll(':scope > .btn')].map(e=>e.getBoundingClientRect());"
                     "for(let i=1;i<b.length;i++){r.push(Math.max(b[i].left-b[i-1].right,b[i].top-b[i-1].bottom))}});return r}")
        reading=self.document['books'][0]['reading_url']
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch()
            try:
                for width in (1280,390,320):
                    context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
                    page=context.new_page()
                    for name in ('index','how-it-works','create','publishing','contribute'):
                        with self.subTest(width=width,page=name):
                            page.goto((self.site/f'{name}.html').as_uri())
                            gaps=page.evaluate(gaps_script)
                            self.assertTrue(gaps)
                            self.assertGreaterEqual(min(gaps),8)
                            for button in page.locator('#quarto-document-content .btn, .links a.star').all():
                                self.assertGreaterEqual(button.bounding_box()['height'],44)
                            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                    context.close()
                context=browser.new_context(viewport={'width':390,'height':900},reduced_motion='reduce')
                page=context.new_page()
                page.route(reading+'**',lambda route: route.fulfill(body='<title>reading</title>',content_type='text/html'))
                page.goto((self.site/'index.html').as_uri())
                page.locator('.cover').first.click()
                page.wait_for_url(reading+'**')
                context.close()
            finally:
                browser.close()

    def test_repeat_render_is_byte_identical(self):
        second=build_portal(self.catalog,self.root/'second',engine='quarto').parent
        first={p.relative_to(self.site):p.read_bytes() for p in self.site.rglob('*') if p.is_file()}
        repeated={p.relative_to(second):p.read_bytes() for p in second.rglob('*') if p.is_file()}
        self.assertEqual(first.keys(),repeated.keys())
        self.assertEqual([str(name) for name in first if first[name]!=repeated[name]],[])

    def test_empty_candidate_and_standalone_design_are_honest(self):
        from handbook_toolkit.portal_quarto import build_quarto_portal
        catalog=self.root/'empty.json';support.write_json(catalog,{'schema_version':'1.0','books':[]})
        path=build_portal(catalog,self.root/'empty',engine='quarto')
        tree=Document(path.read_text()).root
        self.assertFalse(tree.find('article'))
        self.assertIn('The first handbook is being prepared',tree.text())
        single=build_quarto_portal(None,self.root/'design-only',design_only=True)
        style=Document(single.read_text()).root
        self.assertTrue(style.find('table'))
        self.assertFalse(style.find('article'))
        self.assertEqual({p.name for p in single.parent.glob('*.html')},{'index.html'})

    def test_design_page_contains_token_rows_and_every_role(self):
        tree=Document((self.site/'design.html').read_text()).root
        tables=tree.find('table')
        roles={row.find('td')[0].text().strip() for row in tables[0].find('tr') if row.find('td')}
        self.assertEqual(roles,set(design.load_tokens()['color']))
        self.assertEqual(len(tree.find('span',**{'class':'style-swatch'})),len(roles)*3)
        self.assertTrue(any('Note' in node.text() for node in tree.find('div')))
        self.assertFalse(list(self.root.glob('.portal-*')))
