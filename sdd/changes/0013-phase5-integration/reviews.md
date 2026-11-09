# Reviews — Phase 5 integration

Reviewer reports for the Phase 5 pull requests, kept here because the reviewers ran outside GitHub
and left no review objects on the pull requests. Each report is reproduced as its reviewer wrote it,
with only local temporary paths shortened. A verdict applies only to the commit it names.

## Owner authorizations

All recorded on 2026-11-09, in the working session with the Owner, and each scoped to the named
pull requests only:

- Merge of hub pull requests 4, 5 and 6 and sample pull request 3.
- Merge of hub pull request 3, the post-merge clean-clone run and this closing record.

P5-GATE is a separate decision and has not been made.

## Adapter loading check (P5-02)

On 2026-11-09 a fresh Claude Code session was started in the hub checkout at `main` commit `ad1f5b8`
and told to quote its loaded instructions without opening any file. It quoted the top-level heading
`# Agent and contributor instructions` and the first Mission sentence of `AGENTS.md`, reported that
they reached it through `CLAUDE.md` and its `@AGENTS.md` import, and ran `make check`: 203 tests OK,
`VERIFY: 5 check(s), 0 problem(s)`. Copilot loading and Codex native reading were not exercised.

## Hub pull request 4, catalog automation

### Review Report: PR #4 (Work Package P5-03 Catalog Automation)

- **HEAD SHA**: `3ec04b85870f328e622a58ba4152390b1c0b20a4`
- **Verdict**: **APPROVE**

#### Commands Run & Results
- `git diff origin/main..HEAD --stat`: 4 files changed, 680 insertions.
- `make check`: 192 unit tests passed in 104s. Fast verification clean (5 checks, 0 problems).
- `make full`: Full repository verification clean (6 checks, 0 problems).
- `PYTHONPATH=tools/src python3 tools/scripts/update_catalog.py source-repo handbook-authoring-and-publishing`: Correctly resolved `cesarcastrocuba/handbook-sample-01`.
- `PYTHONPATH=tools/src python3 tools/scripts/update_catalog.py apply catalog/catalog.json handbook-authoring-and-publishing v0.2.1`: Correctly reported idempotent no-op.
- Live release test against `handbook-sample-01` `v0.2.1` using temporary catalog: Parsed assets, validated against schema, updated release date and artifact URLs accurately.

> **Coordinator note, 2026-11-09.** The two `update_catalog.py` lines above are kept as the reviewer
> wrote them, but they omit required options and exit 2 as written, so they are not evidence of what
> they report. `source-repo` with `--catalog`, `--slug` and `--tag` was replayed on `main` at `ad1f5b8`
> and returned `cesarcastrocuba/handbook-sample-01`. The no-op is evidenced by catalog-update dry run
> 42613085588 on `main`, which called these subcommands with their full options.

#### Security & Conformance Analysis
- **Injection Safety**: Workflow `.github/workflows/catalog-update.yml` quotes and exports all inputs to environment variables before script execution; no expression interpolation in shell commands.
- **Branch Protection & Permissions**: Global permission read-only (`contents: read`). Write permission scoped strictly to `publish` job when `dry_run == false`. Pushes only to `catalog/<slug>-<tag>`, never to `main`. Dispatches `ci.yml` via `gh workflow run` and prints compare URL.
- **Action Pinning**: All GitHub Actions pinned to 40-character commit SHAs.
- **Validation Logic**: Enforces semver upgrades (rejects downgrades, drafts, prereleases, invalid release formats). Validates schema before and after mutations.

#### Findings
- **Critical**: None
- **Major**: None
- **Minor**: None
- **Optional**:
  - `tools/scripts/update_catalog.py:1`: When run standalone outside editable/venv install, script expects `PYTHONPATH=tools/src`. Adding a sys.path fallback or documenting local invocation improves developer UX.

## Hub pull request 5, runbook, round 1

### Review — PR #5 (P5-05 operations runbook)

**HEAD:** `cffbdce7befb81788bb4c52380a5aa6a143d6933`
**Verdict: CHANGES_REQUESTED**

#### Commands and results
- `make check` — PASS: 167 tests, 5 checks.
- `make full` — PASS: 167 tests, 6 checks.
- `handbook-toolkit --help` — no `artifacts` or `book` subcommand; both invocations exit 2.
- Hub SHAs/subjects match; `toolkit-v0.5.0` is `4e006be`; `988773c`, `62e37ab`, `5f96202` report `0.4.0`.
- `gh`: only sample `v0.2.1` is published at `0549762`; tags `v0.1.0`–`v0.2.0` remain.
- Schema allows `status: archived`; six release assets are declared.

#### Findings

##### Critical
None.

##### Major
1. **Non-existent CLI commands.** `docs/operations-runbook.md:289,363` use `handbook-toolkit artifacts verify`; `sdd/changes/0012-operations-runbook/rehearsal.md:177` uses `handbook-toolkit book build .`. Only `build-book` exists; both fail with exit 2. Use `build-book` and the `verify_publication` API, or add the CLI.
2. **Second build fails.** `operations-runbook.md:113-115,128-129` and `rehearsal.md:227` run `make full` then `make build`. `template/book/Makefile` makes `full` depend on `build`, and `build.py:478-482` refuses an existing output; default `../dist` already exists.
3. **`archived` is not delisting.** `operations-runbook.md:257-259,269-270` treats `status: archived` as portal removal. `portal.py:63-67` still renders archived cards with reading/release/manifest links, which 404 after asset deletion. Immediate withdrawal must delete the entry, or keep assets live.

##### Minor
4. `operations-runbook.md:274` omits `book-source.zip` from the deletion list; six assets are required.
5. `rehearsal.md:165` downloads `handbook-authoring-and-publishing.pdf`; the release asset is `book.pdf`.
6. `operations-runbook.md:331,356` impose 1-hour/30-minute limits without basis or a policy label.
7. `operations-runbook.md:39` says `make check` resolves doc links; only `make full` does.

##### Optional
8. `operations-runbook.md:21` says a reviewer never merges "their own review"; `AGENTS.md` says an implementer never reviews or merges "their own work". `3.2` Case 1 lacks an explicit Owner decision step.

Coverage is complete; REAL, DRY RUN and TABLETOP labels are accurate.

## Hub pull request 5, runbook, round 2

### Re-review — PR #5 (P5-05 operations runbook), round 2

**HEAD:** `ab0f42f07f634030b5a986ac576672c45016b2cb`
**Verdict: CHANGES_REQUESTED**

#### Commands and results
- `make check` — PASS: 167 tests, 5 checks.
- `make full` — PASS: 167 tests, 6 checks; documentation links OK.
- `verify_publication` one-liner against a clean six-file directory — PASS, exit 0; missing directory exits 1.
- `handbook-toolkit build-book --help` — `--repo`, `--commit`, `--output`, `--mode chapter` all valid.
- `git diff cffbdce..HEAD` — only the runbook and rehearsal changed.

#### Round-1 findings
Fixed: non-existent `artifacts`/`book` commands; double-build sequence; `archived` treated as delisting; missing source asset; wrong PDF asset name; unlabelled time limits; `make check` doc-link claim; reviewer wording and missing Owner decision step.

#### Findings

##### Critical
None.

##### Major
1. **`make full` is still claimed to build artifacts for every book.** `docs/operations-runbook.md:112-117,129-130` and `sdd/changes/0012-operations-runbook/rehearsal.md:203` say `make full` executes the local build. That is true only for `template/book/Makefile`; the sample book Makefile says “No artifact build is run” (`/home/ubuntu/github/handbook-sample-01/Makefile:20`). Step 6 therefore performs no artifact build for the only real book, and step 9's review would inspect nothing. Name the book-specific build (sample publication workflow; template `make full`/`make build`) instead of generalizing.

##### Minor
2. `docs/operations-runbook.md:117` assumes the template's default `../dist`; a book with a custom `OUTPUT` would delete the wrong directory. Say “remove the configured output directory”.

#### Could not verify
Live sample-book build execution was not run (review-only, no network); arguments and the verifier were checked directly.

## Hub pull request 5, runbook, round 3

### Re-review — PR #5 (P5-05 operations runbook), round 3

**HEAD:** `99f173c335fe3e899ba7a448dec1618d87288d98`
**Verdict: APPROVE**

#### Commands and results
- `make check` — PASS: 167 tests, 5 checks.
- `make full` — PASS: 167 tests, 6 checks; documentation links OK.
- `git diff ab0f42f..HEAD` — only the runbook note, reviewer step and rehearsal line changed.
- Sample book read-only check: `Makefile:20` confirms no artifact build in `full`; `release.yml` runs `build-book`.

#### Findings
No Critical, Major or Minor findings.

Both round-2 findings are fixed: the runbook now limits the `make full` build claim to books whose Makefile builds and sends `handbook-sample-01` to `build-book`; the stale `../dist` instruction now says the configured output directory. No new defect introduced.

## Hub pull request 6, adapters

### Review Report: PR #6 (Agent Adapters P5-01 & P5-02)

- **HEAD SHA**: `ecb38bf9ab21e14a6876a76c541ed90472e03b9d`
- **Verdict**: **APPROVE**

#### Commands Run & Results
- `git diff origin/main..HEAD --stat`: 4 files changed, 218 insertions (`.github/copilot-instructions.md`, `CLAUDE.md`, `docs/adapter-contract.md`, `tools/tests/test_adapters.py`).
- `make check`: 178 tests passed in 52.2s; fast verification clean (5 checks, 0 problems).
- `make full`: 178 tests passed in 57.9s; full repository verification clean (6 checks, 0 problems; documentation links OK).
- Mutation test: Temporarily appended normative line `"You must follow this rule."` to `CLAUDE.md`; `python3 -m unittest tools/tests/test_adapters.py` failed immediately with `AssertionError: ['CLAUDE.md: normative or status content at line 4: You must follow this rule.']`. Restored with `git checkout CLAUDE.md`; working tree clean.

#### Conformance Analysis
- **Projections without new rules**: `CLAUDE.md` and `.github/copilot-instructions.md` are minimal (3 lines each) and delegate strictly to `AGENTS.md`.
- **Load mechanism**: `CLAUDE.md` uses `@AGENTS.md` native inclusion; Copilot instructions link to `AGENTS.md`.
- **Decoupling**: Adapters are completely decoupled from repository build and toolkit modules; removing an adapter and its registration leaves the platform fully operational.
- **Drift enforcement**: `test_adapters.py` deterministically verifies reference to `AGENTS.md`, length limits (≤12 lines), allowed `make` targets, and absence of normative/status content.

#### Findings
- **Critical**: None
- **Major**: None
- **Minor**: None
- **Optional**: None

## Hub pull request 3, clean-clone

### Review Report: PR #3 (Clean-Clone Matrix P5-04)

- **HEAD SHA**: `3d92335b47b54b4b6872f71aff1b375a5a4ff4ff`
- **Verdict**: **APPROVE**

#### Commands Run & Results
- `git diff 7c09769..HEAD --stat`: 2 files changed, 249 insertions (`.github/workflows/clean-clone.yml`, `docs/clean-clone.md`).
- `make check`: 167 tests passed in 44.1s; fast verification clean (5 checks, 0 problems).
- `make full`: 167 tests passed in 42.9s; full repository verification clean (6 checks, 0 problems; documentation links OK).
- Cross-verified workflow and `docs/clean-clone.md` against `cc-evidence.txt`: Action run `42535908581`, tested commit `b030e21`, sample book commit `4e17627`, test tallies (hub 167, sample book 13), 0 skips, and Poppler package/tooling versions align exactly.

#### Conformance & Robustness Analysis
- **Defect Prevention**: Workflow defaults to `shell: bash` (`-eo pipefail`), preventing pipes from masking failures. Hub clone is deleted via `rm -rf` before book steps; book assertions verify toolkit loads strictly from `BOOK_VENV` `site-packages` with empty `PYTHONPATH`.
- **Security & Permissions**: Permissions scoped to read-only (`contents: read`). External actions are pinned to 40-character SHAs (`actions/setup-python`, `quarto-dev/quarto-actions/setup`). No unvalidated inputs or injection risks.
- **Matrix Acceptance**: Multi-OS matrix (`ubuntu-24.04`, `macos-15`) with `fail-fast: false` satisfies acceptance (Linux plus one additional environment).

#### Findings
- **Critical**: None
- **Major**: None
- **Minor**: None
- **Optional**: None

## Sample pull request 3, round 1

HEAD: `cfe1ac43461e92eb16b4ffcbb7806902cafb8ae6`

Commands and results:
- `git rev-parse HEAD`, `git diff origin/main -- Makefile`, `nl -ba Makefile`, `cat AGENTS.md`: reviewed the exact one-line change.
- `make check` and `make full`: each passed 13 local tests and repository checks, then failed because `handbook-toolkit` was unavailable (Error 127). No sandbox rejection.
- `make -n full` plus `python3 -B -` `/bin/sh` harnesses: dollar expansion correct; TMPDIR containing spaces and a trailing slash succeeded and cleaned up. BSD/macOS was not executed.
- `git status --short`: clean after testing; no tracked edits.

Findings:
- **Major — Makefile:25:** `mv` failure is swallowed by the `&&` list despite `set -e`. Injecting `mv() { return 73; }` continued with the unsuffixed path and returned success in the isolated setup harness. Make the rename failure explicitly fatal.
- **Major — Makefile:25–26:** cleanup is registered after creation and rename. Injected exit before the trap left the original file; SIGTERM immediately after successful rename left the `.yaml` file. Arm cleanup earlier, cover both names and handle termination signals.

Verdict: **CHANGES_REQUESTED**.

## Sample pull request 3, round 2

HEAD: `e7fa80e6538b8b0b083946959630c8bdf1fdc8e5`

Commands and results:
- `git rev-parse HEAD`, `git diff origin/main -- Makefile`, `nl -ba Makefile`, and `cat ../out/revs-round1.md`: verified the exact change and prior findings.
- `make check` and `make full`: each passed 13 local tests and repository checks; both stopped at missing `handbook-toolkit` (Error 127), not a sandbox restriction.
- `make -n full` and `python3 -B -` `/bin/sh` harnesses: correct dollar expansion; spaces/trailing-slash TMPDIR succeeded without leftovers. Injected mktemp failure exited 73; actual profile-write failure exited 2; simulated validation failure exited 1. All cleaned up. HUP/INT/TERM after setup exited 129/130/143 without leftovers.
- `git status --short`: clean. Native BSD/macOS was not executed.

Findings:
- Prior swallowed-rename failure: fixed by eliminating `mv` and using a fixed filename inside a private temporary directory.
- Prior rename-to-trap leak: eliminated; subsequent failures and handled signals clean the directory.
- **Optional — Makefile:25–26:** a small creation-to-trap signal window remains; cleanup is not an absolute guarantee for interruption before trap installation.

No Critical, Major or Minor findings.

Verdict: **APPROVE**.
