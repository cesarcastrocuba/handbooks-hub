# Change 0031 — Native reading-site rendering

- Decision: HUB-DEC-037; work package WP3 of change 0027.
- Role: Implementer. Independent review and coordinator audit are pending.
- Base: 2e294388ea4e4039744b14e4164301f6c085f587 (merged WP1).
- Toolkit: 0.10.0. Template release version and pin remain for the release PR.

## Proofs of concept

1. A three-page Quarto 1.11.9 book in /tmp/wp3-poc evaluated _brand.yml first.
   The dual-scheme brand switched the page background and type, but Cosmo still computed
   body foreground as rgb(52,58,64) and navbar background as rgb(248,249,250) in both schemes.
   Brand alone therefore failed the current shell/ink criterion. Generated Sass defaults compiled successfully
   with Cosmo in both modes. The retained brand supplies the shared palette; Sass supplies both
   schemes. The sample before/after screenshots test the complete mechanism.
2. A native tables.qmd referencing a later chapter's table, figure and listing resolved all three
   to 1.1 with correct chapter.html fragments. The unnumbered list did not consume a chapter number.
   Separate print and HTML configurations avoid duplicate print lists. Quarto clears output on each
   render unless --no-clean is supplied; real builds proved why that switch is required.
3. The behavior-preserving split was committed separately as aa1373e after 24 real-build tests
   passed. Public build_book, BuildError, BuildResult, PAYLOADS and ROLES remain importable.

## Implementation

- build.py orchestrates; build_types defines the command boundary/API types; build_identity checks
  source identity and versions; build_staging validates and stages config; build_html packages;
  build_markdown renders the single-file edition. Each build module is below 400 lines.
- Generated Sass defaults consume the packaged tokens. Packaged html/handbook.css contains the
  remaining handwritten layout; its central geometry substitutions expand from design.py.
- Lists use the shared indexes.py registry and references.py source-label parser. Nonempty native
  table/figure/listing chapters immediately follow the first page in the HTML reading order.
  Cross-reference numbers and destinations, sidebar, search and breadcrumbs are Quarto-owned.
- _inject_table_index, _add_tables_navigation and SIDEBAR_DOCUMENT_CONTROL are deleted.
- Remaining post-render reading-site HTML edits: **none**. Font OFL copying is packaging, not HTML
  mutation. The Markdown writer's raw HTML wrappers are parsed with HTMLParser; they are unwrapped
  to preserve plain Markdown, not used to repair the reading site.

## Verification and limits

See evidence.md for commands and actual results. The baseline had 25 toolkit-authored !important
 declarations; the generated book resources now have zero. This count excludes Quarto's own
 Bootstrap implementation. No migration item uses the old mechanism.

Native lists intentionally acquire page navigation, breadcrumbs and search entries. Their sidebar
labels are their full list titles, replacing the old injected Tables label. Print and Markdown
reading order do not contain these generated web pages. Desktop Word remains unavailable; the
existing native field/LibreOffice tests cover cached content rather than Word's field update.
