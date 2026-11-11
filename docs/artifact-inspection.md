# Inspect rendered formats before publication

The toolkit's `artifacts` module complements publication byte integrity.
`inspect_payload(path, role, source_commit=..., version=...)` returns structural issues for:

- PDF: signature plus successful `pdfinfo` inspection and at least one page.
- DOCX: ZIP/CRC, required package parts, Word XML root and nonempty document text.
- HTML site ZIP: root index, ZIP/CRC and local page, fragment and asset targets.
- Markdown edition: valid UTF-8 and non-empty, opened by a level-one heading and the
  document-control table, with a `Version` field matching the manifest version and a
  `Commit` field matching the source commit. A raw `<script` in prose is rejected, because
  it would render as HTML. Fenced code blocks and inline code spans are documentation and
  are not inspected, so a handbook may show any markup, path or URL in an example: `/tmp/`,
  `/home/`, `/Users/` and `file://` are legitimate book content.
- Source ZIP: canonical Quarto input, descriptor, licenses/notices and a ZIP comment
  matching the independently expected full source commit (as written by `git archive`).
  Its declared reading-order file must exist and cover every canonical chapter once.

Archives reject unsafe paths, duplicates and symlinks. The source bundle also
rejects Git metadata and dependency-cache directories. External URLs are not
fetched by this offline gate; online checking is a separate review/build step.
Archives are bounded to 20,000 members, 1 GiB total uncompressed size and 128 MiB
per member, with a maximum 1000:1 compression ratio. Encrypted members fail.

PDF inspection requires Poppler's `pdfinfo` (`poppler-utils` on Debian/Ubuntu).
Missing inspection tools are failures, not skipped successes. These structural
checks do not replace visual review of figures, tables, layout or factual accuracy.

`archive_tree(source, output, epoch)` writes a fresh ZIP with sorted entries,
fixed UTC timestamps and normalized permissions. Its output must be outside the
input tree. Source archives should instead come from the approved Git commit.
Byte reproducibility is bounded to the pinned Python/zlib toolchain; their exact
runtime versions belong in the manifest. No cross-toolchain byte identity is claimed.

Verification: `python3 -m unittest discover -s tools/tests -p test_artifacts.py`.
The runtime harness also inspects actual Quarto-generated PDF/DOCX/HTML and a
Git source archive. Rollback removes this module, its tests and this guide without
changing publication identity or existing validators.

The Markdown edition is not checked for portable text by the shared inspector. The build
itself rejects a leak of its own absolute paths (the staging workspace, the output parent,
the source repository and the home directory) before writing `book.md`, which catches the
real defect without rejecting content. The online release gate still passes the source
commit, so a changed header fails.

The local runtime proof passed for Quarto 1.11.9 / Pandoc 3.10 / Typst 0.15.1
pilot outputs and a Git archive of the reviewed sample commit. That proof covered
the four original payload inspectors and six-file manifest/checksum verification.
Toolkit `0.6.0` adds the Markdown inspector as a fifth payload; the regression that
covers it is `make check` and the real build in `test_build.py`. Its version is
`0.0.0-test`: it is a build-boundary proof, not an approved book release.
