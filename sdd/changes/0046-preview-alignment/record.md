# Change 0046 — Preview alignment

Align toolkit 0.11.0 with the Owner's supplied portal and reading concepts. This is an
Implementer change; a different Reviewer and Owner acceptance are required before merge.

## Scope and boundaries

- Branch: `feat/preview-alignment`; baseline: `e14dd46` (`origin/main`).
- Exclusive worktree: `/home/ubuntu/github/handbooks-hub.worktrees/preview-align`.
- One PR, as explicitly requested by the approved implementation brief. The shared token contract,
  edition renderers and their regression checks form one coordinated visual change; the authored
  diff exceeds the generic 400-line review guideline. No artificial splitting or compressed tests.
- `STATUS.md`, `docs/decisions.md`, the reference handbook, template pins and released tags are
  outside this write set. No self-review, merge, tag or release.
- English artifacts; Conventional Commits without attribution trailers.

## Result

The generated Sass defines the body/root scale, heading sizes, button dimensions and radius
from the token contract. Cosmo also needs `enable-rounded: true`: changing the radius variables
alone leaves buttons square. Quarto's default root is 17 px; the explicit 16 px root gives the
32–48 px general page titles and exact 14 px buttons. The web palette remains unchanged; the
coordinator correction aligns the print border and chrome-rule roles to `#DDD3C0`.

Portal book cards use 20 px titles without a heading rule, 14 px muted summaries, 13 px link rows,
11 px text tags, 12 px edition chips and the asymmetrically rounded cover. Search, sort and topic
filters are compact and retain at least 24 px target height. The home eyebrow precedes the title;
five responsive guide cards each have one link, description and decorative arrow. Their existing
focus ring and guarded hover lift remain available.

All three editions use surface-filled table bodies and horizontal border rules, including tables
inside callouts. HTML uses separate borders and the card radius, with horizontal scrolling on
phones. Typst wraps tables in a rounded, clipped **breakable** block: the actual themed 100-row
probe preserves rows 0–99 and repeats the header across eight pages. DOCX applies direct cell
shading and bottom borders to both Table and TablePlain data tables, leaving layout/figure wrappers
alone. Word table geometry has square corners; LibreOffice is inspection evidence, not a Word oracle.
The reference DOCX remains byte-identical to its generator.

Cross-document page transitions and their render-blocking capture link are removed from the
shared reading layer and both staging paths. Obsolete motion/stripe tokens and schema entries
are removed. Reading progress, once-only reveals, the card stagger, hover/focus, details and theme
feedback retain reduced-motion guards. No product script or external resource is added.

## Verification and rollback

See [evidence.md](evidence.md) for actual commands, measurements, screenshots and known gaps.
Tests exercise emitted HTML, computed browser styles, focus and target dimensions, scrolling,
DOCX cell formatting/idempotence, the long PDF table and existing field/index invariants.

The work unit is the visual alignment and its tests/docs. Its rollback boundary is the files in
this PR: revert that commit to restore the earlier scale, stripes and page-transition behavior.
No migration, publication, template pin or catalog rollback is involved.

## Integration dependency

The requested version bump makes three existing toolkit 0.10.4 statements in coordinator-owned
`STATUS.md` stale. The currency checker correctly rejects them. The Implementer has neither edited
that file nor weakened the checker. The coordinator must synchronize its status statements before
the full repository gate can become green. Owner preview acceptance and independent review remain
required; the local read-only preview servers are left running.

## Coordinator review corrections

The review of `5ae35ca` identified one Major and three Minor findings. This correction commit
addresses all four together, with the existing STATUS/decisions write exclusion retained.

1. Print `border` and `chrome_rule` now both use `#DDD3C0`; the packaged reference DOCX was
   regenerated so its inherited rules agree with direct cell rules. The color-role regression
   checks both print constants, DOCX values and token validity/contrast.
2. Typst table-cell paragraphs opt out of justification; the body paragraph rule remains justified.
3. Planned topics now have a semantic container, a 20 px grid-gap top margin, 13 px text and the
   muted color. Browser checks verify both the computed margin and the actual card-to-note gap.
4. Only the home hero uses `clamp(1.75rem, 3.2vw, 2.5rem)`, weight 700 and max-width 22 ch.
   A page body class scopes it; other page titles retain their existing scale. Browser checks
   verify the 40/28 px hero and the unchanged 48/32 px Design title at desktop/phone widths.

Updated visual, PDF and DOCX evidence is in evidence.md. The correction can be rolled back as
one commit without reverting the original implementation or coordinator-owned state changes.
