"""Native Word indexes with deterministic, linked cached entries."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import shlex
from xml.etree import ElementTree as ET

from .docx_xml import W, XML_SPACE, fields, field_run, instruction_run, style_of, text_of

from .indexes import LISTS


@dataclass(frozen=True)
class Entry:
    text: str
    bookmark: str
    level: int = 1


def bookmark_name(value: str) -> str:
    """Word accepts ASCII identifiers of at most forty characters."""
    if (value and value[0].isascii() and value[0].isalpha() and len(value) <= 40
            and all(c.isascii() and (c.isalnum() or c == '_') for c in value)):
        return value
    stem = ''.join(c if c.isascii() and (c.isalnum() or c == '_') else '_' for c in value)
    digest = hashlib.sha256(value.encode()).hexdigest()[:10]
    return 'B_' + stem[:27] + '_' + digest


def reference_target(instruction: str) -> str | None:
    command = instruction.split(maxsplit=1)
    if not command or command[0].upper() not in {"REF", "PAGEREF"}:
        return None
    tokens = shlex.split(instruction, posix=False)
    if tokens and tokens[0].upper() in {'REF', 'PAGEREF'}:
        if len(tokens) < 2:
            raise ValueError('DOCX reference field has no target')
        return tokens[1].strip('"')
    return None


def normalise_bookmarks(root: ET.Element) -> None:
    mapping: dict[str, str] = {}
    for node in root.iter(W + 'bookmarkStart'):
        old = node.get(W + 'name', '')
        if old in mapping:
            raise ValueError(f'DOCX duplicate bookmark name: {old}')
        mapping[old] = bookmark_name(old)
        node.set(W + 'name', mapping[old])
    for node in root.iter(W + 'hyperlink'):
        anchor = node.get(W + 'anchor')
        if anchor is not None:
            node.set(W + 'anchor', mapping.get(anchor, anchor))
    for item in fields(root):
        target = reference_target(item.instruction)
        if target in mapping:
            tokens = shlex.split(item.instruction, posix=False)
            tokens[1] = mapping[target]
            item.instructions[0].text = ' ' + ' '.join(tokens) + ' '
            for node in item.instructions[1:]:
                node.text = ''
    for node in root.iter(W + 'fldSimple'):
        instruction = node.get(W + 'instr', '')
        target = reference_target(instruction)
        if target in mapping:
            tokens = shlex.split(instruction, posix=False)
            tokens[1] = mapping[target]
            node.set(W + 'instr', ' '.join(tokens))


def _paragraph_bookmarks(root: ET.Element) -> dict[ET.Element, list[str]]:
    active: dict[str, str] = {}
    result: dict[ET.Element, list[str]] = {}
    for node in root.iter():
        if node.tag == W + 'bookmarkStart':
            active[node.get(W + 'id', '')] = node.get(W + 'name', '')
        elif node.tag == W + 'bookmarkEnd':
            active.pop(node.get(W + 'id', ''), None)
        elif node.tag == W + 'p':
            result[node] = list(active.values()) + [
                n.get(W + 'name', '') for n in node.iter(W + 'bookmarkStart')]
    return result


def _ensure_bookmark(paragraph: ET.Element, root: ET.Element, name: str) -> str:
    existing = {node.get(W + 'name', '') for node in root.iter(W + 'bookmarkStart')}
    base, suffix = name, 1
    while name in existing:
        name = f'{base}_{suffix}'
        suffix += 1
    identifier = str(1 + max((int(n.get(W + 'id', '0'))
                             for n in root.iter(W + 'bookmarkStart')), default=0))
    start = ET.Element(W + 'bookmarkStart', {W + 'id': identifier, W + 'name': name})
    paragraph.insert(1 if paragraph.find(W + 'pPr') is not None else 0, start)
    ET.SubElement(paragraph, W + 'bookmarkEnd', {W + 'id': identifier})
    return name


def _caption_kind(paragraph: ET.Element) -> str | None:
    if style_of(paragraph) not in {'Caption', 'TableCaption', 'ImageCaption', 'ListingCaption'}:
        return None
    text = text_of(paragraph)
    for prefix, caption_label, _title, _letter in LISTS:
        if text.startswith(caption_label):
            return prefix
    return {'TableCaption': 'tbl', 'ImageCaption': 'fig', 'ListingCaption': 'lst'}.get(style_of(paragraph))


def _tc_field(paragraph: ET.Element, text: str, letter: str) -> None:
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    paragraph.extend((field_run('begin', hidden=True),
                      instruction_run(f'TC "{escaped}" \\f {letter} \\l 1', hidden=True),
                      field_run('separate', hidden=True), field_run('end', hidden=True)))


def _collect_entries(root: ET.Element) -> tuple[dict[str, list[Entry]], list[Entry]]:
    captions: dict[str, list[Entry]] = {kind: [] for kind, _caption, _title, _letter in LISTS}
    headings: list[Entry] = []
    marks = _paragraph_bookmarks(root)
    for index, paragraph in enumerate(list(root.iter(W + 'p'))):
        style = style_of(paragraph)
        kind = _caption_kind(paragraph)
        is_heading = style in {'Heading1', 'Heading2', 'Heading3'}
        if kind is None and not is_heading:
            continue
        text = text_of(paragraph)
        if not text:
            continue
        candidates = marks.get(paragraph, [])
        if kind:
            preferred = [v for v in candidates if v.startswith(kind + '-')]
        else:
            preferred = candidates[-1:]
        bookmark = preferred[-1] if preferred else _ensure_bookmark(
            paragraph, root, f'Caption_{index}' if kind else f'Heading_{index}')
        entry = Entry(text, bookmark, int(style[-1]) if is_heading else 1)
        if kind:
            captions[kind].append(entry)
            letter = next(letter for prefix, _caption, _title, letter in LISTS if prefix == kind)
            _tc_field(paragraph, text, letter)
        else:
            headings.append(entry)
    return captions, headings


def _entry_paragraph(entry: Entry) -> ET.Element:
    paragraph = ET.Element(W + 'p')
    properties = ET.SubElement(paragraph, W + 'pPr')
    ET.SubElement(properties, W + 'pStyle', {W + 'val': f'TOC{entry.level}'})
    link = ET.SubElement(paragraph, W + 'hyperlink', {W + 'anchor': entry.bookmark})
    run = ET.SubElement(link, W + 'r')
    ET.SubElement(ET.SubElement(run, W + 'rPr'), W + 'rStyle', {W + 'val': 'Hyperlink'})
    ET.SubElement(run, W + 't', {XML_SPACE: 'preserve'}).text = entry.text
    return paragraph


def cached_field(instruction: str, entries: list[Entry]) -> list[ET.Element]:
    paragraphs = [_entry_paragraph(entry) for entry in entries] or [ET.Element(W + 'p')]
    first = paragraphs[0]
    offset = 1 if first.find(W + 'pPr') is not None else 0
    for node in reversed((field_run('begin'), instruction_run(instruction), field_run('separate'))):
        first.insert(offset, node)
    paragraphs[-1].append(field_run('end'))
    return paragraphs


def _title(text: str) -> ET.Element:
    paragraph = ET.Element(W + 'p')
    ET.SubElement(ET.SubElement(paragraph, W + 'pPr'), W + 'pStyle', {W + 'val': 'TOCHeading'})
    ET.SubElement(ET.SubElement(paragraph, W + 'r'), W + 't').text = text
    return paragraph


def add_indexes(root: ET.Element) -> None:
    """Replace only Pandoc index SDTs, preserving its Contents instruction."""
    body = root.find(W + 'body')
    if body is None:
        raise ValueError('DOCX has no document body')
    captions, headings = _collect_entries(root)
    toc = None
    instruction = ''
    for child in list(body):
        if child.tag != W + 'sdt':
            continue
        instructions = [field.instruction for field in fields(child)]
        toc_instruction = next((value for value in instructions if value.startswith('TOC ')), None)
        if toc_instruction is None:
            continue
        if '\\o ' in toc_instruction:
            toc, instruction = child, toc_instruction
        else:
            body.remove(child)
    if toc is not None:
        content = toc.find(W + 'sdtContent')
        if content is None:
            raise ValueError('DOCX Contents field has no content')
        tokens = shlex.split(instruction, posix=False)
        bounds = tokens[tokens.index('\\o') + 1].strip('"').split('-')
        minimum, maximum = (int(value) for value in bounds)
        selected = [entry for entry in headings if minimum <= entry.level <= maximum]
        content[:] = [_title('Contents'), *cached_field(instruction, selected)]
        index = list(body).index(toc) + 1
    else:
        # A book may explicitly disable Contents. Preserve that choice while
        # inserting caption lists before the first manuscript block.
        index = next((i for i, child in enumerate(body)
                      if child.tag == W + 'bookmarkStart' or style_of(child).startswith('Heading')),
                     len(body) - (1 if body.find(W + 'sectPr') is not None else 0))
    for prefix, _caption, label, letter in LISTS:
        if captions[prefix]:
            blocks = [_title(label), *cached_field(f'TOC \\h \\z \\f {letter}', captions[prefix])]
            for block in blocks:
                body.insert(index, block)
                index += 1
    normalise_bookmarks(root)
