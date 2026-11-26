# Change 0075 — A handbook location does not start a version list

Implementer Claude; reviewer and merger OpenCode 2. Branch `fix/0075-xref-structural-words` from main
`567af52`. No version bump; it ships with the next toolkit release.

## Finding

The Owner's review of the Solutions Architecture Handbook 4.0.0 preview (2026-11-20) found that in
Chapter 9, "Section 2.12" and "Section 4.10" were not links, while "Section 8.4" in the same sentence
was.

## Cause

`xref_links._section_ok` keeps the later numbers of a version list plain ("TLS 1.2 minimum, 1.3
preferred"): it looks back up to 320 characters for a version word followed by a number and no
sentence or clause break. `VERSION_WORDS` also holds the structure words `table`, `figure`, `chapter`,
`chapters`, `appendix` and `section`, so that a number right after them is not read as a bare section
reference. The look-back used the same set, so any earlier location in the sentence ("Section 8.4
introduces …,", "Figure 8.8 gives …") started a "version list" and every later section number in that
sentence stayed plain.

## Fix

`VERSION_LIST` is built from `VERSION_WORDS` minus `STRUCTURE_WORDS`. The previous-word check is
unchanged, so "Table 4.2" still links as a table and never as section 4.2.

## Whole-class proof

The Solutions Architecture Handbook source at book `main` `f1cf3c0` (after PR 21) was staged with
`stage_cross_references` twice, once with `origin/main`'s toolkit and once with this branch, over all
34 entries in reading order. Every link that differs:

| File | Added link | Text |
| --- | --- | --- |
| `ch08-infrastructure-and-cloud-architecture.qmd` | `[Section 8.1.2](#sec_8_1_2)` | "Figure 8.8 gives a selection path based on the criteria of Section 8.1.2" |
| `ch08-infrastructure-and-cloud-architecture.qmd` | `[Section 8.1.2](#sec_8_1_2)` | "Figure 8.8 applies the selection criteria of Section 8.1.2" |
| `ch09-platform-architecture.qmd` | `[Section 2.12](#sec_2_12)` | "…, Section 2.12 sets the principle of standardization and reuse" |
| `ch09-platform-architecture.qmd` | `[Section 4.10](#sec_4_10)` | "…, and Section 4.10 describes the team types" |

No link is removed and no other link changes. An audit of the 4.0.0 preview HTML (CI run
44694058714) found these four explicit cues and no others left unlinked; the remaining unlinked
section-shaped numbers are values and versions (TLS 1.2, WCAG 2.2, CVSS ranges, "about 13.4",
Document Control version numbers).

## Tests

`test_xref_links.test_a_location_after_another_location_is_linked` covers the three Chapter 9
references, the Chapter 8 shape after a figure link and a bare number, and a real version list after
a location. It fails on `origin/main` and passes on this branch.

| Command | Result |
| --- | --- |
| `python -m unittest test_xref_links` (in `tools/tests`, `PYTHONPATH=../src`) | 15 tests OK; on `origin/main` the new test fails |

`make full` (venv from `requirements-dev.txt`): 590 unit tests OK (5 skipped), `VERIFY (full): 7 check(s), 0 problem(s)`.
