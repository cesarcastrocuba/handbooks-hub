# Record — Documentation truth

**Decisions:** none new; `HUB-DEC-020`, `HUB-DEC-023`, `HUB-DEC-031` and `HUB-DEC-035` are cited as
evidence. **Recorded:** 2026-11-13. **Change:** `0030-documentation-truth`.
**Scope:** WP2a of `0027-audit-plan`: findings D1 to D4 for the documentation files listed below.
Documentation only; no code, `docs/decisions.md`, template content or worktree outside WP2a changed.

## What changed

| File | Old claim | New claim | Source of truth checked |
| --- | --- | --- | --- |
| `README.md` | Catalog lists `handbook-authoring-and-publishing` `v0.2.7` | Catalog lists `v0.4.1` | `catalog/catalog.json` (`latest_release.version`) |
| `README.md` | "Quarto, Graphviz, PDF and DOCX rendering belong to the future publication pipeline" and are not required | Rendering ships in the toolkit: `build-book` builds HTML, PDF, DOCX, Markdown and the source bundle, and needs Quarto `1.11.9` and Poppler `pdfinfo`; not required for the checks | `template/book/README.md` (seven-file build), `docs/publication-build.md` (requirements), `tools/pyproject.toml` (`0.9.1`) |
| `README.md` | "This repository does not … deploy a site, publish a release" | `portal-pages` builds and deploys the portal after a catalog change on `main`; `catalog-update` verifies the bytes, pushes a `catalog/<slug>-<tag>` branch and triggers `ci.yml`, and the Owner opens the pull request | `.github/workflows/portal-pages.yml`, `.github/workflows/catalog-update.yml`, `docs/catalog-automation.md` |
| `STATUS.md` | Next action 1: Owner deletes `handbook-template-dryrun-delete-me`; blocker repeats it | Both entries removed; the Phase 6 item is now next action 1 | WP2a brief: the Owner deleted the repository |
| `STATUS.md` | Licensing row cites sample `v0.2.7` as the current sample | Cites the published sample without a stale version, with `HUB-DEC-023` | `STATUS.md` sample row (`v0.4.1`), `docs/decisions.md` `HUB-DEC-023` |
| `docs/design.md` | Web "uses system font stacks"; seven WOFF2 files; alert colours "not part of the brand palette"; conformance tests "in the next phase"; a Pending list of work that is done | Web serves the packaged WOFF2 subsets (ten files: four sans, three serif, three mono); callout values live in `tokens.json` under `callout` and are part of the contract; `tools/tests/test_design_conformance.py` exists; the Pending list is replaced by an Implemented section naming the released versions | `tools/src/handbook_toolkit/design.py` (`FONTS`, `@font-face`), `tools/src/handbook_toolkit/render_data/fonts/` (ten `*.woff2`), `tools/src/handbook_toolkit/design/tokens.json` (`callout`), `tools/tests/test_design_conformance.py` |
| `docs/design.md` | Status says release publication and the sample upgrade "remain owner-gated" | Design shipped in toolkit `0.9.1`, template `1.4.1` and sample `v0.4.1` | `STATUS.md`, `tools/pyproject.toml`, `template/book/README.md` |
| `docs/publication-contract.md` | "Status: planned. No publication pipeline exists in the Phase 1 scaffold." | "Status: in force." `build-book` produces and verifies the artifact set | `docs/publication-build.md`, `catalog/catalog.json` (manifest and five asset links for `v0.4.1`) |
| `docs/publication-contract.md` | Heading "Manifest (planned shape)" | "Manifest shape" | `tools/src/handbook_toolkit/schemas/publication-manifest.schema.json` |
| `CONTRIBUTING.md` | Quarto and Graphviz "not needed until the future publication setup" | Checks need Python, `jsonschema` and `PyYAML` only; rendering needs Quarto `1.11.9` and Poppler `pdfinfo` and is not part of the checks | `docs/publication-build.md`, `requirements-dev.txt` |
| `docs/setup.md` | "Quarto/Graphviz/PDF/DOCX publication toolchain is **future publication setup**" | The render toolchain is the optional build in section 7; not required for the commands on the page | `docs/publication-build.md` |
| `docs/setup.md` | `build-book` exposes a "six-file directory" | Seven-file directory | `docs/publication-build.md`, `template/book/README.md` |
| `docs/setup.md` | Contributor row lists Graphviz among tools not needed | Lists Quarto, Poppler and PDF/DOCX tools; Graphviz is not part of the toolchain | `template/book/publishing/_quarto.yml`, `docs/publication-build.md` |
| `docs/operations-runbook.md` | Step 7 names Selawik and Liberation Sans | Names Handbook Sans and Handbook Serif (HTML/PDF), Source Sans 3 and Source Serif 4 (Word) and JetBrains Mono | `tools/src/handbook_toolkit/design/tokens.json` (`type.*` families), `render_data/typst/typst-show.typ`, `tools/scripts/generate_reference_docx.py` |
| `CONTRIBUTING.md` (review F1) | "The checks need only Python, `jsonschema` and `PyYAML`" | The checks need Python and the packages in `requirements-dev.txt`: the toolkit with `jsonschema` and `PyYAML`, plus `fonttools` and `brotli` for the font tests | `requirements-dev.txt`, `tools/tests/test_design.py` (`from fontTools.ttLib import TTFont`), `0027-audit-plan` known gap |
| `README.md` (review F1) | "Current validators need **Python only**" | The checks need Python and the packages in `requirements-dev.txt`; only the rendering tools are optional | `requirements-dev.txt`, `tools/tests/test_design.py` |
| `docs/setup.md` (review F1) | "`requirements-dev.txt` installs the editable local toolkit (`-e ./tools`) and its `jsonschema`/`PyYAML` dependencies" | Also lists `fonttools` and `brotli` for the font tests | `requirements-dev.txt` |

## Left unchanged, and why

Matches of `grep -rniE "future|planned|not yet|pending|will be|selawik|liberation"` that stay:

| Location | Why it stays |
| --- | --- |
| `docs/implementation-plan.md` (phase gates, "Planned book commands", Appendix A handoff mapping) | Dated Phase 1 plan and handoff appendix, not a current-status page; current state lives in `STATUS.md`. Rewriting phase history would fabricate what the plan said at the time |
| `docs/book-upgrade.md` (Selawik and Liberation Sans in `0.5.0` and `0.8.0` notes) | Historical per-version upgrade notes; they describe what changed in those releases, and `0.8.0` is the record of the font replacement |
| `docs/decisions.md` | Explicitly out of scope (coordinator-owned) |
| `docs/operations-runbook.md` "planned remediation" | Ordinary English about a future remediation, not a claim about current capability |
| `docs/portal.md` "planned topics are marked as planned" | Describes the portal's text policy, not the hub state |
| `docs/catalog-contract.md` "planned facets" | Describes how the portal marks empty facets |
| `docs/assumptions.md` A-08 "future books" | Generic forward-looking assumption, still open |
| `docs/setup.md` "profile … is not yet resolved from the installed package" | True for `validate-manuscript`: `cli.py` still requires an explicit `--profile`; `build-book` resolves the pin and section 7 says so |

## Deviation from the brief

The brief for D1 says the repository "opens catalog pull requests (`catalog-update`)". The workflow
does not open one: GitHub Actions is not permitted to create pull requests in this repository, so it
pushes the verified branch, triggers `ci.yml` and prints a compare URL. `docs/catalog-automation.md`
states this and the README now matches the workflow rather than the brief.

`STATUS.md` is normally written by the coordinator's status pull requests (`0027-audit-plan`). D2 was
assigned to this package by the brief, so the two rows above are the only `STATUS.md` changes.

## Verification

```text
PATH=/tmp/opencode/wp2venv/bin:$PATH make full
Ran 308 tests in 100.782s
OK
...
documentation links: OK
VERIFY (full): 6 check(s), 0 problem(s)
```

The environment's system Python is externally managed, so `requirements-dev.txt` was installed into a
disposable venv (`/tmp/opencode/wp2venv`) first; without it `make full` reports the known
`ModuleNotFoundError: fontTools` gap recorded in `0027-audit-plan`. Not run: `make check` separately
(it is a subset of `make full`) and any book artifact build. This change touches documentation only,
and `verify --full` covers the documentation link check. No rendered artifact changes, so no edition
preview applies.
