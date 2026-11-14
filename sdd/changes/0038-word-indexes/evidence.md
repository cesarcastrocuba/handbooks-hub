# Change 0038 evidence

Started from origin/main f5cf8e0 (WP5 merge), in the exclusive word0102 worktree on fix/word-indexes.
Quarto 1.11.9; LibreOffice 24.2.7.2 420(Build:2); Python 3.12.3. Tools installed in a private venv
from requirements-dev.txt and requirements-edition-preview.txt; Chromium installed with Playwright.

Commands/results already observed:

- test_docx_native.py: 32 tests passed, including positive/negative structural invariant fixtures.
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
