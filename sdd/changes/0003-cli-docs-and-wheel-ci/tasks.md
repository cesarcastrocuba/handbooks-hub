# Tasks — CLI examples and wheel-install CI

**Status:** Proposed
**Change:** `0003-cli-docs-and-wheel-ci`

| ID | Task | Write set | Status |
| --- | --- | --- | --- |
| T1 | Locate every actual CLI example | Markdown files (read-only) | Done |
| T2 | Correct global option order | `tools/README.md`, `docs/implementation-plan.md` | Done |
| T3 | Add documented-example regression | `tools/tests/test_docs_commands.py` | Done |
| T4 | Add wheel build and schema assertion to CI | `.github/workflows/ci.yml` | Done |
| T5 | Add isolated install and independent-book validation | `.github/workflows/ci.yml` | Done |
| T6 | Update status, changelog and SDD | `STATUS.md`, `CHANGELOG.md`, `sdd/` | Done |
| T7 | Run fast, full, YAML and shell syntax checks | None | Done |
| T8 | Commit and record exact HEAD | `.git/`, this record | Done after commit |
| T9 | Independent review | Review comments | Pending |

## Verification mapping

| Criterion | Evidence |
| --- | --- |
| Examples parse | `test_documented_cli_examples_are_parseable` |
| Old order fails | `test_global_options_are_rejected_after_the_subcommand` |
| CI wheel job exists | workflow YAML inspection |
| Workflow syntax | PyYAML parse + `bash -n` on `run` blocks |
| Hub checks | `make check`, `make full` |
| CI not run | Evidence section and final report |
