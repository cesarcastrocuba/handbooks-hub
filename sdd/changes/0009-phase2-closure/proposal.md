# Proposal — Phase 2 closure

**Status:** Ready for owner gate
**Change:** `0009-phase2-closure`
**Branch:** `feat/phase2-closure`
**Base:** `origin/main` at `66d0581689e1e9c91913da25b5cb4a7723f3ec5c`

## Context

Phase 1, manuscript validation, shared render resources and the local publication build are
integrated. Phase 2 still needs the approved profile `1.0.0` classification, the buildable template
`1.0.0`, a consistent toolkit version and the release-blocking Typst chapter-title fix.

## Scope

- Suppress the Typst orange-book chapter-title block that overflowed the right page edge, and prove
  the result from rendered PDF pages.
- Standard profile `1.0.0`: keep the approved `0.2.0` rules unchanged, require an explicit
  `automated`/`assisted`/`manual` classification for every rule, keep `0.2.0` resolvable and compare
  both packaged snapshots byte-for-byte with the maintained profile.
- Book template `1.0.0`: publishing configuration, metadata, licenses, notice, `make check`/`build`/
  `full`, and a test that copies the template outside the hub, replaces identifiers, runs the checks
  and performs a real six-file build.
- Toolkit `0.4.0`: consistent package, CLI, tests, template pin, CI expectation and changelog.
- Document the supported book upgrade procedure.

## Required behavior

- Profile `1.0.0` must be schema-valid, approved, and reject missing or duplicate rule
  classifications.
- The template must contain no copied toolkit source and must pass its own checks from a temporary
  copy with no parent checkout.
- `build-book` must keep resolving the book's exact packaged profile pin, run the reference gate and
  manuscript gate before rendering, and remain atomic.
- The generated Typst project must stage a white brand primary and an explicit black link color.
- The Typst block must be inspected in rendered PDF pages, not inferred from a green test.

## Evidence

- `make check`: 160 unit tests plus fast repository verification.
- `make full`: fast checks plus full repository verification including documentation links.
- `test_template.py`: 3 tests, including a real template copy build of the six payloads.
- Rendered sample-pilot PDF (7 pages) and template PDF (5 pages): the chapter title renders as plain
  black text inside both margins with no coloured block or ink past the right page edge; no blank
  title page; `Table 1.1 — …` renders below its table.
- CI at the exact pushed HEAD (recorded in the pull request or handoff).

## Out of scope

No merge to `main`, no tag, no deployment, no release, no catalog entry and no sample-book chapter
expansion. The owner approves the Phase 2 gate after independent review.
