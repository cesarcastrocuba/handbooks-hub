# Operations runbook

This runbook defines the standard operating procedures for maintainers, contributors and automated
agents operating on the handbooks platform.

All procedures follow the role-based governance defined in [`AGENTS.md`](../AGENTS.md) and
[`decisions.md`](decisions.md).

## 1. Principles and governance

### Roles and responsibilities

Every procedure defines who acts and who decides using three distinct roles:

- **Owner**: Approves editorial gates, licenses, profile changes, releases, and operational
  exceptions. Authorizes pull requests and merges to `main`.
- **Implementer**: Prepares a scoped change in a dedicated branch, runs local verification checks,
  and records command evidence. An implementer must never review or merge their own work.
- **Reviewer**: A different person or agent. Reviews the exact commit or pull-request HEAD,
  re-runs verification checks independently, validates evidence, and posts structured review findings.
  A reviewer may propose a fix but must not silently rewrite the change under review, and never
  reviews or merges their own work. Merges require explicit Owner approval.

### Protected `main` branch

Under `HUB-DEC-018`, the `main` branch in both the hub and book repositories is protected:

- Direct pushes and deletions of `main` are blocked.
- All changes must arrive via a short-lived branch and pull request.
- Changes require passing automated continuous integration (CI) checks.
- Branches must be up to date with main before merge (HUB-DEC-026).
- Review conversations must be resolved before merge.
- Merges to `main` require explicit Owner authorization.

### Verification gates and boundaries

Operations distinguish between two verification gates:

1. **Offline verification (`make check`, `make full`)**:
   - `make check` executes local unit tests, JSON schema validation, profile checks, and descriptor checks.
   - `make full` runs all fast checks plus full repository validation; only `make full` resolves and verifies documentation links and template completeness.
   - Requires no network access.
   - **Limitation**: Offline checks validate only syntax, local files, and schema structures. They
     do **not** verify whether external URLs, release tags, download assets, or live Pages sites
     actually exist or match cryptographic hashes.
2. **Online release verification (`handbook-toolkit.catalog_verification`)**:
   - Executed before portal deployment:
     ```bash
     PYTHONPATH=tools/src python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
     ```
   - Connects over HTTPS (port 443) using pinned public IP addresses.
   - Verifies GitHub release status, tag-to-commit resolution, manifest presence, payload integrity,
     every release asset declared by the manifest, format markers, and byte-for-byte parity of live
     reading sites against the released HTML archive. The asset count follows the manifest schema:
     six assets for `1.0` (published before toolkit `0.6.0`) and seven for `1.1`, which adds
     `book.md`.

### Edition preview and Owner acceptance before tagging

Neither gate above shows what a reader will see. A release is immutable, so the editions are
inspected before anything is tagged (`HUB-DEC-036`).

Every pull request runs the `edition-preview` job of `ci.yml`. It builds the template book and the
sample book with the pull request's toolkit, as a `--preview` build that cannot pass for a release,
and uploads one artifact per book, `edition-preview-template` and `edition-preview-sample`, kept for
14 days:

| Path in the artifact | What it is |
| --- | --- |
| `PREVIEW.md` | Source commit, preview version, file list and any step that was not run |
| `edition/` | The seven files `build-book` produces, including `book.pdf`, `book.docx` and `book-html.zip` |
| `libreoffice/book-docx-as-libreoffice.pdf` | The DOCX as LibreOffice renders it: what a viewer other than Word shows |
| `screenshots/` | The reading site's top-level pages and its largest page, at 1440 px and 390 px, light and dark |

The job is not a required check. A failed sample preview means the pull request's toolkit cannot
build the published sample as it is; say so in the pull request, with the reason.

The same preview runs locally:

```bash
python3 -m pip install -r requirements-dev.txt -r tools/scripts/requirements-edition-preview.txt
python3 -m playwright install chromium
python3 tools/scripts/edition_preview.py --template --output /tmp/edition-preview
python3 tools/scripts/edition_preview.py --repo PATH_TO_BOOK --output /tmp/edition-preview-book
```

Without LibreOffice or Playwright the script still builds the editions and records the skipped step
in `PREVIEW.md`; `--require-tools` turns a missing tool into a failure, as in CI.

**Owner acceptance checklist.** Before tagging a toolkit or template release, or dispatching a book
release, the Owner downloads the artifact of the pull request that is about to merge
(`gh run download RUN_ID -n edition-preview-sample`) and checks:

1. **Word.** Open `edition/book.docx` in desktop Word and accept the prompt to update fields.
   - Callout titles are bold and carry their role colour.
   - "Contents" lists the headings with page numbers.
   - Each list (tables, figures) shows its entries with page numbers, and an entry jumps to its
     target.
   - Captioned tables show their banding; tables inside callouts do not.
   - Text uses the brand fonts, or the declared fallback when they are not installed.
2. **Other viewers.** `libreoffice/book-docx-as-libreoffice.pdf` shows "Contents" and the lists with
   entries, not empty headings.
3. **PDF.** `edition/book.pdf` has the cover, contents, lists and running headers in place.
4. **Reading site.** The screenshots are legible in light and dark at both widths: no overflow, no
   doubled rules, no unreadable contrast.

A defect found here is fixed in the same pull request or the next one. Visual corrections are
grouped into one release per round instead of one release per correction.

---

## 2. Procedure: Toolkit and profile upgrade in a book

Books pin exact versions of `handbook-toolkit` and editorial profiles. Upgrades are deliberate,
reviewed changes; nothing upgrades automatically.

### Order of operations

```text
[Implementer] Review changes & create branch
      │
[Implementer] Bump pins in book.yaml & requirements.txt
      │
[Implementer] Reinstall in .venv & run checks (check, full, build)
      │
[Implementer] Inspect rendered artifacts & open PR
      │
[Reviewer]    Independently reproduce checks & review diff
      │
[Owner]       Approve & merge PR to main
```

### Step-by-step instructions

1. **Review release notes [Implementer]**:
   Read the hub `CHANGELOG.md` and [`docs/book-upgrade.md`](book-upgrade.md) for the target toolkit
   version and all intermediate versions. Identify any changes in build commands, manifest fields,
   or packaged render assets.

2. **Create a working branch [Implementer]**:
   In the book repository clone:
   ```bash
   git switch -c chore/upgrade-toolkit-<target-version>
   ```

3. **Update version pins [Implementer]**:
   Edit `book.yaml` to update the toolkit version and, if approved, the profile version:
   ```bash
   sed -i 's/^toolkit: .*/toolkit: "<target-version>"/' book.yaml
   # Only if adopting a new approved profile version:
   sed -i 's/^  version: .*/  version: "<profile-version>"/' book.yaml
   ```

4. **Update dependency commit [Implementer]**:
   Update `requirements.txt` to reference the exact reviewed hub commit SHA for the target toolkit:
   ```bash
   sed -i 's|github.com/.*/handbooks-hub.git@.*|github.com/cesarcastrocuba/handbooks-hub.git@<reviewed-commit-sha>#subdirectory=tools|' requirements.txt
   ```

5. **Reinstall toolkit [Implementer]**:
   ```bash
   source .venv/bin/activate
   python3 -m pip install --upgrade -r requirements.txt
   handbook-toolkit version
   ```

6. **Execute local verification and artifact build [Implementer]**:
   ```bash
   make check
   make full
   ```
   *(Note: `make full` builds artifacts only in books whose Makefile runs the build, such as those
   using `template/book/Makefile`, which writes to `$(OUTPUT)`. `build-book` refuses to overwrite
   existing output, so remove the configured output directory before building again. A book whose
   `make full` runs no build, such as `handbook-sample-01`, must run `handbook-toolkit build-book`
   directly before step 7; its publication workflow does the same.)*

7. **Inspect rendered outputs [Implementer]**:
   Examine generated HTML, PDF, and DOCX files in the staging directory. Verify font rendering
   (Handbook Sans and Handbook Serif in the HTML and PDF, Source Sans 3 and Source Serif 4 in Word,
   JetBrains Mono for code in every edition), heading layout, table column widths, and page
   breaks.

8. **Submit pull request [Implementer]**:
   Push the branch and open a pull request against `main`. Record the exact commit SHA, updated
   pins, and verification results in the PR description.

9. **Independent review [Reviewer]**:
   Check out the pull-request branch in an isolated clone. Run `make check`, `make full` and
   the book's artifact build as described in step 6. Confirm artifacts meet profile standards. Approve the PR with
   recorded findings.

10. **Authorize and merge [Owner]**:
    Owner verifies that any profile change is intentional, confirms green CI, and merges the pull
    request into `main`.

---

## 3. Procedure: Rollback of a bad hub change or catalog entry

### 3.1 Rolling back a hub code or documentation change

1. **Authorize rollback [Owner]**:
   The Owner authorizes reverting a commit on `main`.

2. **Create revert branch [Implementer]**:
   ```bash
   git switch -c fix/revert-<topic>
   ```

3. **Revert the commit [Implementer]**:
   For a standard commit:
   ```bash
   git revert <commit-sha> --no-edit
   ```
   For a merge commit (keeping parent 1 as `main`):
   ```bash
   git revert -m 1 <merge-commit-sha> --no-edit
   ```

4. **Run local checks [Implementer]**:
   ```bash
   make check
   make full
   ```

5. **Open PR and review [Implementer & Reviewer]**:
   Implementer submits PR. Reviewer independently runs `make check` and `make full`, then approves.

6. **Merge [Owner]**:
   Owner merges the PR to `main`.

---

### 3.2 Rolling back a catalog entry

Reverting a catalog entry to a previous release requires extreme caution due to remote asset state.

> [!WARNING]
> **Rollback vs. Withdrawn Releases**:
> Offline checks (`make check`, `make full`) **do not catch a rollback to a withdrawn release**.
> Offline verification checks only the JSON structure and schema conformance of `catalog/catalog.json`.
> If a catalog entry is reverted to point to a release whose assets or release pages have been deleted
> (such as `v0.1.0` through `v0.2.0` under `HUB-DEC-021`), offline checks will pass (6 checks, 0 problems).
> However, online verification will fail immediately:
> ```text
> handbook-authoring-and-publishing: remote asset returned HTTP 404
> release verification: FAILED
> ```
> Therefore:
> - Reverting the catalog to a previous release is permitted **only if the previous release assets and
>   reading site remain published and live**.
> - If the previous release was withdrawn or deleted, **rolling back in Git history is blocked**.
>   **Rolling forward to a new version (e.g., a patch release `vX.Y.Z`) is the ONLY option.**

#### Case 1: Prior release assets remain published and live

1. **Authorize catalog rollback [Owner]**:
   Owner confirms that the prior release assets, manifests, and reading site remain published and live,
   and explicitly authorizes reverting the catalog entry to the prior release.

2. **Create branch and revert commit [Implementer]**:
   ```bash
   git switch -c fix/revert-catalog-<book-slug>
   git revert <catalog-update-commit> --no-edit
   ```

3. **Execute offline and online verification [Implementer]**:
   ```bash
   make check
   make full
   PYTHONPATH=tools/src python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
   ```

4. **Review and merge [Reviewer & Owner]**:
   Reviewer independently verifies the online release gate pass. Owner merges the PR to `main`.
   The catalog push triggers `portal-pages`, which rebuilds and deploys automatically (`HUB-DEC-024`).

#### Case 2: Prior release was withdrawn (Roll forward required)

1. **Produce replacement release [Implementer]**:
   In the book repository, resolve the defect on a working branch, run `make full`, and obtain
   approval for a new patch version tag (e.g., `v0.2.2`).
2. **Publish new release [Owner / CI]**:
   Trigger the publication workflow on the book's `main` branch to generate the 6 verified assets
   and deploy the updated reading site.
3. **Update hub catalog [Implementer]**:
   In the hub repository, submit a PR updating `catalog/catalog.json` directly to the new version tag.
4. **Verify online [Implementer & Reviewer]**:
   Confirm `handbook-toolkit.catalog_verification` succeeds against the new release.
5. **Merge [Owner]**:
   Owner merges the PR to update the portal.

---

## 4. Procedure: Release withdrawal

### Reconciling withdrawal order

Two different orders of withdrawal appear in platform governance:

- **Publication Contract order** ([`docs/publication-contract.md`](publication-contract.md)):
  *"If a published artifact is wrong, withdraw the catalog entry first, then publish a corrected version."*
- **Remediation order** under `HUB-DEC-021` ([`docs/decisions.md`](decisions.md)):
  *"publish the sample book at v0.2.1 with toolkit 0.5.0, list it in the catalog and withdraw v0.1.0 to v0.2.0 by deleting their release pages and assets while keeping their tags."*

> Since `HUB-DEC-031`, replacing a release does not withdraw the previous one: published releases stay
> published as previous editions, and both orders below apply only to a withdrawal with a recorded
> reason and an explicit Owner decision.

These two orders apply in distinct operational scenarios:

| Order | Sequence | When it applies | Rationale |
| --- | --- | --- | --- |
| **Order A** (Contract default) | 1. Withdraw catalog entry.<br>2. Delete release assets.<br>3. Publish fix later. | Emergency defect, active copyright/licensing infringement, or security vulnerability where **no clean replacement release exists yet**; or permanent book delisting. | Immediately cuts off reader traffic from the portal to defective or infringing assets while remediation is developed. |
| **Order B** (`HUB-DEC-021` order) | 1. Publish replacement release.<br>2. Update catalog to new release.<br>3. Delete obsolete release assets. | Planned remediation or upgrade where **a clean, verified replacement release is already built and ready**. | Ensures zero portal downtime and ensures the catalog never points to a 404 or missing release during the cutover. |

---

### Step-by-step instructions: Order A (Withdraw catalog entry first)

Use when an active release must be pulled immediately without a ready replacement:

1. **Authorize immediate withdrawal [Owner]**:
   Owner decides that a published release must be delisted immediately.

2. **Remove catalog entry [Implementer]**:
   In a new branch in the hub (`fix/withdraw-<book-slug>`):
   - Delete the book entry entirely from `catalog/catalog.json`.
     *(Note: Setting `"status": "archived"` is NOT sufficient for immediate withdrawal because `portal.py` still renders archived cards with active reading, download, and manifest links. Setting `"status": "archived"` is acceptable only if the published assets and reading site stay live.)*
   - Record the withdrawal reason and decision ID in the active change record.

3. **Verify locally [Implementer]**:
   ```bash
   make check
   make full
   ```

4. **Review and merge [Reviewer & Owner]**:
   Reviewer confirms schema compliance. Owner merges the PR to `main`. The catalog push triggers
   `portal-pages`, which rebuilds and publishes the portal without the delisted release.

5. **Delete release assets on Git host [Implementer / Owner]**:
   In the book repository on the Git hosting platform:
   - Delete the release page and all required assets: `book-html.zip`, `book.pdf`, `book.docx`, `book-source.zip`, `publication-manifest.json` and `SHA256SUMS.txt`, plus `book.md` when the manifest schema is `1.1`.
   - **CRITICAL**: **Preserve the Git tag** (e.g., `v1.0.0`). The tag must remain in the repository's
     Git history for cryptographic auditability and commit provenance.

---

### Step-by-step instructions: Order B (Publish replacement release first — `HUB-DEC-021`)

Use during planned remediation when a verified clean replacement is available:

1. **Authorize remediation sequence [Owner]**:
   Owner approves the remediation plan and the replacement release version.

2. **Publish clean release [Implementer & Owner]**:
   In the book repository, merge fixes to `main`, run the publication build (`handbook-toolkit build-book` or CI publication workflow), verify all 7 assets with `handbook_toolkit.publication.verify_publication` (automatically verified by `build-book`), and publish release `vX.Y.Z` with live Pages deployment.

3. **Update catalog entry [Implementer]**:
   In the hub repository, create branch `feat/catalog-<version>`:
   - Update `catalog/catalog.json` with the new version, tag, URLs, and publication date.
   - Run local checks and online verification:
     ```bash
     make check
     make full
     PYTHONPATH=tools/src python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
     ```

4. **Independent review and merge [Reviewer & Owner]**:
   Reviewer independently verifies `catalog_verification` output. Owner merges PR to `main`.
   The catalog push triggers `portal-pages`, which redeploys and links to the clean release.

5. **Withdraw obsolete releases [Owner / Delegated Agent]**:
   Once the portal is verified live pointing to the new release:
   - Delete the release pages and downloadable asset binaries of the superseded releases (`book-html.zip`, `book.pdf`, `book.docx`, `book-source.zip`, `publication-manifest.json` and `SHA256SUMS.txt`, plus `book.md` for manifest schema `1.1`).
   - Retain all Git tags in the book repository.

---

## 5. Procedure: Incident response

### Incident 5.1: Broken reading site (Pages 404, TLS error, or desynchronized HTML)

- **Detection**: Reader report or automated release verification failure (`remote asset returned HTTP 404`
  or `live reading asset differs from released HTML`).
- **Diagnosis [Implementer]**:
  Execute diagnostic HTTP checks against the configured `reading_url`:
  ```bash
  curl -sI https://<owner>.github.io/<repo>/
  curl -sI https://<owner>.github.io/<repo>/index.html
  ```
- **Triage and Remediation**:
  1. *Transient hosting / Pages pipeline glitch*:
     - **Action [Implementer]**: Re-trigger the reading site deployment workflow from the approved
       release commit.
     - **Verification [Reviewer]**: Re-run `catalog_verification` to ensure live reading assets match
       the released `html.zip` byte-for-byte.
  2. *Persistent outage or corrupted build*:
     - If the site cannot be restored within 1 hour (Owner-accepted runbook policy, HUB-DEC-023):
     - **Action [Implementer & Owner]**: Execute **Order A withdrawal** to remove the book entry from
       `catalog/catalog.json` via PR so portal users do not encounter broken links.
     - Once fixed in the book repository, submit a PR to restore the catalog entry.

---

### Incident 5.2: Bad checksum or corrupted release asset

- **Detection**: Reader report or integrity audit showing `sha256sum -c SHA256SUMS.txt` failure or
  `handbook-toolkit.publication` integrity error.
- **Diagnosis [Implementer]**:
  Download all assets to an isolated temporary directory:
  ```bash
  curl -sLO https://github.com/<owner>/<repo>/releases/download/<tag>/SHA256SUMS.txt
  curl -sLO https://github.com/<owner>/<repo>/releases/download/<tag>/publication-manifest.json
  curl -sLO https://github.com/<owner>/<repo>/releases/download/<tag>/<asset-name>
  sha256sum -c SHA256SUMS.txt
  ```
- **Strict Immutability Rule**:
  Under `HUB-DEC-007` and `docs/publication-contract.md`, release assets are immutable.
  **Never silently replace, re-upload, or overwrite assets under an existing release tag.**
- **Remediation Sequence**:
  1. **Authorize response [Owner]**: Owner decides between immediate delisting (Order A) or fast
     replacement cutover (Order B).
  2. **Delist / withdraw [Implementer]**: If no replacement is ready within 30 minutes (Owner-accepted runbook policy, HUB-DEC-023), withdraw the
     catalog entry via PR (Order A).
  3. **Build clean release [Implementer]**:
     - Check out the approved source commit.
     - Build in a clean virtual environment using pinned tools.
     - Verify generated files using the publication verification entry point:
       ```bash
       python3 -c "from pathlib import Path; from handbook_toolkit.publication import verify_publication; res = verify_publication(Path('<build-dir>')); print(res); exit(0 if res.ok else 1)"
       ```
     - Tag a new patch release (e.g., `vX.Y.(Z+1)`).
  4. **Publish and update catalog [Implementer, Reviewer, Owner]**:
     Publish new release, submit hub PR updating `catalog/catalog.json`, review with
     `catalog_verification`, and merge. Delete bad release assets while retaining Git tag.

---

### Incident 5.3: Licensing report or third-party rights defect

- **Detection**: Notification received regarding an unlicensed asset, missing attribution, or
  restrictive license conflict in bundled fonts, templates, or manuscript content.
- **Immediate assessment [Owner]**:
  Owner reviews the notification against [`docs/decisions.md`](decisions.md) (`HUB-DEC-009`,
  `HUB-DEC-020`) and determines if the claim affects hub toolkit resources or book content.
- **Remediation for book content**:
  1. If clean replacement text/media is ready immediately:
     - Apply **Order B**: Publish replacement release `vX.Y.Z` without the disputed asset, update
       hub catalog, then delete the release assets of the infringing release while retaining Git tags.
  2. If replacement text/media requires substantial authoring:
     - Apply **Order A**: Immediately withdraw the catalog entry via hub PR. Delete release download
       assets from the Git host. Retain Git tags for provenance.
- **Remediation for hub toolkit / render resources** (as performed in `HUB-DEC-020`):
  1. **Replace disputed resources [Implementer]**:
     - On a dedicated branch (`fix/licensing-<component>`), replace the disputed files with verified
       open-source equivalents (e.g., replacing Cascadia Code with JetBrains Mono under OFL).
     - Update `NOTICE.md` and licensing records.
     - Bump the toolkit version in `tools/pyproject.toml` and `handbook_toolkit/__init__.py`.
  2. **Verify and test [Implementer]**:
     ```bash
     make check
     make full
     ```
  3. **Independent review [Reviewer]**:
     Reviewer verifies font/asset licenses and re-runs checks.
  4. **Merge and tag [Owner]**:
     Owner merges PR to `main` and creates a new toolkit release tag (e.g., `toolkit-v0.5.0`).
  5. **Upgrade books [Book Implementers]**:
     Book repositories upgrade their pinned toolkit per Procedure 2.
