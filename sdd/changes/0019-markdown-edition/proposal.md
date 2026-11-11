# Proposal — Markdown edition, toolkit 0.6.0

**Change:** `0019-markdown-edition`. **Decisions:** `HUB-DEC-027` (delegation), `HUB-DEC-028`
(Markdown edition, approved in Phase A). **Branch:** `feat/toolkit-0.6.0`.

## What

The toolkit gains a fifth payload and the publication manifest gains schema `1.1`:

- `build-book` renders one `book.md` with Quarto `gfm` from the canonical sources in reading order
  (front matter, chapters, appendices, references) and assembles it with the reviewed payloads.
- The file opens with the document-control fields of the other editions plus the source commit, so
  a reader can identify the edition without the manifest.
- Headings, tables, code blocks, callout text and cross-reference text stay. Quarto's raw HTML
  (`<div>` wrappers and `<a>` cross-reference anchors) is reduced to plain Markdown, and each figure
  becomes its caption or alternative text because one file cannot carry the images.
- The manifest records `schema_version: "1.1"` with five artifacts. `1.0` with four artifacts stays
  valid, because the hub must keep verifying the published sample `v0.2.4` (six assets) until
  `v0.2.5` is listed.
- `publication.py` knows the `markdown` role (media type and `.md` suffix), writes `1.1` and verifies
  both versions. `artifacts.py` inspects `book.md`: header, identity and a raw `<script` in prose,
  while fenced code blocks and inline code spans stay documentation. `build.py` rejects a leak of the
  build's own absolute paths. `catalog_verification.py` derives the release asset count from the
  manifest instead of a fixed six, next to the catalog download-link check.
- `docs/` describes seven assets, the Markdown limits and the `0.5.0` to `0.6.0` migration.

## Why

The platform publishes reading (HTML), print (PDF) and editable (DOCX) editions, but nothing that a
search index, a diff or an AI tool can consume directly. One Markdown file per release closes that
gap without a second content pipeline: it is rendered from the same approved commit and shipped in
the same verified release, so the manifest still proves which bytes belong together.

## Compatibility

- **Additive for books:** `publication.formats` in `book.yaml` does not change. Markdown is implicit,
  like the source bundle, so the book schema and profile need no bump.
- **Migration:** a book bumps its `toolkit` pin and `requirements.txt` commit and updates any release
  workflow that uploads a fixed list of six files. Recorded in `docs/book-upgrade.md` under
  `HUB-DEC-014`.
- **Readers of the manifest:** schema `1.0` remains valid and verifiable. A producer that assumes
  "exactly four artifacts" must accept five; the toolkit's own verifier and the online release gate
  both derive the set from `schema_version`.
- **Catalog:** this change does not add catalog `assets` links; that is the portal and catalog change
  that follows, and `catalog_verification.py` changes only its asset-count logic.

## Out of scope

- Portal rendering and `llms.txt` (`portal.py` and `docs/portal.md` belong to another writer).
- The template export, issue forms and author guide (Phase C).
- The sample `v0.2.5` release and its catalog update (Phase D).
