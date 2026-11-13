"""Native fields and structural gates, with positive and negative OOXML fixtures."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import support
from handbook_toolkit.artifacts import inspect_payload
from handbook_toolkit.docx_post import prepare_docx
from handbook_toolkit.docx_fields import add_indexes, bookmark_name, cached_field, Entry
from handbook_toolkit.docx_fonts import font_table
from handbook_toolkit.docx_xml import W, fields, field_run, instruction_run, text_of
from handbook_toolkit.docx_validation import validate_docx


def paragraph(parent: ET.Element, text: str, style: str = 'Normal') -> ET.Element:
    node = ET.SubElement(parent, W + 'p')
    ET.SubElement(ET.SubElement(node, W + 'pPr'), W + 'pStyle', {W + 'val': style})
    ET.SubElement(ET.SubElement(node, W + 'r'), W + 't').text = text
    return node


def fixture() -> tuple[ET.Element, ET.Element]:
    root = ET.Element(W + 'document')
    body = ET.SubElement(root, W + 'body')
    ET.SubElement(body, W + 'bookmarkStart', {W + 'id': '1', W + 'name': 'Target'})
    paragraph(body, 'Fixture', 'Normal')
    ET.SubElement(body, W + 'bookmarkEnd', {W + 'id': '1'})
    styles = ET.Element(W + 'styles')
    for name, kind in [('Normal', 'paragraph'), ('TOC1', 'paragraph'), ('TOC2', 'paragraph'),
                       ('TOC3', 'paragraph'), ('Hyperlink', 'character'), ('TOCHeading', 'paragraph'),
                       ('Heading1', 'paragraph'), ('Heading2', 'paragraph'), ('Heading3', 'paragraph'),
                       ('Caption', 'paragraph'), ('ImageCaption', 'paragraph'), ('TableCaption', 'paragraph'),
                       ('ListingCaption', 'paragraph'), ('Table', 'table')]:
        node = ET.SubElement(styles, W + 'style', {W + 'styleId': name, W + 'type': kind})
        ET.SubElement(node, W + 'name', {W + 'val': name})
    return root, styles


class DocxValidatorTests(unittest.TestCase):
    def setUp(self):
        self.root, self.styles = fixture()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def check(self, *, valid: bool):
        path = Path(self.temp.name) / 'fixture.docx'
        with ZipFile(path, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types/>')
            archive.writestr('_rels/.rels', '<Relationships/>')
            archive.writestr('word/document.xml', ET.tostring(self.root))
            archive.writestr('word/styles.xml', ET.tostring(self.styles))
        issues = inspect_payload(path, 'docx')
        self.assertEqual(not issues, valid, [str(issue) for issue in issues])

    def test_unique_style_ids(self):
        self.check(valid=True)
        self.styles.append(deepcopy(self.styles[0]))
        self.check(valid=False)

    def test_used_paragraph_style_is_defined(self):
        self.check(valid=True)
        self.root.find('.//' + W + 'pStyle').set(W + 'val', 'Missing')
        self.check(valid=False)

    def test_used_run_style_is_defined_and_has_correct_type(self):
        run = self.root.find('.//' + W + 'r')
        style = ET.Element(W + 'rPr')
        ET.SubElement(style, W + 'rStyle', {W + 'val': 'Hyperlink'})
        run.insert(0, style)
        self.check(valid=True)
        style[0].set(W + 'val', 'Normal')
        self.check(valid=False)

    def test_used_table_style_is_defined(self):
        table = ET.SubElement(self.root.find(W + 'body'), W + 'tbl')
        props = ET.SubElement(table, W + 'tblPr')
        style = ET.SubElement(props, W + 'tblStyle', {W + 'val': 'Table'})
        self.check(valid=True)
        style.set(W + 'val', 'Missing')
        self.check(valid=False)

    def test_row_properties_reject_shading(self):
        props = ET.SubElement(self.root.find('.//' + W + 'p'), W + 'trPr')
        ET.SubElement(props, W + 'cantSplit')
        self.check(valid=True)
        ET.SubElement(props, W + 'shd')
        self.check(valid=False)

    def test_authored_property_containers_reject_unknown_children(self):
        for name in ('pPr', 'rPr', 'tblPr', 'tcPr'):
            with self.subTest(container=name):
                root, self.root = self.root, deepcopy(self.root)
                props = ET.SubElement(self.root, W + name)
                self.check(valid=True)
                ET.SubElement(props, W + 'bogus')
                self.check(valid=False)
                self.root = root

    def test_property_order_and_duplicates(self):
        props = self.root.find('.//' + W + 'pPr')
        ET.SubElement(props, W + 'jc', {W + 'val': 'left'})
        self.check(valid=True)
        ET.SubElement(props, W + 'pStyle', {W + 'val': 'Normal'})
        self.check(valid=False)

    def test_balanced_nested_fields(self):
        body = self.root.find(W + 'body')
        body.extend(cached_field('TOC \\h \\z \\f T', [Entry('Caption', 'Target')]))
        self.check(valid=True)
        body[-1].remove(body[-1][-1])
        self.check(valid=False)

    def test_field_separator_without_begin(self):
        self.check(valid=True)
        self.root.find('.//' + W + 'p').append(field_run('separate'))
        self.check(valid=False)

    def test_double_field_separator(self):
        p = self.root.find('.//' + W + 'p')
        p.extend((field_run('begin'), instruction_run('PAGE'), field_run('separate'), field_run('end')))
        self.check(valid=True)
        p.insert(len(p) - 1, field_run('separate'))
        self.check(valid=False)

    def test_field_end_without_begin(self):
        self.check(valid=True)
        self.root.find('.//' + W + 'p').append(field_run('end'))
        self.check(valid=False)

    def test_hyperlink_target(self):
        p = self.root.find('.//' + W + 'p')
        link = ET.SubElement(p, W + 'hyperlink', {W + 'anchor': 'Target'})
        self.check(valid=True)
        link.set(W + 'anchor', 'Absent')
        self.check(valid=False)

    def test_complex_reference_targets(self):
        for command in ('PAGEREF', 'REF'):
            with self.subTest(command=command):
                root, self.root = self.root, deepcopy(self.root)
                p = self.root.find('.//' + W + 'p')
                instruction = instruction_run(command + ' Target \\h')
                p.extend((field_run('begin'), instruction, field_run('separate'), field_run('end')))
                self.check(valid=True)
                instruction[0].text = command + ' Absent \\h'
                self.check(valid=False)
                self.root = root

    def test_simple_reference_target(self):
        node = ET.SubElement(self.root.find('.//' + W + 'p'), W + 'fldSimple',
                             {W + 'instr': 'REF Target \\h'})
        self.check(valid=True)
        node.set(W + 'instr', 'REF Missing')
        self.check(valid=False)

    def test_bookmark_names_unique(self):
        self.check(valid=True)
        ET.SubElement(self.root.find(W + 'body'), W + 'bookmarkStart',
                      {W + 'id': '2', W + 'name': 'Target'})
        self.check(valid=False)

    def test_bookmark_names_are_valid_word_identifiers(self):
        mark = self.root.find('.//' + W + 'bookmarkStart')
        self.check(valid=True)
        for value in ('', '1Name', '_Name', 'with-hyphen', 'A' * 41, 'Édition'):
            with self.subTest(name=value):
                mark.set(W + 'name', value)
                self.check(valid=False)


class NativeFieldTests(unittest.TestCase):
    def test_caption_registry_and_contents_cache(self):
        root, styles = fixture()
        body = root.find(W + 'body')
        sdt = ET.SubElement(body, W + 'sdt')
        content = ET.SubElement(sdt, W + 'sdtContent')
        content.extend(cached_field('TOC \\o "1-3" \\h \\z \\u', []))
        paragraph(body, 'Chapter one', 'Heading1')
        paragraph(body, 'Nested section', 'Heading2')
        for label, style in [('Table 1: Routes', 'TableCaption'),
                             ('Figure 1: Original image', 'ImageCaption'),
                             ('Listing 1: Code "quoted" \\ path', 'ListingCaption')]:
            paragraph(body, label, style)
        add_indexes(root)
        instructions = [item.instruction for item in fields(root)]
        for letter in ('T', 'F', 'L'):
            self.assertIn('TOC \\h \\z \\f ' + letter, instructions)
        self.assertIn('TOC \\o "1-3" \\h \\z \\u', instructions)
        self.assertTrue(any('Code \\"quoted\\" \\\\ path' in value for value in instructions))
        for link in root.iter(W + 'hyperlink'):
            self.assertTrue(link.get(W + 'anchor'))
        # Unknown page numbers are empty, never invented or copied from another renderer.
        for item in fields(root):
            if item.instruction.startswith('PAGEREF'):
                self.assertEqual(item.begin.get(W + 'dirty'), 'true')
        self.assertIn('Chapter one', text_of(content))
        self.assertIn('Nested section', text_of(content))
        self.assertEqual(len([p for p in body if text_of(p) == 'List of Figures']), 1)

    def test_contents_cache_respects_pandocs_selected_heading_depth(self):
        root, _styles = fixture()
        body = root.find(W + 'body')
        content = ET.SubElement(ET.SubElement(body, W + 'sdt'), W + 'sdtContent')
        content.extend(cached_field('TOC \\o "1-1" \\h \\z \\u', []))
        paragraph(body, 'Chapter one', 'Heading1')
        paragraph(body, 'Nested section', 'Heading2')
        add_indexes(root)
        self.assertIn('Chapter one', text_of(content))
        self.assertNotIn('Nested section', text_of(content))

    def test_empty_caption_lists_are_not_emitted(self):
        root, _styles = fixture()
        content = ET.SubElement(ET.SubElement(root.find(W + 'body'), W + 'sdt'), W + 'sdtContent')
        content.extend(cached_field('TOC \\o "1-3" \\h \\z \\u', []))
        add_indexes(root)
        self.assertFalse(any(text_of(node).startswith('List of ') for node in root.iter(W + 'p')))

    def test_caption_lists_work_when_contents_is_disabled(self):
        root, _styles = fixture()
        paragraph(root.find(W + 'body'), 'Unnumbered original image', 'ImageCaption')
        add_indexes(root)
        codes = [item.instruction for item in fields(root)]
        self.assertIn('TOC \\h \\z \\f F', codes)
        self.assertFalse(any('\\o ' in code for code in codes))

    def test_bookmark_mapping_is_deterministic_and_collision_resistant(self):
        for value in ('tbl-test', 'fig-a' * 20, 'éclair', '1test', '_GoBack'):
            result = bookmark_name(value)
            self.assertEqual(result, bookmark_name(value))
            self.assertEqual(result, bookmark_name(result))
            self.assertLessEqual(len(result), 40)
        self.assertNotEqual(bookmark_name('tbl-test'), bookmark_name('tbl_test'))

    def test_identical_inputs_produce_identical_docx_bytes(self):
        root, styles = fixture()
        body = root.find(W + 'body')
        content = ET.SubElement(ET.SubElement(body, W + 'sdt'), W + 'sdtContent')
        content.extend(cached_field('TOC \\o "1-3" \\h \\z \\u', []))
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ('one.docx', 'two.docx')]
            for path in paths:
                with ZipFile(path, 'w') as archive:
                    archive.writestr('word/document.xml', ET.tostring(root))
                    archive.writestr('word/styles.xml', ET.tostring(styles))
                prepare_docx(path)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())

    def test_font_fallbacks_are_declared_as_single_name_aliases(self):
        fonts = ET.fromstring(font_table())
        mapping = {font.get(W + 'name'): font.find(W + 'altName').get(W + 'val')
                   for font in fonts if font.find(W + 'altName') is not None}
        self.assertEqual(mapping['Source Sans 3'], 'Segoe UI')
        self.assertEqual(mapping['Segoe UI'], 'Calibri')
        self.assertEqual(mapping['Calibri'], 'Arial')
        self.assertEqual(mapping['Source Serif 4'], 'Georgia')
        self.assertEqual(mapping['JetBrains Mono'], 'Consolas')
