"""Structural invariants for the Word payload, independent of a viewer."""
from __future__ import annotations

from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .docx_fields import bookmark_name, reference_target
from .docx_xml import W, ORDER, fields


def _properties(root: ET.Element) -> None:
    containers = {'p': 'pPr', 'r': 'rPr', 'tbl': 'tblPr', 'tr': 'trPr', 'tc': 'tcPr'}
    for node in root.iter():
        name = node.tag.removeprefix(W)
        if name in containers:
            properties = node.findall(W + containers[name])
            if len(properties) > 1 or (properties and node[0] is not properties[0]):
                raise ValueError(f'DOCX {name} has duplicate or misplaced properties')
        if not node.tag.startswith(W):
            continue
        name = node.tag.removeprefix(W)
        if name not in ORDER:
            continue
        allowed = ORDER[name].split()
        ranks = {W + tag: index for index, tag in enumerate(allowed)}
        previous = -1
        seen: set[str] = set()
        for child in node:
            if not child.tag.startswith(W):
                continue
            if child.tag not in ranks:
                raise ValueError(f'DOCX {name} has invalid child {child.tag.removeprefix(W)}')
            rank = ranks[child.tag]
            if rank < previous or child.tag in seen:
                raise ValueError(f'DOCX {name} has duplicate or out-of-order properties')
            previous = rank
            seen.add(child.tag)


def _styles(roots: list[ET.Element], styles: ET.Element) -> None:
    defined: dict[str, str] = {}
    for node in styles.findall(W + 'style'):
        identifier = node.get(W + 'styleId', '')
        if not identifier or identifier in defined:
            raise ValueError(f'DOCX duplicate or empty style ID: {identifier}')
        defined[identifier] = node.get(W + 'type', '')
    if not defined:
        raise ValueError('DOCX styles part has no style definitions')
    for root in roots:
        for node in root.iter():
            expected = {W + 'pStyle': 'paragraph', W + 'rStyle': 'character',
                        W + 'tblStyle': 'table'}.get(node.tag)
            if expected and defined.get(node.get(W + 'val', '')) != expected:
                raise ValueError('DOCX used style is undefined or has the wrong type: ' +
                                 node.get(W + 'val', ''))


def _references(roots: list[ET.Element]) -> None:
    bookmarks: set[str] = set()
    for root in roots:
        for node in root.iter(W + 'bookmarkStart'):
            name = node.get(W + 'name', '')
            if not name or name != bookmark_name(name) or name in bookmarks:
                raise ValueError(f'DOCX bookmark name is invalid or duplicated: {name}')
            bookmarks.add(name)
    for root in roots:
        for node in root.iter(W + 'hyperlink'):
            target = node.get(W + 'anchor')
            if target is not None and target not in bookmarks:
                raise ValueError(f'DOCX hyperlink anchor has no bookmark: {target}')
        instructions = [item.instruction for item in fields(root)]
        instructions.extend(node.get(W + 'instr', '') for node in root.iter(W + 'fldSimple'))
        for instruction in instructions:
            target = reference_target(instruction)
            if target is not None and target not in bookmarks:
                raise ValueError(f'DOCX reference field has no bookmark: {target}')


def validate_docx(archive: ZipFile) -> None:
    """Raise ValueError for a malformed style, property, field or reference."""
    if 'word/styles.xml' not in archive.namelist():
        raise ValueError('DOCX styles part is missing')
    roots = [ET.fromstring(archive.read(name)) for name in sorted(archive.namelist())
             if name.startswith('word/') and name.endswith('.xml')]
    styles = ET.fromstring(archive.read('word/styles.xml'))
    _styles(roots, styles)
    for root in roots:
        _properties(root)
    _references(roots)
