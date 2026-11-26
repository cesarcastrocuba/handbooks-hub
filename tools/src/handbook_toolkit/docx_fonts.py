"""Declare the Word font table and embed the packaged OFL fonts in the Word edition.

The DOCX names Inter for text and headings and JetBrains Mono for code, and carries both families
as obfuscated TrueType parts (ISO/IEC 29500-1, 17.8.1), so Word shows the intended typeface on a
machine without them installed. Both fonts are SIL OFL 1.1 with an installable embedding flag
(OS/2 ``fsType`` 0) and are embedded unmodified; their licences are listed in ``NOTICE.md``.
"""
from __future__ import annotations

import hashlib
from importlib.resources import files as resource_files
import re
import uuid
from xml.etree import ElementTree as ET

from .design import docx_values
from .docx_xml import NS, W, order_properties, register_namespaces

FALLBACKS = {
    'body_font': ('Segoe UI', 'Calibri', 'Arial'),
    'display_font': ('Segoe UI', 'Calibri', 'Arial'),
    'code_font': ('Consolas', 'Courier New'),
}

# Packaged TTF files per Word family, below ``render_data/fonts``, in CT_Font embed order.
EMBEDDED_FONTS: dict[str, tuple[tuple[str, str], ...]] = {
    'Inter': (
        ('embedRegular', 'inter/Inter-Regular.ttf'),
        ('embedBold', 'inter/Inter-Bold.ttf'),
        ('embedItalic', 'inter/Inter-Italic.ttf'),
        ('embedBoldItalic', 'inter/Inter-BoldItalic.ttf'),
    ),
    'JetBrains Mono': (
        ('embedRegular', 'jetbrains-mono/JetBrainsMono-Regular.ttf'),
        ('embedBold', 'jetbrains-mono/JetBrainsMono-Bold.ttf'),
        ('embedItalic', 'jetbrains-mono/JetBrainsMono-Italic.ttf'),
    ),
}
EMBED_TAGS = ('embedRegular', 'embedBold', 'embedItalic', 'embedBoldItalic')
FONT_RELATIONSHIP = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'
OBFUSCATED_FONT = 'application/vnd.openxmlformats-officedocument.obfuscatedFont'
R = '{' + NS['r'] + '}'


def font_table(existing: bytes | None = None) -> bytes:
    root = ET.fromstring(existing) if existing else ET.Element(W + 'fonts')
    values = docx_values()
    for role, fallbacks in FALLBACKS.items():
        chain = (values[role], *fallbacks)
        for index, name in enumerate(chain):
            node = next((n for n in root if n.get(W + 'name') == name), None)
            if node is None:
                node = ET.SubElement(root, W + 'font', {W + 'name': name})
            if index + 1 < len(chain):
                alternate = node.find(W + 'altName')
                if alternate is None:
                    alternate = ET.Element(W + 'altName')
                    node.insert(0, alternate)
                alternate.set(W + 'val', chain[index + 1])
    register_namespaces()
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def font_key(data: bytes) -> str:
    """A GUID derived from the font bytes, so the same font always gets the same key."""
    digest = hashlib.sha256(data).hexdigest()
    return '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'handbook-toolkit:font:' + digest)).upper() + '}'


def obfuscate(data: bytes, key: str) -> bytes:
    """XOR the first 32 bytes with the GUID bytes in reverse order (ISO/IEC 29500-1, 17.8.1)."""
    guid = bytes.fromhex(key.strip('{}').replace('-', ''))[::-1]
    head = bytes(byte ^ guid[index % 16] for index, byte in enumerate(data[:32]))
    return head + data[32:]


def embed_fonts(members: dict[str, bytes]) -> int:
    """Embed the packaged fonts of every family the font table names; return the part count.

    The font table, its relationships, the content types and ``embedTrueTypeFonts`` in the
    settings are rewritten; any earlier embedded font part is replaced.
    """
    if '[Content_Types].xml' not in members or 'word/fontTable.xml' not in members:
        return 0
    register_namespaces()
    table = ET.fromstring(members['word/fontTable.xml'])
    package = resource_files('handbook_toolkit').joinpath('render_data', 'fonts')
    for name in [name for name in members if name.startswith('word/fonts/')]:
        del members[name]
    relationships = []
    count = 0
    for node in table.findall(W + 'font'):
        for tag in EMBED_TAGS:
            for existing in node.findall(W + tag):
                node.remove(existing)
        for tag, relative in EMBEDDED_FONTS.get(node.get(W + 'name', ''), ()):
            count += 1
            data = package.joinpath(*relative.split('/')).read_bytes()
            key = font_key(data)
            part = f'fonts/font{count}.odttf'
            members['word/' + part] = obfuscate(data, key)
            identifier = f'rIdFont{count}'
            relationships.append(f'<Relationship Id="{identifier}" Type="{FONT_RELATIONSHIP}" Target="{part}"/>')
            ET.SubElement(node, W + tag, {R + 'id': identifier, W + 'fontKey': key})
    members['word/fontTable.xml'] = ET.tostring(table, encoding='utf-8', xml_declaration=True)
    if count:
        members['word/_rels/fontTable.xml.rels'] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<Relationships xmlns="{NS["pr"]}">' + ''.join(relationships) + '</Relationships>'
        ).encode('utf-8')
    else:
        members.pop('word/_rels/fontTable.xml.rels', None)
    types = members['[Content_Types].xml'].decode('utf-8')
    types = re.sub(r'<Default Extension="odttf"[^>]*/>', '', types)
    if count:
        default = f'<Default Extension="odttf" ContentType="{OBFUSCATED_FONT}"/>'
        types = re.sub(r'(<Types\b[^>]*>)', lambda match: match.group(1) + default, types, count=1)
    members['[Content_Types].xml'] = types.encode('utf-8')
    if 'word/settings.xml' in members:
        settings = ET.fromstring(members['word/settings.xml'])
        for existing in settings.findall(W + 'embedTrueTypeFonts'):
            settings.remove(existing)
        if count:
            ET.SubElement(settings, W + 'embedTrueTypeFonts')
        order_properties(settings)
        members['word/settings.xml'] = ET.tostring(settings, encoding='utf-8', xml_declaration=True)
    return count
