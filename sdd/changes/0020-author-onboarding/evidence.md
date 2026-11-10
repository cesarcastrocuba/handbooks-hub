# Evidence — Author onboarding (change 0020)

**Decision:** `HUB-DEC-029` (Proposed until the Owner merges). **Change record:**
[`record.md`](record.md). **Implemented:** 2026-11-10 on branch `feat/template-1.1.0`.

## What changed

| Path | Change |
| --- | --- |
| `template/book/.github/workflows/ci.yml` | New: `push` and `pull_request`, installs `requirements.txt`, runs `make check`, `contents: read` |
| `template/book/.github/workflows/release.yml` | New: manual `version` input; guarded build, release and Pages deploy |
| `template/book/.github/workflows/initialize-book.yml` | New: manual identity rewrite, `make check`, branch push, compare URL |
| `template/book/.github/scripts/initialize_book.py` | New: book-owned YAML rewrite with input validation |
| `template/book/.gitignore` | New: build output, Quarto caches, Python caches, virtualenvs |
| `template/book/docs/AUTHOR_QUICKSTART.md` | New: numbered author onboarding steps |
| `template/book/README.md` | Points to the quickstart, documents the new files, `dist` output |
| `template/book/Makefile` | Default build output changed from `../dist` to `dist` so it stays inside the book |
| `tools/scripts/export_template.py` | New: deterministic export of the tracked template tree |
| `tools/tests/test_export_template.py` | New: export equality, determinism and refusal tests |
| `tools/tests/test_issue_forms.py` | New: issue-form YAML and required-field tests |
| `tools/tests/test_template.py` | Extended: workflows, pinning, expressions, initialization |
| `.github/ISSUE_TEMPLATE/request-listing.yml` | New listing issue form |
| `.github/ISSUE_TEMPLATE/request-withdrawal.yml` | New withdrawal issue form |
| `.github/ISSUE_TEMPLATE/config.yml` | Blank issues enabled |
| `docs/author-guide.md` | New end-to-end author guide |
| `docs/template-distribution.md` | New mirror export and release procedure |
| `CONTRIBUTING.md` | "Adding a book" now describes the real path |

Out of scope and untouched: `tools/src/**`, `docs/decisions.md`, `STATUS.md`, `CHANGELOG.md`,
`docs/operations-runbook.md`, `docs/portal.md`, `template/book/requirements.txt` and the `toolkit:`
value in `template/book/book.yaml` (the coordinator pins toolkit `0.6.0` afterwards).

## Commands actually run

All commands ran in this worktree, `/home/ubuntu/github/handbooks-hub.worktrees/template`.

| Command | Result |
| --- | --- |
| `python3 -m unittest tools.tests.test_template tools.tests.test_export_template tools.tests.test_issue_forms tools.tests.test_docs_commands -v` | `Ran 19 tests`, `OK` |
| `make check` | `Ran 223 tests`, `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | `Ran 223 tests`, `OK`; `VERIFY (full): 6 check(s), 0 problem(s)` (documentation links included) |
| `python3 tools/scripts/export_template.py --output /tmp/opencode/template-export` | `exported 18 files`; `diff -r template/book /tmp/opencode/template-export` printed nothing |
| `actionlint template/book/.github/workflows/*.yml` | No findings (actionlint `1.7.7`) |
| `bash -n` on every `run:` script extracted from the three template workflows | No syntax errors |
| `git status --short` | Only the files listed above are staged |

The `make check` and `make full` runs include the existing template copy test and the real six-file
build test. Quarto `1.11.9` and `pdfinfo` are installed in this environment, so the build test was
executed, not skipped.

### What the tests prove

- A copy of `template/book/` outside the hub passes its own `make check` and, when Quarto is
  available, builds exactly the six verified payloads.
- `initialize_book.py` rewrites the identifiers on a copy, leaves `.github/` byte-identical, produces
  a tree that passes `validate-book --full`, refuses a second run and rejects a bad id, a category
  outside the vocabulary, a 281-character summary, an empty title and a non-GitHub repository URL
  without writing anything.
- Every `uses:` in the template workflows is pinned to a 40-character commit SHA that the hub's own
  workflows already use.
- No `${{ ... }}` expression appears inside any `run:` script in the template workflows.
- Both issue forms parse as YAML with the required top-level fields and required inputs, the catalog
  vocabulary is used, and blank issues are enabled.
- The export tree equals the tracked `template/book/` tree file-for-file, including dotfiles, and
  refuses a non-empty or in-template output directory.

## Not run

- The three template workflows were **not executed on GitHub**. No repository was created from the
  mirror and no `initialize-book.yml` dispatch was performed. Workflow validity rests on YAML
  parsing, `actionlint` and `bash -n`, not on a live run.
- No release was published to GitHub Releases and no Pages deployment was performed.
- The mirror `cesarcastrocuba/handbooks-template` was not pushed or tagged `template-v1.1.0`, and the
  repository was not marked as a template; both are Owner actions after merge.
- No initialized book was built end to end with Quarto; only `validate-book --full` was run on the
  initialized copy.
- The hub portal was not rebuilt and the catalog was not changed.

## Known limits

- `initialize_book.py` uses `yaml.safe_dump`, so the generated `book.yaml`, `_quarto.yml` and
  `metadata.yaml` lose the template comments. The resulting files are valid and reviewed through the
  initialization pull request.
- The release workflow requires the repository's Pages source to be **GitHub Actions** and a public
  repository for the unauthenticated `git fetch --tags`; the quickstart states both.
- The default build output moved from `../dist` to `dist` so it stays inside the book; the README and
  `.gitignore` follow the same path.

## Follow-up (coordinator)

- Pin toolkit `0.6.0` in `template/book/book.yaml` and `template/book/requirements.txt`.
- Merge, then export and tag the mirror, mark it as a template, and run the throwaway dry run
  described in `record.md`.
