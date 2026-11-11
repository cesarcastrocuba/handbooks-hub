# Evidence — Markdown edition, toolkit 0.6.0

**Change:** `0019-markdown-edition`. **Branch:** `feat/toolkit-0.6.0`, based on `main` after the
review fix and the merge of PR 17. **Recorded:** 2026-11-10.

## What was implemented

- `build.py`: fifth payload `markdown` → `book.md`. The edition is assembled from the canonical
  reading order in the staged workspace (front matter dropped per file, include shortcodes resolved
  against the combined document), rendered once with Quarto `gfm` (`wrap: none`, same pre-ast
  filters), then cleaned: cross-reference anchors become plain text, figure `<div>` containers become
  `*Figure N: caption*`, table containers keep the caption and the GFM table, remaining images become
  their alternative text. It opens with `edition_fields` plus `Commit`, built with
  `document_control_table` and `license_label`.
- `schemas/publication-manifest.schema.json`: `1.0` (four artifacts, no `markdown`) and `1.1` (five
  artifacts including `markdown`), each with a `contains` set so a version cannot miss a role.
- `publication.py`: `markdown` media type and `.md` suffix; `write_manifest` writes `1.1`;
  `verify_publication` derives the required roles from `schema_version`.
- `artifacts.py`: `inspect_payload(..., version=...)` checks UTF-8, the document-control header and
  the version and commit rows. A raw `<script` in prose is rejected; fenced code blocks and inline
  code spans are documentation and may show any markup. Paths such as `/tmp/`, `/home/`, `/Users/`
  and `file://` are legitimate book content and are not inspected.
- `build.py` fails before writing `book.md` when the text leaks one of this build's own absolute
  paths: the staging workspace, the output parent, the source repository and the home directory.
- `catalog_verification.py`: the expected asset count is `len(payloads) + 2` from the manifest
  (6 for `1.0`, 7 for `1.1`), kept together with the catalog download-link check merged from PR 17.
- Version `0.6.0` in `tools/pyproject.toml` and `handbook_toolkit.__version__`; template pin and
  seven-file comments updated; `CHANGELOG.md` gets `## [0.6.0] - 2026-11-10`; docs updated.

## Commands and results

| Command | Result |
| --- | --- |
| `make check` | `Ran 245 tests in 88.091s` — `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | `Ran 245 tests in 196.335s` — `OK`; `VERIFY: 5 check(s), 0 problem(s)`; `documentation links: OK`; `VERIFY (full): 6 check(s), 0 problem(s)` |
| `python3 -m unittest discover -s tools/tests -p "test_build.py"` | `Ran 19 tests in 104.708s` — `OK` (includes two real Quarto builds) |

New regression coverage: manifest `1.0` and `1.1` both verify, `1.1` without `markdown` fails,
`1.0` with `markdown` fails, duplicate role cannot replace a required payload; Markdown inspector
negatives (missing header, wrong version, wrong commit, non-UTF-8, empty); prose `<script>` rejected
while `/tmp/demo`, `/home/user`, `file://` and fenced or inline `<script>` samples pass; the build
guard raises `BuildError` for this build's paths and accepts `/tmp/demo`; a real build whose
manuscript contains the repository path fails and leaves no output; catalog gate accepts a `1.0`
release with six assets and a `1.1` release with seven, rejects a differing asset count, and keeps
main's conflicting download-link test.

## Real build of the sample book

The sample repository was not modified. It pins toolkit `0.5.0` and its metadata says `0.2.4`, so the
build ran as an explicit non-release preview at its current `HEAD`:

```bash
PYTHONPATH=tools/src python3 -m handbook_toolkit build-book \
  --repo /home/ubuntu/github/handbook-sample-01 \
  --commit e4e3f82cdb30934a71c1ea7c19f2a8b1d9166968 \
  --output /tmp/opencode/sample-build-r2 --version 0.2.5-preview --preview
```

Result: `/tmp/opencode/sample-build-r2: OK`, `commit: e4e3f82c…`, `version: 0.2.5-preview`,
`epoch: 1794352783`, `pandoc=3.10, python=3.12.3, quarto=1.11.9, typst=0.15.1, zlib=1.3`. The
earlier run used the previous sample `HEAD` (`261190b`); the sample merged its withdrawal
documentation as PR 11 in between, so the excerpt below quotes the newer commit.

Seven assets:

```text
SHA256SUMS.txt
book-html.zip
book-source.zip
book.docx
book.md
book.pdf
publication-manifest.json
```

`sha256sum -c SHA256SUMS.txt` — `OK` for all six listed files. The manifest reports
`schema_version: 1.1` with roles `docx, html, markdown, pdf, source`.

A second build into `/tmp/opencode/sample-build-r3` produced a byte-identical `book.md`
(`2c14427fecb3411a93565468fafb9ab04b09452e16ad084bfe93d9761f7e0693`), so the edition is
deterministic for this commit and toolchain. `book.md` holds 2,014 lines and contains no `<div>`,
`<a href`, `<script>`, `file://`, `/home/` or `/tmp/` occurrence.

First 25 lines of `book.md`:

```markdown
# Handbook Authoring and Publishing

| Field | Value |
| :--- | :--- |
| Title | Handbook Authoring and Publishing |
| Subtitle | A practical guide to planning, writing, reviewing and sustaining a technical handbook |
| Author | Franz César Castro Cuba |
| Version | 0.2.5-preview |
| Status | Preview build — not a released edition |
| Date | November 2026 |
| Profile | standard 1.0.0 |
| Language | English |
| Content license | CC BY-SA 4.0 |
| Code license | MIT |
| Commit | e4e3f82cdb30934a71c1ea7c19f2a8b1d9166968 |

> Markdown edition: the whole book in reading order, generated from the same source commit as the other payloads. Figures appear as their captions only; use the HTML, PDF or DOCX payload for the images. Table and figure counters run sequentially in this file.

# Document Control

#### Ownership and Review

| Field | Value |
|:---|:---|
| Approver and maintainer | Franz César Castro Cuba |
```

## Review fix (PR 19, CHANGES_REQUESTED)

The first review found that a generic absolute-path regex and an unconditional `<script` check
rejected legitimate book content: a handbook with `/tmp/` or `file://` in an example, or `<script`
in an HTML code sample, would fail its own build and its catalog verification. Fixed:

- `artifacts.py` no longer scans for local paths. The prose script check skips fenced code blocks
  (backtick or tilde) and inline code spans, so only markup that would render as HTML fails.
- `build.py` gained `_reject_local_paths`, called before `book.md` is written, with the real paths
  of this build: repository, staging workspace, output, output parent and home directory.
- Tests cover both directions: passing content with paths and code markup, failing prose script, and
  a real build failing when its manuscript contains the repository path.

The review's second item is merged: PR 17 (`feat/portal-library`) landed on `main` with catalog
`assets` links. The merge conflict in `tools/tests/test_catalog_verification.py` kept both test sets;
`test_direct_download_links_must_match_the_release_manifest` now uses the legacy four-artifact fixture
so it can still declare an absent `markdown` link. `catalog_verification.py` keeps the `declared`
link check and the manifest-derived asset count. The PR base moved from the Phase 0 branch to `main`.

## Known limits

- Table and figure counters are sequential in `book.md`; the print and HTML editions count them per
  chapter (the sample's only captioned table is `Table 1` here and `Table 2.1` there). No prose in
  the sample cites a table number, so no reference breaks; the note in the file states the limit.
- The online release gate checks the Markdown header, but it passes only the commit, not the version
  (`catalog_verification.py` is outside this change's write set). `build-book` passes both.
- Figure handling is covered by unit tests on the cleaning step; neither the template nor the sample
  contains a figure, so no real build exercised the caption replacement.

## Not run

- No release, tag, upload or deployment. No catalog or portal change.
- `catalog_verification` was not run online against a `1.1` release; none exists yet.
