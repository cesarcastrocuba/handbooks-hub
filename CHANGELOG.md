# Changelog

All notable changes to the hub are recorded here. The format follows Keep a Changelog; versions use
semantic versioning once the toolkit is published.

## [Unreleased]

### Added

- Hub onboarding guide at `docs/setup.md` and a README quickstart covering reader/contributor/
  maintainer/book-author paths, tested Linux prerequisites, in-repo `.venv` install, no-make checks
  and missing-pip/venv troubleshooting.
- Pinned-toolkit installation instructions and `requirements.txt` for the independent book template,
  with the future Quarto/publication toolchain kept separate from current validators.
- Initial hub scaffold: governance, architecture and contract documents, phased implementation plan,
  proposed standard editorial profile, JSON schemas, book template, empty catalog and lightweight SDD
  records.
- `handbook-toolkit` 0.1.0 with deterministic catalog, profile and book validators and unit tests.
- `handbook-toolkit` 0.2.0 adds `validate-manuscript` for structural section-pilot and chapter
  validation against an explicit profile, without requiring visuals.
- `handbook-toolkit` 0.3.0 adds `build-book`: clean-commit archive staging, one Quarto
  HTML/Typst/DOCX render, payload inspection, manifest/checksum identity and atomic finalization,
  without publishing.
- Basic CI running the fast and full repository checks.
- CI `wheel-install` job that builds the wheel, verifies the packaged schemas, installs it in an
  isolated environment and validates a book outside the hub checkout.
- Dual licensing (`LICENSE`, `LICENSE-CODE`) and attribution notice.

### Changed

- Owner approved the Phase 1 foundation, the dual-license defaults, the broad technical/software
  audience and standard profile `0.2.0`, and authorized root integration of the reviewed
  `feat/topic-neutral-profile` branch. Pilot approval and release remain unauthorized. See
  `sdd/changes/0005-owner-approvals/`.
- Standard profile `0.2.0`: the mandatory architecture-specific checklist is now a topic-neutral
  `Review Checklist`; figures and tables are optional when they would not help the reader, and their
  absence is not an exception. The template pins the new profile version. See
  `sdd/changes/0004-topic-neutral-profile/`.

### Fixed

- The toolkit now ships its JSON Schemas as package data and resolves them from the installed package
  by default. An independent book can validate without a hub checkout or a vendored `schemas/`
  directory. `--schemas` remains an explicit override. See
  `sdd/changes/0002-toolkit-packaged-schemas/`.
- Documented CLI examples now put global `--root` and `--schemas` options before the subcommand, and a
  regression test parses every documented example. See
  `sdd/changes/0003-cli-docs-and-wheel-ci/`.

### Notes

- No GitHub repository was created, no site was deployed, no release was published and this change
  did not modify the sample-book or reference-handbook content. The sample repository was scaffolded
  concurrently by its own session.
