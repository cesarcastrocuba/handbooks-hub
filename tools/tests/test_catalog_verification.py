"""Online release/API/hash checks with controlled transport; formats test separately."""

import copy
from pathlib import Path
import tempfile
import socket
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import zlib

import support
from handbook_toolkit.catalog_verification import _download, _public_addresses, verify_catalog_releases
from handbook_toolkit.publication import write_manifest


class CatalogVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.catalog = root / "catalog.json"
        self.document = support.catalog_document()
        book = self.document["books"][0]
        self.prefix = "https://github.com/example/example-book/releases/download/v1.0.0/"
        self.site = book["reading_url"]
        assets = root / "assets"
        assets.mkdir()
        with ZipFile(assets / "html.zip", "w") as archive:
            archive.writestr("index.html", '<link href="style.css"><h1 id="hello">Hello</h1>')
            archive.writestr("style.css", "body{color:black}")
        for name in ("book.pdf", "book.docx", "source.zip"):
            (assets / name).write_bytes(b"transport fixture")
        roles = {"html": "html.zip", "pdf": "book.pdf", "docx": "book.docx", "source": "source.zip"}
        write_manifest(assets, {
            "book": {"id": book["id"], "version": "1.0.0", "commit": "a" * 40},
            "toolkit": "0.2.0", "profile": {"id": "standard", "version": "0.2.0"},
            "build": {"command": "transport fixture", "source_date_epoch": 1,
                      "tool_versions": {"quarto": "1.11.9", "pandoc": "3.10", "typst": "0.15.1", "python": "3.12", "zlib": zlib.ZLIB_RUNTIME_VERSION}},
        }, roles)
        self.bytes = {self.prefix + path.name: path.read_bytes() for path in assets.iterdir()}
        with ZipFile(assets / "html.zip") as archive:
            self.bytes[self.site] = archive.read("index.html")
            self.bytes[self.site + "style.css"] = archive.read("style.css")
        self.release = {"tag_name": "v1.0.0", "draft": False, "prerelease": False,
                        "published_at": "2026-12-01T00:00:00Z",
                        "assets": [{"name": path.name, "state": "uploaded", "browser_download_url": self.prefix + path.name} for path in assets.iterdir()]}
        self.target = {"type": "commit", "sha": "a" * 40}

    def run_gate(self):
        support.write_json(self.catalog, self.document)

        def download(url, destination, limit):
            body = self.bytes[url]
            if len(body) > limit:
                raise ValueError("download exceeds expected size")
            destination.write_bytes(body)

        def fetch_json(url):
            if "/git/" in url:
                return {"object": copy.deepcopy(self.target)}
            return copy.deepcopy(self.release)

        with patch("handbook_toolkit.catalog_verification._download", side_effect=download), patch(
            "handbook_toolkit.catalog_verification._json", side_effect=fetch_json
        ), patch("handbook_toolkit.catalog_verification.inspect_payload", return_value=[]):
            return verify_catalog_releases(self.catalog)

    def test_published_release_payload_hashes_and_all_live_site_files_match(self):
        self.assertTrue(self.run_gate().ok)

    def test_draft_missing_asset_and_wrong_tag_commit_fail(self):
        original = copy.deepcopy(self.release)
        self.release["draft"] = True
        self.assertFalse(self.run_gate().ok)
        self.release = copy.deepcopy(original)
        self.release["assets"].pop()
        self.assertFalse(self.run_gate().ok)
        self.release = original
        self.target["sha"] = "b" * 40
        self.assertFalse(self.run_gate().ok)

    def test_payload_and_live_non_index_corruption_fail(self):
        name = self.prefix + "book.pdf"
        original = self.bytes[name]
        self.bytes[name] = b"x" * len(original)
        self.assertFalse(self.run_gate().ok)
        self.bytes[name] = original
        self.bytes[self.site + "style.css"] = b"x" * len(self.bytes[self.site + "style.css"])
        self.assertFalse(self.run_gate().ok)

    def test_mixed_identity_url_and_bad_ref_shape_fail(self):
        self.document["books"][0]["latest_release"]["manifest_url"] = self.prefix.replace("example-book", "other-book") + "publication-manifest.json"
        self.assertFalse(self.run_gate().ok)
        self.document = support.catalog_document()
        self.target = []
        self.assertFalse(self.run_gate().ok)

    def test_empty_catalog_does_not_fetch_remote_data(self):
        support.write_json(self.catalog, {"schema_version": "1.0", "books": []})
        with patch("handbook_toolkit.catalog_verification._download", side_effect=AssertionError("network not expected")):
            self.assertTrue(verify_catalog_releases(self.catalog).ok)

    def test_private_or_mixed_dns_destinations_fail(self):
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "224.0.0.1"):
            with self.subTest(address=address):
                records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]
                with patch("handbook_toolkit.catalog_verification.socket.getaddrinfo", return_value=records):
                    with self.assertRaises(ValueError):
                        _public_addresses("public-looking.example")

    def test_redirect_to_internal_host_or_http_is_rejected_before_fetch(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        for target in ("https://127.0.0.1/", "http://example.com/", "https://example.com:8443/"):
            destination = Path(self.temp.name) / "redirect-body"

            def resolve(host, *args, **kwargs):
                if host == "127.0.0.1":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 443))]
                return public

            with patch("handbook_toolkit.catalog_verification.socket.getaddrinfo", side_effect=resolve), patch(
                "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
            ) as connection:
                response = connection.return_value.getresponse.return_value
                response.status = 302
                response.getheader.return_value = target
                with self.assertRaises(ValueError):
                    _download("https://public.example/", destination, 100)
                self.assertEqual(connection.call_count, 1)
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
