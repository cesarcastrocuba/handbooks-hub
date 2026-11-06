# Evidence — CLI examples and wheel-install CI

**Change:** `0003-cli-docs-and-wheel-ci`
**Status:** Implemented, pending independent review
**Date:** 2026-11-06
**Fix commit:** pending (recorded by the follow-up evidence commit)
**Starting point reviewed:** `05c73ba50488656cde7cb86e2eac6e0dabb8c2a4`

## Environment

| Item | Value |
| --- | --- |
| OS | Linux, `/home/ubuntu/github/handbooks-hub` |
| Python | 3.12.3 |
| `jsonschema` | 4.10.3 |
| `PyYAML` | 6.0.1 |
| `pip` / `ensurepip` | Not available |
| `build` / `wheel` | Not available |
| GitHub Actions | Not run; no remote and no CI execution from this environment |

The local environment cannot build or install a wheel. The wheel-install job is therefore committed
as CI configuration and was **not executed locally**. Its YAML and shell syntax were checked locally;
its runtime behavior is for the reviewer/CI to confirm.

## Changes

| Area | Change |
| --- | --- |
| CLI examples | Moved the global `--root` option before `verify` in `tools/README.md` and `docs/implementation-plan.md` |
| Regression | `tools/tests/test_docs_commands.py` parses fenced and table examples with the real parser |
| CI | Added the `wheel-install` job: build wheel, assert packaged schemas, isolated venv install, validate an independent book |
| Status | `STATUS.md` records the CI job as not executed locally |
| Changelog | Records the CLI-doc fix and the new CI boundary job |
| SDD | This change record |

## Commands and results

### 1. Fast checks

```bash
make check
```

Result: **PASS**

- 48 unit tests; `OK`.
- 5 checks, 0 problems.

### 2. Full checks

```bash
make full
```

Result: **PASS**

- 48 unit tests; `OK`.
- 6 checks, 0 problems.
- Documentation links resolve.

### 3. Documentation command regression

```bash
PYTHONPATH=tools/src python3 -m unittest discover -s tools/tests -p 'test_docs_commands.py' -v
```

Result: **PASS**, 2 tests.

- `test_documented_cli_examples_are_parseable` extracts fenced and table-cell examples and runs
  `build_parser().parse_args()` on current commands.
- `test_global_options_are_rejected_after_the_subcommand` proves that
  `handbook-toolkit verify --root .` raises `SystemExit`.
- Intentionally invalid examples in the change record are marked with an `# Invalid:` comment and
  skipped.

### 4. Compilation

```bash
python3 -m compileall -q tools
```

Result: **PASS** (exit 0).

### 5. CI workflow syntax

A local Python/YAML check loaded `.github/workflows/ci.yml`, asserted the `wheel-install` job exists
and ran `bash -n` on every `run` block.

Result: **PASS**; YAML parsed and all shell blocks passed syntax checking.

### 6. Clean clone

A clean clone is recorded after the fix commit in the follow-up evidence update.

## CI wheel-install job (not executed)

The job in `.github/workflows/ci.yml`:

1. Installs `build` and runs `python -m build --wheel --outdir "$RUNNER_TEMP/wheelhouse" tools`.
2. Opens the wheel and asserts these entries exist:
   - `handbook_toolkit/schemas/book.schema.json`
   - `handbook_toolkit/schemas/catalog.schema.json`
   - `handbook_toolkit/schemas/profile.schema.json`
3. Creates `$RUNNER_TEMP/toolkit-venv` and installs the wheel.
4. Asserts `handbook_toolkit.__file__` resolves under `site-packages`.
5. Copies `template/book` to `$RUNNER_TEMP/independent-book`, writes decoy
   `schemas/{book,catalog,profile}.schema.json` files with an impossible required field, and runs:
   ```bash
   handbook-toolkit --root . validate-book --full
   ```
   from the independent book, outside the hub checkout.

This is a packaging-boundary check, not a release or publication step.

## Checks not run

| Check | Reason |
| --- | --- |
| GitHub Actions `checks` job | No remote and no CI execution locally |
| GitHub Actions `wheel-install` job | `pip`, `build` and `wheel` are unavailable locally |
| Local wheel build/install | Same tooling gap |
| Quarto/PDF/DOCX | Phase 4 |

## Review handoff

Review the fix commit recorded above, then:

1. Re-run `make check` and `make full`.
2. Inspect `tools/tests/test_docs_commands.py` and confirm the old order fails.
3. Inspect the `wheel-install` job; do not treat local syntax checks as a CI run.
4. Confirm the documented commands use `handbook-toolkit [--root PATH] <command>`.
