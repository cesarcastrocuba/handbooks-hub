"""GitHub star counts baked in at build time (issue 141, change 0085)."""
from __future__ import annotations

import io
import json
import unittest

import support  # noqa: F401  (puts the toolkit on the path)
from handbook_toolkit import stars


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def opener_for(payload, calls):
    def opener(request, timeout):
        calls.append((request.full_url, dict(request.header_items()), timeout))
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(json.dumps(payload).encode())
    return opener


class StarTests(unittest.TestCase):
    def test_repository_is_read_only_from_https_github_urls(self):
        cases = {
            'https://github.com/owner/book': 'owner/book',
            'https://github.com/owner/book.git': 'owner/book',
            'https://github.com/owner/book/releases/tag/v1.0.0': 'owner/book',
            'https://github.com/OWNER/REPOSITORY': None,
            'http://github.com/owner/book': None,
            'https://example.org/owner/book': None,
            'https://github.com/owner': None,
            '': None,
            None: None,
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(stars.github_repository(url), expected)

    def test_nothing_is_fetched_unless_the_build_asks(self):
        calls = []
        for environ in ({}, {'HANDBOOK_STARS': '1'}, {'HANDBOOK_STARS': 'no', 'GITHUB_TOKEN': 't'}):
            with self.subTest(environ=environ):
                self.assertIsNone(stars.star_count('o/r', environ=environ, opener=opener_for({}, calls)))
        self.assertEqual(calls, [])

    def test_the_count_is_read_with_the_workflow_token(self):
        calls = []
        count = stars.star_count('o/r', environ={'HANDBOOK_STARS': 'fetch', 'GITHUB_TOKEN': 'secret'},
                                 opener=opener_for({'stargazers_count': 12}, calls))
        self.assertEqual(count, 12)
        url, headers, timeout = calls[0]
        self.assertEqual(url, 'https://api.github.com/repos/o/r')
        self.assertEqual(headers['Authorization'], 'Bearer secret')
        self.assertEqual(timeout, stars.TIMEOUT)

    def test_any_failure_or_odd_value_degrades_to_no_number(self):
        environ = {'HANDBOOK_STARS': 'fetch'}
        for payload in (OSError('offline'), ValueError('bad json'), {'stargazers_count': -1},
                        {'stargazers_count': True}, {'stargazers_count': '12'}, {}):
            with self.subTest(payload=payload):
                self.assertIsNone(stars.star_count('o/r', environ=environ, opener=opener_for(payload, [])))

    def test_a_count_given_by_the_workflow_wins_and_needs_no_request(self):
        calls = []
        environ = {'HANDBOOK_STAR_COUNTS': '{"Owner/Book": 5}', 'HANDBOOK_STARS': 'fetch'}
        self.assertEqual(stars.star_count('owner/book', environ=environ, opener=opener_for({}, calls)), 5)
        self.assertEqual(calls, [])
        for counts in ('not json', '[5]', '{"owner/book": -2}', '{"other/repo": 3}', ''):
            with self.subTest(counts=counts):
                self.assertIsNone(stars.star_count('owner/book', environ={'HANDBOOK_STAR_COUNTS': counts},
                                                   opener=opener_for({}, calls)))
        self.assertEqual(calls, [])

    def test_the_reading_site_navbar_gets_a_star_link(self):
        from unittest.mock import patch
        from handbook_toolkit.reading_site import _add_star_link
        config = {'repo-url': 'https://github.com/owner/book',
                  'navbar': {'right': [{'text': 'Source', 'href': 'https://github.com/owner/book/tree/main'}]}}
        with patch.dict('os.environ', {'HANDBOOK_STAR_COUNTS': '{"owner/book": 1234}'}, clear=True):
            _add_star_link(config)
        self.assertEqual(config['navbar']['right'][-1],
                         {'text': '★ Star · 1.2k', 'href': 'https://github.com/owner/book'})
        placeholder = {'repo-url': 'https://github.com/OWNER/REPOSITORY'}
        with patch.dict('os.environ', {}, clear=True):
            _add_star_link(placeholder)
        self.assertNotIn('navbar', placeholder)
        bare = {'repo-url': 'https://github.com/owner/book'}
        with patch.dict('os.environ', {}, clear=True):
            _add_star_link(bare)
        self.assertEqual(bare['navbar']['right'], [{'text': '★ Star', 'href': 'https://github.com/owner/book'}])

    def test_compact_counts_and_labels(self):
        self.assertEqual([stars.compact(n) for n in (0, 999, 1000, 1234, 9999, 12000, 123456)],
                         ['0', '999', '1k', '1.2k', '10k', '12k', '123k'])
        self.assertEqual(stars.label('o/r', None), 'Star o/r on GitHub')
        self.assertEqual(stars.label('o/r', 1), 'Star o/r on GitHub, 1 star')
        self.assertEqual(stars.label('o/r', 1234), 'Star o/r on GitHub, 1234 stars')
        self.assertEqual(stars.navbar_text(None), '★ Star')
        self.assertEqual(stars.navbar_text(1234), '★ Star · 1.2k')

    def test_star_link_is_a_real_accessible_link(self):
        link = stars.star_link('https://github.com/o/r', 'o/r', 7)
        self.assertIn('href="https://github.com/o/r"', link)
        self.assertIn('aria-label="Star o/r on GitHub, 7 stars"', link)
        self.assertIn('<span class="star-count">7</span>', link)
        self.assertIn('aria-hidden="true"', link)  # the icon
        self.assertNotIn('star-count', stars.star_link('https://github.com/o/r', 'o/r', None))


if __name__ == '__main__':
    unittest.main()
