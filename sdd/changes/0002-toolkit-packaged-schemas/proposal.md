# Proposal — package the shared schemas with the toolkit

**Status:** Proposed
**Date:** 2026-11-06
**Change:** `0002-toolkit-packaged-schemas`
**Review finding:** independent review of `46b78cc` found a blocking architecture gap.

## Context

The hub is meant to let an independent book install a pinned `handbook-toolkit` and validate its
`book.yaml` without a hub checkout or copied shared scripts. The first scaffold put the schemas in a
top-level `schemas/` directory and defaulted the CLI to `<root>/schemas`. That works inside the hub
but not in a book repository: an installed toolkit cannot see the hub's schema directory, so a book
would have to vendor the schemas or check out the hub. Both contradict the handoff.

## Problem

Schema resolution is coupled to the hub checkout layout:

- `schemas/` lives outside the `handbook_toolkit` package and is not included in a wheel.
- The CLI default `--schemas` path is `<root>/schemas`, which does not exist in a book repository.
- `verify_repository` reads `<root>/schemas`, so even the hub's own check depends on a layout that a
  book cannot reproduce.

## Goals

- Make the schemas part of the `handbook_toolkit` package data.
- Resolve schemas from the installed package by default using `importlib.resources`, which works for
  a normal installation and for zip import.
- Keep an explicit `--schemas` override for local or experimental schema sets.
- Keep the hub's `verify` behavior working.
- Prove the installed-package boundary with an isolated integration test.
- Update documentation and the change record so no artifact still claims the old layout.

## Non-goals

- Changing the profile, book, catalog or manifest contract.
- Cutting a release, approving a gate, deploying or creating a GitHub repository.
- Packaging the profile content itself. A book pins the profile version; schema validation is the
  boundary this change fixes. Profile distribution is reviewed separately if needed.
- Adding a wheel build in this environment (no pip, ensurepip or wheel is available).

## Constraints

- The hub remains the only writable repository in this session.
- No copied schema directory in books.
- Keep the CLI backward-compatible for existing hub checks and explicit overrides.
- English artifacts; conventional commits; no AI attribution.

## Acceptance

1. A copy of only `handbook_toolkit` (including its schemas) validates the template book from a
   temporary directory with a decoy `schemas/` in the book root.
2. A zip-imported copy of the package does the same, proving resource loading is not filesystem-only.
3. `make check` and `make full` still pass in the hub.
4. The package configuration declares `schemas/*.json` as package data.
5. No top-level `schemas/` directory remains.

## Risk

`importlib.resources` behavior differs by loader. The zip test covers the least filesystem-friendly
case; a real wheel install is left to CI because this environment has no packaging tooling. If CI
discovers a wheel-specific problem, the fallback is to keep the package-data declaration and adjust
the resource helper, not to restore a vendored schema layout.
