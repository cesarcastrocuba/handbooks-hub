# Implementation plan — reusable handbook platform

**Status:** Phases 1 to 4 complete; Phases 5 and 6 not started. Current status lives in `STATUS.md`.
**Version:** 0.1.0
**Date:** 2026-11-06
**Scope of this milestone:** local hub repository only. The sample book repository, GitHub
repositories, Pages, releases and migration are explicitly out of scope. The sample repository was
scaffolded concurrently by a separate session; this session only reads and records that fact.

> **Current state (2026-11-08):** Phases 1 to 4 are complete and the sample book is published at
> `v0.2.0`. Sections 2, 3, 8 to 11 and 19 describe the plan as it was carried out and are kept as
> history. Current status lives in [`STATUS.md`](../STATUS.md); section 20 lists the next actions.

This plan turns `IMPLEMENTATION-HANDOFF.md` and the Engram handoff summary #6795 into reviewable work.
It records what was inspected, the contracts the platform must honour, the phase sequence, the work
packages, the gates and the evidence required to close each phase.

The handoff is intentionally short and is not a verbatim copy of the prior design. Where this plan
adds detail, it is either derived from the inspected reference repository or marked as an assumption
in [`assumptions.md`](assumptions.md). Assumptions are not decisions.

---

## 1. Objective

Build a reusable, agent-neutral platform in which:

- independent book repositories own canonical Quarto sources and accept community pull requests;
- the hub owns the static categorized portal, the versioned Python toolkit, schemas, common profiles,
  the book template, documentation and agent-neutral editorial instructions;
- books install a pinned toolkit version and never import a parent checkout or copy shared scripts;
- the hub validates catalog entries and publication metadata, while book-specific tests stay with the
  book and shared tests stay in the toolkit;
- an approved commit produces a verified artifact set, and the portal links to that immutable release;
- humans and agents can implement and review without a tool-specific workflow.

## 2. Success criteria for the first milestone

The milestone is complete when:

1. `handbooks-hub` is a local Git repository with a reviewable scaffold and conventional commits.
2. The scaffold defines the repository boundaries, editorial contract, publication contract, catalog
   contract, standard profile, schemas, template starting point and phased plan.
3. A deterministic toolkit validates the catalog, profile and book descriptor, with tests that cover
   both accepted and rejected input.
4. `make check` and `make full` pass from a clean checkout of the hub.
5. This session writes nothing to the sample repository or the reference repository. The sample
   repository is scaffolded concurrently by a separate session and reviewed in its own lane.
6. No GitHub repository was created; nothing was deployed, released, merged or published.
7. An independent reviewer has reviewed the exact commit and posted classified findings.

## 3. Non-goals for this milestone

- Editing `/home/ubuntu/github/handbook-sample-01`.
- Creating GitHub repositories, organizations or remote configuration.
- Deploying GitHub Pages or any other host.
- Building, tagging or publishing a release.
- Merging or self-reviewing the scaffold.
- Migrating `solutions-architecture-handbook`.
- Implementing the full manuscript validator, Quarto pipeline or portal.

These are separate phases with their own gates.

## 4. Inputs and evidence

| Input | Use | Evidence |
| --- | --- | --- |
| `IMPLEMENTATION-HANDOFF.md` | Scope, architecture, editorial and publication direction | Repository root |
| Engram summary #6795 | Additional context: independent repos, pinned toolkit, roles, phases | `mem_get_observation` 6795 |
| Reference handbook | Read-only source of editorial lessons and build contracts | HEAD `6a15cc211f65e148afdaa75c71a063a8084d1910`, branch `release/v2.1-rc5`, clean worktree |
| Reference `AGENTS.md`, `DECISIONS.md`, `PROJECT_STATUS.md` | Role model, decision log and status discipline | Read-only inspection |
| Reference `sdd/specs/rc3/STYLE.md` | Chapter skeleton, unit labels, figure/table rules | Read-only inspection |
| Reference `scripts/check_structure.py`, `check_crossrefs.py`, `check_links.py` | Validator behaviour to generalize, not copy | Read-only inspection |
| Reference `.github/workflows/*.yml` | Quarto/Python versions, artifact expectations | Read-only inspection |
| Reference `NOTICE.md`, `LICENSE`, `LICENSE-CODE` | Licensing split and attribution pattern | Read-only inspection |

The reference repository was not modified. The sample repository was empty at initial inspection and
was populated by a separate session during this milestone; this session made no writes to it.

## 5. Operating model

### Roles

| Role | May do | May not do |
| --- | --- | --- |
| Owner | Approve briefs, outlines, profiles, licenses, gates, merges and releases | Delegate accountability for a release without recording the authorization |
| Implementer | Change one exclusive write set, run checks, record evidence, open a review | Review or merge their own change |
| Reviewer | Review the exact commit, re-run checks, classify findings, approve or request changes | Silently rewrite the implementation under review |

Any person or agent may hold any role. The constraint is separation of duties, not the product name.

### Work-package discipline

Every work package has:

- one objective and one exclusive write set;
- explicit entry criteria and dependencies;
- a command list that produces evidence;
- an acceptance check that a reviewer can reproduce;
- one owner approval point if it changes a contract, profile, license or release.

Parallel work is allowed only when write sets do not overlap. A shared contract change lands before
its consumers, never concurrently with them.

### Review findings

| Severity | Meaning | Merge effect |
| --- | --- | --- |
| Critical | Wrong, unsafe, unlicensed or unreproducible result | Blocks |
| Major | Contract violation, missing acceptance evidence or broken workflow | Blocks |
| Minor | Quality issue with a contained workaround | Fix or record follow-up |
| Optional | Improvement outside the current scope | Record as follow-up |

A reviewer verdict is valid only for the exact commit reviewed. A later commit requires a new review.

## 6. Architecture and contracts

### Repository boundaries

```text
handbooks-hub
  ├── docs/          contracts, decisions, assumptions, plan
  ├── profiles/      versioned editorial profiles
  ├── tools/         handbook-toolkit package + tests (schemas are package data)
  ├── template/      starting point for a book repository
  ├── catalog/       approved release entries
  └── sdd/           change proposals, specs, tasks, evidence

book repository (independent)
  ├── manuscript/    canonical Quarto sources
  ├── assets/        diagrams and figures
  ├── publishing/    Quarto configuration and metadata
  ├── tests/         book-specific tests
  ├── sdd/           book change records
  └── AGENTS.md      book-specific project rules
```

### Contract summary

| Contract | Artifact | Versioned by | Consumer |
| --- | --- | --- | --- |
| Book descriptor | `book.yaml` | Schema `1.0` | Toolkit, catalog, portal |
| Editorial profile | `profile.yaml` | Profile `1.0.0` | Toolkit, reviewers, books |
| Catalog | `catalog/catalog.json` | Schema `1.0` | Portal, reviewers |
| Publication manifest | `publication-manifest.json` (Phase 4) | Schema `1.0` (planned) | Toolkit, catalog, auditors |
| Toolkit CLI | `handbook-toolkit` | Semver `0.5.0` | Books, CI, portal |

A book pins the toolkit and profile versions it was written and verified against. The toolkit never
silently upgrades a book's profile.

### Dependency rules

1. The hub does not read a book's working tree at build time.
2. A book does not import hub source code; it installs a published toolkit version.
3. The catalog is the only interface from books to the portal.
4. The reference handbook is not a dependency and is never imported.
5. Generated artifacts are outputs, not inputs.

## 7. Phase overview

| Phase | Goal | Primary output | Gate |
| --- | --- | --- | --- |
| 1 | Foundation | Local hub scaffold, contracts, plan, basic CI; sample repository scaffold | Independent review + owner Gate 1 |
| 2 | Shared toolkit, profile and template | Toolkit `0.4.0`, profile `1.0.0`, template `1.0.0`, deterministic validators | Owner approves profile and toolkit contract |
| 3 | Sample book | Approved brief, outline and pilot, then full manuscript | Gate 3a brief, 3b outline, 3c pilot, 3d manuscript |
| 4 | Catalog and publication | Artifact build, manifest, checksums, catalog, portal, Pages/Releases | Owner authorizes publication; independent artifact review |
| 5 | Adapters, automation, stabilization | Optional agent adapters, catalog automation, clean-clone matrix, runbook | Clean-clone verification + owner acceptance |
| 6 | Migration evaluation | Read-only assessment, parity plan and cost/benefit | Separate owner decision; no migration by default |

The phase numbers follow the handoff. The first milestone is Phase 1. It is split into a hub portion
(completed in this session) and a sample-repository portion handled by a separate session; this
session does not write to the sample repository.

---

## 8. Phase 1 — Foundation

### Objective

Establish the two-repository model, the shared contracts, the review workflow and a working hub
scaffold before building the full toolkit or writing the sample book.

### Entry criteria

- Owner supplied the handoff and authorized a local scaffold.
- Reference handbook available read-only.
- Sample repository path existed and may be scaffolded by a separate session concurrently.

### Work packages

| ID | Scope | Exclusive write set | Output | Status |
| --- | --- | --- | --- | --- |
| P1-HUB-01 | Read-only inventory of the existing handbook and handoff | None (read-only) | Contracts and lessons recorded in docs | Done |
| P1-HUB-02 | Hub scaffold and plan | `handbooks-hub/**` | Repository, governance, schemas, profile, template, toolkit skeleton, CI, tests | Done, pending review |
| P1-SAMPLE-01 | Sample repository scaffold | `handbook-sample-01/**` | Independent book repository with AGENTS, SDD and verify command | Scaffolded by a separate session (observed); review pending in that lane |
| P1-GATE | Independent review and owner gate | Review comments only | Classified findings and owner decision | Pending |

### P1-HUB-02 deliverables

- Git repository initialized on `main` with conventional commits and a clean tree.
- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `STATUS.md`, `NOTICE.md`, `CHANGELOG.md`.
- `LICENSE` (CC BY-SA 4.0) and `LICENSE-CODE` (MIT).
- `docs/architecture.md`, `editorial-contract.md`, `publication-contract.md`,
  `catalog-contract.md`, `decisions.md`, `assumptions.md`, `implementation-plan.md`.
- `profiles/standard/profile.yaml` as the approved standard profile (owner approval recorded in `HUB-DEC-015`).
- `tools/src/handbook_toolkit/schemas/profile.schema.json`, `book.schema.json`, `catalog.schema.json`.
- `template/book/` minimal book descriptor and manuscript reading order.
- `catalog/catalog.json` empty and valid.
- `tools/` package `handbook-toolkit` 0.4.0 with CLI, validators and `unittest` tests.
- `.github/workflows/ci.yml` and `.github/pull_request_template.md`.
- `sdd/changes/0001-hub-scaffold/` proposal, spec, tasks and evidence.

### Acceptance criteria

1. `make check` passes, including all toolkit tests.
2. `make full` passes, including template reading-order checks.
3. `handbook-toolkit verify` rejects a catalog with a duplicate slug, a profile with duplicate
   element ids and a book with an unpinned toolkit version.
4. The template book descriptor resolves to an existing manuscript reading order and chapter file.
5. No file outside `handbooks-hub` is modified.
6. A reviewer can reproduce every result from a clean checkout with only Python 3.11+,
   `jsonschema` and `PyYAML`.
7. An independent reviewer posts no open Critical or Major finding.

### Gate 1 owner decisions

- Hub/sample split and the separate sample-repository lane: **approved**.
- Standard profile `0.2.0` and the explicit exceptions model: **approved**.
- Dual-license and notice scope: **approved**.
- Integration of the reviewed `feat/topic-neutral-profile` branch: **authorized**; root integrates.
- Phase 2 may start after integration. Pilot approval, deployment and release remain unauthorized.

### Evidence

```bash
make check
make full
git status --porcelain
git log --oneline --decorate -5
```

---

## 9. Phase 2 — Shared toolkit, profile and template

### Objective

Turn the scaffold into a small, versioned shared platform that a book can install and run without
copying hub code.

### Work packages

| ID | Scope | Depends on | Acceptance |
| --- | --- | --- | --- |
| P2-01 | Freeze the toolkit CLI and package layout | Gate 1 | `handbook-toolkit --help`, `version`, `verify`, `validate-*` documented and tested |
| P2-02 | Standard profile `1.0.0` and schema | Gate 1 | Owner-approved; every required element has a validator rule or an explicit manual-review note |
| P2-03 | Template book `1.0.0` | P2-01, P2-02 | A new book can be copied, pinned and verified locally |
| P2-04 | Manuscript validators | P2-02 | Chapter skeleton, unit labels, section closure, figure/table rules, cross-references |
| P2-05 | Deterministic test suite | P2-01..P2-04 | Positive and negative fixtures for every rule; stable output |
| P2-06 | CI and clean-clone check | P2-01..P2-05 | Fast and full checks pass on a fresh clone |
| P2-GATE | Contract approval | All above | Owner approves profile `1.0.0` and toolkit `0.4.0` |

### Toolkit responsibilities

The toolkit should provide, in order of implementation:

1. **Document loading** — YAML/JSON parsing with stable error messages.
2. **Schema validation** — JSON Schema 2020-12 for book, profile, catalog and manifest, loaded from
   package data by default so an installed toolkit is self-contained. A local `--schemas` directory
   remains available as an explicit override.
3. **Semantic validation** — uniqueness, exact version pins, path safety, tag/version consistency,
   reading-order completeness.
4. **Manuscript validation** — profile-driven checks for the chapter skeleton and section closure.
5. **Reference validation** — section, figure and table references resolve; no duplicate anchors.
6. **Artifact validation** (Phase 4) — manifest completeness, checksums and expected files.
7. **Portal generation** (Phase 4) — static site from the catalog, deterministic output.

The toolkit must not contain book prose, vendor-specific credentials or hidden network calls. It may
not require a parent checkout.

### Profile `1.0.0` acceptance

- Chapter-level elements are required by default: `When to Use This Chapter`, `Key Takeaway`, worked
  example, review checklist and `Further Reading`.
- Section closure is required by default: `Example`, `Common Pitfall`, `Decision & Trade-off`.
- Figures and captioned tables are optional. A section may omit either when it would not help the
  reader; absence is not an exception.
- Unit labels are required in order: `Definition.`, `Purpose.`, `What it includes.`, `Why it is
  needed.`
- Figure rules when used: source present, alt text, maximum natural width, no upscaling, minimum
  effective print size.
- Table rules when used: caption below, numbering outside decision callouts, adaptive widths.
- Cross-reference rules: explicit forms only; automatic glossary links off.
- Exceptions are recorded with owner approval and do not silently disable a rule.
- Every rule is classified as **automated**, **assisted** or **manual review**. The profile must not
  imply automation that does not exist.

### Template `1.0.0` acceptance

- Contains `book.yaml`, `AGENTS.md`, `manuscript/book.yml`, a chapter skeleton and a publishing
  configuration that builds a smoke book.
- Pins the toolkit and profile versions.
- Contains no copied toolkit source.
- Has a `make check` and a documented `make full` that run against the pinned toolkit.
- Is tested by creating a temporary copy, replacing the identifiers and running the checks.

### Phase 2 gate

The owner approves:

- profile `1.0.0` and its automated/manual split;
- toolkit `0.4.0` public API and versioning policy;
- template `1.0.0` and the book upgrade procedure.

No sample-book chapter expansion starts before this gate.

### Evidence

```bash
make check
make full
python3 -m unittest discover -s tools/tests -v
handbook-toolkit --root . verify --full
python3 -m unittest discover -s tools/tests -p test_template.py -v
```

The template test copies `template/book` to a temporary directory, replaces the identifiers, runs the
template's own `make check` and, when Quarto and `pdfinfo` are installed, performs a real `make build`
and inspects the six payloads. The Phase 2 closure record is
[`sdd/changes/0009-phase2-closure/`](../sdd/changes/0009-phase2-closure/).

---

## 10. Phase 3 — Sample book "Handbook Authoring and Publishing"

### Objective

Prove the platform by writing a real book in an independent repository, with owner gates at the
brief, outline, pilot and manuscript.

### Work packages

| ID | Scope | Gate | Output |
| --- | --- | --- | --- |
| P3-01 | Book brief | Owner approves 3a | Audience, outcomes, scope, non-goals, length, profile exceptions |
| P3-02 | Outline | Owner approves 3b | Chapters, sections, figures, tables, checklists, dependencies |
| P3-03 | Pilot section | Owner approves 3c | One complete, reviewed section with a figure, table and artifact preview |
| P3-04 | Chapter expansion | After 3c | Chapters written in small reviewed batches |
| P3-05 | Book QA | After all chapters | Cross-references, checklists, licensing, full artifact build |
| P3-GATE | Manuscript approval | Owner approves 3d | Release candidate |

### Brief content

- Working title and one-sentence purpose.
- Intended reader and the decisions the book helps them make.
- What the book covers and what it deliberately excludes.
- Required length and depth; number of chapters.
- Profile and any recorded exception.
- Success evidence: what a reader can do after reading.
- Licensing and third-party material constraints.

### Outline content

- Chapter titles and one-paragraph purpose.
- Section map with the figure, table and checklist intent for each section.
- Worked example per chapter.
- Dependencies and cross-references.
- Estimated length and review effort.

### Pilot content

One section, not a whole chapter, is enough to test the editorial contract:

- required unit labels and a real decision;
- one readable figure with source and alt text;
- one captioned table with adaptive widths;
- a closing example, pitfall and trade-off;
- a rendered preview that a reviewer can inspect;
- independent review and owner approval before expansion.

### Expansion rules

- One chapter or a small batch per pull request.
- No chapter starts before the pilot is approved.
- Every change records the profile elements it satisfies and any exception.
- Cross-references are updated in the same change that moves a target.
- Factual claims cite real sources; numeric examples are labelled illustrative.
- A chapter is not "done" until its checklist and further reading are complete.

### Phase 3 gates

| Gate | Owner decision | Reviewer evidence |
| --- | --- | --- |
| 3a Brief | Approve audience, scope and constraints | Brief is testable and matches the platform goal |
| 3b Outline | Approve structure and coverage | No duplicate ownership; figures/tables/checklists planned |
| 3c Pilot | Approve editorial quality and artifact readability | Exact commit, rendered preview, profile conformance |
| 3d Manuscript | Approve release candidate | Full build, links, checklists, licensing, sampled pages |

---

## 11. Phase 4 — Catalog and publication

### Objective

Publish the sample book end to end and list it in the hub catalog without mutable links or rebuilt
artifacts.

### Work packages

| ID | Scope | Depends on | Acceptance |
| --- | --- | --- | --- |
| P4-01 | Publication manifest schema and validator | Phase 3 pilot | Manifest validates; missing hash or file fails |
| P4-02 | Book build pipeline | P4-01 | HTML, PDF, DOCX, source bundle built from one commit |
| P4-03 | Artifact verification | P4-02 | Structure, links, checksums, sampled pages |
| P4-04 | Catalog entry workflow | P4-03 | Approved release listed with immutable URLs |
| P4-05 | Static portal | P4-04 | Categorized cards, deterministic HTML, no dead links |
| P4-06 | Pages and Releases automation | P4-05 | Pages serves reading; Release holds downloads |
| P4-07 | End-to-end rehearsal | All above | A clean clone reproduces the release and the catalog verifies |

### Publication sequence

1. Owner approves the release commit and version.
2. CI checks out the exact commit with a clean environment and pinned tools.
3. CI builds once and records tool versions.
4. CI runs structural, link, artifact and visual checks.
5. CI writes the manifest and checksums over the verified bytes.
6. CI publishes the same bytes to the Release and Pages.
7. A hub change adds the catalog entry and validates it.
8. Independent reviewer verifies the release assets and the catalog links.

### Portal acceptance

- Built only from `catalog/catalog.json`; no hand-written book cards.
- Every card links to an immutable release and a reading site.
- Categories are stable and every category page is deterministic.
- Broken asset links fail the build.
- The portal has no tracking, accounts or client-side secrets.
- Accessibility basics: semantic headings, keyboard navigation, visible focus, alt text.

### Phase 4 gate

The owner authorizes publication explicitly. The reviewer confirms that the published bytes match the
verified artifact set and that the catalog points to the same tag.

---

## 12. Phase 5 — Agent adapters, automation and stabilization

### Objective

Make the platform convenient for multiple agents without creating a second source of truth, and prove
it survives clean clones and routine upgrades.

### Work packages

| ID | Scope | Acceptance |
| --- | --- | --- |
| P5-01 | Adapter contract | Adapters are projections of `AGENTS.md`; no new rules |
| P5-02 | Optional adapters | At least one adapter loads the neutral instructions and runs the same checks |
| P5-03 | Catalog automation | Release event or manual dispatch validates and updates the catalog |
| P5-04 | Clean-clone matrix | Hub and sample book verify on Linux and one additional environment |
| P5-05 | Operations runbook | Upgrade, rollback, release withdrawal and incident steps are documented and rehearsed |
| P5-GATE | Stabilization | Owner accepts the runbook and the clean-clone evidence |

### Adapter rules

- The adapter may add tool-specific syntax, not platform policy.
- The adapter must not embed a divergent checklist or a second decision log.
- Removing the adapter must leave the project fully usable.
- A drift check compares adapter references with the neutral instructions.

### Upgrade procedure

1. Read the toolkit/profile changelog and migration note.
2. Bump the exact pin in `book.yaml`.
3. Run the fast checks; fix or record profile exceptions.
4. Run the full build and compare artifacts and manifest.
5. Independent review; owner approval for a profile major version.
6. Publish a new book release; never mutate the previous one.

---

## 13. Phase 6 — Migration evaluation (deferred)

### Objective

Decide whether to migrate `solutions-architecture-handbook` to the platform, with evidence and a
separate owner authorization. **No migration happens by default.**

### Work packages

| ID | Scope | Output |
| --- | --- | --- |
| P6-01 | Read-only content and build inventory | File counts, anchors, diagrams, checklists, scripts, dependencies |
| P6-02 | Parity and risk assessment | What must remain byte- or semantics-identical; what can change |
| P6-03 | Migration plan and cost | Phases, effort, rollback, release strategy |
| P6-GATE | Owner decision | Approve, defer or reject migration |

### Preconditions

- The sample book has completed at least one approved release on the new platform.
- The toolkit and profile are stable enough that migration would not chase a moving target.
- A content freeze and parity baseline are agreed.
- Licensing and attribution are rechecked for the migrated material.
- The reference repository remains untouched until the owner authorizes a separate migration project.

---

## 14. Sequencing and parallelism

```text
Gate 1
  │
  ├── Phase 2 (hub: toolkit, profile, template) ── Gate 2
  │
  └── Phase 1 sample scaffold (separate session, concurrent)
          │
          └── Phase 3 brief → outline → pilot → expansion → Gate 3
                                      │
                                      └── Phase 4 build → verify → catalog → portal → Gate 4
                                                          │
                                                          └── Phase 5 adapters/automation → Gate 5
                                                                                  │
                                                                                  └── Phase 6 evaluation
```

Parallel lanes may run only when they have disjoint write sets. The hub lane owns `docs/`,
`tools/src/handbook_toolkit/schemas/`, `profiles/`, `tools/`, `template/` and `catalog/`. The
sample-book lane owns only its repository. A shared contract change in the hub must land before a
book consumes it.

## 15. Quality gates and commands

### Current hub commands

| Command | Type | What it does |
| --- | --- | --- |
| `make check` | Fast | Runs toolkit unit tests and the catalog/profile/book validators |
| `make full` | Full (current scope) | Runs `check` plus repository-contract and template reading-order checks |
| `handbook-toolkit --root . verify` | Fast | Validates catalog, profile and template descriptor |
| `handbook-toolkit --root . verify --full` | Full | Adds required repository files and manuscript path checks |

### Planned book commands (Phase 2–4)

| Command | Type | What it does |
| --- | --- | --- |
| `handbook-toolkit book check .` | Fast | Validates descriptor, reading order and profile skeleton |
| `handbook-toolkit book references .` | Fast | Checks section, figure and table targets |
| `handbook-toolkit book build .` | Full | Builds HTML, PDF, DOCX and source bundle once |
| `handbook-toolkit artifacts verify dist/` | Full | Verifies manifest, checksums and expected artifacts |
| `handbook-toolkit portal build` | Full | Builds and link-checks the static portal |

The distinction is deliberate: fast checks are suitable for every commit; full checks include
artifacts and are required before a release.

GitHub Actions also runs a `wheel-install` job: it builds the toolkit wheel, checks that the three
schemas are packaged, installs the wheel in a fresh virtual environment and validates an independent
copy of the template book outside the hub checkout, with a decoy `schemas/` directory. This is a
packaging-boundary check, not a publication or release step. Local environments without wheel
tooling cannot run it.

### Green definition

A gate is green only when:

1. Every required command exits 0.
2. The evidence records the exact commit, command and result.
3. The reviewer reproduces the commands on that commit.
4. No Critical or Major finding remains open.
5. Owner approvals are recorded by decision ID.

## 16. Versioning and compatibility

| Artifact | Major change | Minor change | Patch change |
| --- | --- | --- | --- |
| Toolkit | Removed command, removed validation, changed output contract | New command or optional validation | Bug fix, message clarity |
| Profile | New required element or changed placement | New optional element | Wording or typo |
| Book schema | Removed or retyped field | New optional field | Description fix |
| Catalog schema | Removed or retyped field | New optional field | Description fix |
| Publication manifest | Removed or retyped field | New optional field | Description fix |

Rules:

- Books pin exact toolkit and profile versions. A range is rejected.
- A deprecated field or command gets at least one minor release of warning before removal.
- A profile major version requires owner approval and a migration note.
- The catalog may list books on different toolkit versions; it does not force an upgrade.
- The portal supports the catalog schema versions declared in the repository, not every historical
  version.

## 17. Risks and mitigations

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| Scope creep into a full monorepo or CMS | Delays the first useful slice; couples releases | Keep the contract small; phase gates; no feature without a gate | Owner |
| Toolkit and book contract drift | Books break unexpectedly; silent behavior changes | Exact pins; versioned profile; consumer tests in the template | Implementer |
| Non-deterministic artifacts | Published bytes differ from reviewed bytes | Pinned tools, `SOURCE_DATE_EPOCH`, manifest and checksums, build once | Implementer |
| Validator false confidence | Reviewers trust checks that do not cover editorial quality | Classify every rule as automated/assisted/manual; sample pages manually | Reviewer |
| Copied scripts in a book | Divergence and inconsistent fixes | Reject in review; template contains no toolkit source | Reviewer |
| Licensing or attribution gap | Legal exposure; blocked release | Dual-license notice, third-party review, release checklist | Owner |
| Stale catalog links | Broken downloads; loss of trust | Validate immutable URLs and checksums before listing; withdraw on failure | Implementer |
| Agent-specific instructions diverge | Inconsistent behavior across tools | Neutral `AGENTS.md` is the source; adapters are projections; drift check | Reviewer |
| Migration destabilizes the released handbook | Content loss or broken release | Defer migration; content freeze and parity gate; separate project | Owner |
| CI cost or slow feedback | Expensive review loops | Fast checks on every commit; full artifact checks only before release | Implementer |

## 18. Owner decisions required

| Decision | Gate | Current state |
| --- | --- | --- |
| Approve hub/book repository split and the separate sample lane | Gate 1 | **Approved** (`HUB-DEC-001`, `HUB-DEC-012`) |
| Approve standard profile direction and exceptions model | Gate 1/2 | **Approved** `0.2.0` (`HUB-DEC-004`, `HUB-DEC-015`) |
| Confirm licensing and attribution scope | Gate 1 | **Approved** (`HUB-DEC-009`, `HUB-DEC-015`) |
| Approve sample book brief | Gate 3a | **Approved** 2026-11-06 |
| Approve sample book outline | Gate 3b | **Approved** 2026-11-06 |
| Approve pilot section | Gate 3c | **Approved** 2026-11-06 under delegation (`HUB-DEC-016`) |
| Approve manuscript release candidate | Gate 3d | **Approved** 2026-11-06 under delegation (`HUB-DEC-017`) |
| Authorize GitHub repositories and Pages | Before Phase 4 | **Approved** under delegation (`HUB-DEC-016`) |
| Authorize publication and release | Gate 4 | **Approved** for `v0.1.0` (`HUB-DEC-017`) and later releases (`HUB-DEC-019`) |
| Bundled render resources | Rights review | **Approved**: replace those in doubt (`HUB-DEC-020`) |
| Decide on migration | Gate 6 | Deferred (`HUB-DEC-012`) |

## 19. Definition of done for this milestone

- [x] Hub Git repository initialized on `main`.
- [x] Governance, contracts, decisions, assumptions and plan written.
- [x] Standard profile `1.0.0` and schemas added; `0.2.0` remains resolvable.
- [x] Toolkit `0.4.0` with validators, build/reference/render APIs and tests added.
- [x] Empty catalog and buildable book template `1.0.0` added.
- [x] Basic CI and pull-request template added.
- [x] Lightweight SDD record added.
- [x] This session wrote nothing outside `handbooks-hub`; the reference worktree is clean and the sample lane is independent.
- [x] At the initial scaffold, no GitHub repository, deployment, release, merge or migration was performed; the GitHub repositories and CI now exist.
- [ ] Root independent review of the reviewed branch.
- [x] Owner Phase 1 approval and branch integration authorization.

## 20. Immediate next actions

See [`STATUS.md`](../STATUS.md#next-actions). In summary: close the post-Phase-4 remediation, move the
sample book to toolkit `0.5.0`, then start Phase 5 with owner authorization.

---

## Appendix A — Handoff mapping

| Handoff requirement | Artifact in this scaffold | Status |
| --- | --- | --- |
| Independent book repositories own canonical sources | `docs/architecture.md`, `HUB-DEC-001`, template | Contract defined; sample lane separate |
| Hub owns static portal | `docs/catalog-contract.md`, `catalog/`, planned portal | Phase 4 |
| Shared versioned toolkit under `tools/` | `tools/`, `handbook-toolkit` 0.4.0 | Validators implemented |
| Schemas | `tools/src/handbook_toolkit/schemas/*.json` | Book, profile, catalog |
| Common profiles | `profiles/standard/profile.yaml` | Approved `0.2.0` |
| Template | `template/book/` | Minimal; Phase 2 completes |
| Documentation | `docs/` | Complete for Phase 1 |
| Agent-neutral editorial instructions | `AGENTS.md`, `docs/editorial-contract.md` | Complete; adapters deferred |
| Books install pinned toolkit versions | `docs/architecture.md`, `book.schema.json`, `HUB-DEC-002` | Enforced by validator |
| Hub validates catalog and publication | Catalog validator implemented; manifest planned | Partial by design |
| Book-specific tests stay in book; shared tests in toolkit | `docs/architecture.md`, test layout | Contract defined |
| Fast vs full verify | `Makefile`, `docs/implementation-plan.md` | Implemented for hub scope |
| Lightweight SDD | `sdd/`, `HUB-DEC-010` | Scaffolded |
| Book brief, outline, pilot before expansion | Phase 3 gates | Planned |
| Standard profile elements | `profiles/standard/profile.yaml`, `docs/editorial-contract.md` | Approved `0.2.0` |
| Explicit cross-references, no indiscriminate links | `HUB-DEC-005`, profile | Approved |
| Proportional readable diagrams, adaptive tables | `HUB-DEC-006`, profile | Approved; validators in Phase 2 |
| HTML, PDF, DOCX, source bundle, manifest, checksums | `docs/publication-contract.md` | Contract defined; pipeline Phase 4 |
| Build once, publish identical artifacts | `HUB-DEC-007`, publication contract | Proposed |
| Pages for reading, Releases for downloads | `docs/publication-contract.md` | Phase 4 |
| Catalog references approved releases | `docs/catalog-contract.md`, schema | Enforced for entries |
| CC BY-SA 4.0 content, MIT code, notices | `LICENSE`, `LICENSE-CODE`, `NOTICE.md` | Done |
| Pin versions, no generated artifacts committed | `.gitignore`, contracts | Done |
| Phases 1–6 | This plan, Sections 8–13 | Defined |
| Migration deferred | `HUB-DEC-012`, Phase 6 | Deferred |
| No merge/release without owner | `AGENTS.md`, this plan | Enforced by process |

## Appendix B — Work-package write sets

| Lane | Write set |
| --- | --- |
| Hub foundation | `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `STATUS.md`, `NOTICE.md`, `CHANGELOG.md`, `docs/`, `sdd/changes/0001-hub-scaffold/` |
| Hub contracts | `tools/src/handbook_toolkit/schemas/`, `profiles/`, `catalog/` |
| Hub toolkit | `tools/` |
| Hub template | `template/` |
| Hub CI | `.github/` |
| Sample book | `handbook-sample-01/**` only |
| Reference handbook | Read-only; no write set |

No work package may write into another lane. A contract change that affects the toolkit and the
template is split into sequential changes or owned by one package with the other as a consumer.

## Appendix C — Evidence checklist

For every gate:

- [ ] Exact commit SHA recorded.
- [ ] Branch and pull request (or change record) identified.
- [ ] Commands listed exactly as run, with exit status.
- [ ] Output summary or log artifact attached.
- [ ] Files changed, with a one-line purpose per area.
- [ ] Checks not run, and why.
- [ ] Licensing and third-party impact stated.
- [ ] Open owner decisions listed.
- [ ] Reviewer identity differs from implementer.
- [ ] Reviewer verdict applies to the exact commit.
