# Book template

A starting point for an independent handbook repository. Copy this directory into a new repository,
then replace the identifiers and content. The copy is owned by the book; the hub does not update it
in place.

This template is intentionally minimal. The publishing setup (Quarto, Pandoc, Graphviz, PDF/DOCX,
manifests and checksums) is future work and is **not** part of the toolkit installation below.

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
handbook-toolkit --root . validate-book
```

Tested on Linux (Ubuntu 24.04) with Python 3.12. Native Windows commands are not tested; see the
hub's [`docs/setup.md`](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/setup.md) for
prerequisites, no-make guidance and troubleshooting.
The `.venv` lives inside the book clone and must be ignored by the book's `.gitignore`.

`validate-book` is the fast book-descriptor schema and reading-order check. It does not validate the
profile file or manuscript content. After the reading order exists and the pilot is authorized, run:

```bash
handbook-toolkit --root . validate-book --full
```

The toolkit validates structural manuscript form against the explicit profile. It does not judge
prose, factual accuracy, visual usefulness or rendered artifacts. Quarto and the publication
toolchain are a separate future setup.

For structural manuscript validation, pass an explicit reviewed profile until packaged profile
resolution exists. Use an absolute `--profile` path when the profile is outside this book:

```bash
handbook-toolkit --root . validate-manuscript manuscript/chapters/pilot.qmd --mode section-pilot --profile /path/to/reviewed-profile.yaml

handbook-toolkit --root . validate-manuscript manuscript/chapters/ch01.qmd --mode chapter --profile /path/to/reviewed-profile.yaml
```

This checks labels, callouts, ordering and placement only. In chapter mode it applies the section
and unit rules to each ordinary content section; Worked Example and Further Reading keep their
special chapter-level shapes. It does not judge meaning, factual accuracy, prose quality or visual
usefulness, and it never requires a diagram or table.

Once the book has a clean source commit and a reviewed profile, build a local six-file release
directory (not a publication):

```bash
handbook-toolkit build-book --repo . --commit <FULL_SHA> --output /external/release --mode section-pilot
```

The build requires Quarto `1.11.9` and Poppler `pdfinfo`, stages only tracked files, renders once,
inspects every payload and atomically exposes the verified directory. It does not publish or deploy.

## Before the first commit

1. Replace `id`, `title`, `catalog.slug` and `catalog.summary` in `book.yaml`.
2. Keep the `toolkit` and `profile.version` pins exact; never use a range.
3. Replace the hub commit SHA in `requirements.txt` with the reviewed commit.
4. Replace `01-example.qmd` with the approved brief and outline.
5. Add `LICENSE`, `LICENSE-CODE` and `NOTICE.md`.
6. Add the book's own `AGENTS.md` rules without copying hub source code.
7. Run `handbook-toolkit --root . validate-book` and the book's own checks.

## Rules

- Canonical content lives in `manuscript/`.
- Generated artifacts are never committed.
- The book pins the toolkit; it does not import a parent checkout or copy `tools/`, schemas or
  shared scripts.
- The book requests catalog listing only after an approved release.
