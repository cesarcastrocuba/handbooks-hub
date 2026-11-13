"""Declare font aliases without embedding third-party binaries in Word files."""
from __future__ import annotations

from xml.etree import ElementTree as ET

from .design import docx_values
from .docx_xml import W, register_namespaces

FALLBACKS = {
    'body_font': ('Segoe UI', 'Calibri', 'Arial'),
    'display_font': ('Georgia', 'Cambria'),
    'code_font': ('Consolas', 'Courier New'),
}


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
