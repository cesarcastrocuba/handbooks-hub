# Change 0053 — Glossary pointers and analytic Index (G9, G4)

## Scope and provenance

Owner assigned 0053 after PR 88 merged. Base `f37182b269d035fb6b153c9611bb58c5830fb898`;
branch `feat/0053-glossary-index`, worktree `../handbooks-hub.worktrees/glossary-index`.
Tested functional code `8f5d2a1b3a788a44c6589fb1b9f21a70977b4ba0`. Claude reviews and merges.
No self-merge, version bump or tag. Subsequent evidence-only commits do not change tested code.

The matching, alias and Index rules derive from the author's MIT frozen reference builder and tests.
No manuscript prose is copied into the hub: all committed fixtures are synthetic. Actual
`git rev-parse HEAD` and `sha256sum` output:

```text
13d295bfb266c6fb03b8d244666ebbf0e056e6cd
5ea96307c586e6e934fb9b7b6e7f9f451731172ddffd8d64827e28d45c5fe514  /tmp/agy-sa/src/scripts/build_book.py
9c811f5685b6a2ab88177eb0ba95da5f41f35bddc325c6f9fe57a2eadf37f452  /tmp/agy-sa/src/scripts/tests/test_build_book.py
a873b3518a2caf229076831f4c4ae0b90d24575dd9a1276088fb5972533c63c2  tools/src/handbook_toolkit/glossary_index.py
```

## Design and rollback

`manuscript.glossary`, relative to the manuscript root, enables anchors, definition pointers and a
last unnumbered Index. Optional `publication.index_vocabulary` is repository-relative and validated
against the packaged schema. It supports aliases, Index-only entries and visible see-canonical rows.
The glossary must be a canonical reading-order file. Invalid inputs, missing see targets, duplicate
slugs, generated-page collisions and unresolved deliberate glossary links fail the opted-in build.

The 0052 registry can stage section anchors without prose linking. Definition and Index locations
use that registry, including explicit author IDs. Glossary term auto-linking stays off. Only deliberate
author glossary links are rewritten across HTML pages. Word glossary IDs/links are encoded before
Pandoc's 40-character truncation and restored before HTML. Code examples remain unchanged in both
rewriters, including multiline inline code and nested-length fences. The root-source alias is supported.

Index rows are protected by the existing Typst cell rule and a dedicated Word table bookmark marker
that gates `cantSplit` on every generated row. Other tables keep their behavior. The Index is in the
native TOC/navigation and follows all canonical pages. No caption is added to its table, so figure and
table sequences stay unchanged.

The Owner requested one PR for the coupled port/integration/fixtures. Write set: glossary module,
vocabulary/book schemas, build hooks, registry anchor-only option, gated Word row protection,
unit/runtime tests, publication docs, CHANGELOG and this record. Rollback removes these opt-in
hooks/module/schema fields and marker handling together, retaining unrelated numbering/optimization.

## Focused and full checks

Own `.venv` installed from `requirements-dev.txt`. Commands and actual output:

```text
.venv/bin/python -m unittest discover -s tools/tests -p test_glossary_index.py -v
----------------------------------------------------------------------
Ran 11 tests in 0.057s

OK
exit 0
```


```text
make full PYTHON=.venv/bin/python
Ran 523 tests in 457.603s

OK (skipped=3)
VERIFY: 5 check(s), 0 problem(s)
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
exit 0
```

The full suite includes the real synthetic all-edition glossary/Index build: HTML fragment walk,
Word hyperlink/bookmark integrity including a long ID, every Index row's `cantSplit`, final Index
heading and PDF direct page destinations. It runs without prose xref opt-in; the full-book proof below
also enables 0052. Local browser skips are covered by edition-preview CI's Playwright runtime.

Initial runtime failures caught missing Word row markers and an incorrect test assumption that
PDF table-span destinations are named (Typst uses direct page destinations). A later code-example
protection fix restarted the full/book proofs; interrupted runs are not reported as passes.

## Full-book proof and baseline

The full-book render ran at `62d3c8f41d0c108692c6d6d471b2655e677edd0c` before the PR92 rebase.
Current toolkit sources/resources are byte-identical; only the template workflow/docs/tests changed.
The proof is retained, with fresh repository checks and sample comparison on the new base:

```text
git diff --exit-code 62d3c8f41d0c108692c6d6d471b2655e677edd0c..HEAD -- tools/src
exit 0 (empty diff)
```

Book main `a5426bc33586f6a66b53f0209e46bf99a2ecbd0a`, scratch fixture `834ade7a6794cdea2accf4e26fd97b82684a105a`.
All 33 canonical QMD files and figures are unchanged; only three descriptor keys are added.
The book's profile 1.1.0 and toolkit 0.12.0 pins remain unchanged. Default optimization and
required LibreOffice page verification are enabled:

```text
book.yaml | 3 +++
 1 file changed, 3 insertions(+)
diff --git a/book.yaml b/book.yaml
index 60ff1b6..cf5f217 100644
--- a/book.yaml
+++ b/book.yaml
@@ -18,8 +18,11 @@ license:
 manuscript:
   root: manuscript
   reading_order: manuscript/book.yml
+  glossary: appendices/appendix-g-glossary-of-terms-and-acronyms.qmd

 publication:
+  cross_reference_links: true
+  index_vocabulary: publishing/index-vocabulary.yaml
   formats:
     - html
     - pdf
```


```text
.venv/bin/python /tmp/codex-0053-evidence/build_one.py book
BuildResult(output=PosixPath('/tmp/codex-0053-output-book-62d3c8f4'), commit='834ade7a6794cdea2accf4e26fd97b82684a105a', version='3.1.0-rc.1', epoch=1794849684, tool_versions={'quarto': '1.11.9', 'pandoc': '3.10', 'typst': '0.15.1', 'python': '3.12.3', 'zlib': '1.3', 'libreoffice': 'LibreOffice 24.2.7.2 420(Build:2)', 'docx_page_numbers': 'verified bookmark destinations (LibreOffice pagination)'})

exit 0
```


```text
.venv/bin/python /tmp/codex-0053-evidence/audit.py /tmp/codex-0053-output-book-62d3c8f4
{
  "expected_generated_links": 6182,
  "registered_destinations": 1470,
  "generated_label_kinds": {
    "bare_or_list": 5659,
    "Chapter": 130,
    "Appendix": 106,
    "Figure": 114,
    "Table": 153,
    "Section": 20
  },
  "index": {
    "section_links": 3497,
    "glossary_links": 466,
    "glossary_pointers": 493,
    "word_rows_protected": 529
  },
  "glossary_links_outside_index": 0,
  "html": {
    "generated_links": 6182,
    "internal_fragment_links_checked": 7570,
    "broken": []
  },
  "docx": {
    "all_internal_hyperlinks": 7183,
    "navigation_hyperlinks": 6182,
    "broken": [],
    "missing_registered_bookmarks": []
  },
  "pdf": {
    "all_internal_link_annotations": 6887,
    "named_destinations": 621,
    "broken": [],
    "content_prefix_counts": {
      "u:Section ": 5455,
      "u:Table ": 436,
      "u:Figure ": 235,
      "u:page 465": 21,
      "u:page 450": 20,
      "u:page 452": 20,
      "u:page 458": 20,
      "u:page 463": 20,
      "u:page 464": 20,
      "u:page 449": 19,
      "u:page 453": 19,
      "u:page 456": 19
    },
    "first_registered_section_page": 16,
    "body_internal_link_annotations": 6208,
    "outline_and_list_internal_link_annotations": 679,
    "index_first_page": 493,
    "index_physical_link_annotations": {
      "glossary": 466,
      "section": 3499
    },
    "index_wrapped_section_annotation_extras": {
      "sec_app_d": 1,
      "sec_app_e": 1
    }
  },
  "shared_numbered_section_anchors": 573,
  "raw_inventory_named_tokens": 673
}
NAVIGATION_OK: generated HTML/DOCX counts agree; every HTML fragment, DOCX anchor and PDF internal annotation resolves
exit 0
```

HTML walks all relative links/fragments, Word checks every internal hyperlink against bookmarks,
and PDF resolves every internal annotation to an existing page through direct/named destinations.
PDF physical annotation counts differ from logical source links because of wrapping and native lists.
The Word audit also verifies all Index rows carry the protection marker after LibreOffice pagination.
The PDF Index contains all 466 glossary jumps and 3,499 section click areas for 3,497 logical
section links: the Appendix D and E references each wrap once. Per-target comparison confirms
no section destination is missing.

### Explained release delta

v3.0.0 has 502 Index terms, 3,333 Index section links, 466 Index-to-glossary links and 493 glossary
pointers. This port has 502 terms, 3,497 section links, 466 glossary links and 493 pointers. An independent
run of the frozen builder's own functions also produces 3,497 locations. Per-term comparison proves
that the delta is exactly 164 chapter/appendix introduction locations across 111 terms, with zero
missing release locations. The frozen source explicitly includes chapter introductions, so this port
retains those locations rather than silently dropping them to force the older release count.

All ordered Index terms and every term's location/definition target multiset match the frozen builder
(after converting the anchor scheme). Three appendix definition rows are formatted as definitions
instead of ordinary occurrences: the frozen `_defined_sections` creates uppercase appendix anchors
that fail its lowercase catalog lookup; the registry-based port resolves them correctly. This changes
bold/group placement, with no target loss or count change. The comparison output is independent of
the publication rendering:

```text
.venv/bin/python -B /tmp/codex-0053-evidence/compare-scan.py
differing rows 111
DELTA_OK: 164 additional chapter/appendix introduction locations; zero missing release locations
FROZEN_PARITY_OK: all ordered Index terms and each term location/definition target set match frozen builder
Appendix definition formatting corrected through registry: 3 rows
Index terms 502 glossary terms 466 alphabetic separator rows 26
RELEASE_TERMS_OK: all 502 terms and 26 alphabetic separator rows match v3.0.0
exit 0
```

### Numbering regression

Complete ordered sequences are checked against the v3.0.0 HTML/Word release artifacts. The PDF
body/list sequences are compared with the same expected labels. The generated Index adds no float:

```text
.venv/bin/python /tmp/codex-0053-evidence/numbering.py
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

## Disabled sample identity

Common sample fixture `a8946b3d947a0800a3991f152d2759d33416f88c` from main `8ed1b7035430ab3dc25fb65d712577bc197394ef`;
the sole scratch adjustment pins toolkit 0.12.0, equally for both builds. Neither new key is present.
Before uses main `f37182b269d035fb6b153c9611bb58c5830fb898`; after uses `8f5d2a1b3a788a44c6589fb1b9f21a70977b4ba0`.
The scratch harness sets staged QMD mtimes to the actual fixture commit epoch in both builds,
controlling Quarto sitemap lastmod. Production code is unpatched; optimization remains enabled,
and no rendering/validation is bypassed. All seven files, including manifest and checksums, are
byte-identical:

```text
PYTHONPATH=/tmp/codex-0053-main-baseline-f37182b/tools/src .venv/bin/python /tmp/codex-0053-evidence/build_one.py sample-before
.venv/bin/python /tmp/codex-0053-evidence/build_one.py sample-after
.venv/bin/python /tmp/codex-0053-evidence/sample-compare.py
DISABLED_SAMPLE_OK: all seven files byte-identical, including manifest and checksums; staged QMD mtimes controlled equally in both runs
exit 0 (each command)
```


Actual `sha256sum` of the identical after files:

```text
7e31dc8985cf877d815b729418de571e5f93646855dced4c6a279ed2cae80ef5  /tmp/codex-0053-output-sample-after-8f5d2a1b/SHA256SUMS.txt
09459052999c46c39182c8eff3f6246637c6784bf7cc76d9d10ac6b48660578d  /tmp/codex-0053-output-sample-after-8f5d2a1b/book-html.zip
2fc32a7fa6e8bf248c7def184cc9d4cd87ae4cf1704136e2e74a45e653bfa440  /tmp/codex-0053-output-sample-after-8f5d2a1b/book-source.zip
134b4bd991fe0c2a807e6e7b53e23f3d9d2454208e24ed63ab4f0c43b54ad16e  /tmp/codex-0053-output-sample-after-8f5d2a1b/book.docx
53c9b766bacefac5c0e63eaa0bb7ccaac362937e904e5ca733ad4141fbc0ec3f  /tmp/codex-0053-output-sample-after-8f5d2a1b/book.md
08c2356db7f8e3baf5bf871fc672ba09a50d1784d549c053357f943ddac5befb  /tmp/codex-0053-output-sample-after-8f5d2a1b/book.pdf
e91daddb72e77bda853918b20a9fe45bc10430ff655dd76fb5a165291a617be9  /tmp/codex-0053-output-sample-after-8f5d2a1b/publication-manifest.json
```

## Handoff and not-run items

Final CI status and run URL are recorded in the PR after the evidence commit; all eight checks,
including template/sample/solutions-architecture edition previews, must be green before ready.
No Owner desktop Word acceptance, editorial approval, release, tag, deployment or catalog update
is performed. Canonical book repositories and the frozen reference are untouched.
