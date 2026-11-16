# Change 0055 — Lossless Artifact Size Optimization (Phase 6 Size Gap)

Lossless artifact size optimization under **HUB-DEC-043** (toolkit-owned feature supporting all books).
This closes the release asset size gap observed in the full 33-chapter real-book build between the
hub platform build and v3.0.0 release assets.

No version bump or tag is created here. Commits carry the required provenance trailer.
Neither `STATUS.md` nor `docs/decisions.md` is modified.

## Pins and Scope

- **Hub Base**: `0824ddf` (`origin/main`, merge of toolkit 0.12.0 release PR #89).
- **Branch / Worktree**: `feat/0055-artifact-size`, `/home/ubuntu/github/handbooks-hub.worktrees/artifact-size`.
- **Write set**:
  - `tools/src/handbook_toolkit/artifact_optimize.py`
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/cli.py`
  - `tools/src/handbook_toolkit/docx_post.py`
  - `tools/src/handbook_toolkit/artifacts.py`
  - `tools/tests/test_artifact_optimize.py`
  - `sdd/changes/0055-artifact-size/record.md`

## Step 1: Measurement & Findings (Where the Bytes Go)

### Initial Problem (Measured Numbers)

Full 33-chapter book built by toolkit at PR 87 (`/tmp/codex-pr87-round3-dist`) vs v3.0.0 release assets:

| Asset | Platform Build (PR 87) | v3.0.0 Release | Delta |
| --- | ---: | ---: | ---: |
| PDF | 21,360,875 | 16,030,616 | +5,330,259 (+33.2%) |
| DOCX | 16,253,460 | 12,416,306 | +3,837,154 (+30.9%) |
| HTML zip | 17,872,824 | 14,125,177 | +3,747,647 (+26.5%) |

### Byte Breakdown Across Editions

1. **DOCX (Total uncompressed: 23.49 MB, compressed: 16.25 MB)**:
   - **PNG diagrams**: The 121 PNG diagrams in `word/media/` take **15,581,484 bytes** compressed (96.0% of the entire file).
   - **OOXML document parts**: XML files in `word/` take 654,433 bytes (4.0%).

2. **HTML ZIP (Total uncompressed: 25.25 MB, compressed: 17.84 MB)**:
   - **PNG diagrams**: The 121 PNG diagrams take **15,581,484 bytes** (87.3% of the zip).
   - **HTML pages**: 957,325 bytes (5.4%).
   - **Web fonts (WOFF2/TTF)**: 456,271 bytes (2.6%).
   - **Search index JSON**: 396,238 bytes (2.2%).
   - **CSS/JS assets**: 255,212 bytes (1.4%).

3. **PDF (Total: 21.36 MB)**:
   - **Image streams**: 13,424,887 bytes (62.8%).
   - **Content and page streams**: 2,421,239 bytes (11.3%).
   - **Embedded fonts**: 47,140 bytes (0.2%).
   - **Structure tree, uncompressed PDF dictionaries, and cross-reference table**: 5,467,609 bytes (25.6%).

### Recompression Analysis

- **Does PNG recompression alone close the gap?**:
  - **DOCX**: **YES**. Recompressing the 121 PNG diagrams using standard zlib Deflate level 9 with filter 0 reduces PNG size from 17,504,985 uncompressed bytes to 12,676,104 bytes (saving 4,828,881 bytes, 27.59%). In the resulting DOCX package, size drops from 16,253,460 to 12,416,037 bytes (saving 3,837,423 bytes, 23.61%), exactly matching v3.0.0 (12,416,306 bytes, difference of -269 bytes).
  - **HTML ZIP**: **YES**. Recompressing the staged PNG images reduces `book-html.zip` from 17,872,824 to 14,035,401 bytes (saving 3,837,423 bytes, 21.47%), outperforming v3.0.0 (14,125,177 bytes, saving an additional 89,776 bytes).
  - **PDF**: **NO**. Typst decodes input PNG files into raw pixel rasters and recompresses them internally using its own Flate encoder. Pre-recompressing the input PNG files produces an identical 21,360,875-byte PDF (0 bytes saved).

- **How much ZIP repack and qpdf add**:
  - **ZIP repack** (level 9 deflated with deterministic fixed timestamps): saves an additional 20,929 bytes on DOCX (down to 12,394,892 bytes) and 9,491 bytes on HTML ZIP (down to 14,025,694 bytes).
  - **qpdf** (`--object-streams=generate --recompress-flate --compression-level=9`): compresses uncompressed object dictionaries and streams, saving **5,944,799 bytes (27.83%)** on PDF (down to 15,416,076 bytes, beating v3.0.0's 16,030,616 bytes).
  - **qpdf in CI/Release workflow decision**: `qpdf` is not currently installed in the hub CI or the template release workflow. Adding a new binary dependency requires pinned workflow action updates across repositories and an owner decision. In accordance with the brief instructions (*"qpdf only if it is already installed in CI and the release workflow, or added there pinned and verified; otherwise leave it out and say why"*), `qpdf` is omitted from the default build pipeline to preserve zero-external-dependency reproducibility using Python stdlib `zlib` alone.

## Step 2: Implementation Details

1. **`handbook_toolkit/artifact_optimize.py`**:
   - `png_pixels`: Pure Python scanline raster decoder supporting PNG filter types 0..4 (None, Sub, Up, Average, Paeth) across bit depth 8 color types 0 (Grayscale), 2 (RGB), 3 (Indexed/Palette), 4 (Grayscale+Alpha), and 6 (RGBA).
   - `png_recompress`: Losslessly recompresses IDAT chunks using zlib level 9 and filter 0. Performs a mandatory `png_pixels` equality assertion between candidate and source; raises `BuildError` if any pixel differs. Only retains candidate if smaller than source.
   - `optimize_staged_pngs`: Runs optimization across all `*.png` images in the staged build workspace only, never touching canonical repository sources.
   - Note on dead code cleanup: post-hoc ZIP repacking functions (`repack_zip`, `optimize_zip_file`) were removed in favor of direct native level-9 packaging during generation.

2. **Integration into `build_book`**:
   - `build_book` in `handbook_toolkit/build.py`: Accepts `optimize: bool = True`. Calls `optimize_staged_pngs(workspace)` immediately after `_extract_source(source_zip, workspace)` before Quarto compiles or stages outputs. Passes `compresslevel = 9 if optimize else None` to `_payload_paths` and `cache_page_numbers`.
   - `build-book` CLI in `handbook_toolkit/cli.py`: Enabled by default; adds `--no-optimize` flag for opt-out of both PNG recompression and level-9 ZIP packaging.
   - Default ZIP compression: `docx_post._write_package`, `docx_pages.cache_page_numbers`, and `artifacts.archive_tree` configure `ZipFile(..., compresslevel=9)` when `optimize=True`, falling back to standard zlib default compression when `optimize=False` (`--no-optimize`).

## Step 3: Proof & Verification Evidence

### 1. Focused Unit Tests (12/12 Passed)

```bash
PYTHONPATH=tools/src:tools/tests .venv/bin/python -m unittest tools/tests/test_artifact_optimize.py
```

Output:
```
............
----------------------------------------------------------------------
Ran 12 tests in 73.018s

OK
```

The 12 unit tests verify:
- `test_png_recompress_smaller_identical_pixels`: synthetic uncompressed PNG recompresses smaller with identical pixels.
- `test_png_recompress_preserves_already_optimal`: already-optimal PNG is preserved and never inflated.
- `test_png_pixels_decodes_palette_and_grayscale`: decodes non-RGBA PNG formats.
- `test_png_recompress_corrupt_signature_fails`: corrupt PNG signature raises `BuildError`.
- `test_png_recompress_truncated_chunk_fails`: truncated chunk raises `BuildError`.
- `test_png_recompress_crc_error_fails`: invalid CRC raises `BuildError`.
- `test_png_recompress_corrupt_idat_fails`: corrupted IDAT payload raises `BuildError`.
- `test_optimize_png_file_in_place`: in-place file optimization.
- `test_optimize_staged_pngs`: recursive directory traversal and statistics.
- `test_archive_tree_compresslevel`: verifies `compresslevel=None` vs `compresslevel=9` behavior.
- `test_build_book_reproducible_bytes`: builds a book twice from the same commit and asserts identical SHA256 checksums across all publication artifacts.
- `test_build_book_no_optimize_flag`: verifies building with `optimize=False` produces valid artifacts.

### 2. Full Hub Verification (`make full`)

```bash
make full PYTHON=.venv/bin/python
```

Output:
```
.venv/bin/python -m unittest discover -s tools/tests -v
...
Ran 490 tests in 393.209s

OK (skipped=3)
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
catalog/catalog.json: OK
profiles/standard/profile.yaml: OK
template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
catalog/catalog.json: OK
profiles/standard/profile.yaml: OK
template/book/book.yaml: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

### 3. Sample Book Verification (`handbook-sample-01`)

Commit: `8ed1b7035430ab3dc25fb65d712577bc197394ef`

#### Before (`--no-optimize`)
```
total 2608
-rw------- 1 ubuntu ubuntu     479 Nov 16 16:23 SHA256SUMS.txt
-rw-rw-r-- 1 ubuntu ubuntu 1241802 Nov 16 16:22 book-html.zip
-rw-rw-r-- 1 ubuntu ubuntu  148058 Nov 16 16:21 book-source.zip
-rw-rw-r-- 1 ubuntu ubuntu   87838 Nov 16 16:22 book.docx
-rw-rw-r-- 1 ubuntu ubuntu  156640 Nov 16 16:23 book.md
-rw-rw-r-- 1 ubuntu ubuntu 1015718 Nov 16 16:22 book.pdf
-rw------- 1 ubuntu ubuntu    1879 Nov 16 16:23 publication-manifest.json

f808b10988ffdfe949cc470f60df14bab14466b95e6c823f5f88b1bcb01eef1b  /tmp/sample-before/SHA256SUMS.txt
2c1d465ff46ed05a73f97c63d52183a675a7cc3370f058b058e48b5d8f465065  /tmp/sample-before/book-html.zip
02e72398d24736040eb571ccc976fa01bdecc574fba51ffa42ba5652a281cb44  /tmp/sample-before/book-source.zip
cdd1ceda880d5aca3566fa3177cb2a6fd21ab4e3e6c2ba987bd81369191ac389  /tmp/sample-before/book.docx
bbe2a974af04890bcfa8bd6a2f0a7547206badb1a29987c99f9bd851f81b6b29  /tmp/sample-before/book.md
0a05f6668a127f0b05b8b76806964b9655c0ab3ba4fd310a7c6e00eed20b4e4c  /tmp/sample-before/book.pdf
ff25654126f2d0003d85f418fed3c2a0a5d00b7103b7003b8572ee9c249606af  /tmp/sample-before/publication-manifest.json
```

#### After (Default 0055 Optimization)
```
total 2600
-rw------- 1 ubuntu ubuntu     479 Nov 16 16:24 SHA256SUMS.txt
-rw-rw-r-- 1 ubuntu ubuntu 1238664 Nov 16 16:23 book-html.zip
-rw-rw-r-- 1 ubuntu ubuntu  148058 Nov 16 16:23 book-source.zip
-rw-rw-r-- 1 ubuntu ubuntu   85744 Nov 16 16:24 book.docx
-rw-rw-r-- 1 ubuntu ubuntu  156640 Nov 16 16:24 book.md
-rw-rw-r-- 1 ubuntu ubuntu 1015718 Nov 16 16:23 book.pdf
-rw------- 1 ubuntu ubuntu    1879 Nov 16 16:24 publication-manifest.json

5ad533512a25437f71b79592bcfa7d3aac5c4aa0b25706b3a88700b772dffac9  /tmp/sample-after/SHA256SUMS.txt
17b1f99b87cac324bbd352011d55ae958ae333459d645cbb3289398d4dbd31e1  /tmp/sample-after/book-html.zip
02e72398d24736040eb571ccc976fa01bdecc574fba51ffa42ba5652a281cb44  /tmp/sample-after/book-source.zip
4d85e9f504b04dbde364084e182f528be09da1b6510b4d1001fb7a50b0437e0e  /tmp/sample-after/book.docx
bbe2a974af04890bcfa8bd6a2f0a7547206badb1a29987c99f9bd851f81b6b29  /tmp/sample-after/book.md
0a05f6668a127f0b05b8b76806964b9655c0ab3ba4fd310a7c6e00eed20b4e4c  /tmp/sample-after/book.pdf
79cd974920d79dae9de7a158c12088bc173c5a0524446620add256f11b977266  /tmp/sample-after/publication-manifest.json
```

Comparison:
- `book.docx`: 87,838 B -> 85,744 B (-2,094 B saved, hashes differ)
- `book-html.zip`: 1,241,802 B -> 1,238,664 B (-3,138 B saved, hashes differ)
- `book-source.zip`: 148,058 B (identical bytes and SHA256)
- `book.md`: 156,640 B (identical bytes and SHA256)
- `book.pdf`: 1,015,718 B (identical bytes and SHA256)

#### DOCX LibreOffice Validation
```bash
soffice --headless --convert-to pdf /tmp/sample-after/book.docx --outdir /tmp/sample-after-docx-check
```
Output:
```
convert /tmp/sample-after/book.docx as a Writer document -> /tmp/sample-after-docx-check/book.pdf using filter : writer_pdf_Export
```
The DOCX opens and converts cleanly with exit code 0.

### 4. Real Book Verification (`solutions-architecture-handbook`)

Fixture Commit: `1fd4f194776c6ffb022fc636810ef31141962c70`
Profile: `1.1.0`

#### Asset Size Comparison

| Asset | Platform Before (PR 87) | Platform After (0055) | v3.0.0 Release | Delta vs PR 87 | Delta vs v3.0.0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| PDF | 21,360,875 | 21,360,893 | 16,030,616 | +18 B | +5,330,277 B |
| DOCX | 16,253,460 | **12,394,904** | 12,416,306 | **-3,858,556 B (-23.74%)** | **-21,402 B (-0.17%)** |
| HTML zip | 17,872,824 | **14,025,705** | 14,125,177 | **-3,847,119 B (-21.53%)** | **-99,472 B (-0.70%)** |

Both DOCX and HTML ZIP successfully close the size gap and are smaller than the v3.0.0 release.

#### Build Hashes (`/tmp/codex-pr87-round3-dist-0055`)
```
13bf5cf4c87249d925206af75c0d5a71353e711ebafebc585ba4cd332a8634a0  book-html.zip
2c6b83682eba61eb80d4c03242c42fb03d13d91c32d154b45ed78518e3d3d61d  book-source.zip
b89869153c383619fec490f0e260d92129612d8234860d05f2fdd3b7a7bb30fb  book.docx
8d706a13ebe566ca06d813d68dec99c332ea2ffc4f2b3e0f97bcfdf773e7ac04  book.md
3339cd74c0f7e9a3bb1567cb02f5a3327b39e4a819f4069d1d3c0eb226ff4872  book.pdf
a7dba1dd90880ce7a7d2eca024cb26a9f6a82412b19f8e962105e3f4dfce99fc  publication-manifest.json
0cc5ec125bf10d1fb8430df380071864d31c14ff01035395a67abe5515e1448f  SHA256SUMS.txt
```

#### Image Pixel Equality Verification (121/121 Images Decoded & Checked)
```
HTML zip contains 121 PNGs, DOCX contains 121 PNGs
Pixel equality check passed for all 121/121 images!
```

#### Real Book Build Wall-Clock Timing Cost (121 Diagrams)

Measurement on the 121 diagram files from `solutions-architecture-handbook`:
- **PNG optimization pass (`optimize_staged_pngs`)**: **110.15s** wall-clock time across 121 PNG diagrams (saving 4,828,881 bytes, 17,504,985 -> 12,676,104 uncompressed bytes).
- **Total full book build time**: **~4m45s (285s)**.
- **Cost proportion**: The lossless raster decoding, recompression, and bit-level pixel equality verification pass accounts for ~38% of the total build wall-clock time, resulting in a 27.6% reduction in uncompressed image size and a 23.7% reduction in final DOCX package size with zero loss in visual quality or fidelity.

#### PR 87 Parity Script Execution
```bash
python3 /tmp/codex-pr87-round3-compare.py
```
Output:
```
HTML Figure counts 121 121 full ordered equality True
HTML Figure chapter/appendix count 121 ordered equality True
HTML Figure other labels [] => []
DOCX BODY Figure counts 121 121 full ordered equality True
DOCX BODY Figure chapter/appendix ordered equality True
DOCX BODY Figure other labels [] => []
DOCX LIST Figure counts 121 121 core equality True
HTML Table counts 263 263 full ordered equality True
HTML Table chapter/appendix count 255 ordered equality True
HTML Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX BODY Table counts 263 263 full ordered equality True
DOCX BODY Table chapter/appendix ordered equality True
DOCX BODY Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX LIST Table counts 263 263 core equality True
PDF Figure appendix letter labels ['A.1']
PDF Table appendix letter labels ['A.1', 'A.2', 'B.1', 'B.10', 'B.11', 'B.12', 'B.13', 'B.14', 'B.2', 'B.3', 'B.4', 'B.5', 'B.6', 'B.7', 'B.8', 'B.9', 'C.1', 'D.1', 'E.1', 'E.10', 'E.2', 'E.3', 'E.4', 'E.5', 'E.6', 'E.7', 'E.8', 'E.9', 'F.1', 'F.10', 'F.11', 'F.2', 'F.3', 'F.4', 'F.5', 'F.6', 'F.7', 'F.8', 'F.9', 'G.1', 'H.1', 'H.10', 'H.11', 'H.12', 'H.13', 'H.14', 'H.15', 'H.16', 'H.17', 'H.18', 'H.2', 'H.3', 'H.4', 'H.5', 'H.6', 'H.7', 'H.8', 'H.9', 'I.1', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'I.15', 'I.16', 'I.17', 'I.18', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.8', 'I.9', 'J.1', 'J.2', 'J.3', 'J.4', 'J.5', 'J.6', 'J.7']
PDF BODY Figure counts 121 121 full ordered equality True
PDF LIST Figure counts 121 121 full ordered equality True
PDF BODY Table counts 263 263 full ordered equality True
PDF LIST Table counts 263 263 full ordered equality True
PDF list extraction equality True
Comparison complete: full HTML/DOCX body/list/PDF body/list sequences equal to v3.0.0.
```
Exit code: `0`.

