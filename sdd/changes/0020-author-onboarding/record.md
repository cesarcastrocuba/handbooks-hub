# Change 0020 — Author onboarding

**Decision:** `HUB-DEC-029` (Proposed until the Owner merges). **Plan:** Phase C of the plan summarised
in change `0018`.

## Problem

Creating a book means copying `template/book/` by hand. The template has no workflows, neither
repository is a GitHub template, and nothing tells an author how a book gets listed or withdrawn.

## Change

1. **Template `1.1.0`** (`template/book/`): pin toolkit `0.6.0` by commit, add `.gitignore`,
   `docs/AUTHOR_QUICKSTART.md` and three workflows: `ci.yml` (`make check`), `release.yml` (guarded
   release adapted from the sample book) and `initialize-book.yml`.
2. **`initialize-book.yml`**: manual dispatch with title, identifier, author, summary and category.
   It rewrites the descriptor, Quarto metadata and notices, pushes branch `init/<id>` and prints a
   compare link. It refuses to run once the book identifier is no longer `template-book`. It does not
   open a pull request and does not change workflow files, because the default token of a new
   repository may do neither.
3. **Mirror repository** `cesarcastrocuba/handbooks-template`: `tools/scripts/export_template.py`
   writes the template tree to a directory; the result is pushed and tagged `template-v1.1.0`. The
   mirror is generated and is not edited directly. Marking it as a template is an Owner action.
4. **Issue forms** in `.github/ISSUE_TEMPLATE/`: `request-listing.yml` and `request-withdrawal.yml`.
5. **Guides**: `docs/author-guide.md` and the "Adding a book" section of `CONTRIBUTING.md`.

## Rules that do not change

- First listing of a book and every withdrawal are manual, reviewed catalog pull requests merged by
  the Owner. `catalog-update` still only moves a listed book to a newer release.
- Books pin the toolkit and never copy shared scripts (`HUB-DEC-002`).

## Verification planned

- `make check` and `make full` in the hub, including the template copy test.
- Export to a temporary directory and compare it with `template/book/`.
- Dry run of `initialize-book.yml` in a throwaway repository created from the mirror.

Evidence is recorded in this folder by the implementing pull request.
