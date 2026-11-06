# Proposal — correct CLI examples and add wheel-install CI

**Status:** Proposed
**Date:** 2026-11-06
**Change:** `0003-cli-docs-and-wheel-ci`
**Review finding:** review of `05c73ba` found that documented commands place the global `--root`
option after the subcommand, which argparse rejects.

## Context

`handbook-toolkit` defines `--root` and `--schemas` as global options before the subcommand. Some
documentation showed `handbook-toolkit verify --root .`, which fails with a usage error. The package
fix in `0002` made the installed toolkit self-contained, but local wheel tooling is unavailable, so
the new package boundary had not been exercised through a real wheel install.

## Goals

- Correct every actual `handbook-toolkit` example to use the accepted argument order.
- Add a regression that parses documented examples with the real parser.
- Add a CI job that builds a wheel, verifies the packaged schemas, installs the wheel in an isolated
  virtual environment and validates a book outside the hub checkout.
- Keep hub verify behavior working.
- Report honestly that the CI job was not executed locally.

## Non-goals

- Changing the CLI parser to accept global options after the subcommand. The established interface is
  documented and tested; silently accepting both orders would hide mistakes.
- Releasing, deploying, approving a gate or creating a GitHub repository.
- Building a wheel locally; the environment has no pip, ensurepip, build or wheel.

## Acceptance

1. Every current documented `handbook-toolkit` command parses with the real parser.
2. A regression fails on the old `verify --root .` order.
3. The CI workflow contains a wheel build, schema-content assertion, isolated install and independent
   book validation.
4. `make check` and `make full` pass locally.
5. No claim that GitHub Actions ran.
