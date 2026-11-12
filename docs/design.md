# Design contract

The visual language of the platform is data, not taste applied per pull request. One packaged token
document defines the colour roles, type roles, spacing and contrast floors that the portal, the book
HTML, the Typst/PDF edition and the DOCX edition must share.

**Status:** Phases 0 to 4 implemented on the `feat/design-tokens` branch. The portal, the book
stylesheet, the Typst theme and the DOCX reference document take their values from this contract;
the template exposes search, repository actions and a light/dark book theme. Release publication and
the sample upgrade remain owner-gated.

**Date:** 2026-11-12

## Source of truth

| Path | Purpose | License |
| --- | --- | --- |
| `tools/src/handbook_toolkit/design/tokens.json` | Semantic values for every surface | MIT, as toolkit code |
| `tools/src/handbook_toolkit/schemas/design-tokens.schema.json` | Shape contract for the token document | MIT, as toolkit code |
| `tools/src/handbook_toolkit/design.py` | Loader, role checks and WCAG contrast validation | MIT, as toolkit code |
| `tools/tests/test_design.py` | Completeness, contrast and packaging tests | MIT, as toolkit code |
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
- Native capabilities first. Web uses system font stacks and the book's pinned Quarto features;
  print keeps the already-approved OFL fonts.
- No action depends on hover. Keyboard and touch paths are the primary paths.

## Colour roles

All values are uppercase six-digit hex and every role declares a value for the three surface
families: light web, dark web and print.

| Role | Light web | Dark web | Print | Meaning |
| --- | --- | --- | --- | --- |
| `canvas` | `#F6F1E7` | `#141A1B` | `#FFFFFF` | Page background |
| `surface` | `#FFFDF8` | `#1C2526` | `#FFFFFF` | Cards, tables and raised areas |
| `text` | `#1D2A2C` | `#EBE6DA` | `#1D2A2C` | Body copy |
| `muted` | `#55666A` | `#A3B0B0` | `#55666A` | Secondary copy, captions and metadata |
| `heading` | `#1D2A2C` | `#EBE6DA` | `#1D2A2C` | Headings and structural emphasis |
| `accent` | `#0B5D5F` | `#6FCFC6` | `#0B5D5F` | Links, active controls and outlines |
| `accent_solid` | `#0B5D5F` | `#157875` | `#0B5D5F` | Filled surfaces: buttons, covers, table headers |
| `on_solid` | `#FFFFFF` | `#FFFFFF` | `#FFFFFF` | Text on a filled accent surface |
| `border` | `#DDD3C0` | `#33403F` | `#D9E2EC` | Rules, dividers and table borders |

Headings use the same near-black as body text on light and print; hierarchy comes from size, weight
and spacing rather than from a third hue. The dark scheme keeps the same relationship with a light
ink. This preserves the editorial character of the current portal and print editions instead of
introducing a separate heading colour.

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
| `body` | Handbook Sans (Liberation Sans) | Liberation Sans | 16 px | 10 pt | 1.65 | 72 characters |
| `display` | Handbook Sans (Liberation Sans) | Liberation Sans | 40 px | 21 pt | 1.15 | none |
| `code` | Handbook Mono (JetBrains Mono) | JetBrains Mono | 14 px | 9 pt | 1.5 | none |

Spacing uses a 4 px unit with 56 px section rhythm. Controls use a 6 px radius and cards 8 px.

The brand family is **Liberation Sans** (SIL OFL 1.1). The portal and the book self-host it as
subsetted WOFF2 files under the CSS name `Handbook Sans`; the PDF embeds the TTF; the DOCX names
**Arial**, which is metrically compatible, so a reader without Liberation Sans gets no layout shift.
JetBrains Mono remains the code family in every medium. The files ship in the toolkit and are listed
in `NOTICE.md`; no font is fetched from a third-party host. The web subsets carry renamed internal
names, keep the OFL text and URL in their name table, and are published together with their `OFL.txt`
files.

The web designs target a 60 to 75 character measure. Quarto renders the book content column and the
tools page applies `--measure`; the portal keeps its responsive card grid.

## Surface mapping

| Surface | How it consumes the contract |
| --- | --- |
| Portal | Generated `:root` variables in the single HTML page plus seven same-origin WOFF2 files |
| Book HTML | Generated `design-tokens.css` loaded before the layout stylesheet; dark values on `body.quarto-dark` and on the OS media query |
| PDF | Generated `design-tokens.typ` constants read by the Typst theme and print layout |
| DOCX | `generate_reference_docx.py` reads the tokens at generation time; Arial for body text and JetBrains Mono for code |

The Typst theme, the print layout and the DOCX reference no longer carry private palette constants.
The alert colours used by Quarto callouts remain component colours and are not part of the brand
palette.

## Changing the contract

- A new or changed colour role requires an entry for all three schemes, a declared contrast pair
  where the role carries text, and an approved owner decision for a new visual direction.
- A new or changed type role requires both a web and a print value; a font addition requires a prior
  rights review and a `NOTICE.md` entry.
- Renderers may not introduce a raw colour or size that is absent from the tokens. The conformance
  tests added in the next phase enforce that rule.
- Existing books keep their pinned toolkit until they upgrade through the documented path. A design
  change is not retroactive.
- Values that serve only one medium, such as a print rule colour, stay in the token document as an
  explicit per-scheme value rather than as a hidden constant in a renderer.

## Implemented and pending

Implemented on the branch: packaged tokens and contrast tests, generated portal CSS and self-hosted
WOFF2 assets, generated book stylesheet with a Quarto light/dark theme, Typst constants, DOCX style
values, portal source links, accent-insensitive search, book search and repository actions in the
template, and issue forms for corrections and proposals.

Pending, and deliberately not claimed here: the sample book upgrade and release, the catalog update,
the Pages deployment, the independent review record and the owner merge. Those steps run through the
repository's reviewed release path.
