# Change 0085 — Portal guides, mobile buttons, cover links and GitHub stars

Implementer Claude; reviewer a different agent. Branch `feat/portal-guides-stars` from main
`9649ba7`. Ships with toolkit `0.16.1`, whose tag needs the Owner's approval. Web only: the PDF and
Word editions do not change (the Typst body size keeps its value), so no desktop Word check is
needed for this change.

## Owner requests (2026-11-27)

- On a phone, "Browse the library" and "Create your handbook" touch on the home page, and the
  buttons of other pages, such as `create.html`, do the same.
- A click on a book cover opens the book's web edition.
- The guide pages (how the platform works, create your handbook and the others) must be very
  visible, easy to understand and show what the platform can do.
- GitHub stars for the hub, the template and the books (issue 141, decided 2026-11-26:
  count baked at build, after 6.0.0), recorded as `HUB-DEC-046`.
- Issue 142: the PDF body size from the token; two long lines.

## Changes

- **Buttons.** `portal.css`: a paragraph of Markdown buttons (`p:has(> .btn)`) and an `.actions`
  group are flex rows with a 10 px gap, 44 px tall buttons, and on a phone each button takes a
  full row. The rule is a class, so every page is covered, not only the two named ones.
- **Cover link.** `card.html` and the legacy `portal.py` card wrap the cover in a link to the
  reading site. It has `tabindex="-1"` and `aria-hidden="true"`: the visible "Read handbook" link
  stays the single keyboard and screen-reader target for the same URL.
- **Guide pages.** `how-it-works.qmd`, `create.qmd`, `publishing.qmd` and `contribute.qmd` are
  rewritten as cards: the five editions, eight things the platform does, who owns what, the steps
  with who acts in each, the repository layout and the local commands. The home page gains "What
  the platform does" after the library. Icons are inline SVG (`portal_markup.ICONS`) in
  `currentColor`, because the Inter web subset has no check mark or star glyph. Every claim was
  checked against the template README, `docs/publication-build.md` and the change records; no new
  claim was invented.
- **Stars.** New `stars.py`: `github_repository`, `star_count`, `compact`, `star_link`. The count
  comes from `HANDBOOK_STAR_COUNTS` (JSON) or, with `HANDBOOK_STARS=fetch`, from
  `api.github.com/repos/<owner>/<name>` with the workflow token; any failure gives no number.
  Portal header (`portal_quarto.hub_star_item`, replacing the plain "GitHub" item, which pointed
  at the same URL), each card (`portal_markup.card`) and each reading site
  (`reading_site._add_star_link`). Quarto drops an `aria-label` on navbar items, so the navbar
  text itself reads "★ Star · N"; card links carry an `aria-label` with the repository and count.
  `portal-pages` sets `HANDBOOK_STARS=fetch` and runs daily at 04:23 UTC; the deploy gate accepts
  `schedule`. The template's `release.yml` reads the count with `gh api` before the build, so the
  build step never holds the write-scoped token.
- **Issue 142.** `typst_preamble()` emits `hb-body-size` from `type.body.print_size_pt`;
  `handbook-typst.typ` uses it. The Quarto show partial cannot read the constant, so
  `test_design_conformance` checks that its two literal sizes equal the token. `docs/design.md`
  and `STATUS.md` paragraphs reflowed. The catalog's missing link to `EXTRAS-SHA256SUMS.txt` is a
  schema change and stays open in issue 142.
- Docs: `docs/operations-runbook.md` (GitHub star counts), `template/book/README.md` (reader
  navigation), `docs/decisions.md` (`HUB-DEC-046`), `CHANGELOG.md`.

## Evidence

Hub venv (`requirements-dev.txt`, Playwright and Chromium), Python 3.12, Quarto 1.11.9:

- Local portal build with `HANDBOOK_STARS=fetch` and a token: both cards carry
  `aria-label="Star cesarcastrocuba/<repo> on GitHub, 0 stars"`, the navbar reads "★ Star · 0".
- Playwright, 390 and 1280 px: the gap between consecutive buttons is 10 px on index,
  how-it-works, create, publishing and contribute; `scrollWidth` equals the viewport. Screenshots
  were compared at both widths; the five-item rows fit one row at 1280 px and stack in one column
  on a phone.
- Tests added: `test_stars` (8), `test_portal.QuartoPortalTests` (cover link and star link, guide
  components, buttons never touch at 1280/390/320 px with 44 px targets, a cover click opens the
  reading site), `test_portal_pages_workflow` (daily rebuild, deploy gate with `schedule`),
  `test_design_conformance` (body size from the token).
- `make check`: 640 tests, 1 failure:
  `test_reading_site.NativeMotionBrowserTests.test_motion_finishes_once_reduced_motion_is_static_and_progress_reaches_end`
  (`'static' != 'relative'`). This change does not touch `render_data/html/`; the class passed in
  three repeated runs right after, and the same test failed once intermittently in change `0083`.
  Recorded as flaky, not fixed here.
