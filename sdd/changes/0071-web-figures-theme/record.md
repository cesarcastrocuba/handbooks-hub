# Change 0071 — Web figures blend with the canvas; one chrome size

Implementer OpenCode 2; reviewer and merger Claude. Branch `fix/0071-web-figures-theme` from main
`a637501`. No version bump; the coordinator prepares toolkit 0.14.1 afterwards.

## A. Raster figures showed a white box in the light theme

`0061` added `body.quarto-light … img.handbook-raster { mix-blend-mode: multiply; }`, but it had no
effect on the deployed site: Figure 3.1 rendered pure white instead of the canvas. `reading.css` ran
`main section.level2` through the `handbook-reveal` keyframes with `animation-fill-mode: forwards`;
at rest the section kept `transform: translateY(0)`, i.e. `matrix(1,0,0,1,0,0)`, which creates a
stacking context with a transparent background. The image multiplied against that transparency, not
against the body canvas.

`main section.level2` now uses the same registered-custom-property reveal as the callouts and
figures: `opacity: var(--handbook-reveal-alpha)` and `top` from `--handbook-reveal-offset`, driven
by `handbook-object-reveal`. Nothing positioned or transformed remains at rest, so the multiply sees
the body canvas. The reduced-motion block is unchanged (the whole trigger block is already inside
`prefers-reduced-motion: no-preference`), and `.card` keeps its existing reveal.

## B. Dark theme inverts raster figures

The dark theme only now adds, with the light rule's selectors:

```css
body.quarto-dark .quarto-figure img.handbook-raster, … {
  filter: invert(1) hue-rotate(180deg);
  mix-blend-mode: screen;
}
```

Black becomes the dark canvas and the accent stays recognisably blue. SVG figures, PDF and DOCX are
unchanged. The sample's only figure is SVG (`lifecycle.svg`): it keeps its own `#F6F1E7` background
rectangle and `#1D2A2C` ink, so in the dark theme it reads as a cream card with dark lines rather
than an inverted figure. That is reported, not changed.

## C. The theme toggle moved the page 14 px

`design.book_scss()` set `navbar-padding-y` to `1rem` for the dark scheme and `0.5rem` for the light
one, so toggling grew the navbar from 56 px to 69.8 px and shifted all content down 14 px on every
site. Both schemes now use `0.5rem`. A unit test parses both generated SCSS maps and asserts the same
variable names and identical values for every non-colour variable, so a scheme-specific geometry,
type, radius or spacing cannot return.

## Tests

`tools/tests/test_reading_site.py` adds a Chromium fixture: a white PNG raster inside
`section.level2`, with the reveal CSS and the book layout CSS. For each loaded scheme it waits for the
reveal to settle and asserts:

- `getComputedStyle(section.level2).transform` is `none`;
- the figure's white centre pixel is exactly the light canvas (`#F6F1E7`) in the light theme and
  within 2 of the dark canvas in the dark theme;
- `#quarto-header` height and `#quarto-content` top are equal across the two loaded schemes and
  across a live light → dark toggle.

`tools/tests/test_design.py` adds the SCSS scheme-parity test.

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_reading_site.py -v
Ran 14 tests in 15.858s
OK
$ .venv/bin/python -m unittest discover -s tools/tests -p test_design.py
Ran 24 tests in 0.097s
OK
```

## Evidence

```text
$ make full PYTHON=.venv/bin/python
Ran 577 tests in 669.326s

OK
...
VERIFY (full): 7 check(s), 0 problem(s)
```

The CI edition preview of the Solutions Architecture book (this branch's toolkit) is measured with
Playwright on `ch03-architecture-decisions.html`, Figure 3.1:

```text
CI_EVIDENCE
```

Light and dark screenshots are committed next to this record as `figure-3-1-light.png` and
`figure-3-1-dark.png`.

## Known gaps

- The sample's SVG figure is not inverted (by design); on the dark canvas it shows its own cream
  card. SVG files would need the book to ship a dark variant.
- Portal templates are outside this change (change `0072`); the shared `book_scss` navbar value is the
  portal's source as well.
- PDF and DOCX are unchanged.
