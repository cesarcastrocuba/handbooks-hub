"""Catalog automation tests: deterministic update rules and workflow hardening. No network."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

sys.path.insert(0, str(support.TOOLS_ROOT / "scripts"))

import update_catalog  # noqa: E402
from update_catalog import CatalogUpdateError, plan_update, published_date, release_roles  # noqa: E402

SLUG = "example-book"
REPO = "example/example-book"
WORKFLOW = support.REPO_ROOT / ".github/workflows/catalog-update.yml"


def second_book() -> dict:
    book = support.copy_document(support.catalog_document()["books"][0])
    book["id"] = book["slug"] = "zeta-book"
    book["reading_url"] = "https://example.github.io/zeta-book/"
    release = book["latest_release"]
    for field in ("url", "manifest_url", "checksums_url"):
        release[field] = release[field].replace("example/example-book", "example/zeta-book")
    return book


class PlanUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = support.catalog_document()

    def rejected(self, pattern: str, *args, document: dict | None = None) -> None:
        with self.assertRaisesRegex(CatalogUpdateError, pattern):
            plan_update(document or self.document, *args)

    def test_new_release_rewrites_only_latest_release(self) -> None:
        self.document["books"].append(second_book())
        original = support.copy_document(self.document)
        plan = plan_update(self.document, SLUG, REPO, "v1.1.0", "2026-12-15")
        self.assertTrue(plan.changed)
        self.assertEqual(plan.message, "updated: example-book v1.0.0 -> v1.1.0 (published 2026-12-15)")
        self.assertEqual(self.document, original, "the input document must not be modified")
        expected = support.copy_document(original)
        expected["books"][0]["latest_release"] = {
            "version": "1.1.0",
            "tag": "v1.1.0",
            "url": "https://github.com/example/example-book/releases/tag/v1.1.0",
            "published_at": "2026-12-15",
            "manifest_url": "https://github.com/example/example-book/releases/download/v1.1.0/publication-manifest.json",
            "checksums_url": "https://github.com/example/example-book/releases/download/v1.1.0/SHA256SUMS.txt",
        }
        self.assertEqual(plan.document, expected)

    def test_new_release_lists_direct_downloads_for_the_given_roles(self) -> None:
        plan = plan_update(self.document, SLUG, REPO, "v1.1.0", "2026-12-15", ("markdown", "pdf"))
        base = "https://github.com/example/example-book/releases/download/v1.1.0/"
        self.assertEqual(plan.document["schema_version"], "1.1")
        self.assertEqual(
            list(plan.document["books"][0]["latest_release"]["assets"].items()),
            [("pdf", base + "book.pdf"), ("markdown", base + "book.md")],
        )
        self.assertEqual(self.document["schema_version"], "1.0", "the input document must not be modified")

    def test_listed_release_never_gains_or_changes_download_links(self) -> None:
        plan = plan_update(self.document, SLUG, REPO, "v1.0.0", "2026-12-01", ("pdf",))
        self.assertFalse(plan.changed)
        self.assertNotIn("assets", plan.document["books"][0]["latest_release"])
        listed = plan_update(self.document, SLUG, REPO, "v1.1.0", "2026-12-15", ("pdf", "docx")).document
        self.assertFalse(plan_update(listed, SLUG, REPO, "v1.1.0", "2026-12-15", ("pdf", "docx")).changed)
        self.rejected("must not change", SLUG, REPO, "v1.1.0", "2026-12-15", ("pdf",), document=listed)

    def test_versions_compare_numerically(self) -> None:
        self.document["books"][0] = plan_update(self.document, SLUG, REPO, "v1.9.0", "2026-12-15").document["books"][0]
        self.assertTrue(plan_update(self.document, SLUG, REPO, "v1.10.0", "2026-12-16").changed)

    def test_same_tag_is_a_no_op(self) -> None:
        plan = plan_update(self.document, SLUG, REPO, "v1.0.0", "2026-12-01")
        self.assertFalse(plan.changed)
        self.assertEqual(plan.message, "no-op: example-book already lists v1.0.0")
        self.assertEqual(plan.document, self.document)

    def test_same_tag_with_different_data_is_rejected(self) -> None:
        self.rejected("must not change", SLUG, REPO, "v1.0.0", "2026-12-02")

    def test_downgrade_is_rejected(self) -> None:
        self.rejected("downgrade", SLUG, REPO, "v0.9.9", "2026-12-15")

    def test_unknown_book_is_rejected(self) -> None:
        self.rejected("unknown book", "other-book", REPO, "v1.1.0", "2026-12-15")

    def test_malformed_tags_are_rejected(self) -> None:
        for tag in ("1.1.0", "v1.1", "v1.1.0-rc.1", "v01.1.0", "v1.1.0\n", "main", "v1.1.0;id", "v٣.1.0", "v" + "1" * 5000 + ".0.0", ""):
            with self.subTest(tag=tag):
                self.rejected("malformed tag", SLUG, REPO, tag, "2026-12-15")

    def test_malformed_dates_are_rejected(self) -> None:
        for value in ("2026-13-01", "20261215", "2026-12-15T00:00:00Z", ""):
            with self.subTest(value=value):
                self.rejected("malformed published date", SLUG, REPO, "v1.1.0", value)

    def test_malformed_source_repositories_are_rejected(self) -> None:
        for value in ("example", "example/book/extra", "../book", "example/ book", "example/book\n"):
            with self.subTest(value=value):
                self.rejected("malformed source repository", SLUG, value, "v1.1.0", "2026-12-15")

    def test_different_source_repository_is_rejected(self) -> None:
        self.rejected("human change", SLUG, "attacker/example-book", "v1.1.0", "2026-12-15")

    def test_archived_book_is_rejected(self) -> None:
        self.document["books"][0]["status"] = "archived"
        self.rejected("archived", SLUG, REPO, "v1.1.0", "2026-12-15")

    def test_invalid_input_catalog_is_rejected(self) -> None:
        del self.document["books"][0]["title"]
        self.rejected("input catalog is invalid", SLUG, REPO, "v1.1.0", "2026-12-15")

    def test_non_github_release_url_is_rejected(self) -> None:
        release = self.document["books"][0]["latest_release"]
        for field in ("url", "manifest_url", "checksums_url"):
            release[field] = release[field].replace("github.com", "example.org")
        self.rejected("GitHub Releases URLs only", SLUG, REPO, "v1.1.0", "2026-12-15")

    def test_repository_catalog_form_is_stable(self) -> None:
        path = support.REPO_ROOT / "catalog/catalog.json"
        text = path.read_text(encoding="utf-8")
        self.assertEqual(update_catalog.serialize(json.loads(text)), text)


class ReleaseRolesTests(unittest.TestCase):
    PREFIX = "https://github.com/example/example-book/releases/download/v1.1.0/"

    def asset(self, name: str, **changes) -> dict:
        return {"name": name, "state": "uploaded", "browser_download_url": self.PREFIX + name, **changes}

    def test_roles_follow_uploaded_canonical_files_in_display_order(self) -> None:
        release = {"assets": [self.asset(name) for name in ("book.md", "SHA256SUMS.txt", "book.pdf", "notes.txt")]}
        self.assertEqual(release_roles(release, REPO, "v1.1.0"), ("pdf", "markdown"))

    def test_incomplete_foreign_or_missing_assets_give_no_role(self) -> None:
        cases = (
            {},
            {"assets": "book.pdf"},
            {"assets": [self.asset("book.pdf", state="starter")]},
            {"assets": [self.asset("book.pdf", browser_download_url="https://example.org/book.pdf")]},
            {"assets": ["book.pdf", None]},
        )
        for release in cases:
            with self.subTest(release=release):
                self.assertEqual(release_roles(release, REPO, "v1.1.0"), ())


class PublishedDateTests(unittest.TestCase):
    def release(self, **changes) -> dict:
        return {"tag_name": "v1.1.0", "draft": False, "prerelease": False, "published_at": "2026-12-15T22:42:34Z", **changes}

    def test_stable_release_gives_its_date(self) -> None:
        self.assertEqual(published_date(self.release(), "v1.1.0"), "2026-12-15")

    def test_unusable_releases_are_rejected(self) -> None:
        cases = {
            "draft": self.release(draft=True),
            "prerelease": self.release(prerelease=True),
            "draft flag missing": {"tag_name": "v1.1.0", "prerelease": False, "published_at": "2026-12-15T22:42:34Z"},
            "wrong tag": self.release(tag_name="v1.2.0"),
            "null date": self.release(published_at=None),
            "bare date": self.release(published_at="2026-12-15"),
            "not an object": ["v1.1.0"],
        }
        for name, release in cases.items():
            with self.subTest(name), self.assertRaises(CatalogUpdateError):
                published_date(release, "v1.1.0")


class CommandLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        root = Path(self._temp.name)
        self.catalog = support.write_json(root / "catalog.json", support.catalog_document())
        self.release = root / "release.json"

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = update_catalog.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def apply(self, tag: str, **release) -> tuple[int, str, str]:
        support.write_json(self.release, {"tag_name": tag, "draft": False, "prerelease": False, "published_at": "2026-12-01T10:00:00Z", **release})
        return self.run_main("apply", "--catalog", str(self.catalog), "--slug", SLUG, "--tag", tag, "--source-repo", REPO, "--release-json", str(self.release))

    def test_source_repo_is_read_from_the_catalog(self) -> None:
        code, out, _ = self.run_main("source-repo", "--catalog", str(self.catalog), "--slug", SLUG, "--tag", "v1.1.0")
        self.assertEqual((code, out), (0, "example/example-book\n"))

    def test_source_repo_rejects_bad_requests(self) -> None:
        for slug, tag in ((SLUG, "main"), ("other-book", "v1.1.0")):
            with self.subTest(slug=slug, tag=tag):
                code, out, err = self.run_main("source-repo", "--catalog", str(self.catalog), "--slug", slug, "--tag", tag)
                self.assertEqual((code, out), (1, ""))
                self.assertIn("error:", err)

    def test_apply_writes_the_update(self) -> None:
        code, out, _ = self.apply("v1.1.0")
        self.assertEqual(code, 0)
        self.assertIn("updated:", out)
        self.assertEqual(json.loads(self.catalog.read_text(encoding="utf-8"))["books"][0]["latest_release"]["tag"], "v1.1.0")

    def test_apply_lists_the_uploaded_editions(self) -> None:
        prefix = "https://github.com/example/example-book/releases/download/v1.1.0/"
        assets = [{"name": name, "state": "uploaded", "browser_download_url": prefix + name} for name in ("book.pdf", "book.md")]
        code, _, err = self.apply("v1.1.0", assets=assets)
        self.assertEqual((code, err), (0, ""))
        document = json.loads(self.catalog.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], "1.1")
        self.assertEqual(document["books"][0]["latest_release"]["assets"], {"pdf": prefix + "book.pdf", "markdown": prefix + "book.md"})

    def test_apply_no_op_leaves_the_file_untouched(self) -> None:
        before = self.catalog.read_bytes()
        code, out, _ = self.apply("v1.0.0")
        self.assertEqual((code, out), (0, "no-op: example-book already lists v1.0.0\n"))
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_apply_rejection_leaves_the_file_untouched(self) -> None:
        before = self.catalog.read_bytes()
        code, _, err = self.apply("v1.1.0", prerelease=True)
        self.assertEqual(code, 1)
        self.assertIn("prerelease", err)
        self.assertEqual(self.catalog.read_bytes(), before)


class WorkflowHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    def steps(self):
        for job in self.workflow["jobs"].values():
            yield from job["steps"]

    def test_no_expression_reaches_a_shell_script(self) -> None:
        for step in self.steps():
            self.assertNotIn("${{", step.get("run", ""), step.get("name"))

    def test_actions_are_pinned_to_full_commits(self) -> None:
        for step in self.steps():
            if "uses" in step:
                self.assertRegex(step["uses"], re.compile(r"^[\w./-]+@[0-9a-f]{40}$"))

    def test_only_the_publish_job_can_write(self) -> None:
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        self.assertEqual(self.workflow["jobs"]["prepare"]["permissions"], {"contents": "read"})
        self.assertEqual(self.workflow["jobs"]["publish"]["permissions"], {"contents": "write", "actions": "write"})

    def test_the_only_push_targets_the_catalog_branch(self) -> None:
        pushes = [line.strip() for step in self.steps() for line in step.get("run", "").splitlines() if "git push" in line]
        self.assertEqual(pushes, ['git push origin "HEAD:refs/heads/$BRANCH"'])
        self.assertTrue(self.workflow["jobs"]["publish"]["env"]["BRANCH"].startswith("catalog/"))


if __name__ == "__main__":
    unittest.main()
