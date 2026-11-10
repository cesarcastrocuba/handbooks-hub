# Agent and contributor instructions

These rules apply to every contributor, human or AI, whatever tool or model is used. They describe
**roles, not products**. Status lives only in [`STATUS.md`](STATUS.md); decisions live only in
[`docs/decisions.md`](docs/decisions.md).

## Mission

Maintain an agent-neutral platform for independent handbooks. The hub owns shared contracts, the
versioned toolkit, the standard profile, the template, the catalog and the static portal. Books own
their canonical manuscript and their own content checks.

## Roles

| Role | Responsibility |
| --- | --- |
| **Owner** | Approves editorial gates, licenses, profile changes, releases and any decision marked *Owner*. Merges to `main`. |
| **Implementer** | Makes one scoped change in an exclusive write set, runs the relevant checks and records evidence. |
| **Reviewer** | A *different* person or agent. Reviews the exact commit or pull-request HEAD, re-runs the checks and posts classified findings. |

An implementer must never review or merge their own work. A reviewer may propose a fix but must not
silently rewrite the change under review.

## Workflow

1. Read `STATUS.md`, `docs/decisions.md` and the active change record under `sdd/changes/`.
2. Create a short-lived branch from `main`; use `<type>/<topic>` (for example `feat/profile-v1`).
3. Work only inside the assigned write set. One writer per file at a time.
4. Run the fast checks while working and the full checks before handoff.
5. Record evidence in the change record or pull request: files, commands, results and known gaps.
6. Request review from a different agent or person. Critical and Major findings block the merge;
   Minor and Optional findings are fixed or recorded as follow-up issues.
7. The owner merges. Never merge or release without explicit owner approval.

## Source-of-truth rules

- Book repositories own their canonical Quarto sources. The hub never copies manuscript content.
- The hub toolkit is installed at a pinned version. Books must not import a parent checkout or copy
  shared scripts.
- Generated artifacts (HTML, PDF, DOCX, source bundles, manifests, checksums) are built from an
  approved commit, verified and published; they are not edited or committed as source.
- The catalog lists approved releases only. A catalog entry must point to an immutable release.
- `solutions-architecture-handbook` is read-only reference material. Do not modify it and do not
  migrate it without a separate owner decision.

## Content rules

- Repository documentation and handbook content are written in English.
- Be vendor-neutral and decision-oriented. Name products only as labelled examples.
- Never invent sources, standards, mappings, build results or validation claims. Report the commands
  actually run and mark everything else as not run.
- A commit or pull request may name the tool that contributed in a trailer such as
  `Co-Authored-By`; it records provenance only and assigns no role (`HUB-DEC-025`). Each book
  repository sets its own policy.
- Preserve attribution and licensing. Content defaults to CC BY-SA 4.0; code defaults to MIT. A
  third-party rights review is required before importing external material.
- No secrets, personal data or unlicensed third-party assets.

## Verification commands

```bash
make check    # unit tests and fast validators
make full     # fast checks plus full repository validators
```

`make full` checks what this repository owns. Book artifact builds run in the `publication-build` CI
job and the portal builds in the `portal-pages` workflow; `make full` does not replace a book's own
artifact gate.

## Agent adapters

The instructions above are tool-neutral. Tool-specific adapters (skills, commands, plugin files)
are optional projections added in Phase 5. They may not add rules that are absent here, and they
must not become a second source of truth.
