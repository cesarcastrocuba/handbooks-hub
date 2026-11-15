"""Deployed-site check: a page whose stylesheet is not served must fail the check."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402,F401

from handbook_toolkit.site_check import (  # noqa: E402
    SiteCheckError,
    check_site,
    local_assets,
    main,
    missing_assets,
)

PAGE = """<!doctype html><html><head>
<link rel="stylesheet" href="assets/site.css">
<link rel="stylesheet" href="./assets/site.css#top">
<link rel="stylesheet" href="https://other.example/remote.css">
<script src="assets/site.js"></script>
</head><body>
<img src="data:image/png;base64,AAAA" alt="">
<img src="assets/logo.svg" alt="">
<a href="missing-page.html">A link is not an asset</a>
</body></html>
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


class DeployedSiteCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.site = Path(temp.name)
        (self.site / "assets").mkdir()
        (self.site / "index.html").write_text(PAGE, encoding="utf-8")
        for name in ("site.css", "site.js", "logo.svg"):
            (self.site / "assets" / name).write_text("x", encoding="utf-8")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_QuietHandler, directory=str(self.site)))
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{server.server_address[1]}/"

    def test_only_same_origin_assets_are_collected_once(self) -> None:
        self.assertEqual(
            local_assets("https://example.org/book/", PAGE),
            [
                "https://example.org/book/assets/site.css",
                "https://example.org/book/assets/site.js",
                "https://example.org/book/assets/logo.svg",
            ],
        )

    def test_a_complete_site_passes(self) -> None:
        self.assertEqual(missing_assets(self.url, [""]), (3, []))
        self.assertEqual(main([self.url, "--attempts", "1"]), 0)

    def test_an_asset_that_is_not_served_fails_and_is_named(self) -> None:
        (self.site / "assets" / "site.css").unlink()
        count, failures = missing_assets(self.url, [""])
        self.assertEqual(count, 3)
        self.assertEqual(failures, [f"404 {self.url}assets/site.css (loaded by {self.url})"])
        self.assertEqual(main([self.url, "--attempts", "1"]), 1)

    def test_a_missing_page_fails(self) -> None:
        self.assertEqual(missing_assets(self.url, ["design.html"]), (0, [f"404 {self.url}design.html"]))

    def test_it_retries_a_bounded_number_of_times(self) -> None:
        (self.site / "assets" / "site.js").unlink()
        with patch("handbook_toolkit.site_check.time.sleep") as sleep:
            count, failures = check_site(self.url, [""], attempts=3, wait=7)
        self.assertEqual(len(failures), 1)
        self.assertEqual([call.args for call in sleep.call_args_list], [(7,), (7,)])

    def test_a_deployment_that_appears_later_passes(self) -> None:
        missing = self.site / "assets" / "site.js"
        missing.unlink()
        with patch("handbook_toolkit.site_check.time.sleep", side_effect=lambda _: missing.write_text("x")):
            self.assertEqual(check_site(self.url, [""], attempts=2, wait=1), (3, []))

    def test_plain_http_is_refused_except_on_loopback(self) -> None:
        with self.assertRaises(SiteCheckError):
            missing_assets("http://example.org/", [""])
        self.assertEqual(main(["http://example.org/", "--attempts", "1"]), 2)

    def test_at_least_one_attempt_is_required(self) -> None:
        with self.assertRaises(SiteCheckError):
            check_site(self.url, [""], attempts=0)


if __name__ == "__main__":
    unittest.main()
