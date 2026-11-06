# Decision log

Status terms: **Proposed**, **Approved**, **Deferred**. Only the owner can approve a decision.
Decisions supplied in `IMPLEMENTATION-HANDOFF.md` were recorded as **Proposed** until the Gate 1
review. The owner approved the Phase 1 foundation on 2026-11-06; the statuses below reflect that
approval and the later approval of the standard profile `0.2.0`.

| ID | Status | Decision | Rationale / next step |
| --- | --- | --- | --- |
| HUB-DEC-001 | Approved | Independent book repositories own canonical sources; the hub owns the portal, toolkit, schemas, profiles, template, catalog and shared documentation. | Keeps content ownership close to authors, lets the hub evolve without rewriting books and avoids a monorepo release bottleneck. Approved with the Phase 1 foundation. |
| HUB-DEC-002 | Approved | The hub publishes a versioned `handbook-toolkit`; books install an exact pinned version and never import a parent checkout or copy shared scripts. | One implementation of each validator, reproducible book builds and a clear upgrade path. Reject any copied `scripts/` directory during review. |
| HUB-DEC-003 | Approved | Book repositories hold canonical Quarto sources. Generated HTML, PDF, DOCX, source bundles, manifests and checksums are built from an approved commit, verified, published and never committed as source. | Preserves provenance and prevents hand-edited outputs. Enforced by review and CI. |
| HUB-DEC-004 | Approved | The standard editorial profile is the default for new books and is versioned. Explicit alternative profiles and recorded exceptions are allowed with owner approval. | Captures the existing handbook's reader experience without forcing artificial uniformity. The initial `standard` profile `0.1.0` was proposed; owner approval of `0.2.0` was recorded on 2026-11-06. |
| HUB-DEC-005 | Approved | Cross-references are explicit (`Chapter N`, `N.M`, `Figure N.F`, `Table N.T`). Automatic glossary-term linking is off by default. | The reference handbook found indiscriminate term links noisy and prone to broken targets. Glossary and index links, if any, are deliberate. |
| HUB-DEC-006 | Approved | Figures preserve aspect ratio, are not upscaled and keep at least 10 pt effective text in print; captioned tables use adaptive widths and a caption below the table. | Readability at text-column width; validated in Phase 2. These rules come from the reference handbook's `DEC-011` and RC5 corrections. |
| HUB-DEC-007 | Approved | Publication builds once from an approved commit, verifies the artifacts and publishes those exact bytes. The book's Pages site serves reading; its Releases hold downloads. | Guarantees that the reviewed artifact is the published artifact. The manifest and checksums make the claim verifiable. |
| HUB-DEC-008 | Approved | The hub catalog lists approved releases only and references immutable release assets; it never links to a branch, a working tree or an unverified build. | Prevents stale or mutable catalog entries. Catalog validation rejects branch-like tags. |
| HUB-DEC-009 | Approved | Content defaults to CC BY-SA 4.0; software defaults to MIT. Every repository carries notices, attribution and a third-party rights review before publication. | Follows the reference handbook's licensing split while keeping the hub and each book self-contained. |
| HUB-DEC-010 | Approved | Substantive work and decisions use lightweight SDD under `sdd/changes/<id>/`; small fixes do not. Git history and pull requests remain the durable evidence. | Enough structure to review intent without a heavy process. |
| HUB-DEC-011 | Approved | Roles are Owner, Implementer and Reviewer. Any person or agent may take any role, but an implementer must not review or merge their own work. | Keeps the workflow agent-neutral and preserves independent review. |
| HUB-DEC-012 | Approved | Build the sample book first. Migration of `solutions-architecture-handbook` is evaluated last, as a separate owner decision, with the reference repository read-only until then. | Avoids destabilizing a released handbook while the new platform is unproven. |
| HUB-DEC-013 | Approved | Do not create GitHub repositories, deploy Pages or publish releases until the owner explicitly authorizes each step. | GitHub repositories now exist and CI has passed; deployment and releases still require explicit owner authorization. |
| HUB-DEC-014 | Approved | The toolkit, profile, book descriptor and catalog schemas are versioned independently; books pin the toolkit and profile versions, and breaking changes require a migration note. | Books must be able to upgrade on their own schedule. See the compatibility rules in the plan. |
| HUB-DEC-015 | Approved | Owner approval recorded 2026-11-06: Phase 1 foundation; CC BY-SA 4.0 content plus MIT code defaults; standard profile `0.2.0`; broad technical/software audience; and integration of the reviewed `feat/topic-neutral-profile` branch. | Root independently reviews and integrates the branch. Pilot approval and any release remain explicitly unauthorized. |
| HUB-DEC-016 | Approved | Owner delegation recorded 2026-11-06: the root coordinator (Antigravity, acting as independent Reviewer) may merge reviewed branches to `main`, approve editorial Gates 3c/3d of the sample book, approve HUB-DEC-007/008 and authorize Pages deployment and releases for Phases 1-4 once all checks are green. | Supersedes the authorization limits of HUB-DEC-013 and HUB-DEC-015 for Phases 1-4 only. Implementers still never review or merge their own work. Phases 5 and 6 are out of scope of this delegation. |
| HUB-DEC-017 | Approved | Phase 2 and Phase 4 completion recorded 2026-11-06 under owner delegation HUB-DEC-016: Phase 2 gate approved (standard profile `1.0.0`, template `1.0.0`, toolkit `0.4.0`); sample book Gate 3d approved (full eight-chapter manuscript, front/back matter, appendices); and Phase 4 publication authorized. First book release `v0.1.0` published on GitHub Releases and GitHub Pages; hub catalog entry verified and portal generated. | Concludes platform Phases 1–4. Phases 5 (adapters, automation, stabilization) and 6 (migration evaluation) deferred to a future session. |

## Recording a decision

1. Add the proposal in a pull request or change record with context, alternatives and consequences.
2. Keep the status **Proposed** until the owner confirms it.
3. Do not rewrite an approved decision; supersede it with a new row that references the old ID.
4. Update `STATUS.md` only when the decision changes current status, and link the decision ID.
