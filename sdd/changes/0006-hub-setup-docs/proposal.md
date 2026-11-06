# Proposal — hub setup onboarding

**Status:** Proposed
**Change:** `0006-hub-setup-docs`
**Branch:** `docs/hub-setup`

## Context

The approval record is integrated on `main`, but the repository does not yet give users complete
installation and configuration instructions. The sample integration also showed an important test
trap: an external temporary venv does not prove an in-repo `.venv` quickstart, and a scanner can
reject ignored in-repo environments.

## Scope

- Add [`docs/setup.md`](../../../docs/setup.md) covering:
  - readers who need no installation;
  - contributors and maintainers who need Git, Python, pip, venv and optionally make;
  - the tested Linux path and the limits of macOS/Windows native testing;
  - in-repo `.venv` creation, `requirements-dev.txt`, `make` checks and the no-make path;
  - troubleshooting for missing pip, missing venv/ensurepip, externally managed Python, missing make
    and the in-repo venv/scanner distinction.
- Link a concise README quickstart to the guide.
- Update `CONTRIBUTING.md` to point at the guide.
- Add pinned-toolkit installation instructions and a VCS `requirements.txt` to the book template.
- Keep Quarto/Pandoc/Graphviz/PDF/DOCX publication setup explicitly future and separate.
- Update current status to “Phase 1 integrated; Phase 2 next” without per-commit evidence loops.

## Verification

- Exact documented hub quickstart: fresh clone, in-repo `.venv`, install
  `requirements-dev.txt`, `make check`, `make full`.
- Exact no-make path in the same environment.
- Template book: copy outside the hub checkout, in-repo `.venv`, install the pinned VCS toolkit and
  run `handbook-toolkit --root . validate-book`.
- No Quarto build or artifact claim.
- Local checks plus a dispatched CI run at the reported branch HEAD.

## Non-goals

- Approving a pilot, publishing, releasing or deploying.
- Installing Quarto or claiming rendered artifacts.
- Changing the toolkit, profile or book schema contracts.
- Documenting untested native Windows command sequences.
