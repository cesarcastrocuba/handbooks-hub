# Record — Audit of the design work and quality plan

**Decisions:** `HUB-DEC-036` to `HUB-DEC-040` (new). **Recorded:** 2026-11-13.
**Change:** `0027-audit-plan`. **Audited state:** hub `main` at `0db3f69`, toolkit `0.9.1`,
template `1.4.1`, sample `v0.4.1`.

This record is the brief for the work packages below. Each work package has its own change record
and pull request; this file is not rewritten when they land.

## Owner words, verbatim, 2026-11-13

- "quisiera que realices una auditoría del trabajo realizado y si encuentras puntos a mejorar los
  indiques […] quisiera que realices un buen plan por si hay mejoras a realizar para que opencode lo
  resulva y codex revise y mergee […] quiero que sea esto algo profesional."
- On animation, the Owner chose: "CSS nativo, sin librerías". On the Word viewer: "Word de escritorio
  (Windows)".
- "sigue el plan […] la idea es que termines todo el plan, yo iré a dormir, no hace falta que
  verifique, confío en tu trabajo, mañana verificaré cuando esté todo terminado, autorizo a todas las
  ejecuciones y permisos que necesites […] quiero que todo esté actualziado en la documentación y que
  sea refactorizado todo el código […] quiero un producto de calidad […] además que sea la base para
  que pueda migrar mañana mi libro solutions architecture"

### Translation (not verbatim)

- "I would like you to audit the work done and point out what can be improved […] and write a good
  plan so that OpenCode resolves it and Codex reviews and merges […] I want this to be professional."
- Animation: "native CSS, no libraries". Word viewer: "desktop Word (Windows)".
- "Follow the plan […] the idea is that you finish the whole plan; I am going to sleep, I do not need
  to verify, I trust your work, I will verify tomorrow when everything is finished; I authorize every
  execution and permission you need […] I want all documentation up to date and the code refactored
  […] I want a quality product […] and the base on which I can migrate my solutions architecture
  book tomorrow."

## Verdict

No process violation was found in hub pull requests 27 to 46 or sample pull requests 16 to 24: each
had an independent review with real findings, tags point to commits on `main`, and earlier editions
stay published and unchanged.

There is technical debt with one common cause: the toolkit repairs Quarto output **after** rendering
(regular expressions over HTML, XML surgery over DOCX) instead of asking Quarto and Pandoc for the
result natively. The Word edition was reviewed only in LibreOffice, where its defects do not show.

## Findings

Severity: **A** reader-visible defect, **B** fragile or misleading, **C** hygiene. Evidence was taken
from the published `v0.4.1` assets and from `main` at `0db3f69`.

### Word edition

| ID | Sev | Finding | Required outcome |
| --- | --- | --- | --- |
| W1 | A | Callout titles are not bold in Word. `word/styles.xml` defines every callout style twice with the same `w:styleId` (10 duplicates). `docx-callouts.lua` passes the style **ID** (`CalloutNoteTitle`) as `custom-style`; Pandoc matches by style **name** (`Callout Note Title`), does not find it and appends a second, plain style. Word applies the last definition, LibreOffice the first. `_colour_callout_title` in `build.py` is a patch over this | The filter uses the real style names. The colour patch is removed. No duplicate `w:styleId`; every style used is defined exactly once |
| W2 | A | The List of Tables is static paragraphs with links and no page numbers: `_replace_docx_list_of_tables` deletes the field Pandoc emits and writes `TOC1` paragraphs | Lists are real Word fields with a cached result, generalised to figures and listings |
| W3 | A | "Contents" is empty outside Word (LibreOffice, previewers): the TOC field has no cached result | Same mechanism as W2 |
| W4 | A | Table stripes are written as `w:shd` inside `w:trPr` (24 times), which the OOXML schema does not allow; LibreOffice ignores them | Banding comes from the table style (`w:tblStylePr`) in the reference document; the row-level writer is removed |
| W5 | B | The document names "Source Sans 3" and "Source Serif 4" but neither embeds them nor declares fallbacks in `fontTable.xml` | `fontTable.xml` entries with `w:altName` fallbacks |
| W6 | B | Six colours are hard-coded in `build.py` (for example `D9E2EC`, `0B5D5F`), bypassing the tokens; the conformance test does not read that file | Values come from `design.docx_values()`; the conformance test covers every toolkit module |
| W7 | C | ElementTree rewrites lose namespace prefixes (`ns0:`); the callout box overflows the right margin in LibreOffice | Registered namespaces; box width within the text column |
| W8 | B | DOCX tests are `assertIn("string", xml)`; they cannot detect W1, W3 or W4 | Structural validators and a LibreOffice smoke conversion in CI |

### Book HTML

| ID | Sev | Finding | Required outcome |
| --- | --- | --- | --- |
| H1 | A | `tables.html` shows two rules and an empty band under the title: the bottom border of `#title-block-header` plus `border-top`, margin and padding of `.list-of-tables` in `BOOK_CHROME` (`design.py`) | One rule, no empty band |
| H2 | B | `tables.html` is produced by cloning `index.html` and applying eight `re.sub` calls; the sidebar link is injected by a regular expression that looks for the literal text "Document Control" in every page | The list is a generated `.qmd` page rendered by Quarto |
| H3 | B | The book uses `cosmo` for light and `darkly` for dark, two different themes, corrected by about 40 `!important` rules held in a 210-line Python string | A Quarto theme generated from the tokens, the same base in both modes |
| H4 | B | No favicon, no social cards (Open Graph, Twitter), no `description` | Native Quarto options |
| H5 | B | The first page of a book is "Document Control"; the sidebar is flat; no page states which edition is being read | Cover page, parts, edition footer |
| H6 | B | No figure exists in the sample or in the real-build tests: the image path (HTML, PDF, DOCX, `book.md`) has never been exercised. The reference handbook that will be migrated has 121 figures and `lof: true` | A figure in the template and the sample, a List of Figures in every edition, a real-build test with a figure |

### Portal

| ID | Sev | Finding | Required outcome |
| --- | --- | --- | --- |
| P1 | B | HTML, CSS and JavaScript are Python strings in `portal.py`; guide text lives in code | Templates and text as files; later a Quarto website |
| P2 | C | With one book the library fills half the row; no favicon or social cards | Layout for one or two books; metadata |

### Documentation truth

| ID | Sev | Finding |
| --- | --- | --- |
| D1 | A | `README.md` says the catalog lists `v0.2.7` (it lists `v0.4.1`), that "Quarto, PDF and DOCX rendering belong to the future publication pipeline", and that the repository does not deploy a site or publish a release |
| D2 | A | `STATUS.md` says the throwaway repository still exists (it was deleted); the licensing row cites sample `v0.2.7` |
| D3 | A | `docs/design.md` lists as pending work that is done, says the web uses system font stacks (it serves bundled fonts), counts seven WOFF2 files (there are ten), announces conformance tests "in the next phase" (they exist) and says callout colours are not part of the palette while defining them |
| D4 | A | `docs/publication-contract.md` says "Status: planned"; `CONTRIBUTING.md` and `docs/setup.md` mention a "future publication" setup; `docs/operations-runbook.md` names Selawik and Liberation Sans |
| D5 | B | The design preview page lives outside the repository in a tool's private directory and is out of date |
| D6 | B | No change record covers `HUB-DEC-032` to `HUB-DEC-035`, and there is no rights review with hashes for Source Sans 3 and Source Serif 4; the step from the original fonts to the renamed ones is not scripted |

### Process and hygiene

| ID | Sev | Finding | Required outcome |
| --- | --- | --- | --- |
| S1 | B | Four release rounds in about 26 hours: the Owner saw each result only after it was published, and each correction cost another immutable edition | A preview artifact before publishing |
| S2 | C | Development dependencies are version ranges; `ci.yml` uses actions by tag while the other workflows pin a commit | Pinned with hashes and by commit |
| S3 | C | 57 merged remote branches, 26 review worktrees under `/tmp`, `build.py` at 1,606 lines | Clean-up; `build.py` split into modules |

## Work packages

One pull request per numbered item unless stated. The implementer writes the change record named
here. `STATUS.md` and `docs/decisions.md` are written only by the coordinator's status pull requests,
so that parallel branches do not conflict.

| WP | Change record | Scope |
| --- | --- | --- |
| WP0 | `0028-edition-preview` | CI job `edition-preview` that builds the template book with the pull request's toolkit and uploads HTML, PDF, DOCX and screenshots; Owner acceptance checklist in the runbook |
| WP1 | `0029-docx-native-fields` | W1 to W8 and H1 |
| WP2 | `0030-documentation-truth` | D1 to D6, the documentation drift guard in `verify --full`, the `design-preview` command, S2 |
| WP3 | `0031-native-rendering` | H2, H3, P1 and the `build.py` split |
| WP4 | `0032-reading-experience` | H4, H5, H6, P2, native CSS motion, accessibility |
| WP5 | `0033-portal-quarto` | The portal as a generated Quarto website, after WP3 |

### WP1 design constraints

- **Lists are one registry**, for example
  `LISTS = (("tbl", "List of Tables", "T"), ("fig", "List of Figures", "F"), ("lst", "List of Listings", "L"))`.
  A list is emitted only when the book has entries of that kind.
- Next to each caption the toolkit inserts a hidden `TC "<caption>" \f <letter> \l 1` field. The
  list is a `TOC \h \z \f <letter>` field whose **cached result** is the entries, each a hyperlink
  to the caption bookmark with a `PAGEREF <bookmark> \h` field. "Contents" gets a cached result from
  headings 1 to 3 in the same way. `\f` is used instead of `\t "Style,1"` because the `\t` separator
  depends on the Windows list separator. `w:updateFields` is already set in `settings.xml`, so Word
  recalculates page numbers on open.
- Validators in `artifacts.py::inspect_payload` for the `docx` role: unique `w:styleId`; every
  `w:pStyle`, `w:rStyle` and `w:tblStyle` used is defined; `w:trPr` holds only schema children;
  `begin`/`separate`/`end` field characters are balanced; every `w:anchor` targets an existing
  bookmark.

### WP3 acceptance criteria

- Theme: the same screenshots as today with fewer than five `!important` rules; remaining CSS lives
  in a packaged `.css` file, not in a Python string.
- Lists: sidebar, breadcrumbs, dark mode and search work on the list pages with no edit to rendered
  HTML; `_inject_table_index`, `_add_tables_navigation` and `SIDEBAR_DOCUMENT_CONTROL` are removed.
- Each item starts with a proof of concept. If it fails its criterion, the current behaviour stays
  and the change record says why.

### WP4 motion rules

Native CSS only: `@view-transition { navigation: auto }`, reveal with `animation-timeline: view()`
inside `@supports`, a reading progress bar with `animation-timeline: scroll()`, and transitions on
focus, buttons, covers and `<details>`. Everything sits inside
`@media (prefers-reduced-motion: no-preference)`. No script and no external resource is added.

## Release order

1. WP0 and WP2 in parallel with WP1.
2. WP1 → toolkit `0.9.2`, template `1.4.2`, sample `v0.4.2`.
3. WP3 and WP4 → toolkit `0.10.0`, template `1.5.0`, sample `v0.5.0`.
4. WP5.

## Known gaps

- Nobody in this run can open the DOCX in desktop Word. W1 is proven in the XML and matches what the
  Owner saw; W4 and W7 were checked only in LibreOffice. The Owner waived the pre-release check for
  this run and verifies afterwards (`HUB-DEC-040`).
- Whether a `TOC \f` field with a cached result behaves as intended in Word is confirmed only by
  structure and by LibreOffice until the Owner opens the file.
- Whether a Sass or brand theme reproduces the current design in Quarto `1.11.9` is unknown until the
  WP3 proof of concept.
- Local `make full` fails with `ModuleNotFoundError: fontTools` in an environment without
  `requirements-dev.txt`; CI installs it and passes.
