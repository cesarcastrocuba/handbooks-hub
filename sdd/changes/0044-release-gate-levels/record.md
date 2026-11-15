# Record — The release gate does not apply rules newer than the release

**Change:** `0044-release-gate-levels`. **Recorded:** 2026-11-15. **Toolkit:** `0.10.4` (hub-side;
books stay on `0.10.3`).

## Problem

After change `0042` the portal was redeployed (`portal-pages` run 43666966237). The build failed in
`catalog_verification`:

```text
handbook-authoring-and-publishing: remote format failure: …/assets/book.docx: DOCX must not mark fields dirty
release verification: FAILED
```

The listed release is sample `v0.5.0`, built with toolkit `0.10.1`. The rule "no `w:dirty`" was
added in `0.10.2`. The release gate called the same `inspect_payload` as the build, so every rule
added to the build gate was applied to every edition already published. The hidden-path rule of
`0.10.3` would have rejected `v0.5.0` next. With several books in the catalog, one new validator
would block every portal deployment until all of them were released again.

## What changed

- `inspect_payload(..., build_invariants=True)` keeps the build gate as it is. With `False` it
  skips the rules that describe what the current toolkit guarantees about its own output
  (`validate_docx`, hidden site paths) and keeps format checks and local-target resolution.
- `catalog_verification` passes `False`. Integrity (manifest, checksums, tag commit, asset list,
  live site parity) is unchanged.
- Tests: a DOCX with a dirty field and a site archive with a hidden path are rejected by the build
  gate and accepted by the release gate; the release gate is called with `build_invariants=False`.
- `docs/artifact-inspection.md` documents the two gates.

## Why not version-gated rules

Tying each rule to the toolkit version that introduced it would let the release gate apply "the
rules of its time" to each edition, but it needs a registry of rules and versions that must be
kept exact forever. The build gate already ran with those rules, and the manifest and checksums
prove that the published bytes are the ones it accepted.

## Evidence

- `portal-pages` run 43666966237: failure above.
- After the change: `python3 -m handbook_toolkit.catalog_verification catalog/catalog.json`
  against the live `v0.5.0` release (see the pull request).
