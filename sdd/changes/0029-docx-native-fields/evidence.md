# WP1 evidence

Desktop Word: **not opened**. No publication, tag, release or deployment dispatched.

## Completed focused checks

- Fresh local venv created with python3 -m venv .venv; requirements-dev.txt installed successfully.
- Extraction boundary 2ee437c: two focused DOCX helper tests passed.
- Native field/validator fixtures: 22 tests passed.
- Design conformance: 12 tests passed, scanning every toolkit Python module except design.py.
- Copied-template tests: 18 passed, including both real seven-file build paths and initialization.
- LibreOffice cached-list smoke: passed. Its PDF has populated Contents, List of Tables and
  List of Figures. The real fixture contains an original programmatically generated PNG.
- Independent SDK: .NET 10.0.115, DocumentFormat.OpenXml 3.3.0, OpenXmlValidator Office2019:
  **0 errors** for the real figure-build DOCX. The published v0.4.1 baseline reports 125 errors.
  No Word rendering behavior is inferred from this schema check.

Final full/focused build results and the final SDK rerun are appended below after execution.
