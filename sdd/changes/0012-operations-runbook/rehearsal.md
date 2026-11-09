# Rehearsal record — Operations runbook (P5-05)

This document records the rehearsal evidence for work package P5-05, including real past platform
events, dry runs executed in isolated environments, and tabletop walk-throughs.

Reference documentation:
- Operations runbook: [`docs/operations-runbook.md`](../../../docs/operations-runbook.md)
- Governance and roles: [`AGENTS.md`](../../../AGENTS.md)
- Decision log: [`docs/decisions.md`](../../../docs/decisions.md)

---

## 1. REAL events that already happened

The following events were executed on the platform and verified against the Git commit history of
the hub and book repositories.

### Toolkit 0.4.0 to 0.5.0 upgrade and remediation

- **Context and motivation**:
  Under `HUB-DEC-020`, the Owner instructed replacing bundled render resources that had open
  licensing questions. Cascadia Code was replaced with JetBrains Mono under OFL, Liberation Sans was
  bundled, and `reference.docx` was regenerated from clean code without Pandoc template parts.
- **Verified commits in hub Git history**:
  - `988773c`, `62e37ab`, `5f96202`: Post-0.4.0 commits that modified rendering behavior while the
    code still reported version `0.4.0`.
  - `caaa363`: `chore(toolkit): release 0.5.0 for post-0.4.0 rendering changes`.
  - `f9406db`: `fix(render): replace render resources with unresolved license questions`.
  - `bad4781`: `fix(notice): credit Quarto in the packaged typst-show partial`.
  - `5455d6e`: `docs(notice): state exactly how the DOCX reference relates to Pandoc`.
  - `50a3113`, `5a5b6a9`, `d58db4d`, `23fc088`, `a90c9e3`: Successive template pins tracking the
    remediation commits.
  - `4e006be` (tagged `toolkit-v0.5.0`): Merge of pull request #1 (`merge: post-Phase-4 remediation
    and toolkit 0.5.0 (#1)`).
- **Sample book progression**:
  - Sample book releases `v0.1.1` (`55902a7`), `v0.1.2` (`95ce535`), and `v0.2.0` (`1635e69`) had
    been published against pre-remediation commits.
  - Template `1.0.0` was pinned to toolkit `0.5.0` at commit `5455d6e` (later ratified at `a90c9e3`).
  - Evidence recorded in [`sdd/changes/0010-post-phase4-remediation/evidence.md`](../0010-post-phase4-remediation/evidence.md).

---

### Withdrawal of releases `v0.1.0` to `v0.2.0` on 2026-11-08

- **Context and decision**:
  Executed under `HUB-DEC-021`. The Owner directed updating the catalog to the new release and
  withdrawing the old ones by deleting their releases while keeping their tags, and delegated the
  merges of that sequence once.
- **Verified commits and sequence**:
  1. Hub PR #1 merged at `4e006be` (tag `toolkit-v0.5.0`).
  2. Sample book PR #2 merged, and publication release workflow built and published sample release
     `v0.2.1` from book commit `0549762699a95764467ee75cba28d8a791480394`.
  3. Hub PR #2 merged at `7c09769` (`merge: list release v0.2.1 in the catalog (#2)`):
     - `88a930d`: Updated `catalog/catalog.json` to point to `v0.2.1`.
     - `e0917f6`: Recorded successful `catalog_verification` evidence.
     - `552c952`: Documented `HUB-DEC-021` in `docs/decisions.md`.
  4. Portal redeployed from the updated catalog pointing to `v0.2.1`.
  5. The release pages and binary assets of `v0.1.0`, `v0.1.1`, `v0.1.2`, and `v0.2.0` were deleted
     from GitHub Releases, while their Git tags were preserved in the repository.
  - Evidence recorded in [`sdd/changes/0011-release-v0.2.1/evidence.md`](../0011-release-v0.2.1/evidence.md).

---

## 2. DRY RUNS executed in temporary clones

### Dry run: Reverting catalog merge commit `7c09769`

This rehearsal tests what happens when a maintainer attempts to roll back a catalog update to a
previously withdrawn release (`v0.2.0`).

- **Execution details**:
  Executed by the coordinator on 2026-11-08 in an isolated temporary clone at `7c09769`. The
  implementer received these results and did not repeat the run.
- **Commands executed**:
  ```bash
  # 1. Create isolated clone
  git clone . /tmp/dryrun-rollback
  cd /tmp/dryrun-rollback

  # 2. Revert the catalog update merge commit (parent 1 is main)
  git revert -m 1 7c09769 --no-edit

  # 3. Run full offline checks
  PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full

  # 4. Run online release gate
  PYTHONPATH=tools/src python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
  ```

- **Actual results**:
  1. `git revert -m 1 7c09769` succeeded cleanly:
     - Created commit reverting PR #2.
     - Restored `catalog/catalog.json` to point to `v0.2.0`.
     - Deleted `sdd/changes/0011-release-v0.2.1/evidence.md`.
  2. Offline verification (`PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full` / `make full`) **passed**:
     ```text
     repository files: OK
     packaged schemas: OK
     catalog/catalog.json: OK
     profiles/standard/profile.yaml: OK
     template/book/book.yaml: OK
     documentation links: OK
     VERIFY (full): 6 check(s), 0 problem(s)
     ```
  3. Online release verification (`PYTHONPATH=tools/src python3 -m handbook_toolkit.catalog_verification catalog/catalog.json`) **failed** (exit code 1):
     ```text
     handbook-authoring-and-publishing: remote asset returned HTTP 404
     release verification: FAILED
     ```

- **Operational findings and implications**:
  1. **Offline checks do not catch a rollback to a withdrawn release**: Because `catalog.json` was
     syntactically valid against `catalog.schema.json`, `make full` gave a false sense of security (6 checks, 0 problems).
  2. **Online verification caught the missing release**: Because the release page and assets for `v0.2.0`
     were withdrawn and deleted under `HUB-DEC-021`, the remote endpoint returned HTTP 404.
  3. **Roll forward is required**: Reverting the catalog in Git history to a withdrawn version is impossible
     to deploy. Once earlier releases are withdrawn, rolling forward to a new version (e.g., `v0.2.2`) is
     the only viable operational procedure.

---

## 3. TABLETOP walk-throughs

Structured walk-throughs of operational procedures where live execution would cause production
disruption or requires external defect triggers.

### Tabletop 1: Incident response — Broken reading site

- **Trigger scenario**:
  A user reports that navigating to `https://cesarcastrocuba.github.io/handbook-sample-01/` produces an
  HTTP 404 error.
- **Walk-through procedure**:
  1. *Diagnosis [Implementer]*:
     - Run `curl -sI https://cesarcastrocuba.github.io/handbook-sample-01/`. Confirm HTTP 404.
     - Run `curl -sI https://api.github.com/repos/cesarcastrocuba/handbook-sample-01/pages`. Inspect
       deployment status.
  2. *Triage [Implementer]*:
     - Inspect GitHub Actions workflow runs in the book repository for the Pages deployment job.
     - Case A (Transient Pages pipeline failure): Re-trigger the deployment action from tag `v0.2.1`.
     - Case B (Persistent failure or corruption): Notify Owner that reading site is down.
  3. *Mitigation [Implementer & Owner]*:
     - If the site cannot be restored within 1 hour, execute Order A withdrawal in the hub:
       - Implementer branches `fix/delist-broken-reading-site`.
       - Updates `catalog/catalog.json` to remove the book entry or set `"status": "archived"`.
       - Reviewer verifies `make full`. Owner merges PR.
       - Portal redeploys, preventing reader traffic from reaching dead reading links.
  4. *Recovery [Implementer, Reviewer, Owner]*:
     - Repair the book repository Pages configuration or build artifact.
     - Verify with `curl -sI` that the site returns HTTP 200 and matches `html.zip`.
     - Submit hub PR restoring the active catalog entry, verified by `catalog_verification`.
     - Owner merges PR.

---

### Tabletop 2: Incident response — Bad checksum or corrupted artifact

- **Trigger scenario**:
  An external auditor reports that the published PDF for `handbook-authoring-and-publishing` does not
  match the SHA-256 hash listed in `SHA256SUMS.txt`.
- **Walk-through procedure**:
  1. *Verification [Implementer]*:
     - Download assets into a fresh temporary directory:
       ```bash
       curl -sLO https://github.com/cesarcastrocuba/handbook-sample-01/releases/download/v0.2.1/SHA256SUMS.txt
       curl -sLO https://github.com/cesarcastrocuba/handbook-sample-01/releases/download/v0.2.1/handbook-authoring-and-publishing.pdf
       sha256sum -c SHA256SUMS.txt
       ```
     - Confirm failure.
  2. *Containment [Owner & Implementer]*:
     - Enforce immutability: **Do not re-upload or edit assets in place under `v0.2.1`**.
     - Owner directs immediate delisting under Order A to protect readers.
     - Implementer opens hub PR removing the entry from `catalog/catalog.json`.
     - Reviewer checks and Owner merges PR; portal rebuilds.
  3. *Remediation [Implementer]*:
     - In the book repository, check out commit `0549762699a95764467ee75cba28d8a791480394`.
     - Identify root cause (e.g., incomplete upload transfer during release action).
     - Run `handbook-toolkit book build .` in clean environment.
     - Verify all 6 assets with `handbook-toolkit artifacts verify dist/`.
     - Tag a new patch release: `v0.2.2`.
  4. *Restoration [Implementer, Reviewer, Owner]*:
     - Trigger publication workflow on `main` for `v0.2.2`.
     - Submit hub PR updating `catalog/catalog.json` to `v0.2.2`.
     - Reviewer runs `catalog_verification` (online pass).
     - Owner merges PR.
     - Delete defective release `v0.2.1` assets on GitHub; retain tag `v0.2.1`.

---

### Tabletop 3: Incident response — Third-party licensing report

- **Trigger scenario**:
  A notice is received claiming an image embedded in Chapter 2 of the handbook lacks proper attribution
  under CC BY-SA 4.0.
- **Walk-through procedure**:
  1. *Assessment [Owner]*:
     - Owner reviews the claim and confirms attribution was inadvertently omitted.
  2. *Strategy selection [Owner]*:
     - Since attribution can be corrected in `NOTICE.md` and the chapter source within minutes, Owner
       authorizes **Order B** (`HUB-DEC-021` pattern) rather than complete delisting.
  3. *Authoring clean release [Implementer]*:
     - In book repository, branch `fix/licensing-attribution`.
     - Add required attribution to `NOTICE.md` and chapter figure metadata.
     - Run `make full` and `make build`.
     - Merge to `main` via reviewed PR.
     - Publish release `v0.2.2`.
  4. *Cutover [Implementer & Reviewer]*:
     - In hub repository, submit PR updating catalog to `v0.2.2`.
     - Reviewer verifies online gate (`handbook-toolkit.catalog_verification`).
     - Owner merges PR; portal updates to `v0.2.2`.
  5. *Withdrawal [Owner]*:
     - Delete release `v0.2.1` page and download assets on GitHub.
     - Retain Git tag `v0.2.1` in the book repository for historical auditability.

---

### Tabletop 4: Book upgrade to a future major profile release

- **Trigger scenario**:
  Standard profile `2.0.0` is approved by the Owner, introducing mandatory chapter summaries.
- **Walk-through procedure**:
  1. *Preparation [Implementer]*:
     - Implementer creates branch `chore/upgrade-profile-2.0.0` in book repository.
     - Updates `profile.version` in `book.yaml` to `2.0.0`.
     - Runs `make check`. Validator flags missing summary units across chapters.
     - Authors required chapter summaries to conform to profile `2.0.0`.
  2. *Build & Inspection [Implementer & Reviewer]*:
     - Runs `make full` and `make build`.
     - Inspects PDF layout and DOCX output for styling consistency.
     - Submits PR with rendered evidence.
     - Reviewer reproduces full build in isolated clean clone and confirms profile compliance.
  3. *Approval [Owner]*:
     - Owner explicitly approves the editorial changes and merges PR into `main`.
     - Publication workflow cuts release `v1.0.0` of the book.
