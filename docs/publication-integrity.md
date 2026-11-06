# Publication identity and byte integrity

The toolkit's `publication` module creates an identity for already-built payloads
and verifies their exact bytes without rebuilding them. This is the first Phase 4
publication unit; format inspection, build orchestration and publishing are separate.

`write_manifest(directory, metadata, artifacts)` takes four roles mapped to plain
filenames: `html` (site ZIP), `pdf`, `docx`, and `source` (source ZIP). Metadata follows
the bundled `publication-manifest.schema.json`: exact source commit, book/toolkit/
profile versions, build command, source epoch and resolved tool versions. Payload
hashes and sizes are measured from the files, never supplied by the caller.

The fresh output directory contains exactly six release assets: four payloads,
`publication-manifest.json`, and `SHA256SUMS.txt`. The checksums cover the four
payloads and the manifest. A checksum file cannot hash itself. Existing identity
files are not replaced; a new build needs a fresh directory.

`verify_publication(directory)` returns a `CheckResult`. It rejects schema errors,
missing/duplicate roles or names, path traversal, symlinks, extra assets, changed
sizes/hashes, malformed/duplicate checksums and incomplete checksum coverage.

This establishes byte integrity, not trust or editorial approval. The release gate
must independently compare the manifest's source commit with the approved commit,
inspect payload formats and links, and publish these same files. Tests deliberately
use byte fixtures and do not claim that those fixtures are valid PDF/DOCX documents.

Verification: `python3 -m unittest discover -s tools/tests -p test_publication.py`.
Runtime boundary: the API writes and rereads a six-file publication directory;
the regression suite exercises corruption and provenance failures. Rollback removes
this module, schema, tests and guide; existing validators are unaffected.

Run the separate [format inspection](artifact-inspection.md) gate before publication.
