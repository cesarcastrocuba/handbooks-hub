# Tasks — hub scaffold

**Status:** Proposed
**Change:** `0001-hub-scaffold`

## Work packages

| ID | Task | Write set | Depends on | Status |
| --- | --- | --- | --- | --- |
| T1 | Read-only inventory of the reference handbook and handoff | None | — | Done |
| T2 | Initialize the hub Git repository | `.git/` | T1 | Done |
| T3 | Governance, status and licensing | root Markdown, `LICENSE*`, `NOTICE.md` | T2 | Done |
| T4 | Architecture and contracts | `docs/` | T1, T3 | Done |
| T5 | Proposed profile and schemas | `profiles/`, `schemas/` | T4 | Done |
| T6 | Template and catalog | `template/`, `catalog/` | T5 | Done |
| T7 | Toolkit 0.1.0 | `tools/src/` | T5 | Done |
| T8 | Toolkit tests | `tools/tests/` | T7 | Done |
| T9 | Basic CI and PR template | `.github/` | T7, T8 | Done |
| T10 | SDD record | `sdd/` | T3–T9 | Done |
| T11 | Run fast and full checks | None | T8, T9 | Done |
| T12 | Commit the scaffold with conventional commits | `.git/` | T11 | Done |
| T13 | Independent review | Review comments | T12 | Pending |
| T14 | Owner Gate 1 | Decision record | T13 | Pending |

## Verification mapping

| Acceptance criterion | Evidence |
| --- | --- |
| Fast checks pass | `make check` output |
| Full checks pass | `make full` output |
| Negative input rejected | `tools/tests/test_*.py` |
| Template valid in full mode | `validate-book template/book/book.yaml --full` |
| Empty catalog valid | `validate-catalog catalog/catalog.json` |
| No external edits | `git status` in hub; read-only checks of sample/reference |
| Clean tree | `git status --porcelain` after the evidence commit |
| Independent review | Review verdict on the exact commit |

## Deferred tasks

| Task | Reason | Next step |
| --- | --- | --- |
| Sample repository scaffold (`handbook-sample-01`) | This session is restricted to the hub | Separate OpenCode session after Gate 1, non-overlapping write set |
| Full manuscript validator | Phase 2 | Freeze profile 1.0.0, then implement |
| Quarto template build | Phase 2 | Add pinned toolchain and smoke build |
| Publication manifest and portal | Phase 4 | Schema, build-once pipeline, catalog entry |
| Agent adapters | Phase 5 | Project neutral instructions; add drift check |
| Migration evaluation | Phase 6 | Owner decision after a stable sample release |
