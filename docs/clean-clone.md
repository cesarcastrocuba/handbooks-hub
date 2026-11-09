# Clean-clone matrix

## Purpose and acceptance

P5-04 proves the hub and the public sample book work from fresh clones on more than one operating
system, without a developer's existing checkout, virtual environment or downloaded toolchain. The
acceptance in [`implementation-plan.md`](implementation-plan.md) is: the hub and the sample book
verify on Linux and one additional environment.

The matrix deliberately uses a different path from the publication pipeline. It answers "does a
clean clone install and validate?" rather than "are the release artifacts reproducible?".

## What the workflow runs

The workflow is [`.github/workflows/clean-clone.yml`](../.github/workflows/clean-clone.yml). It
runs on `ubuntu-24.04` and `macos-15`, with `fail-fast: false` so each environment reports
independently. A 45-minute timeout bounds each job. The two legs never use `actions/checkout`:
sources come from anonymous `git clone`, and all working directories are created under
`RUNNER_TEMP`, outside any checkout.

The hub leg uses `HUB_COMMIT`, which is the pull-request head for a workflow-changing pull request or
`github.sha` otherwise.

1. **Prepare the environment.** Select paths under `RUNNER_TEMP` for the hub clone, book clone, book
   virtual environment and logs. Install Python 3.12 and Quarto 1.11.9. Install Poppler
   (`poppler-utils` with `apt-get` on Linux, `poppler` with Homebrew on macOS). Record the kernel,
   Python, Git, Make and Quarto versions, the `pdfinfo` and `pdftotext` paths, and the `pdfinfo`
   version.
2. **Hub: clone the commit under test.** Clone the hub, fetch `HUB_COMMIT`, check it out detached,
   print `HEAD` and require a clean working tree.
3. **Hub: create a clean environment.** Create `.venv` in the clone, upgrade pip and install
   `requirements-dev.txt`.
4. **Hub: run the checks.** Run `make check` and `make full`, teeing each log. Then scan both logs:
   print the test summary and fail the leg if any test reports `skipped`.
5. **Book: remove the hub clone.** Delete the hub directory before the book leg, with
   `if: ${{ !cancelled() }}` so a hub failure does not hide a book failure.
6. **Book: clone the public sample book.** Clone `cesarcastrocuba/handbook-sample-01` at branch
   `main` into a separate directory and print the cloned `HEAD`.
7. **Book: install the pinned requirement.** Create a separate virtual environment, install the
   book's `requirements.txt`, print the toolkit version and the installed toolkit distribution.
8. **Book: prove the toolkit is installed, not borrowed.** Require `PYTHONPATH` to be empty, import
   `handbook_toolkit`, and assert its file is inside the book virtual environment and
   `site-packages`.
9. **Book: run the full checks.** Run `make full` and tee the log.
10. **Report.** Append the per-log test summary and verbose skip count to the GitHub step summary,
    including legs that did not run.

## How to run it

- **Manually:** open the workflow in the repository's Actions tab and choose **Run workflow**
  (`workflow_dispatch`).
- **Weekly:** the schedule runs at `17 6 * * 1`, every Monday at 06:17 UTC.
- **Pull requests:** a pull request that changes `.github/workflows/clean-clone.yml` triggers the
  matrix automatically.

## Recorded evidence

Run: <https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42535908581>

Tested commit: `b030e214981c8e89f27f4e829eab9127896de67f`, the workflow branch head.

| Environment | Result | Hub | Sample book |
| --- | --- | --- | --- |
| `ubuntu-24.04` (x86_64) | success | `make check`: 167 tests, OK; `make full`: 167 tests, OK; 0 skipped; `verify` 5 checks and `verify --full` 6 checks, 0 problems | `make full`: 13 tests, OK; required files, 93 relative links, generated artifacts, environment paths, agent-neutral roles, gate state and editorial status OK |
| `macos-15` (arm64) | success | `make check`: 167 tests, OK; `make full`: 167 tests, OK; 0 skipped; `verify` 5 checks and `verify --full` 6 checks, 0 problems | `make full`: 13 tests, OK; required files, 93 relative links, generated artifacts, environment paths, agent-neutral roles, gate state and editorial status OK |

The sample book clone reported `HEAD` `4e17627395500154f6c3491bf0a0a83f6cbc14cb` at the time of the
run. The macOS leg first failed because the sample book's Makefile used a GNU-only `mktemp`
invocation; sample pull request 3 fixed it. That is the kind of cross-platform defect this matrix
exists to find.

## Limits

- **No artifact build runs here.** The hub `make full` and the sample book `make full` are validation
  gates, not publication builds. Artifact builds belong to the `publication-build` CI job and the
  book's release workflow (see [`publication-build.md`](publication-build.md)).
- **Windows is not covered.** The matrix has only `ubuntu-24.04` and `macos-15`.
- **GitHub-hosted runners are not physical workstations.** The result does not cover local
  developer machines, hardware, or network conditions outside the hosted runners.
- **The commit tested is the workflow branch head**, not a post-merge `main` commit. A clean-clone
  run on `main` after merge is still to be recorded.
