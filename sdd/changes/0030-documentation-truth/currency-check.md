# Record — Documentation currency check

**Change:** `0030-documentation-truth` (second part of WP2 of `0027-audit-plan`). **Recorded:**
2026-11-14. The first part corrected findings D1 to D4 by hand; this part keeps them corrected.

## Problem

`README.md` named sample `v0.2.7` three releases after it was replaced, and three documents called
the publication pipeline "future" while it was in use. Nothing failed, because a version written
into a sentence has no connection to the file that owns it.

## What changed

`verify --full` gains a seventh check, `documentation currency`
(`tools/src/handbook_toolkit/doc_currency.py`):

| Statement in prose | Source of truth | Rule |
| --- | --- | --- |
| ``toolkit `X.Y.Z` `` in `README.md` or `STATUS.md` | `tools/pyproject.toml` (in development) and the pin in `template/book/book.yaml` (released) | Must be one of the two |
| ``template `X.Y.Z` `` in `README.md` or `STATUS.md` | Heading of `template/book/README.md` | Must be equal |
| `` `<catalog slug>` `vX.Y.Z` `` in `README.md` | `catalog/catalog.json` | Not allowed: link to the catalog |
| "future publication", "Status: planned" in a root document or `docs/*.md` | — | Not allowed outside history |

History is not checked: `docs/decisions.md`, `docs/implementation-plan.md`, `docs/book-upgrade.md`,
`CHANGELOG.md` and everything under `sdd/`.

`README.md` no longer names the sample's release; it links to the catalog.

## Design choices

- **The README does not repeat the catalog.** `catalog-update` pushes a branch that changes only
  `catalog/catalog.json`. A rule "the README must equal the catalog" would fail that automated
  branch, so the duplicate is removed instead of synchronised.
- **`STATUS.md` may lag the catalog, not the toolkit.** The status record is written after a
  release is verified, so its catalog row is not checked. Its toolkit and template statements are:
  the pull request that moves the template pin is written by a person or agent, who updates the
  status in the same change.
- **Two toolkit versions are current.** Between the merge of a toolkit change and its tag,
  `pyproject.toml` is ahead of the template pin; both are accepted.
- **Narrow patterns.** Only a version in backticks directly after the word is a statement. "Yes from
  toolkit `0.6.0`" in other documents is a fact about history and is outside the two checked files.

## Limits

- The check cannot tell that a sentence without a version is false. Review still owns that.
- A current-state claim in any other document (for example `docs/design.md`) is not checked.
