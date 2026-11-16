# Change 0052 — Opt-in cross-reference links (G8)

## Scope and provenance

Owner brief: cross-reference portion of `brief-0052-0053-reference-navigation.md`.
Implementer branch `feat/0052-cross-reference-links`; Claude reviews and merges.
No self-merge, version bump or tag. This record replaces the pre-0051 evidence.

Final code `08d6ef94df9dbe075651e2a52408a88572f719ad`, rebased onto main `5ad910534ccde35e5fcd74bf931549dee7d2b3e8`
(after changes 0051, 0054, 0055 and template 1.7.0). Later evidence-only commits do not change tested code.

Cue rules and test intent are ported from the author's MIT reference builder and tests at
frozen source commit below. The reference clone is read-only. No manuscript prose is copied into
the hub; all committed test fixtures are synthetic. Actual `git rev-parse HEAD` / `sha256sum`:

```text
13d295bfb266c6fb03b8d244666ebbf0e056e6cd
5ea96307c586e6e934fb9b7b6e7f9f451731172ddffd8d64827e28d45c5fe514  /tmp/agy-sa/src/scripts/build_book.py
9c811f5685b6a2ab88177eb0ba95da5f41f35bddc325c6f9fe57a2eadf37f452  /tmp/agy-sa/src/scripts/tests/test_build_book.py
5d5cf28b1b5f80a3ce420a085359e9a0aa92481b25572f69c7cb426b949274a3  tools/src/handbook_toolkit/xref_links.py
```
Write set: `xref_links.py`, two orchestration hooks in `build.py`, the packaged book schema,
unit/runtime tests, publication-build docs, CHANGELOG and this record. `build_staging.py` is
unchanged. The CHANGELOG entry is Unreleased; toolkit 0.12.0 excludes this feature.

## Design

`publication.cross_reference_links` is an optional boolean, default false. With it enabled,
a whole-book whitelist is collected before staging strips heading numbers. Only resolved
references link; duplicate anchors and ambiguous numbered targets fail the build.
Section IDs are Word-safe `sec_ch_1`, `sec_app_a`, `sec_1_2` and `sec_a_1`, shared by
HTML/PDF/DOCX. Existing author IDs remain authoritative, using Word's existing encoding.

Float registration uses 0051's native scanners and reading groups: continuous `0.N` in front
matter, displayed chapter numbers, appendix letters and `BM.N` in back matter. It replaces the
pre-rebase file-hash table IDs. The opt-in stage normalizes class-first table caption attributes
to put their existing ID first, preserving classes and allowing the native table wrapper to keep
the author ID. No displayed numbering logic is replaced.

Generated links carry `handbook-xref`. Print receives internal fragments; after print, only
these generated links are rebased to their source page for multi-page HTML. The root `index.qmd`
alias is normalized explicitly. The existing index-resource fallback already preserved valid
production links; the navigation helper now handles the alias itself.

Named references, ranges/lists and cue-qualified bare numbers are supported. Code, YAML,
comments, headings, images/captions, existing links, bibliography, versions/dates/measurements
stay plain. Reference columns still reject protocol version contexts. No automatic glossary-term
linking, glossary pointers or analytic Index: those remain change 0053.

## Focused and full checks

Own `.venv` installed with `.venv/bin/python -m pip install -r requirements-dev.txt`.
Commands and real output on the rebased code:

```text
.venv/bin/python -m unittest discover -s tools/tests -p test_xref_links.py -v
----------------------------------------------------------------------
Ran 14 tests in 0.046s

OK
exit 0
```

```text
make full PYTHON=.venv/bin/python
Ran 506 tests in 512.417s

OK (skipped=3)
VERIFY: 5 check(s), 0 problem(s)
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
exit 0
```
The three local skips require the Playwright browser installed in edition-preview CI.
The full run includes both real synthetic opt-in builds: native front-table/custom float
IDs with HTML/DOCX/PDF destinations, and a root-source `index.qmd` alias. The 14 focused tests
cover cue/protection rules, whitelist/duplicates, schema compatibility and native front/back/
appendix numbering. The native-ID fixture includes two front files and class-first custom IDs.

## Fresh full-book proof

Book main `a5426bc33586f6a66b53f0209e46bf99a2ecbd0a`; scratch fixture `63b3e8b38545b475b4d0ada019a020c545f26e2b`
at `/tmp/codex-0052-final-book`. All 33 canonical QMD files are unchanged.
The only descriptor edit is one opt-in line; profile 1.1.0 and toolkit 0.12.0 remain canonical:

```text
diff --git a/book.yaml b/book.yaml
index 60ff1b6..bdf3d26 100644
--- a/book.yaml
+++ b/book.yaml
@@ -20,6 +20,7 @@ manuscript:
   reading_order: manuscript/book.yml

 publication:
+  cross_reference_links: true
   formats:
     - html
     - pdf
```

```text
.venv/bin/python /tmp/codex-0052-final-evidence/build_one.py book
BuildResult(output=PosixPath('/tmp/codex-0052-output-book-08d6ef94'), commit='63b3e8b38545b475b4d0ada019a020c545f26e2b', version='3.1.0-rc.1', epoch=1794846786, tool_versions={'quarto': '1.11.9', 'pandoc': '3.10', 'typst': '0.15.1', 'python': '3.12.3', 'zlib': '1.3', 'libreoffice': 'LibreOffice 24.2.7.2 420(Build:2)', 'docx_page_numbers': 'verified bookmark destinations (LibreOffice pagination)'})

exit 0
```

```text
.venv/bin/python /tmp/codex-0052-final-evidence/audit.py /tmp/codex-0052-output-book-08d6ef94
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
  "pdf": {
    "all_internal_link_annotations": 2921,
    "named_destinations": 620,
    "broken": [],
    "content_prefix_counts": {
      "u:Section ": 1956,
      "u:Table ": 436,
      "u:Figure ": 235,
      "u: \u201cQuality Attribute Scenario": 2,
      "u: \u201cArchitecture Decision Reco": 2,
      "u: \u201cWorked Example: Right-Sizi": 2,
      "u: \u201cChapter 1: Architecture Re": 2,
      "u: \u201cChapter 2: Architecture Pr": 2,
      "u: \u201cChapter 3: Architecture De": 2,
      "u: \u201cChapter 4: Architecture Go": 2,
      "u: \u201cChapter 5: Data Architectu": 2,
      "u: \u201cChapter 6: Integration Arc": 2
    },
    "first_registered_section_page": 16,
    "body_internal_link_annotations": 2243,
    "outline_and_list_internal_link_annotations": 678
  },
  "shared_numbered_section_anchors": 573,
  "raw_inventory_named_tokens": 673
}
NAVIGATION_OK: generated HTML/DOCX counts agree; every HTML fragment, DOCX anchor and PDF internal annotation resolves
exit 0
```
The PDF audit resolves every internal GoTo annotation to an existing page through direct or
named destinations. DOCX verifies every internal hyperlink against bookmarks, and HTML walks
all relative links/fragments in the zip. Every registered numbered section has a PDF named
anchor. LibreOffice page destinations are required, not bypassed.

### Explained link delta

The inventory's 673 baseline is a raw source named-token count, independently recounted from
frozen source, rather than a count of all v3.0.0 rendered hyperlinks. The current generated
HTML and DOCX navigation counts agree. The PDF audit counts all internal annotations, including
TOC/list links. The audit separately finds 2,243 body click-area annotations and 678
outline/list annotations. PDF click areas are not a one-to-one count of logical prose references
(a wrapped link can produce multiple annotations); the source/HTML/DOCX logical count is 2,219.

```text
.venv/bin/python /tmp/codex-0052-final-evidence/delta.py
{
  "raw_named_inventory_baseline": 673,
  "generated_total": 2219,
  "inventory_named_tokens_linked": 468,
  "inventory_named_tokens_not_linked": 205,
  "unlinked_categories": {
    "heading": 46,
    "non_reference_or_unresolved": 2,
    "table_header": 1,
    "protected_code_or_markup": 0,
    "table_caption": 36,
    "image_caption": 120,
    "bibliography": 0
  },
  "generated_by_label_kind": {
    "bare_or_list": 1748,
    "Chapter": 130,
    "Appendix": 54,
    "Figure": 114,
    "Table": 153,
    "Section": 20
  },
  "additional_bare_plural_or_lettered_links": 1751,
  "delta_vs_673": 1546,
  "non_reference_or_unresolved_tokens": {
    "Section 8.1.2": 2
  }
}

exit 0
```
The two unresolved `Section 8.1.2` mentions stay plain because that heading does not exist.
The additional links are cue-qualified bare numbers and plural/lettered references outside the
inventory's narrow numeric regexes. No headings or captions are counted as generated prose links.

### Numbering regression against v3.0.0

The complete ordered sequences are compared independently with the frozen v3.0.0 release
artifacts (`/tmp/codex-pr82-release`), including all front/back-matter labels, not just chapters.

```text
.venv/bin/python /tmp/codex-0052-final-evidence/numbering.py
HTML Figure counts 121 121 full ordered equality True
HTML Figure chapter/appendix count 121 ordered equality True
HTML Figure other labels [] => []
DOCX BODY Figure counts 121 121 full ordered equality True
DOCX BODY Figure chapter/appendix ordered equality True
DOCX BODY Figure other labels [] => []
DOCX LIST Figure counts 121 121 core equality True
HTML Table counts 263 263 full ordered equality True
HTML Table chapter/appendix count 255 ordered equality True
HTML Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX BODY Table counts 263 263 full ordered equality True
DOCX BODY Table chapter/appendix ordered equality True
DOCX BODY Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX LIST Table counts 263 263 core equality True
PDF Figure appendix letter labels ['A.1']
PDF Table appendix letter labels ['A.1', 'A.2', 'B.1', 'B.10', 'B.11', 'B.12', 'B.13', 'B.14', 'B.2', 'B.3', 'B.4', 'B.5', 'B.6', 'B.7', 'B.8', 'B.9', 'C.1', 'D.1', 'E.1', 'E.10', 'E.2', 'E.3', 'E.4', 'E.5', 'E.6', 'E.7', 'E.8', 'E.9', 'F.1', 'F.10', 'F.11', 'F.2', 'F.3', 'F.4', 'F.5', 'F.6', 'F.7', 'F.8', 'F.9', 'G.1', 'H.1', 'H.10', 'H.11', 'H.12', 'H.13', 'H.14', 'H.15', 'H.16', 'H.17', 'H.18', 'H.2', 'H.3', 'H.4', 'H.5', 'H.6', 'H.7', 'H.8', 'H.9', 'I.1', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'I.15', 'I.16', 'I.17', 'I.18', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.8', 'I.9', 'J.1', 'J.2', 'J.3', 'J.4', 'J.5', 'J.6', 'J.7']
PDF BODY Figure counts 121 121 full ordered equality True
PDF LIST Figure counts 121 121 full ordered equality True
PDF BODY Table counts 263 263 full ordered equality True
PDF LIST Table counts 263 263 full ordered equality True
PDF list extraction equality True
Comparison complete: full HTML/DOCX body/list/PDF body/list sequences equal to v3.0.0.

exit 0
```
## Disabled sample: before/after current main

Canonical sample `8ed1b7035430ab3dc25fb65d712577bc197394ef`; common scratch fixture `a8946b3d947a0800a3991f152d2759d33416f88c`.
The sole descriptor adjustment pins toolkit 0.12.0 instead of 0.11.0, equally for both builds;
manuscript is untouched and the opt-in key is absent. Before uses an archive of main
`5ad910534ccde35e5fcd74bf931549dee7d2b3e8`; after uses tested code `08d6ef94df9dbe075651e2a52408a88572f719ad`.

The scratch harness sets staged QMD mtimes to the same actual fixture commit epoch before
both renders, controlling Quarto sitemap `lastmod`, which otherwise depends on wall-clock
staging time. Both runs keep 0055 optimization enabled (the default); no `optimize` override is passed. Production code is unpatched; no render or validation is bypassed. Commands:

```text
PYTHONPATH=/tmp/codex-0052-main-baseline-5ad9105/tools/src .venv/bin/python /tmp/codex-0052-final-evidence/build_one.py sample-before
.venv/bin/python /tmp/codex-0052-final-evidence/build_one.py sample-after
.venv/bin/python /tmp/codex-0052-final-evidence/sample-compare.py
DISABLED_SAMPLE_OK: all seven files byte-identical, including manifest and checksums; staged QMD mtimes controlled equally in both runs
exit 0 (each command)
```

Actual `sha256sum` of the identical after artifacts:

```text
7e31dc8985cf877d815b729418de571e5f93646855dced4c6a279ed2cae80ef5  /tmp/codex-0052-output-sample-after-08d6ef94/SHA256SUMS.txt
09459052999c46c39182c8eff3f6246637c6784bf7cc76d9d10ac6b48660578d  /tmp/codex-0052-output-sample-after-08d6ef94/book-html.zip
2fc32a7fa6e8bf248c7def184cc9d4cd87ae4cf1704136e2e74a45e653bfa440  /tmp/codex-0052-output-sample-after-08d6ef94/book-source.zip
134b4bd991fe0c2a807e6e7b53e23f3d9d2454208e24ed63ab4f0c43b54ad16e  /tmp/codex-0052-output-sample-after-08d6ef94/book.docx
53c9b766bacefac5c0e63eaa0bb7ccaac362937e904e5ca733ad4141fbc0ec3f  /tmp/codex-0052-output-sample-after-08d6ef94/book.md
08c2356db7f8e3baf5bf871fc672ba09a50d1784d549c053357f943ddac5befb  /tmp/codex-0052-output-sample-after-08d6ef94/book.pdf
e91daddb72e77bda853918b20a9fe45bc10430ff655dd76fb5a165291a617be9  /tmp/codex-0052-output-sample-after-08d6ef94/publication-manifest.json
```
## Handoff, rollback and not-run items

Final PR CI must be green, including template, sample and solutions-architecture edition previews,
before marking ready. CI URLs/status are recorded in the PR description after the final push.

Remove the optional schema property, two orchestration hooks and xref module/tests/docs as one
unit to roll back. Books without the key do not execute the linker. Canonical books and the
read-only reference remain untouched. No release, tag, deployment, Owner desktop Word acceptance,
editorial approval or change 0053 work was performed.
