# Book template 1.0.0

A starting point for an independent handbook repository. Copy this directory into a new repository,
then replace the identifiers and content. The copy is owned by the book; the hub does not update it
in place.

The template pins toolkit `0.4.0` and standard profile `1.0.0`. It contains no copied toolkit source
and never imports a parent hub checkout.

## What is included

| Path | Purpose |
| --- | --- |
| `book.yaml` | Book descriptor, exact toolkit/profile pins, licenses and catalog metadata |
| `manuscript/book.yml` | Reading order |
| `manuscript/chapters/01-example.qmd` | Replaceable chapter that passes the standard profile |
| `publishing/_quarto.yml` | Quarto project configuration for HTML, Typst/PDF and DOCX |
| `publishing/metadata.yaml` | Book version and status consumed by the build |
| `Makefile` | `check`, `build` and `full` targets |
| `LICENSE`, `LICENSE-CODE`, `NOTICE.md` | Licensing and attribution |
| `AGENTS.md` | Book-owned contributor rules |

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
chapter against the profile, renders HTML, Typst/PDF and DOCX once with `--no-execute`, inspects the
payloads and atomically creates a six-file directory in `../dist`:

- `book-html.zip`
- `book.pdf`
- `book.docx`
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

1. Replace `id`, `title`, `catalog.slug` and `catalog.summary` in `book.yaml`.
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
