"""Build the opt-in, offline Quarto portal in an isolated staging directory."""
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
from typing import Any
import yaml
import xml.etree.ElementTree as ET

from . import design
from .portal_catalog import read_catalog
from .portal_design import design_page
from .portal_markup import library_page, resource

from .build_types import QUARTO_VERSION
PAGES = ('how-it-works','create','publishing','contribute','faq')
SITE_URL = 'https://cesarcastrocuba.github.io/handbooks-hub/'


def stage_theme(workspace: Path) -> dict[str, Any]:
    """Consume WP3/WP4's shared generators verbatim; no private portal theme copy."""
    folder=workspace/'.handbook-render/html'
    folder.mkdir(parents=True)
    for name,content in [('design-tokens.css',design.book_theme_css()),('handbook.css',design.book_layout_css()),
                         ('reading.css',design.reading_css()),('favicon.svg',design.favicon_svg()),
                         ('portal.css',design.portal_layout_css())]:
        (folder/name).write_text(content,encoding='utf-8')
    for relative,data in {**design.font_assets(),**design.font_licenses()}.items():
        target=workspace/'.handbook-render/fonts'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    # Preserve the old, public OFL notice URLs as well as the shared book font layout.
    for relative,data in design.font_licenses().items():
        target=workspace/'fonts'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    theme={}
    for scheme in ('light','dark'):
        name=f'handbook-{scheme}.scss'
        (workspace/name).write_text(design.book_scss(scheme),encoding='utf-8')
        theme[scheme]=['cosmo',name]
    return {'theme':theme, 'css':[str(path.relative_to(workspace)) for path in sorted(folder.glob('*.css'))],
            'toc':True, 'respect-user-color-scheme':True,'canonical-url':True,
            'include-in-header':[{'text':resource('metadata.html').replace('{{light-canvas}}',design.load_tokens()['color']['canvas']['light']).replace('{{dark-canvas}}',design.load_tokens()['color']['canvas']['dark'])}],
            'include-after-body':[{'text':resource('filter.html')}]}


def stage_site(workspace: Path, books: list[dict[str, Any]], *, design_only: bool=False) -> None:
    from .portal import HUB_URL, llms_text
    workspace.mkdir(parents=True,exist_ok=True)
    html=stage_theme(workspace)
    if design_only:
        html.pop('include-after-body')
        (workspace/'index.qmd').write_text(design_page(),encoding='utf-8')
        navigation=[{'text':'Design','href':'index.qmd'}]
    else:
        (workspace/'index.qmd').write_text(library_page(books),encoding='utf-8')
        for name in PAGES:
            (workspace/(name+'.qmd')).write_text(resource(name+'.qmd'),encoding='utf-8')
        (workspace/'design.qmd').write_text(design_page(),encoding='utf-8')
        navigation=[{'text':'Library','href':'index.qmd'},
                    {'text':'Guides','menu':[{'href':name+'.qmd'} for name in PAGES]},
                    {'text':'Design','href':'design.qmd'}, {'text':'GitHub','href':HUB_URL}]
    (workspace/'llms.txt').write_text(llms_text(books),encoding='utf-8')
    website={'title':'Handbook Hub','description':'Independent technical handbooks published as verified releases.',
             'site-url':SITE_URL,'favicon':'.handbook-render/html/favicon.svg','open-graph':True,
             'twitter-card':{'card-style':'summary'},'navbar':{'right':navigation},
             'page-footer':{'center':resource('footer.html')}}
    config={'project':{'type':'website','output-dir':'_site','resources':['llms.txt','fonts/**','.handbook-render/fonts/**']},
            'website':website,'format':{'html':html},'execute':{'enabled':False}}
    (workspace/'_quarto.yml').write_text(yaml.safe_dump(config,sort_keys=True,allow_unicode=True),encoding='utf-8')


def _run(command: list[str], workspace: Path, environment: dict[str,str]) -> str:
    try:
        result=subprocess.run(command,cwd=workspace,env=environment,capture_output=True,text=True,timeout=300)
    except (OSError,subprocess.SubprocessError) as exc:
        raise ValueError(f'cannot run Quarto portal renderer: {exc}') from exc
    if result.returncode:
        raise ValueError('Quarto portal render failed: '+(result.stderr or result.stdout)[-3000:])
    return result.stdout.strip()


def _omit_sitemap_times(site: Path) -> None:
    """Quarto uses staging mtimes despite SOURCE_DATE_EPOCH; omit optional, unknown lastmod."""
    path=site/'sitemap.xml'
    if not path.exists():
        return
    tree=ET.parse(path)
    namespace='http://www.sitemaps.org/schemas/sitemap/0.9'
    for url in tree.getroot().findall('{'+namespace+'}url'):
        for timestamp in url.findall('{'+namespace+'}lastmod'):
            url.remove(timestamp)
    ET.register_namespace('',namespace)
    tree.write(path,encoding='utf-8',xml_declaration=True)


def build_quarto_portal(catalog: Path | None, output: Path, *, design_only: bool=False) -> Path:
    books=[] if catalog is None else read_catalog(catalog)
    output=Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.portal-',dir=output.parent))
    try:
        environment=dict(os.environ,SOURCE_DATE_EPOCH='0',TZ='UTC')
        if _run(['quarto','--version'],staging,environment)!=QUARTO_VERSION:
            raise ValueError(f'Quarto {QUARTO_VERSION} is required for the Quarto portal')
        stage_site(staging,books,design_only=design_only)
        _run(['quarto','render','.','--to','html','--no-execute'],staging,environment)
        site=staging/'_site'
        if not (site/'index.html').is_file():
            raise ValueError('Quarto did not produce the portal index')
        _omit_sitemap_times(site)
        if output.exists() or output.is_symlink():
            raise FileExistsError(output)
        site.rename(output)
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    return output/'index.html'
