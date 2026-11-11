# Evidence — Author onboarding (change 0020)

**Decision:** `HUB-DEC-029` (Proposed until the Owner merges). **Change record:**
[`record.md`](record.md). **Implemented:** 2026-11-10 on branch `feat/template-1.1.0`. **Toolkit
0.6.0 merged from `main`:** 2026-11-11.

## What changed

| Path | Change |
| --- | --- |
| `template/book/.github/workflows/ci.yml` | New: `push` and `pull_request`, installs `requirements.txt`, runs `make check`, `contents: read` |
| `template/book/.github/workflows/release.yml` | New: manual `version` input; guarded build, release and Pages deploy |
| `template/book/.github/workflows/initialize-book.yml` | New: manual identity rewrite, `make check`, branch push, compare URL |
| `template/book/.github/scripts/initialize_book.py` | New: book-owned YAML rewrite with input validation |
| `template/book/.gitignore` | New: build output, Quarto caches, Python caches, virtualenvs |
| `template/book/docs/AUTHOR_QUICKSTART.md` | New: numbered author onboarding steps |
| `template/book/README.md` | Points to the quickstart, documents the new files, `../dist` output |
| `template/book/Makefile` | Unchanged default build output `../dist`; the toolkit refuses an output inside the source repository |
| `template/book/book.yaml` | Toolkit pin `0.6.0` merged from `main` |
| `template/book/requirements.txt` | Toolkit pinned to `c200fd26924d1ba32ce203091d26ea69961ded1a`, hub main at `toolkit-v0.6.0` |
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
`docs/operations-runbook.md` and `docs/portal.md`. The template's toolkit and requirements pins were
out of scope during the first review round and were applied in the toolkit 0.6.0 integration below.

## Review fixes (2026-11-11)

The coordinator requested changes on PR 18 at `12e301b`. Fixed on the same branch:

1. **Build output.** `template/book/Makefile` keeps `OUTPUT ?= ../dist`. `handbook_toolkit`
   `build_book` refuses an output path inside the source repository, so the previous `dist` default
   would have failed for every new book. The README, the author quickstart and the `.gitignore`
   (where `dist/` remains a safety net for an explicit override) follow the same path. A new test
   resolves the Makefile default and asserts it is outside the copied book; a real default-output
   build test runs when Quarto is available.
2. **Least privilege.** All three template workflows now declare `permissions: contents: read` at
   workflow level. `release.yml` grants `contents: write` and `pages: read` only to the build job;
   the deploy job keeps `pages: write` and `id-token: write`. `initialize-book.yml` grants
   `contents: write` only to its job. A test asserts the workflow-level permissions.
3. **Release ordering.** `release.yml` uploads the Pages artifact before it creates the release, so a
   Pages packaging failure cannot leave a published release without a site. A test asserts the step
   order.

## Toolkit 0.6.0 integration (2026-11-11)

Merged `origin/main` at `c200fd26924d1ba32ce203091d26ea69961ded1a` (PR 19, `toolkit-v0.6.0`). The
conflicts were resolved by keeping both intents:

- `template/book/README.md`: the quickstart pointer and the `0.6.0` pin sentence, plus the merged
  seven-file build description and `book.md`.
- `template/book/Makefile`: `OUTPUT ?= ../dist` from this branch, plus the merged "seven-file"
  comment.
- `template/book/book.yaml`: `toolkit: "0.6.0"` from `main`; the rest of the descriptor is unchanged.
- `tools/tests/test_template.py`: the seven-file payload set and manifest `1.1`/Markdown assertions
  from `main`, plus this branch's workflow, initialization, default-output and permission tests.

The template now pins the toolkit to hub commit
`c200fd26924d1ba32ce203091d26ea69961ded1a` (`toolkit-v0.6.0`) in `requirements.txt`, and
`book.yaml` carries `toolkit: "0.6.0"`. The author guide, quickstart and template README describe
seven release files and `book.md`, the single-file Markdown edition for AI tools and plain-text
readers.

## Commands actually run

All commands ran in this worktree, `/home/ubuntu/github/handbooks-hub.worktrees/template`.

| Command | Result |
| --- | --- |
| `python3 -m unittest tools.tests.test_template tools.tests.test_export_template tools.tests.test_issue_forms tools.tests.test_docs_commands -v` | `Ran 23 tests`, `OK` |
| `make check` | `Ran 264 tests`, `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | `Ran 264 tests`, `OK`; `VERIFY (full): 6 check(s), 0 problem(s)` (documentation links included) |
| `python3 tools/scripts/export_template.py --output /tmp/opencode/template-export` | `exported 18 files`; `diff -r template/book /tmp/opencode/template-export` printed nothing |
| `actionlint template/book/.github/workflows/*.yml` | No findings (actionlint `1.7.7`) |
| `bash -n` on every `run:` script extracted from the three template workflows | No syntax errors |
| `git status --short` | Only the files listed above are staged |

The `make check` and `make full` runs include the existing template copy test and the real seven-file
build test. Quarto `1.11.9` and `pdfinfo` are installed in this environment, so the build test was
executed, not skipped. The runs reported above were repeated after merging `origin/main` (change
`0021`, portal library, and then `toolkit-v0.6.0`), so the test count includes those changes' tests
and the review fixes.

### What the tests prove

- A copy of `template/book/` outside the hub passes its own `make check` and, when Quarto is
  available, builds exactly the seven verified payloads: HTML ZIP, PDF, DOCX, Markdown, source ZIP,
  publication manifest and checksums.
- The built manifest uses schema `1.1`, declares the `markdown` role, and `book.md` records the
  version and commit and contains the chapter text.
- The template Makefile's default `OUTPUT` resolves outside the copied book directory, and
  `make build` with that default succeeds on the copy (when Quarto and `pdfinfo` are available).
- `initialize_book.py` rewrites the identifiers on a copy, leaves `.github/` byte-identical, produces
  a tree that passes `validate-book --full`, refuses a second run and rejects a bad id, a category
  outside the vocabulary, a 281-character summary, an empty title and a non-GitHub repository URL
  without writing anything.
- Every `uses:` in the template workflows is pinned to a 40-character commit SHA that the hub's own
  workflows already use.
- The workflow-level permissions of all three template workflows are `contents: read`; write
  permissions exist only on the jobs that need them.
- No `${{ ... }}` expression appears inside any `run:` script in the template workflows.
- The release is published only after the Pages artifact has been uploaded, so a Pages packaging
  failure cannot leave a release without a site.
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
- The default build output stays `../dist`, outside the book repository, because the toolkit refuses
  an output path inside the source tree. `.gitignore` still ignores `dist/` as a safety net for an
  explicit `OUTPUT=dist`.

## Follow-up (coordinator)

- Merge, then export and tag the mirror `template-v1.1.0`, mark it as a template, and run the
  throwaway dry run described in `record.md`.
