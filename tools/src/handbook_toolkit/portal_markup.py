"""Bind validated catalog data to packaged, non-executable library templates."""
from html import escape
import re
from importlib.resources import files
from string import Template
from typing import Any

from . import stars


# Stroke icons drawn in currentColor, so they follow both themes and need no icon font: the web
# font subsets do not carry symbols such as a check mark or a star.
ICONS = {
    'check': '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    'hash': '<path d="M5 9h14M5 15h14M10 4 8 20M16 4l-2 16"/>',
    'layout': '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M10 10v10"/>',
    'shield': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    'pin': '<path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5"/>',
    'design': '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>',
    'people': '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.8.4 5 2.8 5 5.8"/>',
    'open': '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.7-1.5"/>',
    'editions': '<rect x="3" y="5" width="11" height="14" rx="1.5"/><path d="M17 7h2.5A1.5 1.5 0 0 1 21 8.5v9a1.5 1.5 0 0 1-1.5 1.5H17M7 9h3M7 13h3"/>',
    'home': '<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>',
    'pencil': '<path d="M4 20h4L20 8l-4-4L4 16z"/>',
    'star': '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z"/>',
}
ICON = re.compile(r'\{\{icon:([a-z]+)\}\}')


def icon(name: str) -> str:
    return ('<svg class="icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            + ICONS[name] + '</svg>')


def resource(name: str) -> str:
    text = files('handbook_toolkit').joinpath('render_data/portal', name).read_text(encoding='utf-8')
    return ICON.sub(lambda match: icon(match.group(1)), text)


def text(value: Any) -> str:
    # Prevent untrusted newlines from ending a Pandoc raw-HTML fence. The HTML reader restores them.
    return escape(str(value), quote=True).replace('\r', '&#13;').replace('\n', '&#10;')


def template(name: str, **values: str) -> str:
    return Template(resource(name)).substitute(values)


def link(url: str, label: str, *, css: str = '', accessible: str | None = None) -> str:
    return template('link.html', url=text(url), text=text(label),
                    label=text(accessible or label), **{'class': text(css)})


def card(book: dict[str, Any]) -> str:
    from .portal import FORMATS, _repository_url, authors_text
    release = book['latest_release']
    repository = _repository_url(release['url'])
    authors = list(book.get('authors', []))
    byline = text(authors_text(authors)) if authors else ''
    values = {name: text(book[name]) for name in ('title', 'summary', 'reading_url')}
    values.update(version=text(release['version']), date=text(release['published_at']),
                  category=text(book['categories'][0]), category_keys=' '.join(book['categories']),
                  authors_attr=text(' | '.join(authors)),
                  cover_author=f'<span class="cover-author">{byline}</span>' if byline else '',
                  authors_line=f'<p class="authors">By {byline}</p>' if byline else '',
                  tags=''.join(template('tag.html', category=text(category.title())) for category in book['categories']),
                  archived=resource('archived.html') if book['status']=='archived' else '',
                  source=link(repository, 'Source and issues') if repository else '',
                  release_url=text(release['url']), manifest_url=text(release['manifest_url']),
                  checksums_url=text(release['checksums_url']))
    owner_name = stars.github_repository(repository)
    values['star'] = (stars.star_link(repository, owner_name, stars.star_count(owner_name))
                      if repository and owner_name else '')
    assets = release.get('assets', {})
    editions = ''.join(link(assets[role], label, css='fmt', accessible=f'Download {book["title"]} as {label}')
                       for role, label in FORMATS.items() if role in assets)
    extras = release.get('extras')
    if extras:
        editions += link(extras['archive'], 'Extras', css='fmt',
                         accessible=f'Download {book["title"]} extras')
        values['extras_checksums'] = link(extras['checksums_url'], 'Extras checksums')
    else:
        values['extras_checksums'] = ''
    values['formats'] = template('formats.html',editions=editions) if editions else ''
    return template('card.html', **values)


def library_page(books: list[dict[str, Any]]) -> str:
    from .portal import CATEGORIES
    categories = sorted({category for book in books for category in book['categories']})
    if books:
        controls = ''.join(template('category.html', category=text(category), label=text(category.title())) for category in categories)
        author_names = sorted({name for book in books for name in book.get('authors', [])},
                              key=lambda value: (value.casefold(), value))
        author_options = ''.join(template('author.html', author=text(name), label=text(name))
                                 for name in author_names)
        content = '```{=html}\n' + template('library.html', categories=controls,
                       authors=author_options,
                       count=str(len(books)), noun='handbook' if len(books)==1 else 'handbooks',
                       cards=''.join(map(card, books))) + '\n```'
    else:
        content = resource('empty.qmd')
    planned = sorted(CATEGORIES-set(categories))
    note = '**Planned topics (not listed books):** ' + ', '.join(category.title() for category in planned) if planned else ''
    if note:
        note = '::: {.planned}\n\n' + note + '\n\n:::'
    return resource('index.qmd').replace('{{library}}', content).replace('{{planned}}', note)
