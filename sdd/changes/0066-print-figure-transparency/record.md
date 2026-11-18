# Change 0066 — Raster figures blend with the page in PDF and Word

Implementer OpenCode 2; reviewer and merger Claude. Branch `fix/0066-print-figure-transparency`
from main `2bc6acf`. No version bump or tag; it joins toolkit 0.14.0, which is not tagged yet.

Owner finding from the template 1.9.0 previews: the print editions still showed a white box around
raster figures. The Typst page and the Word background are the cream canvas `#F6F1E7`, while the SA
PNGs are opaque Graphviz images with a white background (88 RGBA and 33 RGB). Change `0061` fixed
only HTML, through `mix-blend-mode: multiply` in the light theme.

## Design

`print_figures.py` stages a print-only copy of a white-backed PNG and points the Typst and Word
Markdown at it. The pairs of white-to-transparent pixels use GIMP-style colour-to-alpha: the pixel is
first composited over white (which folds an existing alpha into the visible colour), then
`a = max_i((255 - c_i) / 255)` and `c'_i = (c_i - 255 * (1 - a)) / a` for `a > 0`. Composited over
white it reproduces the original pixels; over the cream page it blends like the HTML multiply. The
output is RGBA8, non-interlaced, filter 0, zlib level 9, with `pHYs` and the other valid ancillary
chunks preserved, so it is byte-deterministic and keeps the physical size that `0061` uses.

The fast path skips all-white rows and computes opaque pixels without the over-white composite;
a reference per-pixel implementation in the tests asserts that the output bytes are identical.
It converts the 121 SA figures in 185.8 s, down from 340 s (~6 min) for the straightforward loop.

Only a raster with a white canvas is converted: an 8-bit, non-interlaced, RGB or RGBA PNG whose
one-pixel perimeter is at least 90 % near white (every channel ≥ 250). A photograph, a coloured
border, palette/16-bit/interlaced PNGs, JPEG, WebP and every other format keep the original bytes,
because colour-to-alpha would tint their non-white content over cream. SVG is untouched. The rule
derives nothing from the book and needs no per-figure list.

The staged copy lives under `handbook-render/print-figures/<workspace-relative path>`. The entry
Markdown is rewritten for the typst and docx renders and restored before the HTML and Markdown
renders, so HTML keeps the original PNG (light multiply, dark readable white) and the two writers
reference different files. Source bytes in the book repository are never modified; figure ids,
widths, captions, anchors and the Markdown edition are unchanged.

## Evidence

All runs in this round: hub branch `fix/0066-print-figure-transparency` (main `2bc6acf`); SA book
`637caf689d96810f4c087c38dfcac994568cb9f7`; sample `8ed1b7035430ab3dc25fb65d712577bc197394ef`;
before = the toolkit-0.14.0 release build of the same book content without this change
(`9dfbfe2`, 514 pages, 16,019,203 B after qpdf). Local Quarto 1.11.9, Typst 0.15.1, LibreOffice
24.2.7.2, qpdf 11.9.0 and poppler 24.02.

### 1. Unit tests

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_print_figures.py -v
Ran 9 tests in 0.016s
OK
```

The tests cover the exact round trip over white for RGB and for RGBA with existing alpha (maximum
channel error 1 from rounding), determinism, a non-white border, a non-RGB PNG, the fast path against
the reference bytes, the staging rewrite/restore and inline-code protection. The synthetic book test
also asserts that HTML keeps the original PNG pixels and that the Word media PNG is RGBA with a
transparent corner.

### 2. Pure-white area on figure pages, SA PDF at 100 dpi

`pdftoppm` renders every page that carries one of the 121 raster figures; pure white is counted on
the page and inside the figure boxes:

```text
$ .venv/bin/python white_audit.py <before SA PDF> white-before.json
{
  "pdf": ".../release/book.pdf",
  "pages_with_figures": 121,
  "white_pixels_on_figure_pages": 26039948,
  "white_pixels_in_figure_boxes": 25913939
}
$ .venv/bin/python white_audit.py <after SA PDF> white-after.json
{
  "pdf": "/tmp/opencode/oc2-0066/release-sa/book.pdf",
  "pages_with_figures": 121,
  "white_pixels_on_figure_pages": 116569,
  "white_pixels_in_figure_boxes": 0
}
```

No pure-white pixel remains in any figure box; the residual page count is page text and rules.

Figures 1.2 and 1.4, dominant colour inside the figure box at 100 dpi:

```text
before  fig-1-2 page 34: (255,255,255) 131000 px, (242,242,242) 46190 px
        fig-1-4 page 44: (255,255,255) 199857 px, (242,242,242) 54383 px
after   fig-1-2 page 34: (246,241,231) 131079 px, (233,228,219) 46346 px
        fig-1-4 page 44: (246,241,231) 199927 px, (233,228,219) 54548 px
```

The empty canvas is now exactly `246,241,231`; the light-grey node fill (`242,242,242`) becomes
`233,228,219`, which is cream multiplied by the same ratio, matching the HTML blend.

### 3. Word

```text
$ .venv/bin/python docx_audit.py release-sa/book.docx
figure media with alpha: 121 of 121
transparent corner pixels verified on 5 images
```

The DOCX embeds 121 RGBA figure PNGs with transparent corners. The LibreOffice rendering of that
DOCX shows the figure on the page colour, not on white:

```text
$ .venv/bin/python figure_page_audit.py <DOCX-as-LibreOffice.pdf>
  fig-1-2 page 51: (246,241,231) 130267 px, (233,228,219) 45964 px
  fig-1-4 page 65: (246,241,231) 199334 px, (233,228,219) 54583 px
```

### 4. Widths, HTML and sample

The `0061` width check, adapted to assert the Word media has alpha instead of unchanged Word pixels:

```text
$ .venv/bin/python widths_check.py <after SA payload> sa-0066
HTML widths + raster class: 121/121; PDF widths + image/caption body bounds: 121/121; DOCX widths + RGBA media: 121/121
maximum PDF image + caption height: 603.459 pt; body: 705.827 pt
$ .venv/bin/python html_audit.py <after SA book-html.zip>
HTML original PNGs verified: 121 of 121
```

Every figure keeps its stated width in HTML, PDF and DOCX; HTML references the original paths and
its decoded pixels equal the book's PNGs. The sample's only figure is SVG: its PDF is still 61 pages
and the SVG in `book-html.zip` is byte-identical to the source.

### 5. PDF size and the build gates

The after release build (qpdf on) records:

```text
manifest optimization.pdf: optimized, 18140235 -> 10683944 bytes (7456291 saved), qpdf 11.9.0
book.pdf: 514 pages, 10683944 bytes
```

The previous release PDF of the same content was 16,019,203 bytes. Transparent pixels compress
better, so the compacted PDF shrinks to 10.7 MB rather than growing.

```text
$ make full PYTHON=.venv/bin/python
Ran 558 tests in 601.182s

OK (skipped=3)
...
VERIFY (full): 7 check(s), 0 problem(s)
```

### 6. CI

```text
$ gh run view 44207727480
checks success, quickstart success, template-install success, wheel-install success,
publication-build success, edition-preview (template|sample|solutions-architecture) success
```

The downloaded SA artifact is byte-identical to the local release build
(`sha256 fd4d9c47524cd48cc1792e5012e075474436e78490692de86ff52ec9b4474840` for both), and the CI
recheck prints the same numbers: 121 figure pages, **0** pure-white pixels in figure boxes,
121/121 Word figure media with alpha, 121/121 HTML originals, 121/121 widths in HTML/PDF/DOCX,
514 pages; the CI sample stays at 61 pages with a byte-identical SVG.
