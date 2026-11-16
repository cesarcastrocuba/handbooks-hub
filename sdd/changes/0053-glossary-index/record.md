# Change 0053 — Glossary pointers and analytic Index (G9, G4)

Owner assigned this change after 0052 merged. Base `50d9481`; branch
`feat/0053-glossary-index`, worktree `../handbooks-hub.worktrees/glossary-index`.
Claude reviews and merges. No self-merge, version bump or tag.

## Design and provenance

Ports the author's MIT frozen builder at `/tmp/agy-sa/src`, commit `13d295b`, with synthetic
fixtures only. No manuscript prose is copied into the hub. The glossary is a manuscript-relative
opt-in; optional vocabulary is repository-relative and schema-validated. Both use 0052's registry.
Section anchors can be staged without enabling prose cross-reference linking. Deliberate glossary
links are whitelisted and rebased for HTML. Word IDs are encoded before Pandoc can truncate them.
The final Index is unnumbered, with native TOC/navigation, and its own marker gates `cantSplit`.
Typst's existing cell rule prevents row splitting. Automatic glossary-term linking stays off.

The Owner requested one PR for 0053; the port, integration and synthetic fixtures form one review
unit. Write set: glossary module, vocabulary/book schemas, build hooks, the registry's independent
anchor-only option, gated Word row protection, unit/runtime tests, publication docs, CHANGELOG,
and this record. Rollback removes these opt-in hooks/module/schema fields and the Index marker
handling together; no unrelated numbering or optimization change is included.

## Initial checks and measured baseline

Own requirements-dev venv. Focused unit tests: 9 tests, 0.038s, OK. Synthetic real publication:
1 test, 20.466s, OK (HTML fragment walk, Word links/bookmarks and row markers, PDF page destinations).
The existing 14 cross-reference unit tests also pass. Fresh full checks and real-book proof follow.

Independent staging on book main `a5426bc` produced 466 Index glossary links, 493 glossary pointers
and 3,497 Index section locations. The v3.0.0 HTML has 466, 493 and 3,333 respectively. Running the
frozen `13d295b` builder's own functions also produces 3,497 locations. The delta is exactly 164
chapter/appendix introduction locations across 111 terms, with zero missing release locations.
These are supported by the frozen reference's documented inclusion of chapter intros; the
implementation retains them and reports the difference instead of forcing the release count.
Scripts and real output: `/tmp/codex-0053-evidence/stage.py`, `compare-scan.py`, `scan-delta.log`.

## Pending final evidence

Full-book builds, all-edition anchor audit, disabled sample byte identity, `make full` and CI
will be recorded before the review handoff. No Owner desktop Word check, publication or tag is run.
