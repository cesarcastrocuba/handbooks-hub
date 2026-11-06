# Book template

A starting point for an independent handbook repository. Copy this directory into a new repository,
then replace the identifiers and content. The copy is owned by the book; the hub does not update it
in place.

This template is intentionally minimal in Phase 1. Phase 2 adds the working Quarto configuration, the
pinned toolkit installation, the full chapter skeleton and the template's own checks.

## Before the first commit

1. Replace `id`, `title`, `catalog.slug` and `catalog.summary` in `book.yaml`.
2. Keep `toolkit` and `profile.version` at exact versions; never use a range.
3. Replace `01-example.qmd` with the approved brief and outline.
4. Add `LICENSE`, `LICENSE-CODE` and `NOTICE.md`.
5. Add the book's own `AGENTS.md` rules without copying hub source code.
6. Run `handbook-toolkit validate-book book.yaml --full` and the book's own checks.

## Rules

- Canonical content lives in `manuscript/`.
- Generated artifacts are never committed.
- The book pins the toolkit; it does not import a parent checkout or copy `tools/`.
- The book requests catalog listing only after an approved release.
