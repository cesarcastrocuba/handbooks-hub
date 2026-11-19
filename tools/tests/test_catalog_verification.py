"""Online release/API/hash checks with controlled transport; formats test separately."""

import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import socket
import unittest
from unittest.mock import MagicMock, patch
from zipfile import ZipFile
import zlib

import support
from handbook_toolkit.catalog_verification import (
    _PinnedHTTPSConnection,
    _download,
    _public_addresses,
    _request_headers,
    verify_catalog_releases,
)
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
        for name in ("book.pdf", "book.docx", "book.md", "source.zip"):
            (assets / name).write_bytes(b"transport fixture")
        roles = {"html": "html.zip", "pdf": "book.pdf", "docx": "book.docx",
                 "markdown": "book.md", "source": "source.zip"}
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

    def rewrite_as_legacy(self) -> None:
        """Replace the release fixture by a schema 1.0 release with six assets."""

        legacy = Path(self.temp.name) / "legacy"
        legacy.mkdir()
        with ZipFile(legacy / "html.zip", "w") as archive:
            archive.writestr("index.html", '<link href="style.css"><h1 id="hello">Hello</h1>')
            archive.writestr("style.css", "body{color:black}")
        names = {"html": "html.zip", "pdf": "book.pdf", "docx": "book.docx", "source": "source.zip"}
        media = {"html": "application/zip", "pdf": "application/pdf",
                 "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "source": "application/zip"}
        artifacts = []
        for role, name in names.items():
            if role != "html":
                (legacy / name).write_bytes(b"transport fixture")
            path = legacy / name
            artifacts.append({"role": role, "path": name,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "bytes": path.stat().st_size, "media_type": media[role]})
        document = {
            "schema_version": "1.0",
            "artifacts": artifacts,
            "book": {"id": "example-book", "version": "1.0.0", "commit": "a" * 40},
            "toolkit": "0.2.0",
            "profile": {"id": "standard", "version": "0.2.0"},
            "build": {"command": "transport fixture", "source_date_epoch": 1,
                      "tool_versions": {"quarto": "1.11.9", "pandoc": "3.10", "typst": "0.15.1",
                                        "python": "3.12", "zlib": zlib.ZLIB_RUNTIME_VERSION}},
        }
        encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
        (legacy / "publication-manifest.json").write_bytes(encoded)
        digests = {entry["path"]: entry["sha256"] for entry in artifacts}
        digests["publication-manifest.json"] = hashlib.sha256(encoded).hexdigest()
        (legacy / "SHA256SUMS.txt").write_text(
            "".join(f"{digests[name]}  {name}\n" for name in sorted(digests)), encoding="utf-8"
        )
        self.bytes = {self.prefix + path.name: path.read_bytes() for path in legacy.iterdir()}
        with ZipFile(legacy / "html.zip") as archive:
            self.bytes[self.site] = archive.read("index.html")
            self.bytes[self.site + "style.css"] = archive.read("style.css")
        self.release["assets"] = [
            {"name": path.name, "state": "uploaded", "browser_download_url": self.prefix + path.name}
            for path in sorted(legacy.iterdir())
        ]

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
        ), patch("handbook_toolkit.catalog_verification.inspect_payload", return_value=[]) as inspect:
            result = verify_catalog_releases(self.catalog)
        self.inspections = inspect.call_args_list
        return result

    def test_published_release_payload_hashes_and_all_live_site_files_match(self):
        self.assertTrue(self.run_gate().ok)

    def test_a_published_release_is_not_held_to_rules_newer_than_its_build(self):
        self.assertTrue(self.run_gate().ok)
        self.assertTrue(self.inspections)
        for call in self.inspections:
            self.assertIs(call.kwargs["build_invariants"], False)

    def test_legacy_one_point_zero_release_with_six_assets_passes(self):
        self.rewrite_as_legacy()
        self.assertEqual(len(self.release["assets"]), 6)
        self.assertTrue(self.run_gate().ok)

    def test_asset_count_comes_from_the_manifest(self):
        self.assertTrue(self.run_gate().ok)
        self.release["assets"].pop()
        self.assertFalse(self.run_gate().ok)

    def configure_authors(self, authors, metadata_author="Example Author"):
        """State catalog authors and write the matching metadata into the release source zip."""

        self.document["schema_version"] = "1.2"
        self.document["books"][0]["authors"] = authors
        assets = Path(self.temp.name) / "assets"
        source = assets / "source.zip"
        with ZipFile(source, "w") as archive:
            if metadata_author is not None:
                archive.writestr(
                    "publishing/metadata.yaml",
                    "author: " + json.dumps(metadata_author) + "\n",
                )
        manifest_path = assets / "publication-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        data = source.read_bytes()
        for entry in manifest["artifacts"]:
            if entry["role"] == "source":
                entry["sha256"] = hashlib.sha256(data).hexdigest()
                entry["bytes"] = len(data)
        encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        manifest_path.write_bytes(encoded)
        digests = {entry["path"]: entry["sha256"] for entry in manifest["artifacts"]}
        digests["publication-manifest.json"] = hashlib.sha256(encoded).hexdigest()
        (assets / "SHA256SUMS.txt").write_text(
            "".join(f"{digests[name]}  {name}\n" for name in sorted(digests)), encoding="utf-8"
        )
        for name in ("source.zip", "publication-manifest.json", "SHA256SUMS.txt"):
            self.bytes[self.prefix + name] = (assets / name).read_bytes()

    def test_catalog_authors_match_the_release_metadata(self):
        self.configure_authors(["Example Author"])
        self.assertTrue(self.run_gate().ok)

    def test_catalog_authors_accept_a_metadata_list(self):
        self.configure_authors(["Example Author", "Second Author"],
                               metadata_author=["Example Author", "Second Author"])
        self.assertTrue(self.run_gate().ok)

    def test_catalog_authors_mismatch_fails(self):
        self.configure_authors(["Someone Else"])
        result = self.run_gate()
        self.assertIn("catalog authors differ", str(result.issues[0]))

    def test_a_release_without_metadata_cannot_verify_catalog_authors(self):
        self.configure_authors(["Example Author"], metadata_author=None)
        result = self.run_gate()
        self.assertIn("publishing/metadata.yaml", str(result.issues[0]))

    def add_extras(self, *, sums=None, zip_bytes=None):
        if zip_bytes is None:
            buffer = io.BytesIO()
            with ZipFile(buffer, "w") as archive:
                archive.writestr("exports/checklist.csv", "id,status\n1,pass\n")
            zip_bytes = buffer.getvalue()
        digest = hashlib.sha256(zip_bytes).hexdigest()
        sums_bytes = (
            sums if sums is not None else f"{digest}  book-extras.zip\n"
        ).encode("utf-8")
        self.bytes[self.prefix + "book-extras.zip"] = zip_bytes
        self.bytes[self.prefix + "EXTRAS-SHA256SUMS.txt"] = sums_bytes
        self.release["assets"].extend(
            [
                {
                    "name": "book-extras.zip",
                    "state": "uploaded",
                    "browser_download_url": self.prefix + "book-extras.zip",
                    "size": len(zip_bytes),
                },
                {
                    "name": "EXTRAS-SHA256SUMS.txt",
                    "state": "uploaded",
                    "browser_download_url": self.prefix + "EXTRAS-SHA256SUMS.txt",
                    "size": len(sums_bytes),
                },
            ]
        )

    def test_optional_extras_pair_passes(self):
        self.add_extras()
        self.assertTrue(self.run_gate().ok)

    def test_release_must_carry_both_extras(self):
        self.add_extras()
        self.release["assets"] = [
            asset for asset in self.release["assets"] if asset["name"] != "EXTRAS-SHA256SUMS.txt"
        ]
        result = self.run_gate()
        self.assertIn("must carry both", str(result.issues[0]))
        self.add_extras()
        self.release["assets"] = [
            asset for asset in self.release["assets"] if asset["name"] != "book-extras.zip"
        ]
        result = self.run_gate()
        self.assertIn("must carry both", str(result.issues[0]))

    def test_an_unknown_tenth_asset_fails(self):
        self.add_extras()
        self.release["assets"].append(
            {"name": "notes.txt", "state": "uploaded",
             "browser_download_url": self.prefix + "notes.txt"}
        )
        result = self.run_gate()
        self.assertIn("exactly", str(result.issues[0]))

    def test_extras_checksum_mismatch_fails(self):
        self.add_extras(sums="0" * 64 + "  book-extras.zip\n")
        result = self.run_gate()
        self.assertIn("checksum does not match", str(result.issues[0]))

    def test_malformed_extras_sums_fails(self):
        for sums in (
            "not a checksum\n",
            f"{'0' * 64}  other.zip\n",
            f"{'0' * 64}  book-extras.zip\n{'1' * 64}  book-extras.zip\n",
        ):
            with self.subTest(sums=sums):
                self.setUp()
                self.add_extras(sums=sums)
                result = self.run_gate()
                self.assertIn("EXTRAS-SHA256SUMS.txt", str(result.issues[0]))

    def test_extras_zip_with_unsafe_member_fails(self):
        buffer = io.BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("../escape.txt", "x")
        self.add_extras(zip_bytes=buffer.getvalue())
        result = self.run_gate()
        self.assertIn("unsafe member path", str(result.issues[0]))

    def test_extras_zip_must_be_a_valid_archive(self):
        self.add_extras(zip_bytes=b"not a zip")
        result = self.run_gate()
        self.assertIn("not a valid ZIP", str(result.issues[0]))

    def test_direct_download_links_must_match_the_release_manifest(self):
        self.rewrite_as_legacy()
        self.document["schema_version"] = "1.1"
        release = self.document["books"][0]["latest_release"]
        release["assets"] = {"pdf": self.prefix + "book.pdf", "docx": self.prefix + "book.docx"}
        self.assertTrue(self.run_gate().ok)
        release["assets"]["markdown"] = self.prefix + "book.md"
        result = self.run_gate()
        self.assertIn("download link for markdown", str(result.issues[0]))

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

    def test_credentials_and_redirect_ceiling_fail_without_writing(self):
        destination = Path(self.temp.name) / "not-downloaded"
        with self.assertRaises(ValueError):
            _download("https://user:password@example.com/", destination, 100)
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection:
            response = connection.return_value.getresponse.return_value
            response.status = 302
            response.getheader.return_value = "https://public.example/loop"
            with self.assertRaises(ValueError):
                _download("https://public.example/loop", destination, 100)
            self.assertEqual(connection.call_count, 6)
            self.assertFalse(destination.exists())

    def test_the_token_is_sent_to_the_github_api_host_and_to_no_other(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "secret-value"}):
            self.assertEqual(_request_headers("api.github.com")["Authorization"], "Bearer secret-value")
            for host in ("github.com", "objects.githubusercontent.com", "api.github.com.example"):
                with self.subTest(host=host):
                    self.assertNotIn("Authorization", _request_headers(host))
        with patch.dict("os.environ", {}, clear=True):
            self.assertNotIn("Authorization", _request_headers("api.github.com"))

    def test_a_redirect_away_from_the_api_drops_the_token(self):
        destination = Path(self.temp.name) / "redirected"
        with patch.dict("os.environ", {"GITHUB_TOKEN": "secret-value"}), patch(
            "handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]
        ), patch("handbook_toolkit.catalog_verification._PinnedHTTPSConnection") as connection:
            first, second = MagicMock(), MagicMock()
            connection.return_value.getresponse.side_effect = [first, second]
            first.status = 302
            first.getheader.return_value = "https://objects.example/asset"
            second.status = 200
            second.read.side_effect = [b"bytes", b""]
            _download("https://api.github.com/repos/o/r/releases/assets/1", destination, 100)
        sent = [call.kwargs["headers"] for call in connection.return_value.request.call_args_list]
        self.assertEqual(sent[0]["Authorization"], "Bearer secret-value")
        self.assertNotIn("Authorization", sent[1])
        self.assertEqual(destination.read_bytes(), b"bytes")

    def test_an_exhausted_rate_limit_is_named_with_its_host_and_remedy(self):
        destination = Path(self.temp.name) / "limited"
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection:
            response = connection.return_value.getresponse.return_value
            response.status = 403
            response.getheader.side_effect = {"X-RateLimit-Remaining": "0"}.get
            with self.assertRaisesRegex(
                ValueError, r"HTTP 403 from api\.github\.com: the GitHub API rate limit is exhausted; set GITHUB_TOKEN"
            ):
                _download("https://api.github.com/repos/o/r", destination, 100)
            response.getheader.side_effect = {}.get
            with self.assertRaisesRegex(ValueError, r"HTTP 403 from api\.github\.com$"):
                _download("https://api.github.com/repos/o/r", destination, 100)
        self.assertFalse(destination.exists())

    def transient(self, status, retry_after=None):
        response = MagicMock()
        response.status = status
        headers = {"Retry-After": retry_after} if retry_after is not None else {}
        response.getheader.side_effect = headers.get
        return response

    def test_a_transient_server_error_is_retried(self):
        destination = Path(self.temp.name) / "retried"
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection, patch("handbook_toolkit.catalog_verification._sleep") as sleep:
            success = MagicMock()
            success.status = 200
            success.read.side_effect = [b"bytes", b""]
            connection.return_value.getresponse.side_effect = [self.transient(503), success]
            _download("https://public.example/asset", destination, 100)
        self.assertEqual(destination.read_bytes(), b"bytes")
        self.assertEqual(connection.call_count, 2)
        sleep.assert_called_once_with(2.0)

    def test_transient_retry_honours_a_numeric_retry_after(self):
        destination = Path(self.temp.name) / "retry-after"
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection, patch("handbook_toolkit.catalog_verification._sleep") as sleep:
            success = MagicMock()
            success.status = 200
            success.read.side_effect = [b"bytes", b""]
            connection.return_value.getresponse.side_effect = [
                self.transient(503, retry_after="7"), success
            ]
            _download("https://public.example/asset", destination, 100)
        sleep.assert_called_once_with(7.0)

    def test_four_transient_errors_fail_with_the_existing_message(self):
        destination = Path(self.temp.name) / "never-written"
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection, patch("handbook_toolkit.catalog_verification._sleep") as sleep:
            connection.return_value.getresponse.side_effect = [self.transient(503) for _ in range(4)]
            with self.assertRaisesRegex(ValueError, r"remote asset returned HTTP 503 from public\.example$"):
                _download("https://public.example/asset", destination, 100)
        self.assertEqual(sleep.call_count, 3)
        self.assertFalse(destination.exists())

    def test_a_not_found_response_is_not_retried(self):
        destination = Path(self.temp.name) / "not-found"
        with patch("handbook_toolkit.catalog_verification._public_addresses", return_value=["93.184.216.34"]), patch(
            "handbook_toolkit.catalog_verification._PinnedHTTPSConnection"
        ) as connection, patch("handbook_toolkit.catalog_verification._sleep") as sleep:
            connection.return_value.getresponse.return_value = self.transient(404)
            with self.assertRaisesRegex(ValueError, r"HTTP 404 from public\.example$"):
                _download("https://public.example/asset", destination, 100)
        self.assertEqual(connection.call_count, 1)
        sleep.assert_not_called()
        self.assertFalse(destination.exists())

    def test_pinned_connection_preserves_tls_hostname_without_resolving_again(self):
        connection = _PinnedHTTPSConnection("public.example", "93.184.216.34")
        with patch("handbook_toolkit.catalog_verification.socket.create_connection") as connect, patch.object(
            connection, "_context"
        ) as context, patch("handbook_toolkit.catalog_verification.socket.getaddrinfo", side_effect=AssertionError("no DNS lookup")):
            connection.connect()
            connect.assert_called_once_with(("93.184.216.34", 443), timeout=30)
            context.wrap_socket.assert_called_once_with(connect.return_value, server_hostname="public.example")


if __name__ == "__main__":
    unittest.main()
