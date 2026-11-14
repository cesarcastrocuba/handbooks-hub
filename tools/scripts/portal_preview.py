#!/usr/bin/env python3
"""Build both portal engines and publish reproducible parity evidence and browser screenshots."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urlsplit, unquote

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from handbook_toolkit import design
from handbook_toolkit.portal import build_portal, _repository_url
from handbook_toolkit.portal_catalog import read_catalog


class Links(HTMLParser):
    def __init__(self,html: str):
        super().__init__(convert_charrefs=True)
        self.links: set[str]=set();self.ids: set[str]=set()
        self.feed(html)
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='a' and values.get('href'):self.links.add(values['href'])
        if values.get('id'):self.ids.add(values['id'])


def weights(site: Path) -> dict[str,int]:
    return {suffix:sum(path.stat().st_size for path in site.rglob('*') if path.is_file() and path.suffix==suffix)
            for suffix in ('.html','.css','.js','.woff2','.woff','.ttf','.otf')}


def link_parity(legacy: Path,candidate: Path) -> dict[str,object]:
    old=Links((legacy/'index.html').read_text())
    pages={path.relative_to(candidate).as_posix():Links(path.read_text()) for path in candidate.rglob('*.html')}
    public={link for page in pages.values() for link in page.links if link.startswith('https://')}
    missing=[]
    for link in old.links:
        parsed=urlsplit(link)
        if parsed.scheme:
            if link not in public:missing.append(link)
        elif parsed.fragment and not parsed.path:
            if unquote(parsed.fragment) not in pages['index.html'].ids:missing.append(link)
        elif parsed.path not in ('.','./','') and not (candidate/unquote(parsed.path)).is_file():
            missing.append(link)
    return {'pass':not missing,'missing':sorted(missing),'checked':len(old.links)}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


@contextmanager
def serve(root: Path):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(root)))
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    try:yield f'http://127.0.0.1:{server.server_port}/'
    finally:server.shutdown();server.server_close();worker.join()


def browser_checks(root: Path,fixture: bool) -> dict:
    from playwright.sync_api import sync_playwright
    result={};screens=root/'screenshots';screens.mkdir()
    remote=[]
    with serve(root) as base, sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        try:
            for engine in ('legacy','quarto'):
                for width,label in ((1440,'desktop'),(390,'phone')):
                    for scheme in ('light','dark'):
                        context=browser.new_context(viewport={'width':width,'height':1800},color_scheme=scheme,reduced_motion='reduce')
                        def guard(route):
                            if route.request.url.startswith(base):route.continue_()
                            else:remote.append(route.request.url);route.abort()
                        context.route('**/*',guard)
                        page=context.new_page();loaded={}
                        page.on('response',lambda response:loaded.update({response.url:int(response.headers.get('content-length','0'))}) if urlsplit(response.url).path.endswith(('.html','.css','.js','.woff2','.woff','.ttf','.otf')) else None)
                        page.goto(base+engine+'/index.html',wait_until='networkidle');page.evaluate('document.fonts.ready')
                        key=f'{engine}:{label}:{scheme}'
                        result[key]={'width':page.evaluate('document.documentElement.scrollWidth'),'viewport':width,'loaded_bytes':sum(loaded.values())}
                        pairs=page.evaluate("""() => {
                          const bg=(e)=>{while(e){let c=getComputedStyle(e).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent')return c;e=e.parentElement;}throw Error('No canvas');};
                          let pairs={};for(let [name,fg,b] of [['body','body','body'],['summary','.book .summary','.book'],['link','.book .links a','.book'],['selected','button[aria-pressed=true]','button[aria-pressed=true]'],['footer','footer','footer']]){
                            let e=document.querySelector(fg),back=document.querySelector(b);if(e&&back)pairs[name]=[getComputedStyle(e).color,bg(back)];}
                          return pairs;
                        }""")
                        ratios={}
                        for role,pair in pairs.items():
                            def rgb(value):
                                return '#'+''.join(f'{int(float(channel.strip())):02X}' for channel in value.split('(',1)[1].split(')',1)[0].split(',')[:3])
                            ratio=design.contrast_ratio(*map(rgb,pair))
                            if ratio<4.5:raise ValueError(f'component contrast failed: {key} {role} {ratio:.2f}')
                            ratios[role]=round(ratio,2)
                        result[key]['contrast']=ratios
                        if engine=='quarto' and result[key]['width']>width:raise ValueError(f'candidate page overflow: {key}')
                        page.screenshot(path=str(screens/f'{key.replace(":",".")}.png'))
                        page.keyboard.press('Tab')
                        focused=page.evaluate('({tag:document.activeElement.tagName,text:document.activeElement.textContent,outline:getComputedStyle(document.activeElement).outlineStyle})')
                        if focused['tag']!='A' or 'Skip' not in focused['text']:raise ValueError(f'skip link is not first: {key}')
                        if focused['outline']=='none':raise ValueError(f'no visible keyboard outline: {key}')
                        result[key]['skip']=True
                        if page.locator('#search').count():
                            for query,expected in [('missing-portal-fixture',0),('',len(read_catalog(root/'catalog.json')))]:
                                page.locator('#search').fill(query)
                                if page.locator('article.book:visible').count()!=expected:raise ValueError(f'search failed: {key}')
                        if engine=='quarto':
                            for name in ('design','how-it-works'):
                                page.goto(base+engine+'/'+name+'.html',wait_until='networkidle');page.evaluate('document.fonts.ready')
                                page.screenshot(path=str(screens/f'{name}.{label}.{scheme}.png'))
                                if name=='design':
                                    for anchor,suffix in (('type-scale','components'),('buttons','controls')):
                                        page.locator('#'+anchor).evaluate("el=>el.scrollIntoView({block:'start'})")
                                        page.screenshot(path=str(screens/f'design-{suffix}.{label}.{scheme}.png'))
                            page.locator('#quarto-search').click()
                            page.locator('.aa-Input').fill('withdrawal')
                            match=page.locator('.aa-Panel a[href*="publishing.html"]').first
                            match.wait_for(state='visible')
                            page.screenshot(path=str(screens/f'guide-search.{label}.{scheme}.png'))
                            match.click();page.wait_for_load_state('networkidle')
                            if not urlsplit(page.url).path.endswith('publishing.html'):
                                raise ValueError('native guide search did not reach its page')
                            result[key]['guide_search']=True
                        context.close()
                if fixture:
                    for width,label in ((1440,'desktop'),(390,'phone')):
                        for scheme in ('light','dark'):
                            context=browser.new_context(viewport={'width':width,'height':1800},color_scheme=scheme,reduced_motion='reduce')
                            context.route('**/*',guard)
                            tab=context.new_page();tab.goto(base+'fixture-'+engine+'/index.html',wait_until='networkidle');tab.evaluate('document.fonts.ready')
                            if engine=='quarto' and tab.evaluate('document.documentElement.scrollWidth')>width:
                                raise ValueError(f'two-book mobile overflow: {scheme}')
                            tab.screenshot(path=str(screens/f'fixture.{engine}.{label}.{scheme}.png'))
                            context.close()
                    page=browser.new_page(viewport={'width':1440,'height':1800})
                    page.route('**/*',guard)
                    page.goto(base+'fixture-'+engine+'/index.html',wait_until='networkidle')
                    counts=[]
                    for query,expected in [('cafe',1),('CAFÉ',1),('zurich security',1),('missing',0),('',2)]:
                        page.locator('#search').fill(query);actual=page.locator('article.book:visible').count();counts.append(actual)
                        if actual!=expected:raise ValueError(f'case/accent/multiword search failed: {engine} {query}')
                    page.locator('[data-filter=security]').click()
                    if page.locator('article.book:visible').count()!=1:raise ValueError('category filter failed')
                    page.locator('#search').fill('cafe')
                    if page.locator('article.book:visible').count():raise ValueError('category/search intersection failed')
                    page.locator('#search').fill('');page.locator('[data-filter=all]').click()
                    page.locator('#sort').select_option('za')
                    titles=page.locator('article.book:visible').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.title)')
                    if titles!=['Zürich Security','Café Authoring']:raise ValueError('descending title sort failed')
                    page.locator('#sort').select_option('latest')
                    if page.locator('article.book:visible').first.get_attribute('data-title')!='Zürich Security':raise ValueError('latest sort failed')
                    result[engine+':fixture']={'counts':counts,'category':True,'sort':True}
                    page.close()
            if remote:raise ValueError('external resources requested: '+str(sorted(set(remote))))
        finally:browser.close()
    return result


def preview(catalog: Path,output: Path) -> dict:
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    books=read_catalog(catalog);output.mkdir(parents=True)
    (output/'catalog.json').write_bytes(catalog.read_bytes())
    for engine in ('legacy','quarto'):build_portal(catalog,output/engine,engine=engine)
    fixture=bool(books)
    if fixture:
        first=deepcopy(books[0]);first.update(title='Café Authoring',categories=['authoring'])
        first['latest_release']['published_at']='2026-01-01'
        second=deepcopy(first);second.update(id='security-fixture',slug='security-fixture',title='Zürich Security',categories=['security'],reading_url='https://example.org/security/')
        second['latest_release']['published_at']='2026-01-02'
        old_repository=_repository_url(second['latest_release']['url'])
        assert old_repository is not None
        for key in ('url','manifest_url','checksums_url'):
            second['latest_release'][key]=second['latest_release'][key].replace(old_repository,'https://github.com/portal-fixtures/security')
        second['latest_release']['assets']={key:value.replace(old_repository,'https://github.com/portal-fixtures/security') for key,value in second['latest_release'].get('assets',{}).items()}
        path=output/'fixture.json';path.write_text(json.dumps({'schema_version':'1.1','books':[first,second]}))
        for engine in ('legacy','quarto'):build_portal(path,output/('fixture-'+engine),engine=engine)
    before=weights(output/'legacy');after=weights(output/'quarto')
    report={'links':link_parity(output/'legacy',output/'quarto'),
            'llms':{'pass':(output/'legacy/llms.txt').read_bytes()==(output/'quarto/llms.txt').read_bytes()},
            'weight':{'before':before,'after':after,'pass':sum(after.values())<=sum(before.values())},
            'browser':browser_checks(output,fixture)}
    (output/'parity.json').write_text(json.dumps(report,indent=2)+'\n')
    summary=['# Portal preview and parity','', '| Row | Result |','| --- | --- |',
             f'| Existing links ({report["links"]["checked"]}) | {"PASS" if report["links"]["pass"] else "FAIL"} |',
             f'| llms.txt bytes | {"PASS" if report["llms"]["pass"] else "FAIL"} |',
             '| Edition links, search, categories, sorting, keyboard and mobile | Browser/structural checks recorded in parity.json |',
             f'| HTML + CSS + JS + fonts | {sum(before.values())} → {sum(after.values())} bytes: {"PASS" if report["weight"]["pass"] else "FAIL"} |','',
             'Page weight fails: the deployed default remains legacy. Quarto is opt-in (--engine quarto).',
             'Both site trees and screenshots are included. fixture-* are invented test data, never approved catalog entries.',
             'The design and guide screenshots show the Quarto candidate in light/dark at 1440/390.']
    (output/'PREVIEW.md').write_text('\n'.join(summary)+'\n')
    if not report['links']['pass'] or not report['llms']['pass']:raise ValueError('functional parity failed; see parity.json')
    return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,default=Path('catalog/catalog.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:preview(args.catalog.resolve(),args.output.resolve())
    except (OSError,ValueError) as exc:parser.exit(2,f'portal-preview: {exc}\n')
    print((args.output/'PREVIEW.md').read_text())
    return 0

if __name__=='__main__':raise SystemExit(main())
