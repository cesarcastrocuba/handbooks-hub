# Evidence — hub scaffold

**Change:** `0001-hub-scaffold`
**Status:** Implemented, pending independent review and owner Gate 1
**Date:** 2026-11-06
**Scaffold commit:** `8162e916781670d32e1f927b1849911781d976f2`

## Environment

| Item | Value |
| --- | --- |
| OS | Linux, `/home/ubuntu/github/handbooks-hub` |
| Git | 2.43.0 |
| Python | 3.12.3 |
| `jsonschema` | 4.10.3 |
| `PyYAML` | 6.0.1 |
| `pytest` | Not installed; tests use `unittest` |
| Quarto | Not on `PATH`; not required in this phase |
| `pip` | Not available in the local interpreter; packaging install was not run locally |

## Files delivered

| Area | Files |
| --- | --- |
| Governance | `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `STATUS.md`, `NOTICE.md`, `CHANGELOG.md`, `LICENSE`, `LICENSE-CODE` |
| Contracts | `docs/architecture.md`, `docs/editorial-contract.md`, `docs/publication-contract.md`, `docs/catalog-contract.md`, `docs/decisions.md`, `docs/assumptions.md` |
| Plan | `docs/implementation-plan.md` |
| Profile | `profiles/standard/profile.yaml` |
| Schemas | `schemas/book.schema.json`, `schemas/catalog.schema.json`, `schemas/profile.schema.json` |
| Template | `template/book/README.md`, `AGENTS.md`, `book.yaml`, `manuscript/book.yml`, `manuscript/chapters/01-example.qmd` |
| Catalog | `catalog/catalog.json` |
| Toolkit | `tools/pyproject.toml`, `tools/README.md`, `tools/src/handbook_toolkit/*.py` |
| Tests | `tools/tests/support.py`, `test_book.py`, `test_catalog.py`, `test_cli.py`, `test_profile.py`, `test_repository.py`, `test_schemas.py` |
| CI | `.github/workflows/ci.yml`, `.github/pull_request_template.md` |
| SDD | `sdd/README.md`, `sdd/changes/0001-hub-scaffold/*` |
| Repository hygiene | `.gitignore`, `.gitattributes`, `.editorconfig`, `Makefile`, `requirements-dev.txt` |

## Commands and results

### 1. Fast checks

```bash
make check
```

Result: **PASS**

- 42 unit tests ran; `OK`.
- `verify`: 4 checks, 0 problems.
- Validated the empty catalog, the proposed standard profile and the template book descriptor.

### 2. Full checks

```bash
make full
```

Result: **PASS**

- Re-ran the 42 unit tests; `OK`.
- `verify --full`: 5 checks, 0 problems.
- Documentation-link check passed for every root/document/SDD Markdown file.

### 3. Individual validators

```bash
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . validate-catalog catalog/catalog.json
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . validate-profile profiles/standard/profile.yaml
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . validate-book template/book/book.yaml --full
PYTHONPATH=tools/src python3 -m handbook_toolkit version
```

Result: **PASS**; the three documents report `OK` and the version is `handbook-toolkit 0.1.0`.

### 4. Python compilation

```bash
python3 -m compileall -q tools
```

Result: **PASS** (exit 0).

### 5. Document parsing

```bash
python3 -c "import json, pathlib, yaml; ... "
```

Result: **PASS**; every JSON and YAML document parses, and every schema declares Draft 2020-12.

### 6. Repository isolation

```bash
git -C /home/ubuntu/github/solutions-architecture-handbook status --porcelain
ls -la /home/ubuntu/github/handbook-sample-01
```

Result: at initial inspection (15:32) the sample directory was empty. During this session a separate
session created its Git repository and two commits (observed HEAD
`bbcba3ef6fd2a3495de33dfcb1eac4ca5a697aa7`). This session only read it and made no writes. The
reference worktree is clean at `6a15cc211f65e148afdaa75c71a063a8084d1910` (branch
`release/v2.1-rc5`); the hub commands did not write to it.

### 7. Git state

```bash
git status --porcelain
git log --oneline --decorate
```

Result: clean tree after the evidence commit; three conventional commits on `main` (scaffold,
evidence and isolation correction).

## Negative cases covered by tests

The suite proves rejection of:

- duplicate catalog ids, slugs and release URLs;
- tag/version mismatch, mutable release URLs and invalid dates;
- unsorted catalog entries;
- duplicate profile element ids/titles and inconsistent closing order;
- invalid unit word ranges, labels without a period and required figures with a zero minimum;
- figure upscaling;
- non-exact toolkit pins and path traversal;
- missing reading order, missing chapters, duplicate entries, non-QMD entries and unknown groups;
- unlisted manuscript files and missing formats for an active book;
- broken or escaping documentation links.

## Checks not run

| Check | Reason |
| --- | --- |
| `pip install -e ./tools` and the installed console script | `pip` and `ensurepip` are not available in the local Python; CI has pip via `setup-python` |
| GitHub Actions CI | No remote GitHub repository was created, by explicit scope |
| Quarto/PDF/DOCX build | Not implemented in Phase 1; no Quarto on `PATH` |
| Portal build and artifact verification | Phase 4 |
| Sample repository verification | Sample repository was not modified in this session |
| Independent review | Pending; the implementer cannot self-review |

## Known gaps

- Schemas are resolved from `<root>/schemas`. Packaging the schemas inside the wheel is Phase 2 work;
  until then the toolkit is used from a hub checkout or with `--schemas`.
- The manuscript skeleton, references, artifact manifest and portal are contracts only.
- The standard profile is `proposed`, not approved.
- The sample repository scaffold was produced by a separate session; its review is separate from
  this hub review.
- The reference handbook was not migrated.

## Review handoff

Review the scaffold commit recorded above, then re-run:

```bash
make check
make full
```

Verify that this session wrote nothing outside the hub, that the reference worktree is clean and that
no generated artifact, deployment, release or GitHub repository was created. Review the sample
repository in its own lane.
