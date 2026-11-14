# Record — Edition preview before publishing

**Decision:** `HUB-DEC-036`. **Recorded:** 2026-11-13. **Change:** `0028-edition-preview`.
**Scope:** WP0 of `0027-audit-plan`, finding S1.

## Problem

Four release rounds in about 26 hours showed the Owner each result only after it was published, and
each correction cost another immutable edition. Reviewers inspected the DOCX only through
LibreOffice. Nothing in a pull request showed what the editions would look like.

## What changed

- `tools/scripts/edition_preview.py` builds one book with `build-book --preview` and adds what a
  reviewer needs to judge it: the reading site unpacked, the DOCX converted to PDF by LibreOffice and
  Chromium screenshots of the site's top-level pages and its largest page, at 1440 px and 390 px, in
  light and dark. `PREVIEW.md` lists the source commit, the version, every file and each step that
  was not run. `--template` previews the hub's template book from its tracked files; `--repo`
  previews any book repository with a clean working tree.
- `ci.yml` gains the job `edition-preview`: pull requests only, read-only permissions, actions
  pinned by commit, one matrix entry for the template and one for the public sample book. Each
  uploads an artifact kept for 14 days. The job is not a required check.
- `tools/scripts/requirements-edition-preview.txt` pins the screenshot dependency. It is not a
  toolkit dependency and no book installs it.
- `docs/operations-runbook.md` documents the artifact, the local command and the Owner acceptance
  checklist before tagging.

## Design choices

- **A script, not shell in YAML.** The decisions (which pages to capture, how a preview version is
  marked, what counts as skipped) are unit-tested in `tools/tests/test_edition_preview.py`.
- **The book's pinned toolkit never runs.** The job installs the pull request's toolkit and calls it
  directly; `--preview` allows the pin mismatch and forces a prerelease version, so the output cannot
  pass for a release.
- **Pages are chosen from the built site**, not from the book descriptor: every top-level page (the
  first page and the generated lists) plus the largest page below. The script therefore does not
  depend on a book's directory layout.
- **Playwright instead of browser flags.** Emulating `prefers-color-scheme` through command-line
  flags differs between Chromium versions; the pinned package sets it through the supported API.
- **Missing tools are recorded, not hidden.** Locally the script skips the conversion or the
  screenshots and writes the reason to `PREVIEW.md`; CI passes `--require-tools`.

## Limits

- The preview does not open desktop Word. The LibreOffice PDF shows what other viewers display; the
  Word check stays a manual Owner step in the runbook.
- The sample is built from its default branch. A pull request that needs a matching book change
  fails the sample preview until the book is upgraded; the job is not required for that reason.
- Screenshots capture the top 1,800 px of each page, not the full length.
