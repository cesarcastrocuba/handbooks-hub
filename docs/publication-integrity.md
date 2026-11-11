# Publication identity and byte integrity

The toolkit's `publication` module creates an identity for already-built payloads
and verifies their exact bytes without rebuilding them. This is the first Phase 4
publication unit; format inspection, build orchestration and publishing are separate.

`write_manifest(directory, metadata, artifacts)` takes five roles mapped to plain
filenames: `html` (site ZIP), `pdf`, `docx`, `markdown` (`book.md`) and `source`
(source ZIP). Metadata follows the bundled `publication-manifest.schema.json`: exact
source commit, book/toolkit/profile versions, build command, source epoch and resolved
tool versions. Payload hashes and sizes are measured from the files, never supplied by
the caller.

The writer emits manifest schema `1.1`, which requires exactly those five payloads.
Schema `1.0` (four payloads, without `markdown`) remains valid and verifiable, because
releases published before toolkit `0.6.0` carry it and must stay checkable.

The fresh output directory contains exactly seven release assets: five payloads,
`publication-manifest.json`, and `SHA256SUMS.txt`. The checksums cover the five
payloads and the manifest. A checksum file cannot hash itself. Existing identity
files are not replaced; a new build needs a fresh directory.

The writer rejects directories with unrelated files and enforces `.zip`, `.pdf`,
`.docx` and `.md` extensions. Provenance records Typst as well as Quarto, Pandoc and
Python. Both identity files are staged before exclusive creation; exceptions
remove any identity files created by this call so a retry remains possible.
This is not a crash-atomic two-file transaction. The build must use a private
staging directory and atomically rename the complete verified directory into its
final location; publication must never observe an in-progress staging directory.

`verify_publication(directory)` returns a `CheckResult`. It rejects schema errors,
missing/duplicate roles or names, path traversal, symlinks, extra assets, changed
sizes/hashes, malformed/duplicate checksums and incomplete checksum coverage. The
expected role set comes from the manifest `schema_version`: `1.0` needs four payloads
and `1.1` needs five, so a `1.1` manifest without `markdown`, or a `1.0` manifest that
carries it, fails.

This establishes byte integrity, not trust or editorial approval. The release gate
must independently compare the manifest's source commit with the approved commit,
inspect payload formats and links, and publish these same files. Tests deliberately
use byte fixtures and do not claim that those fixtures are valid PDF/DOCX documents.

Verification: `python3 -m unittest discover -s tools/tests -p test_publication.py`.
Runtime boundary: the API writes and rereads a seven-file publication directory;
the regression suite exercises corruption and provenance failures. Rollback removes
this module, schema, tests and guide; existing validators are unaffected.

Run the separate [format inspection](artifact-inspection.md) gate before publication.
