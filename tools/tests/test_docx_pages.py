"""Bookmark pagination, fallback and convergence contracts independent of the viewer."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import support
from handbook_toolkit.build_types import BuildError
from handbook_toolkit.docx_fields import Entry, cached_field, cached_links
from handbook_toolkit.docx_pages import (ConvergenceError, Section, cache_page_numbers,
    destination_name, destination_pages, logical_pages, numbering_sections)
from handbook_toolkit.docx_xml import W, fields


def package(path: Path) -> None:
    root = ET.Element(W + 'document')
    body = ET.SubElement(root, W + 'body')
    body.extend(cached_field('TOC \\o "1-3" \\h \\z \\u', [Entry('Title', 'Target')]))
    p = ET.SubElement(body, W + 'p')
    ET.SubElement(p, W + 'bookmarkStart', {W + 'name': 'Target', W + 'id': '1'})
    ET.SubElement(ET.SubElement(p, W + 'r'), W + 't').text = 'Title'
    ET.SubElement(p, W + 'bookmarkEnd', {W + 'id': '1'})
    ET.SubElement(body, W + 'sectPr')
    with ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', ET.tostring(root))


class DestinationTests(unittest.TestCase):
    def test_mapping_uses_written_bookmarks_not_caption_text(self):
        self.assertEqual(destination_name('B_some_5F'), 'B5Fsome5F5F')
        with patch('handbook_toolkit.docx_pages._run', return_value='Page Destination Name\n 12 [ XYZ 0 0 null ] "B5Fsome5F5F"\n'):
            self.assertEqual(destination_pages(Path('file.pdf'), {'B_some_5F'}), {'B_some_5F': 12})

    def test_missing_conflicting_and_ambiguous_destinations_fail(self):
        for text, names in [('', {'Missing'}), ('', {'A_B', 'A5FB'}),
            ('1 [ XYZ ] "Target"\n2 [ XYZ ] "Target"', {'Target'})]:
            with self.subTest(text=text, names=names), patch('handbook_toolkit.docx_pages._run', return_value=text):
                with self.assertRaises(BuildError):
                    destination_pages(Path('file.pdf'), names)

    def test_decimal_section_restarts_use_displayed_numbers(self):
        plan = [Section('S0', None, frozenset({'Intro'})),
                Section('S1', 10, frozenset({'Chapter'})),
                Section('S2', None, frozenset({'Next'}))]
        physical = {'S0': 1, 'Intro': 2, 'S1': 4, 'Chapter': 5, 'S2': 6, 'Next': 7}
        self.assertEqual(logical_pages(physical, plan, {'Intro', 'Chapter', 'Next'}),
                         {'Intro': '2', 'Chapter': '11', 'Next': '13'})

    def test_section_bookmarks_and_formats_are_checked(self):
        root = ET.Element(W + 'document');body = ET.SubElement(root, W + 'body')
        ET.SubElement(body, W + 'p')
        numbering = ET.SubElement(ET.SubElement(body, W + 'sectPr'), W + 'pgNumType',
                                 {W + 'start': '9', W + 'fmt': 'decimal'})
        plan = numbering_sections(root)
        self.assertEqual(plan[0].start, 9)
        self.assertTrue(root.findall('.//' + W + 'bookmarkStart'))
        numbering.set(W + 'fmt', 'lowerRoman')
        with self.assertRaisesRegex(BuildError, 'decimal'):
            numbering_sections(root)
        numbering.set(W + 'fmt', 'decimal');numbering.set(W + 'chapStyle', '1')
        with self.assertRaisesRegex(BuildError, 'chapter-prefixed'):
            numbering_sections(root)


class CacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name);self.docx = self.root / 'book.docx';package(self.docx)

    def read(self):
        with ZipFile(self.docx) as archive:
            return ET.fromstring(archive.read('word/document.xml'))

    def test_missing_optional_tools_leave_no_tab_pageref_or_dirty(self):
        with patch('handbook_toolkit.docx_pages.shutil.which', return_value=None):
            report = cache_page_numbers(self.docx, self.root)
            self.assertIn('titles-only', report['docx_page_numbers'])
            self.assertEqual(report['libreoffice'], 'unavailable')
            self.assertFalse(self.read().findall('.//' + W + 'tab'))
            self.assertFalse(any(f.instruction.startswith('PAGEREF') for f in fields(self.read())))
            with self.assertRaisesRegex(BuildError, 'required DOCX'):
                cache_page_numbers(self.docx, self.root, required=True)

    def simulate(self, page_values, *, required=True):
        values = iter(page_values)
        def destinations(_pdf, marks):
            page = next(values)
            return {name: (page if name == 'Target' else 1) for name in marks}
        with patch('handbook_toolkit.docx_pages.shutil.which', return_value='/tools/tool'), \
             patch('handbook_toolkit.docx_pages._run', return_value='LibreOffice fixture'), \
             patch('handbook_toolkit.docx_pages.font_environment', return_value={}), \
             patch('handbook_toolkit.docx_pages.export_pdf', return_value=Path('fixture.pdf')) as export, \
             patch('handbook_toolkit.docx_pages.destination_pages', side_effect=destinations):
            report = cache_page_numbers(self.docx, self.root, required=required)
            return report, export.call_count

    def test_two_pass_cache_is_numeric_and_deterministic(self):
        result, count = self.simulate([7, 7])
        self.assertIn('verified', result['docx_page_numbers']);self.assertEqual(count, 2)
        link = cached_links(self.read())[0]
        self.assertEqual(link.get(W + 'history'), '1')
        self.assertEqual([n.text for f in fields(link) for n in f.result], ['7'])
        first = self.docx.read_bytes();package(self.docx)
        self.simulate([7, 7]);self.assertEqual(first, self.docx.read_bytes())

    def test_unknown_width_is_established_before_final_verification(self):
        _result, count = self.simulate([12, 12, 12])
        self.assertEqual(count, 3)
        self.assertEqual([n.text for f in fields(cached_links(self.read())[0]) for n in f.result], ['12'])

    def test_nonconvergence_is_never_a_silent_optional_fallback(self):
        for required in (True, False):
            package(self.docx)
            with self.assertRaises(ConvergenceError):
                self.simulate([7, 8], required=required)

    def test_failed_optional_probe_falls_back_and_required_probe_fails(self):
        with patch('handbook_toolkit.docx_pages.shutil.which', return_value='/tools/tool'), \
             patch('handbook_toolkit.docx_pages._run', side_effect=BuildError('timed out')):
            result = cache_page_numbers(self.docx, self.root)
            self.assertIn('titles-only', result['docx_page_numbers'])
            self.assertFalse(self.read().findall('.//' + W + 'tab'))
            with self.assertRaisesRegex(BuildError, 'timed out'):
                cache_page_numbers(self.docx, self.root, required=True)
