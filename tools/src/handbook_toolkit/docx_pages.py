"""Cache native index pages from named PDF destinations, without rewriting the DOCX in LO."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .build_types import BuildError
from .docx_fields import _ensure_bookmark, cached_links, set_cached_pages
from .docx_post import _write_package
from .docx_xml import W, order_properties, register_namespaces

PDF_FILTER = 'pdf:writer_pdf_Export:{"ExportBookmarksToPDFDestination":{"type":"boolean","value":"true"}}'


class ConvergenceError(BuildError):
    """Pagination changed after writing the final cache; never publish guessed numbers."""


def _run(command: list[str], *, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(f'DOCX page probe failed: {exc}') from exc
    if result.returncode:
        raise BuildError('DOCX page probe failed: ' + (result.stderr or result.stdout)[-2000:])
    return result.stdout


def font_environment(fonts: Path, directory: Path) -> dict[str, str]:
    """Only packaged print fonts, with a private cache and no host fontconfig include."""
    if not list(fonts.rglob('*.ttf')):
        raise BuildError('DOCX page probe has no staged toolkit fonts')
    root = ET.Element('fontconfig')
    ET.SubElement(root, 'dir').text = str(fonts.resolve())
    ET.SubElement(root, 'cachedir').text = str(directory / 'font-cache')
    # The DOCX uses original family names; packaged Sans/Serif TTFs have OFL-safe names.
    for original, packaged in [('Source Sans 3', 'Handbook Sans'), ('Source Serif 4', 'Handbook Serif')]:
        alias = ET.SubElement(root, 'alias')
        ET.SubElement(alias, 'family').text = original
        ET.SubElement(ET.SubElement(alias, 'prefer'), 'family').text = packaged
    config = directory / 'fonts.conf'
    ET.ElementTree(root).write(config, encoding='utf-8', xml_declaration=True)
    return dict(os.environ, FONTCONFIG_FILE=str(config), FONTCONFIG_PATH=str(directory), TZ='UTC')


def export_pdf(docx: Path, directory: Path, *, env: dict[str, str] | None = None) -> Path:
    """Export named destinations with a private profile, bounded runtime and loud failures."""
    directory.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='libreoffice-profile-') as temporary:
        profile = Path(temporary)
        _run(['soffice', '-env:UserInstallation=' + profile.as_uri(), '--headless',
              '--convert-to', PDF_FILTER, '--outdir', str(directory), str(docx.resolve())], env=env)
    output = directory / (docx.stem + '.pdf')
    if not output.is_file():
        raise BuildError('DOCX page probe: LibreOffice did not produce a PDF')
    return output


def destination_name(bookmark: str) -> str:
    """LO's PDF name encoding for our validated ASCII alphanumeric/underscore bookmarks."""
    if not bookmark or not all(c.isascii() and (c.isalnum() or c == '_') for c in bookmark):
        raise BuildError(f'DOCX page probe: invalid bookmark {bookmark!r}')
    return bookmark.replace('_', '5F')


def destination_pages(pdf: Path, bookmarks: set[str]) -> dict[str, int]:
    names = {destination_name(bookmark): bookmark for bookmark in bookmarks}
    if len(names) != len(bookmarks):
        raise BuildError('DOCX page probe: ambiguous encoded bookmark names')
    result: dict[str, int] = {}
    for line in _run(['pdfinfo', '-dests', str(pdf)]).splitlines():
        pieces = line.strip().split(None, 1)
        if not pieces or not pieces[0].isdecimal():
            continue
        quoted = line.rsplit('"', 2)
        if len(quoted) != 3 or quoted[1] not in names:
            continue
        bookmark = names[quoted[1]]
        page = int(pieces[0])
        if page < 1 or (bookmark in result and result[bookmark] != page):
            raise BuildError('DOCX page probe: conflicting or invalid destination page')
        result[bookmark] = page
    missing = bookmarks - result.keys()
    if missing:
        raise BuildError('DOCX page probe: missing bookmark destinations: ' + ', '.join(sorted(missing)))
    return result


@dataclass(frozen=True)
class Section:
    marker: str
    start: int | None
    bookmarks: frozenset[str]


def numbering_sections(root: ET.Element) -> list[Section]:
    """Track decimal restarts by actual section-start bookmarks, not physical-page guesses."""
    body = root.find(W + 'body')
    if body is None:
        raise BuildError('DOCX page probe: no body')
    groups: list[tuple[list[ET.Element], ET.Element | None]] = []
    blocks: list[ET.Element] = []
    for block in body:
        if block.tag == W + 'sectPr':
            groups.append((blocks, block))
            blocks = []
            continue
        blocks.append(block)
        section = block.find(W + 'pPr/' + W + 'sectPr')
        if section is not None:
            groups.append((blocks, section))
            blocks = []
    if blocks:
        groups.append((blocks, None))
    result = []
    format_name = 'decimal'
    for index, (group, properties) in enumerate(groups):
        numbering = properties.find(W + 'pgNumType') if properties is not None else None
        start = None
        if numbering is not None:
            format_name = numbering.get(W + 'fmt', format_name)
            if numbering.get(W + 'chapStyle') or numbering.get(W + 'chapSep'):
                raise BuildError('DOCX page probe does not support chapter-prefixed page numbers')
            value = numbering.get(W + 'start')
            if value is not None:
                if not value.isdecimal() or int(value) < 1:
                    raise BuildError('DOCX page probe: invalid page-number restart')
                start = int(value)
        if format_name != 'decimal':
            raise BuildError('DOCX page probe supports decimal page numbering only; found ' + format_name)
        paragraphs = [p for block in group for p in block.iter(W + 'p')]
        if not paragraphs:
            continue
        marker = _ensure_bookmark(paragraphs[0], root, f'PaginationSection{index}')
        marks = frozenset(n.get(W + 'name', '') for block in group for n in block.iter(W + 'bookmarkStart'))
        result.append(Section(marker, start, marks))
    return result


def logical_pages(physical: dict[str, int], sections: list[Section], targets: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    offset = 0
    for section in sections:
        if section.start is not None:
            offset = section.start - physical[section.marker]
        for target in section.bookmarks & targets:
            value = physical[target] + offset
            if value < 1:
                raise BuildError('DOCX page probe calculated an invalid logical page')
            result[target] = str(value)
    if result.keys() != targets:
        raise BuildError('DOCX page probe cannot assign every cached entry to a section')
    return result


def cache_page_numbers(path: Path, fonts: Path, *, required: bool = False, compresslevel: int | None = 9) -> dict[str, str]:
    """Probe/cache/verify; missing or failed optional tools leave honest title-only caches."""
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(members['word/document.xml'])
    original = ET.tostring(root)
    targets = {link.get(W + 'anchor', '') for link in cached_links(root)}
    version = 'unavailable'

    def save() -> None:
        register_namespaces()
        order_properties(root)
        members['word/document.xml'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        _write_package(path, members, compresslevel=compresslevel)

    try:
        if not shutil.which('soffice') or not shutil.which('pdfinfo'):
            raise BuildError('LibreOffice soffice and pdfinfo are required for cached page numbers')
        version = _run(['soffice', '--version']).strip()
        sections = numbering_sections(root)
        marks = targets | {section.marker for section in sections}
        placeholders = {target: '1' for target in targets}
        with tempfile.TemporaryDirectory(prefix='docx-pages-', dir=path.parent) as temporary:
            directory = Path(temporary)
            environment = font_environment(fonts, directory)

            def probe(label: str) -> dict[str, str]:
                pdf = export_pdf(path, directory / label, env=environment)
                return logical_pages(destination_pages(pdf, marks), sections, targets)

            set_cached_pages(root, placeholders)
            save()
            pages = probe('width-probe')
            # Width cannot be known before pagination. Stabilize it before the final two passes.
            if any(len(pages[key]) != len(placeholders[key]) for key in targets):
                set_cached_pages(root, {key: '8' * len(value) for key, value in pages.items()})
                save()
                measured = probe('sized-probe')
                if any(len(measured[key]) != len(pages[key]) for key in targets):
                    raise ConvergenceError('DOCX page-number placeholder widths did not converge')
                pages = measured
            set_cached_pages(root, pages)
            save()
            if probe('verification') != pages:
                raise ConvergenceError('DOCX cached page numbers did not converge with bookmark destinations')
        return {'libreoffice': version, 'docx_page_numbers': 'verified bookmark destinations (LibreOffice pagination)'}
    except ConvergenceError:
        raise
    except (BuildError, OSError, ValueError) as exc:
        if required:
            raise BuildError(f'required DOCX page numbers failed: {exc}') from exc
        root = ET.fromstring(original)
        set_cached_pages(root, None)
        save()
        reason = 'titles-only (page probe unavailable or failed; see build stderr)'
        print('DOCX page numbers: ' + reason + ': ' + str(exc), file=sys.stderr)
        return {'libreoffice': version, 'docx_page_numbers': reason}
