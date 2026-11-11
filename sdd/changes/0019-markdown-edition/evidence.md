# Evidence — Markdown edition, toolkit 0.6.0

**Change:** `0019-markdown-edition`. **Branch:** `feat/toolkit-0.6.0`, stacked on
`docs/decision-027-withdraw-v0.2.2`. **Recorded:** 2026-11-10.

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
- `artifacts.py`: `inspect_payload(..., version=...)` checks UTF-8, the document-control header, the
  version and commit rows, and rejects raw `<script>` and absolute local paths.
- `catalog_verification.py`: the expected asset count is `len(payloads) + 2` from the manifest
  (6 for `1.0`, 7 for `1.1`); no catalog `assets` logic was added.
- Version `0.6.0` in `tools/pyproject.toml` and `handbook_toolkit.__version__`; template pin and
  seven-file comments updated; `CHANGELOG.md` gets `## [0.6.0] - 2026-11-10`; docs updated.

## Commands and results

| Command | Result |
| --- | --- |
| `make check` | `Ran 224 tests in 125.254s` — `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | Same tests pass; `VERIFY: 5 check(s), 0 problem(s)`; `documentation links: OK`; `VERIFY (full): 6 check(s), 0 problem(s)` |
| `python3 -m unittest discover -s tools/tests -p "test_build.py"` | `Ran 17 tests in 35.816s` — `OK` (includes the real Quarto build) |

New regression coverage: manifest `1.0` and `1.1` both verify, `1.1` without `markdown` fails,
`1.0` with `markdown` fails, duplicate role cannot replace a required payload; Markdown inspector
negatives (missing header, wrong version, wrong commit, non-UTF-8, absolute path, `<script>`, empty);
catalog gate accepts a `1.0` release with six assets and a `1.1` release with seven, and rejects a
release whose asset count differs from the manifest.

## Real build of the sample book

The sample repository was not modified. It pins toolkit `0.5.0` and its metadata says `0.2.4`, so the
build ran as an explicit non-release preview at its current `HEAD`:

```bash
PYTHONPATH=tools/src python3 -m handbook_toolkit build-book \
  --repo /home/ubuntu/github/handbook-sample-01 \
  --commit 261190b0515729e7135405e184da1440815fa215 \
  --output /tmp/opencode/sample-build --version 0.2.5-preview --preview
```

Result: `/tmp/opencode/sample-build: OK`, `commit: 261190b0…`, `version: 0.2.5-preview`,
`epoch: 1794352248`, `pandoc=3.10, python=3.12.3, quarto=1.11.9, typst=0.15.1, zlib=1.3`.

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

A second build into `/tmp/opencode/sample-build-2` produced a byte-identical `book.md`
(`8694eb97bc13bbdce875e4ed8e8ca686537967678e513a7bc1be38707d9c8582`), so the edition is
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
| Commit | 261190b0515729e7135405e184da1440815fa215 |

> Markdown edition: the whole book in reading order, generated from the same source commit as the other payloads. Figures appear as their captions only; use the HTML, PDF or DOCX payload for the images. Table and figure counters run sequentially in this file.

# Document Control

#### Ownership and Review

| Field | Value |
|:---|:---|
| Approver and maintainer | Franz César Castro Cuba |
```

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
