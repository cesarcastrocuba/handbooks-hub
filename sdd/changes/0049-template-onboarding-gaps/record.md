# Change 0049 — Template Onboarding Gaps (G1, G10, G11)

Implementation of template onboarding gaps G1, G10, and G11 identified in change 0048 (PR #82)
under Owner decision `HUB-DEC-043`. These changes resolve friction for reference books publishing
candidate releases and configuring branch protection. No template version bump or tag is created
here; these updates ship with template 1.7.0 alongside toolkit 0.12.0.

## Pins and Scope

- **Hub Base**: `c6032fe64d355fcb5f863037a03d688c947ffb21` (`origin/main`, merge of PR 82).
- **Branch / Worktree**: `feat/0049-template-onboarding-gaps`, `/home/ubuntu/github/handbooks-hub.worktrees/tpl-gaps`.
- **Write set**:
  - `template/book/.github/workflows/release.yml`
  - `template/book/.github/scripts/initialize_book.py`
  - `template/book/docs/AUTHOR_QUICKSTART.md`
  - `docs/author-guide.md`
  - `docs/book-upgrade.md`
  - `CHANGELOG.md`
  - `tools/tests/test_template.py`
  - `sdd/changes/0049-template-onboarding-gaps/record.md`

`STATUS.md` and `docs/decisions.md` are deliberately not edited.

## Implemented Behaviors

1. **G1 — Pre-Release Editions (`release.yml`)**:
   - `release.yml` input validation relaxed to accept `^[0-9]+\.[0-9]+\.[0-9]+(-rc\.[1-9][0-9]*)?$`.
   - Rejects invalid tags, bare RC tags without number, leading zeros (`-rc.0`, `-rc.01`), and arbitrary pre-release strings.
   - For releases matching `-rc\.`, `gh release create` is invoked with `--prerelease --latest=false`.
   - The HTML edition deployment to GitHub Pages and the read-only post-deployment `site_check` job run for both RC and stable releases, allowing author/owner verification on the live reading site.
   - Verified that `catalog.schema.json` and `catalog_verification.py:169` continue to strictly reject pre-release tags from catalog listings.

2. **G10 — Required Check Name Alignment**:
   - Updated `docs/author-guide.md` and `template/book/docs/AUTHOR_QUICKSTART.md` to specify `Fast checks` as the exact status check name required in branch protection rules on `main`.
   - The underlying job in `ci.yml` (`check`, with `name: Fast checks`) remains untouched, preserving compatibility with existing books.

3. **G11 — Tailored Book README Generation (`initialize_book.py`)**:
   - `initialize_book.py` now replaces the template boilerplate README with a tailored book README containing:
     - H1 title and catalog summary provided during initialization.
     - Pointers to contributor governance (`AGENTS.md`) and attribution (`NOTICE.md`).
     - Conditional pointers to `PROJECT_STATUS.md` and `DECISIONS.md` if present in the book root (note: the template repository does not include these files by default, so these links are omitted during first-time initialization from the template workflow, but fire when initialized locally or when a book repository creates them beforehand).
     - Local virtual environment setup and validation commands (`make check`, `make full`).

## Verification Evidence

- In worktree `/home/ubuntu/github/handbooks-hub.worktrees/tpl-gaps`:
  - Focused template tests:
    `PYTHONPATH=tools/src /tmp/codex-pr82-venv/bin/python -m unittest tools/tests/test_template.py`:
    **Ran 25 tests in 37.096s, OK** (all workflow, initialization, and build tests passed).
  - Fast verify:
    `PYTHONPATH=tools/src /tmp/codex-pr82-venv/bin/python -m handbook_toolkit --root . verify`:
    **5 check(s), 0 problem(s)**.
  - Full check suite:
    `make full PYTHON=/tmp/codex-pr82-venv/bin/python`:
    **Ran 440 tests in 283.491s, OK (skipped=3); VERIFY (full): 7 check(s), 0 problem(s)**.
  - Whitespace & format check:
    `git diff --check`: **Clean, exit code 0**.

## What Was NOT Run

- Manual `gh workflow run release.yml` dispatch was not executed against a live book repository (workflow changes are tested via schema validation, regex unit tests, and structural AST tests).
