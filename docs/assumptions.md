# Assumptions and verified inputs

This file distinguishes what was verified from what is assumed. The implementation plan depends on
both; a reviewer should challenge the assumptions before Gate 1.

## Verified during the scaffold

| Fact | Evidence |
| --- | --- |
| The reference handbook exists locally and is a Git repository | `/home/ubuntu/github/solutions-architecture-handbook`; `git rev-parse HEAD` |
| Reference HEAD inspected | `6a15cc211f65e148afdaa75c71a063a8084d1910`, branch `release/v2.1-rc5`, clean worktree |
| The sample repository directory exists but is empty | `ls -la /home/ubuntu/github/handbook-sample-01` returned no files |
| The hub directory contained only the handoff | `ls -la /home/ubuntu/github/handbooks-hub` before `git init` |
| Python is 3.12.3; Git is 2.43.0 | `python3 --version`, `git --version` |
| `jsonschema` 4.10.3 and `PyYAML` 6.0.1 are available | Import check during scaffold |
| `pytest` is not installed | Import check during scaffold; tests use `unittest` |
| Quarto is not on `PATH` | `which quarto` returned nothing; publication is not part of this milestone |
| Reference chapter skeleton uses `When to Use This Chapter`, `Key Takeaway`, `Architecture Review Checklist` and `Further Reading` | Inspected `ch01` and `ch16`; `sdd/specs/rc3/STYLE.md` |
| Reference build declares Quarto `1.11.9` and Python 3.12 | `.github/workflows/ci.yml`, `.github/workflows/book.yml`, `requirements.txt` |
| Reference licensing split is CC BY-SA 4.0 for content and MIT for code | `NOTICE.md`, `LICENSE`, `LICENSE-CODE` |

The reference repository was inspected read-only. No file in it was created, modified or deleted.

## Assumptions

| ID | Assumption | Impact if wrong | How to validate |
| --- | --- | --- | --- |
| A-01 | The owner wants a hub plus independent book repositories, not a monorepo. | The whole repository boundary and toolkit pinning would change. | Gate 1 owner approval. |
| A-02 | Python 3.11+ is an acceptable floor for book repositories. | Some books may need an older runtime; we would lower the floor or publish a compatibility layer. | Test in the template and sample book on the target runner. |
| A-03 | Quarto `1.11.9` remains the primary toolchain, with Pandoc `3.10` and Graphviz. | A version change affects build scripts, artifact checks and reproducibility. | Revalidate in Phase 2; record the resolved versions in the manifest. |
| A-04 | GitHub Pages for reading and GitHub Releases for downloads are acceptable. | Publication and catalog contracts would need a different host. | Owner decision at Gate 4. |
| A-05 | The sample book is named "Handbook Authoring and Publishing". | Titles, ids and slugs need changes. | Owner approval of the brief in Phase 3. |
| A-06 | The standard profile's required section closure (figure, table, example, pitfall, trade-off) fits most chapters, with recorded exceptions. | The profile could become too rigid and slow authoring. | Pilot review in Phase 3; amend the profile version if needed. |
| A-07 | An empty catalog is valid before the first approved release. | The portal would need a placeholder or a pre-release state. | Portal tests in Phase 4. |
| A-08 | One toolkit release can serve both the sample book and future books. | Books may need divergent behavior; profiles and versioned options should absorb it, not forks. | Clean-clone test with two books in Phase 5. |
| A-09 | The existing handbook remains read-only and is not a build dependency. | Migration would contaminate the new platform. | Review check at every phase; `HUB-DEC-012`. |
| A-10 | No GitHub organization or repository names are fixed yet. | Catalog URLs and Pages domains are placeholders. | Owner supplies names before Phase 4. |

## Open questions for the owner

1. Confirm the dual-license scope in `NOTICE.md`, including whether hub documentation should be
   CC BY-SA 4.0 or a permissive documentation license.
2. Confirm the standard profile direction and the required section closure before Phase 2 freezes
   `1.0.0`.
3. Confirm whether the sample repository scaffold should be delegated to a separate OpenCode session
   immediately after Gate 1, as assumed in the plan.
4. Confirm the GitHub owner/organization and repository names before any catalog URL is written.
5. Confirm the release cadence and who may authorize a release after the initial owner-gated setup.

## Source precedence

If sources disagree, use this order:

1. The owner's explicit written decision recorded in `docs/decisions.md`.
2. `IMPLEMENTATION-HANDOFF.md` and the Engram handoff summary #6795.
3. The inspected reference repository, for editorial and build lessons only.
4. This document's assumptions.

Do not silently resolve a conflict. Record it in the change evidence and ask the owner.
