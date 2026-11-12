# Book template 1.1.1

A starting point for an independent handbook repository. Copy this directory into a new repository,
then replace the identifiers and content. The copy is owned by the book; the hub does not update it
in place.

**New to the platform? Start with [`docs/AUTHOR_QUICKSTART.md`](docs/AUTHOR_QUICKSTART.md).** It
covers creating the repository from the template, the one-time repository settings, the Initialize
book workflow, the first release and the catalog listing request, with no prior knowledge assumed.

The template pins toolkit `0.6.0` and standard profile `1.0.0`. It contains no copied toolkit source
and never imports a parent hub checkout.

## What is included

| Path | Purpose |
| --- | --- |
| `book.yaml` | Book descriptor, exact toolkit/profile pins, licenses and catalog metadata |
| `manuscript/book.yml` | Reading order |
| `manuscript/chapters/01-example.qmd` | Replaceable chapter that passes the standard profile |
| `publishing/_quarto.yml` | Quarto project configuration for HTML, Typst/PDF and DOCX; book search, repository edit/issue actions, a library link and a light/dark theme |
| `publishing/metadata.yaml` | Book version and status consumed by the build |
| `Makefile` | `check`, `build` and `full` targets |
| `LICENSE`, `LICENSE-CODE`, `NOTICE.md` | Licensing and attribution |
| `AGENTS.md` | Book-owned contributor rules |
| `.github/workflows/` | `ci.yml` (fast checks), `release.yml` (guarded release and Pages), `initialize-book.yml` (one-time identity rewrite) |
| `.github/ISSUE_TEMPLATE/` | Plain-language forms for a content correction and a content proposal |
| `.github/scripts/initialize_book.py` | Book-owned bootstrap rewrite used by `initialize-book.yml` |
| `.gitignore` | Ignores build output, Quarto caches, Python caches and virtualenvs |
| `docs/AUTHOR_QUICKSTART.md` | Step-by-step author onboarding |

## Reader navigation and contributions

- The reading site has full-book search and a light/dark toggle that follows the reader's preference.
- `repo-url` and `repo-actions` add **Edit this page**, **Report an issue** and **View source**. The
  Initialize book workflow replaces the `OWNER/REPOSITORY` placeholder with the real repository.
- The navbar links back to the hub library and to the repository's releases page.
- Two issue forms ask for the page or section, the problem and the evidence, so a report is
  actionable without knowing the internal review process.

## Install the pinned toolkit

The book installs `handbook-toolkit` from a full hub commit, not from a parent checkout and not from
copied hub files. `requirements.txt` contains the pin:

```text
handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@<FULL_HUB_COMMIT_SHA>#subdirectory=tools
```

Create a venv inside the book clone and install it:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The `.venv` lives inside the book clone and must be ignored by the book's `.gitignore`.

Tested on Linux (Ubuntu 24.04) with Python 3.12. Native Windows commands are not tested; see the
hub's [`docs/setup.md`](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/setup.md) for
prerequisites, no-make guidance and troubleshooting.

## Check and build

```bash
make check
```

`make check` validates the descriptor and reading order, then runs the cross-reference/label/local
image gate. It is the fast check suitable for every commit.

```bash
make build
make full
```

`make build` requires a clean git commit, Quarto `1.11.9` and Poppler `pdfinfo`. It validates every
chapter against the profile, renders a single-file Markdown edition and renders HTML, Typst/PDF and
DOCX once with `--no-execute`, inspects the payloads and atomically creates a seven-file directory in
`../dist`:

- `book-html.zip`
- `book.pdf`
- `book.docx`
- `book.md`
- `book-source.zip`
- `publication-manifest.json`
- `SHA256SUMS.txt`

`make full` runs `check` and then `build`. The build does not publish or deploy. Override the output
with `make build OUTPUT=/external/path`.

Without `make`, run the same commands directly:

```bash
handbook-toolkit --root . validate-book --full
handbook-toolkit --root . validate-references book.yaml
handbook-toolkit build-book --repo . --commit "$(git rev-parse HEAD)" --output ../dist --mode chapter
```

## Before the first commit

1. Run the Initialize book workflow, or replace `id`, `title`, `catalog.slug` and `catalog.summary`
   in `book.yaml` by hand. The workflow also rewrites the Quarto metadata, the notices and the README
   title.
2. Replace `publishing/metadata.yaml` with the real version and status.
3. Keep the `toolkit` and `profile.version` pins exact; never use a range.
4. Replace the hub commit SHA in `requirements.txt` with the reviewed commit.
5. Replace `01-example.qmd` with the approved brief and outline.
6. Replace the copyright and attribution in `NOTICE.md` with the book's own.
7. Add the book's own `AGENTS.md` rules without copying hub source code.
8. Run `make check` and the book's own reviews.

## Upgrade the book

Books upgrade deliberately, not automatically. Follow the hub's
[`docs/book-upgrade.md`](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/book-upgrade.md):
read the changelog, update the toolkit commit and the profile pin together, reinstall, run
`make check` and `make full`, and review the rendered HTML/PDF/DOCX before merging.

## Rules

- Canonical content lives in `manuscript/`.
- Generated artifacts are never committed.
- The book pins the toolkit; it does not import a parent checkout or copy `tools/`, schemas or
  shared scripts.
- The book requests catalog listing only after an approved release.
