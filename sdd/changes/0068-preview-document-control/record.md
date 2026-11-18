# Change 0068 — Document Control validation in preview builds

Implementer OpenCode 2; reviewer and merger Claude. Branch `fix/0068-preview-document-control` from
main `2c8ba83`. No version bump or tag; this ships in the next toolkit release after
`toolkit-v0.14.0`.

## Defect

Change `0060` validates the book-owned Document Control `Version` row in every edition and accepts a
`major.minor` value only for an edition `X.Y.0`. `tools/scripts/edition_preview.py` builds a preview
with `<metadata version>-preview` (or the metadata version as is when it already carries a dash), so a
final `3.1.0` book that states Version `3.1` failed its preview build:

```text
book Document Control table version '3.1' does not match edition version '3.1.0-preview'
```

A release build (`--version 3.1.0`) passed. This surfaced when the Solutions Architecture book set
Document Control to the final `3.1` (book PR 16) while its metadata became `3.1.0` (book main
`b50911e`).

## Fix

`build_identity.py` now owns the preview suffix once, `PREVIEW_SUFFIX = "-preview"`, and
`validation_version(version, preview)` strips that suffix only for a preview build; release builds
keep the exact version. Both validation call sites use it:

- `build.py` → `inject_document_control` for the print editions;
- `reading_site.py` → `validate_document_control_version` for the HTML reading site.

`tools/scripts/edition_preview.py` imports the constant instead of defining a second copy, so the
preview identity exists in one place. The manifest and page furniture still show the preview version;
only the Document Control comparison uses the release version the preview describes. A preview of a
`3.1.0-rc.1` book passes its rc.1 version unchanged, because the suffix is not `-preview`.

## Tests

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_appendices_document_control.py
Ran 9 tests in 69.979s
OK
```

- `validation_version` strips `-preview` only when `preview=True`; `3.1.0-rc.1` and release builds are
  unchanged.
- Preview of final `3.1.0` with Version `3.1` passes; preview of `3.1.0-rc.1` with
  `3.1 (pre-release 3.1.0-rc.1)` passes.
- Release `3.1.0` with `3.0` fails; a mismatched rc release still fails; a release with the
  `-preview` identity never matches.
- A real two-build integration test (release `1.0.0` with Version `1.0`, then preview
  `1.0.0-preview`) exercises both the print and reading-site paths.

## Evidence

```text
$ make full PYTHON=.venv/bin/python
Ran 561 tests in 711.038s

OK (skipped=3)
...
VERIFY (full): 7 check(s), 0 problem(s)
```


### CI

Run 44310926423 at `6543a8b` is green on every job, including the three edition previews. The SA
edition preview built book main `b50911e7698a300fcfd233ef3c954ee6459684d5` (metadata `3.1.0`,
Document Control Version `3.1`, Status `Released`) as version `3.1.0-preview`. That is exactly the
case that failed before this change; the preview completed, and its Document Control page shows
`Version 3.1` and `Status Released`.
