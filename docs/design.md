# Design contract

The visual language of the platform is data, not taste applied per pull request. One packaged token
document defines the colour roles, type roles, spacing and contrast floors that the portal, the book
HTML, the Typst/PDF edition and the DOCX edition must share.

**Status:** Phase 0 of the unified design change. The contract, its schema and the contrast tests are
in place. Renderers do not consume the tokens yet; generation from them is the next phase, so this
document records intent plus validated starting values, not a claim that every surface already
matches.

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
| `accent` | `#0B5D5F` | `#6FCFC6` | `#0B5D5F` | Links, active controls and primary actions |
| `on_accent` | `#FFFFFF` | `#0C1A1A` | `#FFFFFF` | Text on an accent background |
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
| `on_accent` on `accent` | light, dark, print | 7.65:1, 9.69:1, 7.65:1 |

These figures cover declared token pairs only. They do not certify a rendered page, which still needs
a human review of real components, disabled states, focus rings, images and overlays.

## Type and layout roles

| Role | Web family | Print family | Web size | Print size | Line height | Measure |
| --- | --- | --- | --- | --- | --- | --- |
| `body` | System sans stack | Selawik | 16 px | 10 pt | 1.65 | 72 characters |
| `display` | System sans stack | Selawik | 40 px | 21 pt | 1.15 | none |
| `code` | System monospace stack | JetBrains Mono | 14 px | 9 pt | 1.5 | none |

Spacing uses a 4 px unit with 56 px section rhythm. Controls use a 6 px radius and cards 8 px.

The web keeps system stacks on purpose: no new font is downloaded, no external request is created
and no additional license enters the project. The print editions keep the fonts already approved
and bundled. A single typeface family across all surfaces is a separate owner decision because it
would add a packaged asset and change the licensing surface.

## Surface mapping

| Surface | Current state | Target |
| --- | --- | --- |
| Portal | Inline styles in the portal generator | Generated CSS from these roles |
| Book HTML | Packaged stylesheet plus the Quarto base theme | Generated stylesheet plus local light/dark themes |
| PDF | Typst theme with its own constants | Typst values derived from these roles |
| DOCX | Generated reference document with its own constants | Generated styles with these roles |

PDF and DOCX already share one palette and one font set. The work is to make that shared baseline
the same one the web uses, not to redesign print from scratch.

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

## Not covered yet

This phase changes no rendered output. It does not add search, repository actions, issue forms,
light/dark configuration for the book, generated portal CSS, Typst variables, DOCX style generation or
any release. Those are the following phases of the unified design change, and each one is expected to
update this document with what it actually implemented and verified.
