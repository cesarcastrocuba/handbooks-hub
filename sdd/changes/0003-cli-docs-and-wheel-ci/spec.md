# Spec — CLI examples and wheel-install CI

**Status:** Proposed
**Change:** `0003-cli-docs-and-wheel-ci`

## Deliverables

| ID | Deliverable | Location | State |
| --- | --- | --- | --- |
| D1 | Correct global option order in docs | `tools/README.md`, `docs/implementation-plan.md` | Done |
| D2 | Documented-example parser regression | `tools/tests/test_docs_commands.py` | Done |
| D3 | Wheel build and schema-content assertion in CI | `.github/workflows/ci.yml` | Done |
| D4 | Isolated wheel install and independent book validation in CI | `.github/workflows/ci.yml` | Done |
| D5 | Status, changelog and SDD updates | `STATUS.md`, `CHANGELOG.md`, `sdd/` | Done |

## CLI contract

Global options must precede the subcommand:

```text
handbook-toolkit [--root PATH] [--schemas PATH] <command> [command options]
```

Accepted:

```bash
handbook-toolkit --root . verify --full
handbook-toolkit --root /path/to/book validate-book --full
```

Rejected:

```bash
# Invalid: global options must precede the subcommand.
handbook-toolkit verify --root .
```

The regression extracts fenced and table-cell examples from Markdown, skips future commands not yet
implemented and runs current examples through `build_parser().parse_args()`. It also asserts that the
old order raises `SystemExit`.

## CI wheel-install job

The job is independent of the `checks` job and performs:

1. `python -m build --wheel --outdir "$RUNNER_TEMP/wheelhouse" tools`.
2. Open the wheel and assert the three `handbook_toolkit/schemas/*.json` entries are present.
3. Create a fresh virtual environment and install the wheel.
4. Assert `handbook_toolkit.__file__` is under `site-packages`.
5. Copy `template/book` to `$RUNNER_TEMP/independent-book`, add decoy root schemas with an impossible
   required field, and run:
   ```bash
   handbook-toolkit --root . validate-book --full
   ```
   from the independent book.

The job uses no hub checkout path for validation and does not publish anything.

## Acceptance criteria

1. `make check` passes: 48 tests, 5 checks, 0 problems.
2. `make full` passes: 48 tests, 6 checks, 0 problems.
3. The docs test catches `handbook-toolkit verify --root .`.
4. The workflow is valid YAML and its `run` blocks pass `bash -n`.
5. The workflow contains the wheel, schema assertion, isolated install and independent-book steps.
6. Local reports mark the CI job as not run.

## Out of scope

- Running GitHub Actions from this environment.
- Installing a wheel locally.
- Changing global option parsing.
- Publication or release automation.
