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
chapter labels before change 0051 lands. Unnumbered table IDs use a short file hash so Pandoc/Word cannot truncate them. The runtime fixture covers an unnumbered front table. It does not change displayed figure/table numbering.

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

## Root-source alias verification

The runtime fixture also opts in a book with `manuscript.root: .` and first source
`index.qmd`, verifying that inbound links resolve to `handbook-source-index.html#sec_ch_1`.
The navigation rewriter normalizes `./index.qmd` itself instead of relying on the existing
index-resource filter's fallback. That fallback already preserved valid production links;
this change makes the navigation helper self-contained for the path form returned by reading order.

```text
.venv/bin/python -m unittest discover -s tools/tests -p test_build.py -k root_source_index_links -v
Ran 1 test in 17.328s
OK
```

## Pre-rebase evidence and current dependency

The implementation below is verified on original base 95658f9. PR 87 at 1fe1fff is held by
review Major R5: its custom PDF outline entries flow as run-on paragraphs. This branch remains
on the original base until 0051 is fixed and merged. The draft PR is not a merge-ready handoff.
After rebasing, navigation's unnumbered float IDs must use 0051's native continuous `0.N`/`BM.N`
contract, followed by fresh real-book and sample evidence. No source changes were made to PR 87.

### Focused and full checks

```text
.venv/bin/python -m unittest discover -s tools/tests -p test_xref_links.py -v
----------------------------------------------------------------------
Ran 13 tests in 0.033s

OK
make full PYTHON=.venv/bin/python
Ran 476 tests in 335.018s
OK (skipped=3)
VERIFY: 5 check(s), 0 problem(s)
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
exit 0
```

The 476-test full run is at the float-ID fix commit; the subsequent root-alias change is covered
by its additional real-build test above. A fresh full check is required for the final handoff.
The three local skips are Playwright browser tests; edition-preview CI installs that runtime.

### Real-book scratch proof on original base

Book main `6c017bf0cfcbe52f918c8232a2b0df02422ebe36`, fixture `0b80d3b7cdab34563195dd29ab753e8b8a87fd08` (all 33 files;
profile 1.1.0 and opt-in selected in scratch only), toolkit code `9f42e700fe5f2fb0327631e21aa9acc89b5251fb`.
Build output `/tmp/codex-xref-realbook-handoff`, exit 0, with required LibreOffice page destinations.
Actual build result:

```text
BuildResult(output=PosixPath('/tmp/codex-xref-realbook-handoff'), commit='0b80d3b7cdab34563195dd29ab753e8b8a87fd08', version='3.1.0-rc.1', epoch=1794834387, tool_versions={'quarto': '1.11.9', 'pandoc': '3.10', 'typst': '0.15.1', 'python': '3.12.3', 'zlib': '1.3', 'libreoffice': 'LibreOffice 24.2.7.2 420(Build:2)', 'docx_page_numbers': 'verified bookmark destinations (LibreOffice pagination)'})

```

Audit command: `.venv/bin/python /tmp/codex-xref-evidence/audit-navigation.py /tmp/codex-xref-realbook-handoff`, exit 0.
It walks every HTML local fragment, all DOCX hyperlink anchors and every PDF internal annotation
(qpdf JSON, resolving named and direct page destinations). Actual summary:

```json
{
  "expected_generated_links": 2219,
  "registered_destinations": 1004,
  "generated_label_kinds": {
    "bare_or_list": 1748,
    "Chapter": 130,
    "Appendix": 54,
    "Figure": 114,
    "Table": 153,
    "Section": 20
  },
  "html": {
    "generated_links": 2219,
    "internal_fragment_links_checked": 3606,
    "broken": []
  },
  "docx": {
    "all_internal_hyperlinks": 3219,
    "navigation_hyperlinks": 2219,
    "broken": [],
    "missing_registered_bookmarks": []
  },
  "shared_numbered_section_anchors": 573,
  "raw_inventory_named_tokens": 673
}
```

PDF: 2921 internal annotations, 620 named destinations, zero broken destinations.
The PDF annotation total includes native navigation and wrapped-link annotations; the generated
logical input is 2,219 links. Word's 3,219 includes native cached navigation; 2,219 are prose links.

The brief's baseline 673 is the raw named-token count, independently reproduced from frozen source.
The delta is `2,219 - 673 = 1,546`: 468 original named tokens link; 205 are excluded (120 image
captions, 36 table captions, 46 headings, one table header and two unresolved `Section 8.1.2`
citations); 1,751 additional bare/plural-list/lettered references link. No missing target is invented.
The actual v3 HTML main-content section/figure/table link count is 5,307, including 3,333 on its
analytic Index. That is a different metric; full generated-section parity belongs to change 0053.

### Disabled sample, original base

Sample commit `8ed1b7035430ab3dc25fb65d712577bc197394ef`. Uncontrolled before/after builds differ only in
Quarto sitemap `lastmod` timestamps. A controlled scratch pair freezes staged QMD mtimes equally
before each render; production code is unchanged. Commands actually run:

```bash
PYTHONPATH=/tmp/codex-xref-before/tools/src .venv/bin/python /tmp/codex-xref-evidence/sample-clock-build.py /tmp/codex-xref-sample-clock-before
.venv/bin/python /tmp/codex-xref-evidence/sample-clock-build.py /tmp/codex-xref-sample-clock-after
.venv/bin/python /tmp/codex-xref-evidence/sample-compare.py
```

All seven files, including the manifest and checksum file, are byte-identical (comparison exit 0).
Actual `sha256sum` output for the before pair (after hashes are identical):

```text
808531aabe5c5731a463dd3d3e177c26de3ef37773d3616cd960c916ced15c98  /tmp/codex-xref-sample-clock-before/SHA256SUMS.txt
af9fcac1da5ceda13c0efdd1d1a47c0f83a5d1456c733702a65280d75923cbc3  /tmp/codex-xref-sample-clock-before/book-html.zip
02e72398d24736040eb571ccc976fa01bdecc574fba51ffa42ba5652a281cb44  /tmp/codex-xref-sample-clock-before/book-source.zip
39840e3f266b0ea5938d752f51458615c31eb2ed91306aabc73e9c9e341b1d00  /tmp/codex-xref-sample-clock-before/book.docx
591e9ac40b7a3a1ba7cd635883d085ed463bf5d20896a5806476bf8f90a4230f  /tmp/codex-xref-sample-clock-before/book.md
2dc7f135dadd29a8e38b7ed423949c5b6185b335b2a54d1b73a048bcd521f44e  /tmp/codex-xref-sample-clock-before/book.pdf
dd42181249c14c123b682c2aced9b188e57cbe8864546c6d137f51afb2285af6  /tmp/codex-xref-sample-clock-before/publication-manifest.json

```

Final post-0051 sample comparison, real-book proof, CI and merge readiness are still pending.
