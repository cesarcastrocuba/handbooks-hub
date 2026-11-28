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
                         {'text': '[★ Star · 1.2k]{.star-link}',
                          'href': 'https://github.com/owner/book'})
        placeholder = {'repo-url': 'https://github.com/OWNER/REPOSITORY'}
        with patch.dict('os.environ', {}, clear=True):
            _add_star_link(placeholder)
        self.assertNotIn('navbar', placeholder)
        bare = {'repo-url': 'https://github.com/owner/book'}
        with patch.dict('os.environ', {}, clear=True):
            _add_star_link(bare)
        self.assertEqual(bare['navbar']['right'],
                         [{'text': '[★ Star]{.star-link}', 'href': 'https://github.com/owner/book'}])

    def test_a_redirect_is_refused_so_the_token_never_leaves_the_api_host(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append((self.server.server_port, self.headers.get('Authorization')))
                if self.path.startswith('/repos/'):
                    self.send_response(302)
                    self.send_header('Location', f'http://127.0.0.1:{other.server_port}/elsewhere')
                    self.end_headers()
                else:
                    body = b'{"stargazers_count": 9}'
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def log_message(self, *args):
                pass

        api, other = HTTPServer(('127.0.0.1', 0), Handler), HTTPServer(('127.0.0.1', 0), Handler)
        for server in (api, other):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            from unittest.mock import patch
            with patch.object(stars, 'API', f'http://127.0.0.1:{api.server_port}/repos/'):
                count = stars.star_count('o/redirect', environ={'HANDBOOK_STARS': 'fetch', 'GITHUB_TOKEN': 'sekret'})
        finally:
            api.shutdown(); other.shutdown()
            # shutdown() stops serve_forever but leaves the listening socket open, which would
            # raise a ResourceWarning at interpreter exit.
            api.server_close(); other.server_close()
            stars._CACHE.pop('o/redirect', None)
        self.assertIsNone(count)
        self.assertEqual(seen, [(api.server_port, 'Bearer sekret')])

    def test_each_repository_is_read_once_per_build(self):
        from unittest.mock import patch
        calls = []
        stars._CACHE.pop('o/cached', None)
        try:
            with patch.object(stars, '_open', opener_for({'stargazers_count': 4}, calls)):
                counts = [stars.star_count('o/cached', environ={'HANDBOOK_STARS': 'fetch'}) for _ in range(3)]
        finally:
            stars._CACHE.pop('o/cached', None)
        self.assertEqual(counts, [4, 4, 4])
        self.assertEqual(len(calls), 1)

    def test_prefetch_reads_each_distinct_repository_once_and_keeps_order(self):
        calls = []
        counts_by_repository = {'o/a': 3, 'o/c': 5}

        def opener(request, timeout):
            repository = request.full_url.removeprefix('https://api.github.com/repos/')
            calls.append(repository)
            if repository == 'o/bad':
                raise OSError('offline')
            return FakeResponse(json.dumps({'stargazers_count': counts_by_repository[repository]}).encode())

        counts = stars.prefetch_counts(['o/a', 'O/A', 'o/bad', 'o/c', 'o/a'],
                                       environ={'HANDBOOK_STARS': 'fetch'}, opener=opener)
        self.assertEqual(sorted(calls), ['o/a', 'o/bad', 'o/c'])
        self.assertEqual(list(counts), ['o/a', 'o/bad', 'o/c'])
        self.assertEqual(counts, {'o/a': 3, 'o/bad': None, 'o/c': 5})

    def test_prefetch_looks_up_repositories_concurrently(self):
        import threading
        barrier = threading.Barrier(3)

        def opener(request, timeout):
            # A sequential implementation would wait for itself here and break the barrier.
            barrier.wait(timeout=5)
            return FakeResponse(b'{"stargazers_count": 7}')

        counts = stars.prefetch_counts(['o/a', 'o/b', 'o/c'],
                                       environ={'HANDBOOK_STARS': 'fetch'}, opener=opener)
        self.assertEqual(counts, {'o/a': 7, 'o/b': 7, 'o/c': 7})

    def test_prefetch_is_a_no_op_unless_the_build_asks_for_counts(self):
        calls = []
        self.assertEqual(stars.prefetch_counts(['o/a', 'o/b'], environ={},
                                               opener=opener_for({}, calls)), {})
        self.assertEqual(calls, [])

    def test_compact_counts_and_labels(self):
        self.assertEqual([stars.compact(n) for n in (0, 999, 1000, 1234, 9999, 12000, 123456)],
                         ['0', '999', '1k', '1.2k', '10k', '12k', '123k'])
        self.assertEqual(stars.label('o/r', None), 'Star o/r on GitHub')
        self.assertEqual(stars.label('o/r', 1), 'Star o/r on GitHub, 1 star')
        self.assertEqual(stars.label('o/r', 1234), 'Star o/r on GitHub, 1234 stars')
        self.assertEqual(stars.navbar_text(None), '★ Star')
        self.assertEqual(stars.navbar_text(1234), '★ Star · 1.2k')
        self.assertEqual(stars.navbar_markup(None), '[★ Star]{.star-link}')
        self.assertEqual(stars.navbar_markup(1234), '[★ Star · 1.2k]{.star-link}')

    def test_star_link_is_a_real_accessible_link(self):
        link = stars.star_link('https://github.com/o/r', 'o/r', 7)
        self.assertIn('href="https://github.com/o/r"', link)
        self.assertIn('aria-label="Star o/r on GitHub, 7 stars"', link)
        self.assertIn('<span class="star-count">7</span>', link)
        self.assertIn('aria-hidden="true"', link)  # the icon
        self.assertNotIn('star-count', stars.star_link('https://github.com/o/r', 'o/r', None))


if __name__ == '__main__':
    unittest.main()
