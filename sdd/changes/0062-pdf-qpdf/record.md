# Change 0062 — PDF compaction with qpdf

Lossless PDF compaction under **HUB-DEC-043** (toolkit-owned size work), requested by the Owner for
every book: the v3.0.0 optimisation of the Solutions Architecture Handbook now runs in the platform
build instead of in the book's own scripts.

No version bump and no tag. Neither `STATUS.md` nor `docs/decisions.md` is modified. Commits carry
the provenance trailer allowed by `HUB-DEC-025`.

## Scope

- **Hub base**: `4773684` (`origin/main`, merge of PR 95, template 1.8.0).
- **Branch / worktree**: `feat/0062-pdf-qpdf`,
  `../handbooks-hub.worktrees/0062-pdf-qpdf`.
- **Write set**:
  - `tools/src/handbook_toolkit/artifact_optimize.py`
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/cli.py`
  - `tools/src/handbook_toolkit/schemas/publication-manifest.schema.json`
  - `tools/tests/test_artifact_optimize.py`
  - `.github/workflows/ci.yml`
  - `template/book/.github/workflows/ci.yml`
  - `template/book/.github/workflows/release.yml`
  - `README.md`, `template/book/README.md`, `docs/publication-build.md`,
    `docs/publication-contract.md`, `docs/book-upgrade.md`
  - `CHANGELOG.md`
  - `sdd/changes/0062-pdf-qpdf/record.md`

## Attribution

`optimize_pdf` is a port of `optimize_pdf` from
`src/scripts/artifact_optimize.py` at tag `v3.0.0` (`13d295b`) of
`cesarcastrocuba/solutions-architecture-handbook`, the frozen v3.0.0 source of the Solutions
Architecture Handbook, read from a local read-only copy. Same author, MIT-licensed repository code. The port keeps the
option set and verification steps and adapts them to the hub toolkit (typed result dictionary,
`BuildError`, release/preview behaviour, manifest record).

## Implementation

1. **`artifact_optimize.optimize_pdf`**
   - Runs `qpdf` with `--deterministic-id --object-streams=generate --compress-streams=y
     --stream-data=compress --recompress-flate --compression-level=9` into a temporary file beside
     the PDF.
   - Requires qpdf **11 or later**; reads `$QPDF` when it names a file, otherwise the executable on
     `PATH`.
   - Verifies with `qpdf --check --warning-exit-0` and compares `qpdf --show-npages` before and
     after. A changed page count or a qpdf error raises `BuildError`.
   - Replaces the PDF only when the candidate is strictly smaller; otherwise reports
     `kept: no gain` and leaves the bytes untouched.
   - `required=True` (a release build) raises when qpdf is missing or older than 11; a preview
     build returns `skipped: qpdf not found` or `skipped: qpdf 11 or later is required`.
2. **`build_book`** calls the optimizer once, after the payloads are staged and before the manifest
   is written, with `required=not preview`. `--no-optimize` skips it with
   `skipped: --no-optimize`. The qpdf version joins `build.tool_versions` when available.
3. **Manifest**: `build.optimization.pdf` records `tool`, `version`, `status`, and `before`, `after`
   and `saved` bytes. The field is optional in schema `1.1`, so older manifests stay valid.
4. **CI**: `publication-build` and `edition-preview` install `qpdf` next to `poppler-utils` and
   LibreOffice Writer; the template release workflow installs it and fails the release when the
   manifest does not show a compacted PDF; the template CI installs it for `make build`/`make full`.
5. **Docs**: the build requirements, the manifest description and the manifest example name qpdf and
   `build.optimization.pdf`.

## Focused tests

`tools/tests/test_artifact_optimize.py` gained six tests: missing qpdf fails a release build and is
recorded as skipped by a preview build; version parsing; lossless compaction with an unchanged page
count and byte-identical second run (`kept: no gain`); a changed page count raises; a synthetic-book
build records the manifest entry; and `--no-optimize` records the skip.

```
$ PYTHONPATH=tools/src:tools/tests .venv/bin/python -m unittest tools.tests.test_artifact_optimize.PdfOptimizeTests -v
test_build_book_records_the_pdf_optimization (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_build_book_records_the_pdf_optimization) ... ok
test_missing_qpdf_fails_a_release_build_and_skips_a_preview (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_missing_qpdf_fails_a_release_build_and_skips_a_preview) ... ok
test_no_optimize_skips_pdf_compaction (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_no_optimize_skips_pdf_compaction) ... ok
test_optimize_pdf_is_lossless_and_deterministic (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_optimize_pdf_is_lossless_and_deterministic) ... ok
test_optimize_pdf_rejects_changed_page_count (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_optimize_pdf_rejects_changed_page_count) ... ok
test_qpdf_version_is_parsed (tools.tests.test_artifact_optimize.PdfOptimizeTests.test_qpdf_version_is_parsed) ... ok

----------------------------------------------------------------------
Ran 6 tests in 37.560s

OK
```

The same class with qpdf hidden proves the `checks` CI job (no qpdf, no Quarto) stays green: the
three qpdf tests skip and the preview build records `skipped: qpdf not found`.

```
$ PYTHONPATH=tools/src:tools/tests QPDF=/nonexistent/qpdf .venv/bin/python -m unittest tools.tests.test_artifact_optimize.PdfOptimizeTests -v
...
Ran 6 tests in 41.827s

OK (skipped=3)
```

## Hub checks

```
$ make check PYTHON=./.venv/bin/python
...
Ran 529 tests in 497.579s

OK (skipped=3)
...
VERIFY: 5 check(s), 0 problem(s)

$ make full PYTHON=./.venv/bin/python
...
Ran 529 tests in 515.613s

OK (skipped=3)
site-check: 1 page(s), 3 asset(s), all 200
...
VERIFY: 5 check(s), 0 problem(s)
...
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

Local environment: qpdf `11.9.0`, Quarto `1.11.9`, LibreOffice `24.2.7.2`, Poppler `pdfinfo`,
Python `3.12.3`.

## Solutions Architecture Handbook measurement

Book repository `cesarcastrocuba/handbook-solutions-architecture` at commit `ba9e1df`, version
`3.1.0-rc.1`, built three times with this branch's toolkit and `--require-page-numbers`:

```
$ PYTHONPATH=<worktree>/tools/src .venv/bin/python -m handbook_toolkit build-book \
    --repo <book> --commit ba9e1df1c985a48d1b5dedb98e2b982101d03fbb \
    --output /tmp/opencode/0062/before --require-page-numbers --no-optimize
/tmp/opencode/0062/before: OK
...
$ ... --output /tmp/opencode/0062/after1 --require-page-numbers
/tmp/opencode/0062/after1: OK
tool_versions: ... qpdf=11.9.0 ...
$ ... --output /tmp/opencode/0062/after2 --require-page-numbers
/tmp/opencode/0062/after2: OK
tool_versions: ... qpdf=11.9.0 ...
```

The manifest of the compacted build:

```
$ jq '.build.optimization, .build.tool_versions.qpdf' after1/publication-manifest.json
{
  "pdf": {
    "after": 16025005,
    "before": 24388085,
    "saved": 8363080,
    "status": "optimized",
    "tool": "qpdf",
    "version": "11.9.0"
  }
}
"11.9.0"
```

### Size, pages and links

Measured with pypdf 7.1.0 in the local venv (links = annotation dictionaries with `/Subtype /Link`;
all of them are internal destinations in this book):

| Build | PDF bytes | Pages | Links | SHA256 |
| --- | ---: | ---: | ---: | --- |
| `before` (`--no-optimize`) | 24,388,085 | 513 | 6,887 | `cbc571c10bf445feb8817cb86329969f9e14f3cd8ac845148c775bf1c7e49955` |
| `after1` (qpdf) | 16,025,005 | 513 | 6,887 | `cf104b4f65cc20f2565b6cf44a711c6ce95d9fa6197fe8858d14df9c7675d2b5` |
| `after2` (qpdf) | 16,025,005 | 513 | 6,887 | `cf104b4f65cc20f2565b6cf44a711c6ce95d9fa6197fe8858d14df9c7675d2b5` |

- **PDF size**: 24,388,085 B → 16,025,005 B, 8,363,080 B saved (34.29 % smaller), 65.71 % of the
  original size.
- **Page count**: 513 before and after (also checked inside the build by `qpdf --show-npages`, which
  fails the build on a mismatch).
- **Link count**: 6,887 before and after; qpdf recompression moves no annotation.
- **Reference**: the v3.0.0 PDF of the same book is 16,030,616 B, so this build is 5,611 B smaller
  than the frozen release while carrying the 513 pages of the current toolkit.

### Reproducibility

```
$ sha256sum after1/book.pdf after2/book.pdf
cf104b4f65cc20f2565b6cf44a711c6ce95d9fa6197fe8858d14df9c7675d2b5  after1/book.pdf
cf104b4f65cc20f2565b6cf44a711c6ce95d9fa6197fe8858d14df9c7675d2b5  after2/book.pdf
$ cmp after1/book.pdf after2/book.pdf && echo identical
identical
```

Two independent builds of the same commit produce the same PDF bytes (`--deterministic-id`).
`book.docx`, `book.md` and `book-source.zip` are also identical between the two builds;
`book-html.zip` differs by 5 bytes (`14,093,882` vs `14,093,887`), a reading-site artefact
nondeterminism that predates this change and is outside its scope.

### Extracted text unchanged

```
$ pdftotext -layout before/book.pdf before.txt
$ pdftotext -layout after1/book.pdf after1.txt
$ sha256sum before.txt after1.txt
1e4ae22b2b181cfb810197c953c3290e9226fd288a1723665d77bfa15ea11163  before.txt
1e4ae22b2b181cfb810197c953c3290e9226fd288a1723665d77bfa15ea11163  after1.txt
$ diff -q before.txt after1.txt && echo "full text identical"
full text identical
$ wc -l before.txt after1.txt
  22949 before.txt
  22949 after1.txt
$ diff <(pdftotext -f 1 -l 20 before/book.pdf -) <(pdftotext -f 1 -l 20 after1/book.pdf -) \
    && diff <(pdftotext -f 495 -l 513 before/book.pdf -) <(pdftotext -f 495 -l 513 after1/book.pdf -) \
    && echo "pages 1-20 and 495-513 identical"
pages 1-20 and 495-513 identical
```

The whole extracted text, front matter through Index, is byte-identical; the first twenty and the
last nineteen pages are shown separately as the requested spot check.

## Known follow-up (outside this change)

The Solutions Architecture book and the sample book keep their own release workflows, which still
install only `poppler-utils` and LibreOffice. A book that moves to toolkit 0.13.0 must add `qpdf` to
its release workflow, exactly as the template release workflow now does; a release build fails
without it by design. This belongs to the books' own repositories and their Owner-approved release
round, not to this hub change.

