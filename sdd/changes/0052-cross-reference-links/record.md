# Change 0052 — Opt-in cross-reference links (G8)

## Scope and provenance

Owner brief: cross-reference portion of `brief-0052-0053-reference-navigation.md`.
Implementer branch `feat/0052-cross-reference-links`, based on hub main `95658f9817b808351360e30e1f72bb87a398f1b1`.
Claude reviews and merges. No self-merge, version bump or tag.

The cue rules and tests' intent come from the author's MIT reference builder and tests at
frozen `13d295bfb266c6fb03b8d244666ebbf0e056e6cd`. The reference clone is read-only. No manuscript prose is copied into the hub;
all committed fixtures are synthetic. Actual source hashes (`sha256sum`):

```text
5ea96307c586e6e934fb9b7b6e7f9f451731172ddffd8d64827e28d45c5fe514  /tmp/agy-sa/src/scripts/build_book.py
9c811f5685b6a2ab88177eb0ba95da5f41f35bddc325c6f9fe57a2eadf37f452  /tmp/agy-sa/src/scripts/tests/test_build_book.py
```

Write set: `xref_links.py`, build orchestration in `build.py`, the packaged book schema,
`test_xref_links.py`, the synthetic runtime test in `test_build.py`, publication-build docs,
CHANGELOG and this record. `build_staging.py` is untouched, keeping PR 87's numbering work separable.

## Design

`publication.cross_reference_links` is an optional boolean, default false. When enabled, a
whole-book registry is collected before staging strips heading numbers. Existing IDs remain
authoritative; only registered targets link. Numbered section IDs are Word-safe `sec_ch_N`,
`sec_app_a`, `sec_N_M` and `sec_a_N`, identical in HTML/PDF/DOCX. Duplicate/ambiguous targets fail.
The existing Word encoder continues to handle figure/table and explicit author IDs.

Generated links carry `handbook-xref`. Print writers get fragment links; only after print does
HTML staging rebase these links to their owning pages. The root-source alias is handled explicitly.
Code/fences/YAML/comments, headings, image/caption lines, existing links, bibliography and value
contexts are excluded. Explicit reference columns cannot turn protocol versions into links.
Unlike the legacy builder, bibliography lines suppress named references too, as required by this
brief. Terminal full stops after chapter numbers work; value ranges stay plain at both ends.

No glossary auto-linking, glossary pointers or analytic Index: change 0053 owns those features.
The opt-in path gives unnumbered captioned tables file-scoped IDs to avoid collisions with numbered
chapter labels before change 0051 lands. It does not change displayed figure/table numbering.

## Verification

Evidence is appended below from real commands before handoff. Runtime evidence includes the
synthetic two-chapter build, disabled sample comparison, and the opted-in real-book scratch build.
The disabled sample's uncontrolled raw runs differ only in Quarto sitemap lastmod timestamps.
A second pair controls staged QMD mtimes equally in the scratch harness; production is unpatched.
Full SHA/manifest comparison results will be recorded, without claiming raw equality if it fails.

## Rollback and not-run items

Remove the optional schema property, orchestration calls and xref module/tests/docs as one unit.
Books without the opt-in never execute this module. No release, deployment, Owner desktop Word
acceptance or editorial approval is performed. The real-book proof uses profile 1.1.0 in scratch;
the canonical book is untouched. PR 87's numbering behavior is outside this change.
