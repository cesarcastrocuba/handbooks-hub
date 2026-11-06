# Publication contract

> **Status: planned.** No publication pipeline exists in the Phase 1 scaffold. This document fixes the
> target contract so the toolkit, template, book repositories and catalog can be designed against it.

## Artifact set

Each approved book release produces exactly these assets:

| Asset | Purpose | Required |
| --- | --- | --- |
| HTML site bundle (`.zip`) | Offline reading and archival copy of the Pages site | Yes |
| PDF | Print and review | Yes |
| DOCX | Editable derivative for accessibility and review | Yes |
| Source bundle (`.zip`) | Canonical sources and build inputs at the release commit | Yes |
| `publication-manifest.json` | Identity, provenance, artifact hashes and tool versions | Yes |
| `SHA256SUMS.txt` | Human- and machine-checkable checksums | Yes |

The book's GitHub Pages site serves the HTML reading experience. The release holds the downloadable
assets. The catalog links to the release, not to a branch.

## Build once, publish the same bytes

1. The owner approves a commit on `main` and authorizes a release.
2. CI checks out that exact commit, with a clean environment.
3. CI builds HTML, PDF, DOCX and the source bundle once.
4. CI runs structural, link, artifact and rendering checks.
5. CI writes the manifest and checksums over the verified artifacts.
6. CI attaches those exact files to the release and publishes the same HTML to Pages.
7. The catalog entry is updated only after the release assets verify.

No artifact is rebuilt between verification and publication. A failed check blocks the release; it
does not produce a partial catalog entry.

## Reproducibility

- Pin Quarto, Pandoc, Python, Graphviz and Python dependencies. Record the resolved versions in the
  manifest.
- Set a fixed `SOURCE_DATE_EPOCH` for reproducible builds where the toolchain supports it.
- Record the source commit SHA, book version, profile version, toolkit version and build command.
- Normalize archive timestamps and ordering where practical.
- A rebuild may differ in non-semantic metadata; the manifest must state which artifacts are
  bit-identical and which are semantically verified.

## Manifest (planned shape)

```json
{
  "schema_version": "1.0",
  "book": { "id": "example-book", "version": "1.0.0", "commit": "<40-hex>" },
  "toolkit": "0.3.0",
  "profile": { "id": "standard", "version": "0.2.0" },
  "build": {
    "started_at": "<ISO-8601 UTC>",
    "command": "handbook-toolkit book build .",
    "source_date_epoch": 1761868800,
    "tool_versions": { "quarto": "1.11.9", "pandoc": "3.10", "python": "3.12" }
  },
  "artifacts": [
    { "path": "book.pdf", "sha256": "<64-hex>", "bytes": 123456, "media_type": "application/pdf" }
  ]
}
```

The final schema is introduced in Phase 4 and validated by the toolkit before any release is
published. The example is illustrative, not a released format.

## Quality gates

| Gate | Check | Failure behavior |
| --- | --- | --- |
| Source | Reading order covers every manuscript file exactly once | Block |
| Structure | Profile skeleton, section closure and required labels | Block |
| References | Section, figure, table, citation and URL targets resolve | Block |
| Artifacts | PDF/DOCX open, minimum size, page count and expected format markers | Block |
| Links | Internal HTML fragments and cross-file links resolve | Block |
| Checksums | Every published asset is listed and hashes match | Block |
| Visual | Sampled pages and every figure inspected at print size | Block |

## Access, retention and rollback

- Release assets are immutable. A correction is a new version, never an in-place replacement.
- Keep the manifest and checksums with the release so a later audit can verify the bytes.
- If a published artifact is wrong, withdraw the catalog entry first, then publish a corrected
  version. Never silently replace assets.
- Pages is a projection of an approved release. A failed Pages deployment leaves the previous
  approved site in place.

## Prohibited

- Committing generated artifacts to the book source repository.
- Publishing from an unmerged branch, a dirty worktree or an untagged commit.
- Linking the catalog to a mutable URL.
- Publishing without a license and notice review.
