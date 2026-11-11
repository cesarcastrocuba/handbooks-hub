# Evidence — Template 1.1.1 text-preserving initialization

**Change:** template 1.1.1, initialize-book comment preservation and the release tag check.
**Branch:** `fix/template-1.1.1`. **Implemented:** 2026-11-11.

## Problem

`template/book/.github/scripts/initialize_book.py` rewrote `book.yaml`, `publishing/_quarto.yml`
and `publishing/metadata.yaml` with `yaml.safe_dump`. That dropped every comment and the template's
quoting (`toolkit: "0.6.0"` became `toolkit: 0.6.0`), and it reformatted key order and blank lines.
A second defect appeared in a real private-repository run of the release workflow: the workflow
checked out with `persist-credentials: false` and then ran `git fetch --tags --force origin`, which
fails without a credential helper.

## Change

1. **Text-preserving rewrite.** `initialize_book.py` now edits the three YAML files as text:
   `set_scalar` replaces only the value after a key, keeping indentation, the space after the colon
   and the line ending; `set_sequence` replaces only the `categories` list items at their existing
   indentation. Comments, quoting, key order, blank lines and every other byte survive.
2. **Safe scalars.** Every written value is a JSON string, which is a valid YAML double-quoted
   scalar and is guaranteed to stay on one physical line for colons, double and single quotes,
   `#`, leading or trailing spaces and non-ASCII text.
3. **Exact round-trip check.** Before writing, the script parses each edited text and compares it
   with the expected document built from the parsed original. It refuses to continue if a requested
   value does not round-trip or if any unrelated key changed. It then writes all six files, re-loads
   the three YAML files, compares them again, verifies the written bytes, and restores the originals
   if anything fails.
4. **Inputs are no longer stripped.** Validation still rejects blank titles, authors and summaries,
   but the exact input is written, so leading and trailing spaces round-trip.
5. **Version 1.1.1.** `template/book/README.md` heading and the `docs/template-distribution.md`
   export, commit and `template-v1.1.1` tag examples.
6. **Release tag check through the API.** `release.yml` no longer runs `git fetch`; it checks the
   tag with `gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$TAG"` using the `GH_TOKEN` already on
   that step.
7. **Tests.** `tools/tests/test_template.py` now checks that only the intended lines change in all
   three YAML files, that comments and quoting survive, that awkward inputs round-trip exactly with
   unrelated keys unchanged, and that no template workflow runs `git fetch` or `git push` after a
   `persist-credentials: false` checkout without explicit authentication.

## Commands actually run

All commands ran in this worktree, `/home/ubuntu/github/handbooks-hub.worktrees/template`.

| Command | Result |
| --- | --- |
| `python3 /tmp/opencode/init-text/.github/scripts/initialize_book.py --root /tmp/opencode/init-text --id platform-handbook --title 'A: "quoted" #hash '\''single'\'' — Ünïcode' --author '  Zoë O'\''Brien: #1 "Author"  ' --summary 'A: summary # with '\''single'\'', "double", ünïcode. ' --category engineering --repository-url https://github.com/example/platform-handbook` | Succeeded; comments and quoting preserved, every changed value double-quoted |
| `python3 -m handbook_toolkit --root /tmp/opencode/init-text validate-book --full` (with `PYTHONPATH=tools/src`) | `: OK` |
| `python3 -m unittest tools.tests.test_template -v` | `Ran 15 tests`, `OK` (before the two release-workflow tests were added) |
| `python3 -m unittest tools.tests.test_template.TemplateWorkflowTests -v` | `Ran 8 tests`, `OK` |
| `actionlint template/book/.github/workflows/*.yml` (1.7.7) | No findings |
| `make check` | `Ran 268 tests`, `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | `Ran 268 tests`, `OK`; `VERIFY (full): 6 check(s), 0 problem(s)` (documentation links included) |

The real template build test ran: Quarto `1.11.9` and `pdfinfo` are installed here, so the copied
template produced the seven verified payloads, including `book.md`.

One earlier `make full` invocation after a long `make check` reported one failure. Its output was
filtered and the failing test name was not captured. The immediately following `make full` and
`make check` both passed, and no failure has reproduced since. It is recorded here rather than
hidden; it is not attributed to this change.

## Release workflow runs (reported by the coordinator)

Both runs were executed by the coordinator in a private throwaway repository; they were not executed
from this worktree.

| Run | Result |
| --- | --- |
| `43041194049`, throwaway repository | Failed at `git fetch --tags --force origin`: `fatal: could not read Username for https://github.com` because the checkout used `persist-credentials: false` |
| `43041314185`, throwaway repository | With the API tag check, the release workflow built, published seven assets and deployed Pages successfully |

## Not run

- The template workflows were not executed on GitHub from this branch; the push will start the
  hub's own checks. The two runs above were executed by the coordinator, not here.
- No mirror export, tag or template-setting change was performed.
- No initialized book was built end to end here; the initialized copy was validated with
  `validate-book --full`.

## Files

- `template/book/.github/scripts/initialize_book.py`
- `template/book/.github/workflows/release.yml`
- `template/book/README.md`
- `docs/template-distribution.md`
- `tools/tests/test_template.py`
- `sdd/changes/0023-template-1.1.1/evidence.md`

## End-to-end run from the template-v1.1.1 tree (2026-11-11)

The missing end-to-end check was completed later in the throwaway repository
`cesarcastrocuba/handbook-template-dryrun-delete-me`:

- `main` was reset to the exact `template-v1.1.1` tree: commit `f0e264afda43ee6cdb9afbcb9bb9884ca4ae385e`,
  whose tree is identical to the tree of tag `template-v1.1.1` (`f07a7af`); the file list matches.
- `initialize-book` run 43114371187 succeeded on `main` with the title
  `Field Notes: "Day 2" Operations # Draft`, id `field-notes` and author `Ana Ñandú`.
- Branch `init/field-notes` changed six files: `book.yaml` +6 −6, `publishing/_quarto.yml` +2 −2,
  `publishing/metadata.yaml` +2 −2, `NOTICE.md` +2 −2, `LICENSE-CODE` +1 −1 and `README.md` +1 −2.
  `book.yaml` kept its header comments and the quoting of the untouched values.
- Its pull request passed the template `ci` check (run 43114478414) and was merged.
- Release run 43114575628 succeeded (build, verify and publish; deploy the HTML edition) and published
  `v0.2.0` with seven assets; `sha256sum -c SHA256SUMS.txt` is OK for the six listed files. `book.md`
  opens with version `0.2.0` and the title, and the Pages site shows the title with its quotes and `#`.
- Not done: nothing else. The throwaway repository still awaits the Owner's deletion.
