"""Bind validated catalog data to packaged, non-executable library templates."""
from html import escape
from importlib.resources import files
from string import Template
from typing import Any


def resource(name: str) -> str:
    return files('handbook_toolkit').joinpath('render_data/portal', name).read_text(encoding='utf-8')


def text(value: Any) -> str:
    # Prevent untrusted newlines from ending a Pandoc raw-HTML fence. The HTML reader restores them.
    return escape(str(value), quote=True).replace('\r', '&#13;').replace('\n', '&#10;')


def template(name: str, **values: str) -> str:
    return Template(resource(name)).substitute(values)


def link(url: str, label: str, *, css: str = '', accessible: str | None = None) -> str:
    return template('link.html', url=text(url), text=text(label),
                    label=text(accessible or label), **{'class': text(css)})


def card(book: dict[str, Any]) -> str:
    from .portal import FORMATS, _repository_url
    release = book['latest_release']
    repository = _repository_url(release['url'])
    values = {name: text(book[name]) for name in ('title', 'summary', 'reading_url')}
    values.update(version=text(release['version']), date=text(release['published_at']),
                  category=text(book['categories'][0]), category_keys=' '.join(book['categories']),
                  tags=''.join(template('tag.html', category=text(category.title())) for category in book['categories']),
                  archived=resource('archived.html') if book['status']=='archived' else '',
                  source=link(repository, 'Source and issues') if repository else '',
                  release_url=text(release['url']), manifest_url=text(release['manifest_url']),
                  checksums_url=text(release['checksums_url']))
    assets = release.get('assets', {})
    editions = ''.join(link(assets[role], label, css='fmt', accessible=f'Download {book["title"]} as {label}')
                       for role, label in FORMATS.items() if role in assets)
    values['formats'] = template('formats.html',editions=editions) if editions else ''
    return template('card.html', **values)


def library_page(books: list[dict[str, Any]]) -> str:
    from .portal import CATEGORIES
    categories = sorted({category for book in books for category in book['categories']})
    if books:
        controls = ''.join(template('category.html', category=text(category), label=text(category.title())) for category in categories)
        content = '```{=html}\n' + template('library.html', categories=controls,
                       count=str(len(books)), noun='handbook' if len(books)==1 else 'handbooks',
                       cards=''.join(map(card, books))) + '\n```'
    else:
        content = resource('empty.qmd')
    planned = sorted(CATEGORIES-set(categories))
    note = '**Planned topics (not listed books):** ' + ', '.join(category.title() for category in planned) if planned else ''
    return resource('index.qmd').replace('{{library}}', content).replace('{{planned}}', note)
