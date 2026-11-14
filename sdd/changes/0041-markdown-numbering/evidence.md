# Change 0041 evidence

Started from origin/main aee261567d434745284868a15927f99a1abfbc64 (PR 65 merged), in the exclusive
mdnum worktree, branch fix/markdown-numbering. Toolkit stays 0.10.2; no tag is created.

- Created a venv and installed requirements-dev.txt as requested.
- Quarto 1.11.9 proof: /tmp/mdnum-poc/proof.qmd rendered as one default-project GFM document with
  crossref.chapters:true and number-sections:true. Output has Table 1 (unnumbered Introduction),
  Figure 1.1, Table 2.1 and Listing 2.1 and their matching references. Raw .appendix alone does not
  select alphabetic appendix numbering; the implementation follows the actual staged book labels.
- /tmp/mdnum-book-poc: book-project GFM rejected as unsupported by Quarto. It was not used.
- Focused Markdown/source-reference/list-page suite: 24 tests passed in 0.174 s before the final
  real-build check. Final focused/full counts are recorded below after execution.
- Fresh clone /tmp/mdnum-sample-source resolves to 778ebdba065dc668a43284354d3af0698503c580.
  The sample's stale local checkout was not used or modified.
- Ran `python tools/scripts/edition_preview.py --repo /tmp/mdnum-sample-source
  --output /tmp/mdnum-sample-preview`. Seven files, a reading site and LibreOffice PDF produced.
  Local screenshots were explicitly skipped because Playwright is not in requirements-dev.txt;
  this task inspects label structure, and CI installs the browser for edition-preview artifacts.

## Observed sample labels

Before (published v0.5.0 / original Markdown behavior): Figure 1 in the caption/reference,
Table 1 for Task-Based Reading Routes and Table 2 for the illustrative brief.

After, from generated book.md:

- Table 1: Task-Based Reading Routes
- Figure 1.1: The seven lifecycle states in order, from brief to retirement.
- Table 2.1: Illustrative brief for a fictional API handbook; names, targets and evidence are not real.
- Section 1.3 closing sentence: "Figure 1.1 shows those states in order, from brief to retirement."

Reading-site comparisons, final commands, test results and CI are recorded in the handoff.

## Final commands and results

- `make full`: **407 tests passed in 351.391 s**, fast verification 5 checks/0 problems and full
  verification 7/0.
- `python -m unittest discover -s tools/tests -p test_build.py -v`: **32 passed in 263.173 s**.
- Real new caption/reference parity fixture: passed in 26.545 s. It checks all seven captions
  (front table; chapter table/figure/listing; appendix table/figure/listing), two reference sentences,
  and the preserved unnumbered front-matter label. An initial fixture lacked a blank line before
  a pipe table; the real artifact gate rejected its missing fragment. That fixture was corrected.
- The source/reference/list tests passed 24 checks. Code-fence body examples do not declare labels;
  listing IDs in opening attributes are valid reference declarations.
- A final preview from the same fresh clone was produced at /tmp/mdnum-sample-final. Parsed native
  figcaption/caption nodes and Markdown lines match exactly for all three sample captions above.
  The section 1.3 cross-reference sentence matches exactly as well. Report:
  /tmp/mdnum-label-report.json. Local browser screenshots remain explicitly not run.
- Downloaded actual published v0.5.0 book.md with gh release download into /tmp/mdnum-published:
  confirmed Figure 1 / Table 1 / Table 2 and "Figure 1 shows those states..." before this change.
  No release asset was modified.

No numbering fallback or rendered-label rewrite was needed. GFM uses native Quarto chapter
counters with the same source structure and crossref options. Toolkit remains 0.10.2, with the
Owner's desktop Word acceptance pending before any tag. Final HEAD and CI results are recorded
in the PR handoff rather than inventing them here before execution.
