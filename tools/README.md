# `handbook-toolkit`

The shared, versioned Python package for handbook repositories. It validates the contracts that
books and the catalog must honour. It contains no book prose and makes no network calls.

## Install

```bash
python3 -m pip install -e ./tools
```

Books install a published release at an exact version. They do not import this checkout or copy its
source.

## Commands

```bash
handbook-toolkit version
handbook-toolkit --root . verify
handbook-toolkit --root . verify --full
handbook-toolkit validate-catalog catalog/catalog.json
handbook-toolkit validate-profile profiles/standard/profile.yaml
handbook-toolkit --root . validate-manuscript manuscript/chapters/pilot.qmd --mode section-pilot --profile profiles/standard/profile.yaml
handbook-toolkit --root . validate-manuscript manuscript/chapters/ch01.qmd --mode chapter --profile profiles/standard/profile.yaml
# from a book repository root:
handbook-toolkit validate-book --full
# from the hub checkout:
handbook-toolkit validate-book template/book/book.yaml --full
# local publication build; does not publish
handbook-toolkit build-book --repo /path/to/book --commit <FULL_SHA> --output /external/release --profile /path/to/profile.yaml
```

`validate-book` defaults to `book.yaml` in the repository root, so a book can run it with no path.
`validate-manuscript` requires an explicit `--profile` until packaged profile resolution is
implemented. Its `--mode` is `section-pilot` or `chapter`. The profile path is resolved relative to
`--root`; use an absolute path when the profile lives outside the book checkout.

Schemas are bundled inside the installed package. `--schemas` optionally overrides them with a
local directory; a book does not need a hub checkout or a vendored `schemas/` copy.

## Current scope

Version `0.3.0` validates:

- catalog schema, unique ids/slugs, exact tag/version agreement, immutable release URLs and real dates;
- profile schema, unique element ids, closing-order consistency, label style and figure/table
  constraints;
- book descriptor schema, pinned toolkit version and path safety;
- reading-order existence, duplicates and, in full mode, completeness against every `.qmd` file;
- manuscript structure against an explicit profile:
  - `section-pilot`: required unit labels, closing element order and actual bold-paragraph/callout
    forms;
  - `chapter`: opening callouts, worked example, review checklist placement and final Further Reading,
    plus the section/unit rules for each ordinary content section; Worked Example and Further Reading
    are special sections and are exempt from the ordinary section shape;
  - fenced code is excluded with delimiter-length-aware fences; unclosed/malformed callouts,
    duplicates, missing body text and misordering/wrong forms are reported;
- repository-required files and, in full mode, relative documentation links.

The manuscript validator checks **structure only**. It does not judge meaning, factual accuracy, prose
quality or whether a diagram/table is useful, and it never requires visuals. The local publication build uses the shared publication/artifact modules; it stages only tracked files from an exact clean commit, renders HTML/Typst/DOCX once, inspects all payloads, writes and verifies the manifest/checksums, then atomically exposes the final directory. It does not publish. See [`docs/publication-build.md`](../docs/publication-build.md). The reference resolver and portal generator remain separate work.

## Tests

```bash
python3 -m unittest discover -s tools/tests -v
```

Tests use only the standard library runner and cover both accepted and rejected input. They also
parse every documented `handbook-toolkit` example, so a doc example with global options after the
subcommand fails the suite.

GitHub Actions additionally builds a wheel, verifies that the three schemas are inside it, installs
the wheel in an isolated virtual environment and validates a copy of the template book outside the
hub checkout. That job is not a publication step.
