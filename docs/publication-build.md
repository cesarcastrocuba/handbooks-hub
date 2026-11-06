# Local publication build

`handbook-toolkit build-book` builds a verified six-file release directory from an exact clean
book commit. It does **not** publish, upload, deploy, tag or release anything.

## Requirements

- Git and a clean book repository at the exact full commit.
- Quarto `1.11.9`.
- Poppler `pdfinfo` for PDF inspection.
- An explicit reviewed profile YAML. Profile packaging/resolution is not implemented yet.
- A book-side `publishing/_quarto.yml` and `manuscript/book.yml` reading order.
- A `book.yaml` toolkit pin exactly equal to the installed builder version. `--preview` is an
  explicit, non-release exception and is recorded in the manifest command.

Quarto supplies its bundled Pandoc and Typst. The current validators do not require Quarto; only this
publication build does.

## Command

```bash
handbook-toolkit build-book --repo /path/to/book --commit 0123456789abcdef0123456789abcdef01234567 --output /external/path/release-1.0.0 --profile /path/to/reviewed-profile.yaml
```

Optional arguments:

- `--version 1.0.0` overrides `publishing/metadata.yaml` for the book version.
- `--epoch 1761868800` overrides the default commit timestamp / `SOURCE_DATE_EPOCH`.
- `--quarto /path/to/quarto` selects the executable; it must report `1.11.9`.
- `--mode chapter` (default) validates every chapter in the reading order. Use
  `--mode section-pilot` for a partial pilot build; it requires exactly one chapter entry.
- `--preview` allows a `book.yaml` toolkit pin that differs from the builder, only for an explicit
  non-release preview. The manifest command records `--preview`.

The output directory must not exist and must be outside the source repository.

## What the build does

1. Rejects a dirty repository or a commit that is not `HEAD`.
2. Creates a private staging directory beside the final output.
3. Extracts only tracked files from the exact commit with `git archive`.
4. Inspects the source ZIP before extracting or rendering: reading order coverage, canonical
   manuscript, descriptor and notices must be valid at the commit.
5. Reads and validates `book.yaml`, `publishing/metadata.yaml` and the reading order from the staged
   source, not from the mutable working tree.
6. Checks the book's toolkit pin against the builder version (unless explicit `--preview`).
7. Runs the structural manuscript validator for every chapter from the staged source with the
   explicit reviewed profile before render.
8. Generates a deterministic Quarto project config, using the book-side `publishing/_quarto.yml`
   and reading order; renders only HTML, Typst and DOCX with `--no-execute` and
   `SOURCE_DATE_EPOCH`.
9. Packages the HTML site as a ZIP, the PDF and DOCX as files, and the tracked source as a ZIP whose
   comment is the full source commit.
10. Inspects every payload with the shared format inspector.
11. Writes `publication-manifest.json` and `SHA256SUMS.txt`, then runs `verify_publication`.
12. Atomically renames the complete verified directory to `--output`.

No writer staging directory is visible at the final output path. A failed build leaves no final
output and removes its private staging directory.

## Output

Exactly six assets:

- `book-html.zip`
- `book.pdf`
- `book.docx`
- `book-source.zip`
- `publication-manifest.json`
- `SHA256SUMS.txt`

The manifest records the exact commit, book version, toolkit/profile versions, build command, source
epoch, and Quarto/Pandoc/Typst/Python/zlib runtime versions.

## Limits

The build verifies presence, structure, links within the HTML archive, checksums and identity. It does
**not** prove editorial quality, factual accuracy, visual layout, accessibility, PDF pagination or
reproducible bit-for-bit output across all environments. Human review remains required before any
publication gate.
