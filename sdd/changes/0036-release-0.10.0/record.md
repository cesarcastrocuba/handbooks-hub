# Record — Template `1.5.0` and toolkit `0.10.0`

**Change:** `0036-release-0.10.0`. **Released:** 2026-11-14. **Implementer pull request:** this
release branch. **Reviewer:** a different agent; the Owner merges.

## What the release contains

Toolkit `0.10.0` ships two work packages of change `0027`:

**WP3, change `0031` — native reading-site rendering.**
- The reading-site theme is generated from the design tokens, with one Cosmo base in light and dark
  and no authored `!important`; the packaged stylesheet keeps the remaining layout.
- Nonempty table, figure and listing indexes are native Quarto chapters immediately after the first
  page, owned by Quarto search, breadcrumbs and the sidebar. The post-render Tables page and sidebar
  injection are gone, and no rendered HTML is repaired.
- `build.py` is split into focused modules: orchestration, API types, source identity, staging,
  HTML packaging and Markdown packaging.

**WP4, change `0032` — native book reading experience.**
- The HTML cover is generated from the descriptor and publication metadata, followed by Document
  Control on its own page; the reading-order groups become Quarto parts and nonempty caption lists
  sit in front matter.
- An edition footer carries edition identity on every page; figures and a List of Figures are native.
- Native site URL and canonical links, description, Open Graph and Twitter metadata, and a
  token-derived SVG favicon are generated.
- Authored motion is native CSS inside the reduced-motion query: view transitions, view-timeline
  reveals, scroll progress and control transitions, with no script or external asset.
- Accessibility: visible focus, the native skip link and tab order, and static content when the
  motion features are unsupported.

Template `1.5.0` adapts the shipped configuration: `publishing/_quarto.yml` already selects
`dark: cosmo` and has no legacy navbar Tables entry, so the `0.9.2` to `0.10.0` note in
`docs/book-upgrade.md` requires no further template change.

## Pins

| File | Value |
| --- | --- |
| `template/book/book.yaml` | `toolkit: "0.10.0"` |
| `template/book/requirements.txt` | `handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@dcfd8c86a616c931ae68450c60dbd220cfd49a08#subdirectory=tools` |
| `template/book/README.md` | heading `# Book template 1.5.0`, pins toolkit `0.10.0` |
| `.github/workflows/ci.yml` | no edit: `template-install` derives the expected version from `template/book/book.yaml` |

`dcfd8c86a616c931ae68450c60dbd220cfd49a08` is the commit of tag `toolkit-v0.10.0`, read with
`git rev-list -n1 toolkit-v0.10.0`.

## Steps still to run after merge

1. Export `template/book/` with `python3 tools/scripts/export_template.py`, push it to
   `cesarcastrocuba/handbooks-template` and tag `template-v1.5.0`.
2. Upgrade the sample book to toolkit `0.10.0`: re-pin `book.yaml` and `requirements.txt`, remove any
   legacy navbar Tables entry, run its checks, review the rebuilt HTML, PDF, DOCX and Markdown
   editions and publish the next release.
3. Update the catalog to that release with the `catalog-update` workflow, review the pull request and
   merge it so `portal-pages` redeploys.
