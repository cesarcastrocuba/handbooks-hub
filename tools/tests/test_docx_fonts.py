"""The Word edition embeds the packaged Inter and JetBrains Mono fonts."""
from __future__ import annotations

from importlib.resources import files as resource_files
import unittest
from xml.etree import ElementTree as ET

import support  # noqa: F401
from handbook_toolkit.docx_fonts import EMBEDDED_FONTS, embed_fonts, font_table, obfuscate
from handbook_toolkit.docx_xml import NS, W

R = '{' + NS['r'] + '}'
PR = '{' + NS['pr'] + '}'
CT = '{' + NS['ct'] + '}'
FONTS = resource_files('handbook_toolkit').joinpath('render_data', 'fonts')


def package() -> dict[str, bytes]:
    return {
        '[Content_Types].xml': (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Types xmlns="{NS["ct"]}"><Default Extension="xml" ContentType="application/xml"/></Types>'
        ).encode(),
        'word/fontTable.xml': font_table(),
        'word/settings.xml': f'<w:settings xmlns:w="{NS["w"]}"><w:zoom w:percent="100"/></w:settings>'.encode(),
    }


class EmbeddedFontTests(unittest.TestCase):
    def setUp(self) -> None:
        self.members = package()
        self.count = embed_fonts(self.members)
        self.table = ET.fromstring(self.members['word/fontTable.xml'])
        self.relationships = {
            node.get('Id'): node for node in ET.fromstring(self.members['word/_rels/fontTable.xml.rels'])
        }

    def test_every_packaged_face_is_embedded_once(self) -> None:
        expected = sum(len(faces) for faces in EMBEDDED_FONTS.values())
        self.assertEqual(self.count, expected)
        parts = sorted(name for name in self.members if name.startswith('word/fonts/'))
        self.assertEqual(len(parts), expected)
        self.assertTrue(all(name.endswith('.odttf') for name in parts))

    def test_each_embed_points_at_a_part_that_restores_the_packaged_font(self) -> None:
        for family, faces in EMBEDDED_FONTS.items():
            node = next(n for n in self.table if n.get(W + 'name') == family)
            for tag, relative in faces:
                with self.subTest(family=family, face=tag):
                    embed = node.find(W + tag)
                    self.assertIsNotNone(embed)
                    relationship = self.relationships[embed.get(R + 'id')]
                    self.assertTrue(relationship.get('Type').endswith('/relationships/font'))
                    data = self.members['word/' + relationship.get('Target')]
                    original = FONTS.joinpath(*relative.split('/')).read_bytes()
                    self.assertNotEqual(data[:32], original[:32])
                    self.assertEqual(obfuscate(data, embed.get(W + 'fontKey')), original)

    def test_embeds_follow_the_alternate_name_in_schema_order(self) -> None:
        node = next(n for n in self.table if n.get(W + 'name') == 'Inter')
        tags = [child.tag.removeprefix(W) for child in node]
        self.assertEqual(tags, ['altName', 'embedRegular', 'embedBold', 'embedItalic', 'embedBoldItalic'])

    def test_package_declares_the_obfuscated_font_type_and_word_setting(self) -> None:
        types = ET.fromstring(self.members['[Content_Types].xml'])
        defaults = [node for node in types.findall(CT + 'Default') if node.get('Extension') == 'odttf']
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0].get('ContentType'),
                         'application/vnd.openxmlformats-officedocument.obfuscatedFont')
        self.assertNotIn(b'ns0:', self.members['[Content_Types].xml'])
        settings = ET.fromstring(self.members['word/settings.xml'])
        self.assertEqual([child.tag.removeprefix(W) for child in settings], ['zoom', 'embedTrueTypeFonts'])

    def test_embedding_twice_gives_the_same_package(self) -> None:
        again = dict(self.members)
        embed_fonts(again)
        self.assertEqual(again, self.members)

    def test_a_package_without_content_types_is_left_alone(self) -> None:
        members = {'word/fontTable.xml': font_table()}
        self.assertEqual(embed_fonts(members), 0)
        self.assertEqual(set(members), {'word/fontTable.xml'})


if __name__ == '__main__':
    unittest.main()
