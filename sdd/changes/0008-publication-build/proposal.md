# Proposal — staged publication build

**Status:** Proposed
**Change:** `0008-publication-build`
**Branch:** `feat/publication-build`

## Context

The toolkit now has a publication identity API (`write_manifest`, `verify_publication`) and format
inspection/archive APIs. The next step is a build orchestrator that uses them for a real book source
without exposing an incomplete output directory.

## Interface

```text
handbook-toolkit build-book --repo PATH --commit FULL_SHA --output NEW_EXTERNAL_PATH --profile PROFILE [--version VERSION] [--epoch EPOCH] [--quarto QUARTO]
```

`build_book(repo, commit, output, profile=..., version=None, epoch=None, quarto="quarto")` returns a
`BuildResult` with output path, commit, version, epoch and resolved tool versions.

## Required behavior

- Require a clean repository at the exact `HEAD` commit.
- Refuse an output path that exists or is inside the source repository.
- Create a private staging directory beside the final output.
- Extract only tracked files from the exact commit with `git archive`.
- Generate deterministic `_quarto.yml` and `index.qmd`; use the explicit reading order and profile.
- Render HTML, Typst/PDF and DOCX once with Quarto `1.11.9`.
- Package the HTML site, PDF, DOCX and source archive with the required suffixes.
- Require the source ZIP comment to be the full source commit.
- Inspect all four payloads before writing identity.
- Write manifest/checksums, verify the complete six-file directory, then atomically rename staging to
  output. A failure leaves no final output and no private staging directory.
- Record Quarto/Pandoc/Typst/Python/zlib runtime versions, profile and epoch.
- Never publish, upload, deploy or release.

## Boundaries

This change does not implement the portal/catalog branch, release automation or editorial approval.
It uses the shared publication dependency stack; root owns those modules and their independent
review. The build is structural: it does not prove prose quality or visual layout.

## Acceptance

- Real Quarto build of an isolated pilot fixture, not a mocked subprocess.
- Six files exactly; manifest and checksums verify.
- Source commit comment, reading order, notices and descriptor survive inspection.
- Existing output, dirty source and failed builds are refused without exposing final output.
- CI build job runs the real pilot build when Quarto/pdfinfo are available.
