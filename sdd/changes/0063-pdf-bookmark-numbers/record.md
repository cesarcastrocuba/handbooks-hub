# Change 0063 — PDF bookmarks keep their section numbers (issue #99)

Small fix for a pre-existing defect: numbered headings lost their number in the PDF outline and
kept only the separating space, while the Contents page showed the number. No version bump and no
tag; the change joins toolkit 0.14.0 only if it is merged before the release pull request.

## Scope

- **Hub base**: `6d464ef` (`origin/main`, merge of PR 96 / change `0060`).
- **Branch / worktree**: `fix/0063-pdf-bookmark-numbers`,
  `../handbooks-hub.worktrees/0063-pdf-bookmarks`.
- **Write set**:
  - `tools/src/handbook_toolkit/render_data/typst/handbook-typst.typ`
  - `tools/tests/test_build.py`
  - `CHANGELOG.md`
  - `sdd/changes/0063-pdf-bookmark-numbers/record.md`

## Root cause

`handbook-numbering` in `handbook-typst.typ` was a `context` function: it read
`handbook-appendix-state` to print "Appendix A — …" for the native appendix counter. Typst cannot
resolve a contextual function while it builds the PDF outline, so the bookmark for every numbered
heading received an empty number and Typst kept the space it puts between numbering and title:
` The Lifecycle` instead of `3.3 The Lifecycle`. Chapter bookmarks lost the number too
(` Why Handbooks Fail`).

A minimal Typst probe reproduces it without the toolkit (Quarto's bundled Typst 0.15.1):

```
$ typst compile plain.typ && qpdf --json=2 --json-key=outlines plain.pdf | grep '"title"'
#set heading(numbering: "1.1")  →  "1 Chapter One", "1.1 Section A"
$ typst compile context.typ && qpdf --json=2 --json-key=outlines context.pdf | grep '"title"'
#set heading(numbering: ctx)    →  " Chapter One", " Section A"
```

Since change `0060`, appendix headings are staged as literal unnumbered headings
(`Appendix A — Title`, `A.1 Title`), so the appendix branch of the numbering function is dead.
Removing it makes the function plain and the bookmarks carry the number again.

## Fix

`handbook-numbering` is now a plain function: `numbering("1.", n)` for level 1 and
`numbering("1.1", ..nums)` below it. The `handbook-appendix-state` lookups that still serve figure
and table numbering are unchanged, as are the show rules near the table code that change `0061`
works on.

## Tests

`tools/tests/test_build.py` gains
`test_pdf_bookmarks_keep_the_section_numbers_of_the_contents`: it builds a synthetic chapter book
with `optimize=False`, reads the outline with `qpdf --json=2 --json-key=outlines`, and asserts that
`1. A Build Chapter` and `1.1 A Content Section` are present and that no title has leading or
trailing whitespace. It skips when Quarto, `pdfinfo` or `qpdf` is unavailable.

## Proof

Measurements come from `qpdf --json=2 --json-key=outlines` on real builds.

### Sample book (`handbook-sample-01`, `8ed1b70`, built as a preview)

```
before entries: 84
after entries:  84
titles with leading/trailing space before: 48
titles with leading/trailing space after:  0
numbered bookmarks not matching a Contents entry after: 0
changed entries: 48
first change: (' Why Handbooks Fail', '1. Why Handbooks Fail')
last change: (' Further Reading', '8.5 Further Reading')
```

The 48 changed entries are exactly the numbered chapter and section headings; every entry that was
already correct is byte-identical: front matter (`Document Control`, `Ownership and Review`…),
appendices (`Appendix A — …`, `A.1 Glossary Terms`…), `References` and its subheadings. The bookmark
text now equals the Contents page line, including the period after a chapter number and none after a
section number, as the Contents renders them.

### Solutions Architecture Handbook (`d9eca79`, built as a preview)

```
entries before/after: 620 620
leading-space before/after: 482 0
changed entries: 482
first: (' Architecture Requirements', '1. Architecture Requirements')
last: (' Further Reading', '18.10 Further Reading')
changed entries that did not start with a space: []
appendix entries after: ['Appendix A — Worked Architecture Cases',
                         'A.1 Reference Design: Resilient Checkout with External Payment', ...]
tail after: [... 'AI and Machine Learning', 'Index']
```

Every one of the 620 bookmarks is present in both builds. The 482 that change are exactly the
numbered chapter and section headings; they gain their number and lose the leading space. Appendices
(`Appendix A — …` through `A.1 …`), front matter, References and the Index are byte-identical.

Level 1 and level 2 bookmarks match their Contents line, except one heading that keeps straight
quotes in the outline where the printed page sets curly ones (`1.6 Worked Example: Turning
"Always-On Checkout" …`). Both builds show it, so it precedes this change and is unrelated to the
number. Level 3 and deeper headings (318 of the 620) are not printed in the Contents; they also gain
their number, e.g. `1.1.1 Business Capabilities`.

### Hub checks

```
$ make full PYTHON=./.venv/bin/python
...
Ran 536 tests in 638.321s

OK (skipped=3)
site-check: 1 page(s), 3 asset(s), all 200
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
.../catalog/catalog.json: OK
.../profiles/standard/profile.yaml: OK
.../template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
.../catalog/catalog.json: OK
.../profiles/standard/profile.yaml: OK
.../template/book/book.yaml: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

### CI

Run `44156774390` on head `0ee937a`: every job passed, including the three edition previews. The
sample (`8ed1b70`) and Solutions Architecture (`176c6aa`) artifacts were downloaded and compared with
builds of the same content made by the toolkit before this change (`6d464ef`):

```
== sample: entries 84/84; leading-space 48 -> 0; changed 48; unnumbered changed 0
   first: (' Why Handbooks Fail', '1. Why Handbooks Fail')
   last:  (' Further Reading', '8.5 Further Reading')
   appendix/reference/index entries intact: True
== solutions-architecture (176c6aa): entries 619/619; leading-space 482 -> 0; changed 482
   first: (' Architecture Requirements', '1. Architecture Requirements')
   last:  (' Further Reading', '18.10 Further Reading')
   changed entries that were already clean: []
   appendix/reference entries intact: True
```

The Solutions Architecture baseline is a build of `176c6aa` (the merged document-control change) with
hub `6d464ef`, so the comparison isolates this change; the local comparison above used `ba9e1df`,
whose outline still contained the removed "Planned Revisions" entry.
