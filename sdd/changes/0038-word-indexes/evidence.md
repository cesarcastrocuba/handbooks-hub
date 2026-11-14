# Change 0038 evidence

Started from origin/main f5cf8e0 (WP5 merge), in the exclusive word0102 worktree on fix/word-indexes.
Quarto 1.11.9; LibreOffice 24.2.7.2 420(Build:2); Python 3.12.3. Tools installed in a private venv
from requirements-dev.txt and requirements-edition-preview.txt; Chromium installed with Playwright.

Commands/results already observed:

- test_docx_native.py: 34 tests passed, including positive/negative structural invariant fixtures.
- test_docx_pages.py: 9 tests passed (named-destination parsing, decimal restarts, unsupported
  formats, missing/failing optional/required tools, numeric caches, deterministic bytes and
  width/final convergence).
- Strict real pilot build: seven-file output produced, manifest records LibreOffice version and
  verified bookmark pagination. Initial sample strict probe rejected missing B_author_path_f9740f67b0.
  Confirmed the same missing destination by exporting the published v0.5.0 DOCX. Authoring index
  point bookmarks inside paragraphs removes reliance on that omitted body-level range.
- test_edition_preview.py: 18 tests passed after using the bounded destination-enabled exporter.

Final full/real-build/template/sample/SDK results and cached index entry numbers are appended after
execution. No desktop Word result is claimed by the implementer.

## Final verification and sample

- Strict `test_build.py`: **30 tests passed in 272.786 s**, including a multi-page fixture whose
  heading, table and figure are on three different pages. Its caches equal fresh destination pages.
- Strict `test_template.py`: **18 tests passed in 65.292 s**, including seven files and initialization.
- `test_reference_docx.py`: **2 passed**, matching the regenerated package and rejecting conditional
  banding/update requests in it. `test_docx_pages.py`: **9 passed**.
- Ran the requested edition_preview command on /home/ubuntu/github/handbook-sample-01. That local
  main checkout is stale at 70383d1/v0.4.1 and has no figure; it cannot prove v0.5.0's three indexes.
  It was not modified. Cloned the published v0.5.0 tag to an owned temporary repository instead;
  GitHub's tag ref and local HEAD both resolve to ba6666ea84731ca8aeffc04c3e60f2dfb26ba977.
- `python tools/scripts/edition_preview.py --repo /tmp/word0102-v050-source
  --output /tmp/word0102-v050-preview --require-tools`: completed, 18 HTML pages, screenshots,
  seven edition files and a destination-enabled LibreOffice PDF. This is a non-release preview.
- `sha256sum -c SHA256SUMS.txt`: all six listed files OK; verify_publication has no issues.
- Parsed all Word XML parts: **0 dirty attributes**, **0 updateFields**. All 3 TC fields have no
  separator. All **83** numeric caches match pdfinfo -dests on the preview's fresh LibreOffice PDF.
- Open XML SDK 3.3.0, OpenXmlValidator / Office2019: **0 errors** on the v0.5.0 preview DOCX.
  Executed `dotnet run --project /tmp/wp1-openxml -- .../edition/book.docx`.
- Inspected rendered LibreOffice PDF pages 2, 4, 5 and 21: populated Contents/Lists with numbered
  leaders, cream canvas, teal/white table header, visible alternating body fills and plain callout
  body rows. The actual Table 2.1 cells have header 0B5D5F then F6F1E7/F2ECE0 alternation.
- Two identical DOCX inputs passed the real LibreOffice probe independently and produced
  byte-identical output caches. The packaged body font has equal digit advances (497 units each),
  corroborating the digit-width placeholder check. Probe/preview fontconfig excludes host fonts;
  temporary profiles and caches are removed and are not uploaded in the artifact.

### Cached pages in the published-source sample preview

These are LibreOffice pages, checked by bookmarks, not a claim of matching desktop Word pagination.
Contents has 80 entries; its page numbers in entry order are:

```text
6, 8, 8, 8, 8, 8, 9, 9, 10, 10, 10, 10, 12, 12, 13, 14, 16, 17, 18, 18, 19, 22, 23, 24, 25, 25, 26, 27, 28, 29, 30, 30, 31, 32, 33, 34, 35, 35, 36, 37, 38, 39, 40, 40, 41, 42, 43, 44, 45, 45, 46, 47, 48, 49, 50, 50, 51, 52, 53, 54, 55, 55, 56, 60, 60, 62, 63, 64, 64, 65, 66, 67, 67, 69, 70, 71, 71, 71, 71, 71
```

| Index | Entry | Cached page |
| --- | --- | ---: |
| List of Tables | Table 1: Task-Based Reading Routes | 10 |
| List of Tables | Table 2.1: Illustrative brief | 21 |
| List of Figures | Figure 1.1: The seven lifecycle states | 15 |

The raw XML/PDF destination report is retained locally as /tmp/word0102-v050-entries.json;
CI's edition-preview-sample artifact supplies the actual DOCX/PDF for Owner acceptance.

### Explicit limits/refinements

- Multi-digit caches require an extra width-establishment conversion before the final verified
  cache. Width cannot be obtained before pagination; unstable widths or pages fail the build.
- Decimal section restarts are supported. Non-decimal/chapter-prefixed numbering is rejected by
  strict builds; optional builds warn and retain linked titles, avoiding invented decimal pages.
- The released template pin stays at 0.10.1 until its separate reviewed pin/export update. Its
  updated release workflow must be used with the 0.10.2 upgrade described in book-upgrade.md.
- Desktop Word acceptance is not available to the agent. The Owner must check the PR artifact
  without a prompt, then F9 in each index, and visible banding before any tag. No tag was created.

Merged main 6238ddb (Owner-approved portal deployment) without editing its decisions/status.
Final make full and CI receipts are recorded below and in the PR handoff.

Final merged-source `make full`: **404 tests passed in 313.032 s**; fast verify 5 checks/0 problems,
full verify 7/0. No desktop Word check is represented by these results. All final implementation
changes are in c1bbc24 plus the main merge; this receipt only adds documentation evidence.
