# Evidence — Markdown leak guard detects escaped paths

**Change:** `0025-markdown-leak-guard`. **Branch:** `fix/markdown-leak-guard-escapes`.
**Recorded:** 2026-11-11. **Defect found by:** the independent review of PR 23.

## The defect

`_reject_local_paths` in `build.py` compared this build's absolute paths against the raw rendered
Markdown. The gfm writer escapes ASCII punctuation in prose, so a path containing `_`, `*` or `[`
appears escaped and the literal comparison misses it. Reproduced while reviewing PR 23 (probe of the
unguarded build, one temporary directory in ten):

```text
FAIL: test_local_path_in_the_markdown_fails_the_build
AssertionError: BuildError not raised : a local path must fail the build: /tmp/tmp9hbyofb_/book
excerpt: 'lives at /tmp/tmp8rupjek\\_/book/manuscript.'
raw path present: False
```

Two consequences: the test flaked whenever the random temporary-directory name contained `_`, and a
real leak of the build's own path was missed in the same case. No published `book.md` is affected;
the `v0.2.6` payload contains no local path.

## The fix

- `build.py`: a new `_unescape_markdown` removes a backslash before ASCII punctuation (the CommonMark
  escape rule). `_reject_local_paths` now rejects a path found in the raw text **or** in the
  unescaped copy. Paths with fewer than three components are still ignored, and book content may
  still mention `/tmp/demo`, `/home/...` or `file://`.
- `test_build.py`: `test_local_path_guard_sees_markdown_escaped_paths` covers `_`, `*` and `[` in
  both raw and escaped form, and checks that unrelated paths pass.
  `test_local_path_in_the_markdown_fails_the_build` now runs two real builds under parents named
  `plain` and `under_score`, so the escaped case is exercised on every run instead of depending on
  the random temporary name.

## Commands and results

| Command | Result |
| --- | --- |
| `python3 -m unittest test_build.MarkdownEditionTests` | `Ran 6 tests` — `OK` |
| `test_local_path_in_the_markdown_fails_the_build` ×30 in a loop | 30/30 `OK`, 0 failures; each run performs two real builds, including the escaped `under_score` path |
| `make check` | `Ran 269 tests in 74.023s` — `OK`; `VERIFY: 5 check(s), 0 problem(s)` |
| `make full` | `Ran 269 tests in 73.190s` — `OK`; `VERIFY: 5 check(s), 0 problem(s)`; `documentation links: OK`; `VERIFY (full): 6 check(s), 0 problem(s)` |

The suite now runs 269 tests, one more than the 268 at `main`, because of the new escaped-path test.

## Versioning

No version bump: the fix is recorded under `## [Unreleased]` → `### Fixed` and ships with the next
toolkit version. Tag `toolkit-v0.6.0` and the template pins stay as tagged.

## Not done

- No release, tag, upload or deployment. No change to `STATUS.md`, `docs/decisions.md`, the template or
  the catalog.
- No real sample build was re-run for this change; the fix is covered by the two-build regression and
  a suite that already builds real books.
