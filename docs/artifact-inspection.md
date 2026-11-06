# Inspect rendered formats before publication

The toolkit's `artifacts` module complements publication byte integrity.
`inspect_payload(path, role, source_commit=...)` returns structural issues for:

- PDF: signature plus successful `pdfinfo` inspection and at least one page.
- DOCX: ZIP/CRC, required package parts, Word XML root and nonempty document text.
- HTML site ZIP: root index, ZIP/CRC and local page, fragment and asset targets.
- Source ZIP: canonical Quarto input, descriptor, licenses/notices and a ZIP comment
  matching the independently expected full source commit (as written by `git archive`).

Archives reject unsafe paths, duplicates and symlinks. The source bundle also
rejects Git metadata and dependency-cache directories. External URLs are not
fetched by this offline gate; online checking is a separate review/build step.

PDF inspection requires Poppler's `pdfinfo` (`poppler-utils` on Debian/Ubuntu).
Missing inspection tools are failures, not skipped successes. These structural
checks do not replace visual review of figures, tables, layout or factual accuracy.

`archive_tree(source, output, epoch)` writes a fresh ZIP with sorted entries,
fixed UTC timestamps and normalized permissions. Its output must be outside the
input tree. Source archives should instead come from the approved Git commit.

Verification: `python3 -m unittest discover -s tools/tests -p test_artifacts.py`.
The runtime harness also inspects actual Quarto-generated PDF/DOCX/HTML and a
Git source archive. Rollback removes this module, its tests and this guide without
changing publication identity or existing validators.

The local runtime proof passed for Quarto 1.11.9 / Pandoc 3.10 / Typst 0.15.1
pilot outputs and a Git archive of the reviewed sample commit. All four payload
inspectors and six-file manifest/checksum verification passed. Its version is
`0.0.0-test`: it is a build-boundary proof, not an approved book release.
