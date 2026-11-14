# Handbook portal

The deployed portal is the Quarto website generated from the catalog. `HUB-DEC-041` switched the
deployed engine from the single-page generator to `--engine quarto`, and the legacy generator stays
in the toolkit as `--engine legacy` for rollback. The Owner accepted the measured page weight.
See [change 0033](../sdd/changes/0033-portal-quarto/record.md) for the parity table.

> **2026-11-14 — deployed engine changed.** `HUB-DEC-041` deploys the Quarto website. The parity
> evidence of change `0033` is unchanged; its page-weight row (481,658 to 2,425,994 bytes) is the
> cost the Owner accepted.

## Build locally

The deployed Quarto engine requires **Quarto 1.11.9**:

```sh
handbook-toolkit build-portal --catalog catalog/catalog.json --output /tmp/handbook-portal-quarto --engine quarto
handbook-toolkit design-preview --output /tmp/handbook-design
```

The legacy generator needs the installed toolkit and no renderer; it is kept for rollback:

```sh
handbook-toolkit build-portal --catalog catalog/catalog.json --output /tmp/handbook-portal --engine legacy
# The workflow-compatible entry point remains supported:
python3 -m handbook_toolkit.portal catalog/catalog.json --output /tmp/handbook-portal-module
```

Every output must be new. Generation validates the catalog, stages only packaged resources in a
private directory, disables execution and atomically exposes a complete result. Generation makes
no network request. Quarto's optional sitemap modification times are omitted through a parsed XML
step: staging filesystem times are not content history and change between otherwise identical
builds. No rendered HTML is edited. Repeat-render tests compare every published file byte for byte.

## Site structure

| Page/resource | Source and behavior |
| --- | --- |
| Library | Validated catalog data bound to packaged templates; generated category cover, title, summary, release date/version and only declared edition buttons |
| Guides | Five packaged Markdown pages: how the platform works, creating a handbook, publishing/withdrawal, contributing and questions/answers |
| Design | Living style guide generated from packaged tokens: role swatches, recomputed contrast, type, callouts, tables, code, buttons and cards |
| Navigation, search, metadata | Native Quarto website navbar, site search, light/dark toggle, description, favicon, social metadata and canonical URLs |
| Library controls | Shared packaged inline filter, without a hosted script/library: case/accent-insensitive multiword search, category intersection and title/latest sorting |
| Theme and motion | The book's exact generated Sass, CSS and self-hosted fonts; native CSS motion respects reduced motion |
| `llms.txt` | Same bytes and structure as the current generator; Markdown-edition link when declared, reading-site link otherwise |

The catalog does not carry each book's licence. Cards link readers to the handbook's declaration;
the generator does not assume the platform's content licence applies to every book. Empty catalogs
stay empty, and planned topics never become fictional entries. Generated covers need no remote
image. Existing guide fragments and public font-notice URLs remain available.

The single-page generator's templates remain while it is deployed. Its shared filter resource was
extracted without changing the generated page bytes. The new guides, markup and styles are package
data rather than Python strings. Both consumers use the same theme factories; the portal carries
only its own layout rules. Cosmo's Google Fonts import is explicitly disabled in the shared Sass;
all type assets are self-hosted and all three OFL notices travel with them.

## Verify and inspect

The online catalog gate remains separate and mandatory before deployment:

```sh
python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
python3 -m unittest discover -s tools/tests -p test_portal.py -v
```

That gate verifies stable releases, tag/source identity, manifests, checksums, download URLs and
published asset/site bytes. HTTPS, public-IP, redirect and size protections are unchanged. The
workflow still passes its read-only `GITHUB_TOKEN` to authenticate GitHub API reads.

For browser evidence install `tools/scripts/requirements-edition-preview.txt` and Chromium, then run:

```sh
python3 tools/scripts/portal_preview.py --catalog catalog/catalog.json --output /tmp/portal-preview
```

It builds both engines, checks legacy links and `llms.txt`, exercises search/filter/sort with clearly
marked two-book fixtures, checks keyboard focus and real component contrast, records byte counts,
and captures light/dark screenshots at 1440/390. The local inspection server binds only loopback;
external browser requests are blocked and fail the check. Both real site trees, fixture trees,
`parity.json` and `PREVIEW.md` are retained. Fixture entries are never deployed or verified releases.
The template edition-preview CI artifact includes these portal screenshots and evidence.

## Deployment

`portal-pages` retains its catalog-only push trigger on `main`, manual build/deploy input,
permissions, deploy gate and `GITHUB_TOKEN` for the release verification. It installs pinned Quarto
1.11.9 (the same action commit as `ci.yml`) and renders the site with `--engine quarto` into `_site`,
which is the directory uploaded to Pages. To roll back, set the engine back to `legacy` in the
workflow through a reviewed pull request (`HUB-DEC-041`). The book publication and release workflows
remain independent.
