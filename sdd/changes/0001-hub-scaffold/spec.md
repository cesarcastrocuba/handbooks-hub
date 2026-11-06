# Spec — hub scaffold

**Status:** Proposed
**Change:** `0001-hub-scaffold`

## Deliverables

| ID | Deliverable | Location | State |
| --- | --- | --- | --- |
| D1 | Local Git repository on `main` | `.git/` | Done |
| D2 | Governance and repository map | `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `STATUS.md`, `NOTICE.md` | Done |
| D3 | Architecture and contracts | `docs/architecture.md`, `editorial-contract.md`, `publication-contract.md`, `catalog-contract.md` | Done |
| D4 | Decision log and assumptions | `docs/decisions.md`, `docs/assumptions.md` | Done |
| D5 | Phased implementation plan | `docs/implementation-plan.md` | Done |
| D6 | Proposed standard profile | `profiles/standard/profile.yaml` | Done, proposed |
| D7 | JSON schemas | `tools/src/handbook_toolkit/schemas/*.json` (package data) | Done |
| D8 | Minimal book template | `template/book/` | Done; Phase 2 completes |
| D9 | Empty catalog | `catalog/catalog.json` | Done |
| D10 | Toolkit 0.1.0 | `tools/` | Done |
| D11 | Tests | `tools/tests/` | Done, 42 at scaffold; 46 after `0002`; 48 after `0003`; 52 after `0004` |
| D12 | Basic CI and PR template | `.github/` | Done |
| D13 | SDD record | `sdd/changes/0001-hub-scaffold/` | This record |
| D14 | Independent review | Review comments | Pending |

## Interfaces

### Toolkit CLI

```text
handbook-toolkit [--root PATH] [--schemas PATH] <command>

  verify [--full]
  validate-catalog [PATH]
  validate-profile [PATH]
  validate-book [PATH] [--full]
  version
```

Exit codes: `0` all checks pass; `1` validation problems or unreadable input; `2` usage error from
`argparse`.

### Book descriptor

A YAML document matching the packaged `book.schema.json` with:

- exact `toolkit` and `profile.version`;
- `manuscript.root` and `manuscript.reading_order` relative to the book root;
- `publication.formats` from `html`, `pdf`, `docx`;
- `catalog.slug`, `catalog.categories` and `catalog.summary`.

### Reading order

A YAML mapping with optional `front`, `chapters`, `back`, `appendices` and `references` lists. Entries
are `.qmd` paths relative to the manuscript root. Every listed file must exist; full mode requires
every `.qmd` file to appear exactly once and at least one chapter.

## Acceptance criteria

1. `make check` passes: 52 unit tests and five repository validations.
2. `make full` passes: adds documentation-link checks.
3. Negative tests prove rejection of:
   - duplicate catalog id, slug and release URL;
   - tag/version mismatch and mutable release URLs;
   - invalid dates and unsorted catalog entries;
   - duplicate profile element ids/titles and inconsistent closing order;
   - invalid word ranges, labels, required-figure minimum and upscaling;
   - non-exact toolkit pins and path traversal;
   - missing reading order, missing chapter, duplicate entries, non-QMD entries, unknown groups,
     unlisted manuscript files and missing publication formats for an active book;
   - broken or escaping documentation links.
4. This session writes no file outside `handbooks-hub`. The reference worktree remains clean; the
   sample repository was scaffolded concurrently by a separate session and is out of scope here.
5. The template validates in full mode.
6. The catalog is valid while empty.
7. The repository is clean after the evidence commit.
8. Independent review has no open Critical or Major finding.

## Invariants

- The toolkit is deterministic: no timestamps, no network, sorted error output.
- The toolkit contains no manuscript prose.
- A book pins exact versions; ranges are rejected.
- Catalog entries point to immutable tags and release assets.
- Generated artifacts are never committed.
- The reference handbook is not a dependency.

## Out of scope

- Manuscript skeleton validation, reference resolution, artifact manifest validation and portal
  generation.
- A working Quarto build.
- The sample book and its editorial gates. A separate session has scaffolded the sample repository;
  this change does not review or modify it.
- GitHub repository creation, Pages, Releases and migration.

## Assumptions

See `docs/assumptions.md`. The most consequential are A-01 (hub/book split), A-03 (Quarto 1.11.9
toolchain) and A-06 (section closure fits most chapters).
