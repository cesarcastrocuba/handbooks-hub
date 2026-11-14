# Design contract

The visual language of the platform is data, not taste applied per pull request. One packaged token
document defines the colour roles, type roles, spacing and contrast floors that the portal, the book
HTML, the Typst/PDF edition and the DOCX edition must share.

**Status:** Phases 0 to 4 implemented, with the 0.9 design polish adding compact web chrome, cream Word pages, unified callout boxes and table stripes. The portal, the book
stylesheet, the Typst theme and the DOCX reference document take their values from this contract;
the template exposes search, repository actions and a light/dark book theme. The design shipped in
toolkit `0.9.1` and template `1.4.1`, and sample `v0.4.1` is published with it.

**Date:** 2026-11-13

## Source of truth

| Path | Purpose | License |
| --- | --- | --- |
| `tools/src/handbook_toolkit/design/tokens.json` | Semantic values for every surface | MIT, as toolkit code |
| `tools/src/handbook_toolkit/schemas/design-tokens.schema.json` | Shape contract for the token document | MIT, as toolkit code |
| `tools/src/handbook_toolkit/design.py` | Loader, role checks and WCAG contrast validation | MIT, as toolkit code |
| `tools/tests/test_design.py` | Completeness, contrast and packaging tests | MIT, as toolkit code |
| `tools/tests/test_design_conformance.py` | Conformance of every generated surface with the tokens | MIT, as toolkit code |
| `docs/design.md` | This contract and its rationale | CC BY-SA 4.0 |

The tokens ship inside the installed toolkit package. A book receives them with its pinned toolkit
and never imports a hub checkout or copies a shared stylesheet.

## Principles

- Reading comes before decoration. Long-form text targets a 60 to 75 character measure, generous
  line height and an unambiguous heading hierarchy.
- One action leads. The portal offers one primary path per audience, and every book page offers
  reading, search, source and correction actions.
- A role keeps its meaning on every surface. Accent marks interaction, heading marks structure,
  canvas marks the platform.
- No borrowed identity. Values are original; no external theme catalogue, brand stylesheet or
  hosted design asset enters the product.
- Native capabilities first. Web uses the packaged WOFF2 subsets and the book's pinned Quarto
  features; print embeds the same approved OFL families.
- No action depends on hover. Keyboard and touch paths are the primary paths.

## Colour roles

All values are uppercase six-digit hex and every role declares a value for the three surface
families: light web, dark web and print.

| Role | Light web | Dark web | Print | Meaning |
| --- | --- | --- | --- | --- |
| `canvas` | `#F6F1E7` | `#141A1B` | `#F6F1E7` | Page background |
| `surface` | `#FFFDF8` | `#1C2526` | `#FFFDF8` | Cards and raised areas |
| `table_stripe` | `#F2ECE0` | `#1F2A2B` | `#F2ECE0` | Alternate table rows |
| `text` | `#1D2A2C` | `#EBE6DA` | `#1D2A2C` | Body copy |
| `muted` | `#55666A` | `#A3B0B0` | `#55666A` | Secondary copy, captions and metadata |
| `heading` | `#1D2A2C` | `#EBE6DA` | `#1D2A2C` | Headings and structural emphasis |
| `accent` | `#0B5D5F` | `#6FCFC6` | `#0B5D5F` | Links, active controls and outlines |
| `accent_solid` | `#0B5D5F` | `#157875` | `#0B5D5F` | Filled surfaces: buttons, covers, table headers |
| `on_solid` | `#FFFFFF` | `#FFFFFF` | `#FFFFFF` | Text on a filled accent surface |
| `border` | `#DDD3C0` | `#33403F` | `#D9E2EC` | Rules, dividers and table borders |
| `code` | `#F1F3F5` | `#1B2426` | `#F1F3F5` | Code and licence blocks |

Headings use the same near-black as body text on light and print; hierarchy comes from size, weight
and spacing rather than from a third hue. The dark scheme keeps the same relationship with a light
ink. This preserves the editorial character of the current portal and print editions instead of
introducing a separate heading colour.

| `callout` | Accent | Tint |
| --- | --- | --- |
| Note | `#0065B3` | `#EFF6FC` |
| Tip | `#107C10` | `#F1FAF1` |
| Warning | `#D83B01` | `#FDF3F0` |
| Important | `#5C2D91` | `#F5F0FA` |
| Review | `#55666A` | `#F2F1ED` |

The `review` role is opt-in: a callout carries the `review` class (for example
`::: {.callout-note .review title="Review Checklist"}`) and all three renderers use the neutral
accent and tint instead of the note blue. Tables inside a callout never receive the alternating
stripe; their rows keep the callout tint.

Web, PDF and DOCX use the same callout accent/tint values. The PDF and DOCX page canvas is
`#F6F1E7`, the same paper tone as the reading site.

## Contrast policy

Every foreground/background pair used for text is declared in the token document with the schemes
it serves and a minimum ratio. The loader rejects a declaration below the WCAG 2.2 AA floor of
4.5:1 for normal text, and the test suite recomputes each ratio from the token values.

| Pair | Schemes | Measured |
| --- | --- | --- |
| `text` on `canvas` | light, dark, print | 13.14:1, 14.13:1, 14.79:1 |
| `text` on `surface` | light, dark | 14.55:1, 12.57:1 |
| `muted` on `canvas` | light, dark, print | 5.34:1, 7.87:1, 6.01:1 |
| `muted` on `surface` | light, dark | 5.91:1, 7.00:1 |
| `heading` on `canvas` | light, dark, print | 13.14:1, 14.13:1, 14.79:1 |
| `accent` on `canvas` | light, dark, print | 6.80:1, 9.57:1, 7.65:1 |
| `on_solid` on `accent_solid` | light, dark, print | 7.65:1, 5.28:1, 7.65:1 |

These figures cover declared token pairs only. They do not certify a rendered page, which still needs
a human review of real components, disabled states, focus rings, images and overlays.

Two accent roles are deliberate. `accent` is the link and outline colour, so it stays legible on
both canvases. `accent_solid` is the fill of buttons, covers and table headers and always pairs with
`on_solid`. In dark mode the solid stays deep enough for a white label (5.28:1) and still separates
from the canvas (3.33:1); using the light link accent as a fill would have forced a dark label and
lost that separation.

## Type and layout roles

| Role | Web family | Print family | Web size | Print size | Line height | Measure |
| --- | --- | --- | --- | --- | --- | --- |
| `body` | Handbook Sans (Source Sans 3) | Handbook Sans | 15 px | 10 pt | 1.55 | 68 characters |
| `display` | Handbook Serif (Source Serif 4) | Handbook Serif | 34 px | 21 pt | 1.15 | none |
| `code` | Handbook Mono (JetBrains Mono) | JetBrains Mono | 13 px | 9 pt | 1.5 | none |

Spacing uses a 4 px unit with 56 px section rhythm. Controls use a 6 px radius and cards 8 px.

The brand pairing is **Source Sans 3** for text and **Source Serif 4** for display headings, both
SIL OFL 1.1. The portal and the book self-host subsetted WOFF2 files under the CSS names `Handbook
Sans` and `Handbook Serif`; the PDF embeds the renamed TTFs; the DOCX names the upstream families
**Source Sans 3** and **Source Serif 4**, so a reader with those fonts installed gets the intended
rendering without distributing a modified binary through Word. JetBrains Mono remains the code
family in every medium. The files ship in the toolkit and are listed in `NOTICE.md`; no font is
fetched from a third-party host. The web subsets carry renamed internal names, keep the OFL text and
URL in their name table, and are published together with their `OFL.txt` files.

The web designs target a 60 to 75 character measure. Quarto renders the book content column and the
tools page applies `--measure`; the portal keeps its responsive card grid.

## Surface mapping

| Surface | How it consumes the contract |
| --- | --- |
| Portal | Generated `:root` variables in the single HTML page plus the ten same-origin WOFF2 files |
| Book HTML | Generated `design-tokens.css` loaded before the layout stylesheet; dark values on `body.quarto-dark` and on the OS media query |
| PDF | Generated `design-tokens.typ` constants read by the Typst theme and print layout |
| DOCX | `generate_reference_docx.py` reads the tokens at generation time; Source Sans 3 for body text, Source Serif 4 for headings and JetBrains Mono for code |

The Typst theme, the print layout and the DOCX reference no longer carry private palette constants.
The callout accent and tint values are defined in the token document under `callout`, with a light,
dark and print entry for each role, so they are part of the contract like every other colour role.
Web, PDF and DOCX read them from there; they are not a separate component palette.

## Word layout and indexes

The Word post-processor is isolated from publication orchestration. It works on parsed OOXML.
The reference generator and Pandoc callout filter obtain human-readable style names from
design.docx_callout_styles(), so titles inherit their bold face and token color from one style
definition. Callout boxes use a single non-splitting row within the text column.

Table stripes live in the reference style's band1Horz/band2Horz conditionals. Plain tables inside
callouts have no banding. The toolkit writes no row-level shading. Print colors in toolkit Python
come from design.docx_values(); the conformance gate scans every toolkit module.

Contents and caption lists are complex fields with cached hyperlinks. One registry covers tables,
figures and listings. Hidden caption TC fields select entries with portable field identifiers;
the list uses TOC with its field-identifier switch, not a localized style-list separator.
When pagination is unknown, cached entries contain only the linked title, with no tab or PAGEREF
field. Updating the outer TOC field regenerates the paginated result. Bookmark normalization preserves internal links. Empty lists are omitted.

Word font declarations include single-name alternate-font chains: Source Sans 3 → Segoe UI →
Calibri → Arial, Source Serif 4 → Georgia → Cambria, and JetBrains Mono → Consolas → Courier New.
An altName represents one alternate name, not a CSS fallback list; actual substitution remains
the viewer's choice. No font binary is embedded in the DOCX.

## Changing the contract

- A new or changed colour role requires an entry for all three schemes, a declared contrast pair
  where the role carries text, and an approved owner decision for a new visual direction.
- A new or changed type role requires both a web and a print value; a font addition requires a prior
  rights review and a `NOTICE.md` entry.
- Renderers may not introduce a raw colour or size that is absent from the tokens. The conformance
  tests in `tools/tests/test_design_conformance.py` enforce that rule on every generated surface.
- Existing books keep their pinned toolkit until they upgrade through the documented path. A design
  change is not retroactive.
- Values that serve only one medium, such as a print rule colour, stay in the token document as an
  explicit per-scheme value rather than as a hidden constant in a renderer.

## Implemented

Implemented and released in toolkit `0.9.1`, template `1.4.1` and sample `v0.4.1`: packaged tokens
and their contrast tests, generated portal CSS and self-hosted WOFF2 assets, generated book
stylesheet with a Quarto light/dark theme, Typst constants, DOCX style values, portal source links,
book search and repository actions in the template, and issue forms for corrections and proposals.
The catalog lists the release and `portal-pages` serves the portal built from it.
