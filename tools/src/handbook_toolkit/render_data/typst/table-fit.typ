// Context is transparent to pagination; layout() would box and clip a tall table.
#let handbook-margin(side) = {
  let m = page.margin
  if type(m) == dictionary { m.at(side) } else { m }
}
#let handbook-body-height() = {
  let top = handbook-margin("top")
  let bottom = handbook-margin("bottom")
  let h = page.height
  h - top.length - top.ratio * h - bottom.length - bottom.ratio * h
}
#let handbook-body-width() = {
  let left = handbook-margin("left")
  let right = handbook-margin("right")
  let w = page.width
  w - left.length - left.ratio * w - right.length - right.ratio * w
}

// The leading heading/short introduction is part of the float's first-page budget.
#let handbook-float-budget = state("handbook-float-budget", none)
#let handbook-figure-start = state("handbook-figure-start", (page: 1, x: 0pt, y: 0pt))
#let handbook-float-group(lead: [], body: []) = context {
  let previous = handbook-float-budget.get()
  let probe = block(height: 1pt)[#rect(width: 1pt, height: 1pt)]
  let leading = measure([#block(sticky: true, lead)#probe], width: handbook-body-width()).height - 1pt
  // A breakable wrapper around an image would scale it down to the remaining space;
  // measure the group, then keep it unbreakable when it fits the page body.
  let full = measure([#block(sticky: true, lead)#probe#body], width: handbook-body-width()).height - 1pt
  handbook-float-budget.update(handbook-body-height() - leading)
  if full <= handbook-body-height() {
    block(breakable: false)[#lead#body]
  } else {
    lead
    body
  }
  handbook-float-budget.update(previous)
}

// A figure stays right after the text that introduces it, as in the Word edition
// (docx_figure_place). Every raster figure prints at PRINT-SCALE of its stated
// size (Owner request 2026-11-23: figures looked large). When its group would
// still move whole to the next page and leave a gap of at least MIN-GAP of the
// body in front of it, it is scaled further to fit that gap. Neither step goes
// below MIN-NATURAL of the image's natural size, which keeps diagram text at
// 8 pt or more.
#let handbook-print-scale = 0.85
#let handbook-min-gap = 0.15
#let handbook-min-natural = 0.75
#let handbook-gap-safety = 10pt

// The printed width an image asks for, from its own width argument.
#let handbook-printed-width(im, natural, width) = {
  let w = im.width
  if type(w) == ratio { w * width }
  else if type(w) == relative { w.length + w.ratio * width }
  else if type(w) == length { w }
  else { calc.min(natural, width) }
}

// The print scale of one image, bounded by the natural-size floor.
// A gap fit that would cross the floor is not applied: the figure moves to the
// next page at the print scale, as in docx_figure_place.decide. Round first: a
// factor that rounds to 1.0 must not apply a sub-pixel scale or record itself
// as scaled, matching docx_figure_place.print_scale.
#let handbook-print-factor(natural, printed, fit) = {
  let floor = calc.min(1, handbook-min-natural * natural / printed)
  let wanted = handbook-print-scale * fit
  calc.round(
    if wanted >= floor { wanted } else { calc.max(handbook-print-scale, floor) },
    digits: 4,
  )
}

// Scale every image of `body` by `fit` times the print scale, never below the
// natural-size floor. `open` is `p => image(p, alt: "handbook-natural")` written
// in the document, so that an image path resolves from the document and not from
// this file; the alt text marks that probe so this rule leaves it alone.
#let handbook-scale-images(body, open, width, fit) = {
  show image: im => if im.alt == "handbook-natural" { im } else {
    let natural = if open == none or type(im.source) != str { 0pt } else { measure(open(im.source)).width }
    let printed = handbook-printed-width(im, natural, width)
    if natural == 0pt or printed == 0pt { return im }
    let factor = handbook-print-factor(natural, printed, fit)
    if factor >= 1 { return im }
    [#metadata((event: "scaled", scale: factor, fit: fit, page: here().page())) <handbook-figure-fit>]
    // A relative width resolves against the text width inside the box, not
    // against the region that reflow has already scaled.
    scale(factor * 100%, reflow: true, box(width: width, align(center, im)))
  }
  body
}

// The gap gate and the gap fit are pure so that the 15% threshold and the 10 pt
// safety margin can be tested without building a page.
#let handbook-gap-admits(room, height, full) = {
  full > room and room >= handbook-min-gap * height and full <= height
}

#let handbook-gap-fit(full, room, pictures) = {
  let need = full - room + handbook-gap-safety
  if pictures > 0pt and need < pictures {
    calc.round((pictures - need) / pictures, digits: 4)
  } else {
    1.0
  }
}

#let handbook-figure-group(open: none, lead: [], body: []) = {
  // A zero-height block where the group starts if it stays: the end of the text
  // before it. It records its own position in a state; a bare metadata tag would
  // travel to the next page with the group, and a query for a labelled marker
  // kept the table measurement of the same document from converging.
  block(height: 0pt, below: 0pt, context handbook-figure-start.update(here().position()))
  context {
    let start = handbook-figure-start.get()
    let height = handbook-body-height()
    let width = handbook-body-width()
    let bottom = handbook-margin("bottom")
    let room = page.height - bottom.length - bottom.ratio * page.height - start.y
    let probe = block(height: 1pt)[#rect(width: 1pt, height: 1pt)]
    let printed = handbook-scale-images(body, open, width, 1.0)
    let full = measure([#block(sticky: true, lead)#probe#printed], width: width).height - 1pt
    let fit = 1.0
    if handbook-gap-admits(room, height, full) {
      let bare = measure([#block(sticky: true, lead)#probe#{ show image: none; body }], width: width).height - 1pt
      let pictures = full - bare
      fit = handbook-gap-fit(full, room, pictures)
    }
    let group = [#lead#handbook-scale-images(body, open, width, fit)]
    // Measure the height the group actually prints at. At the print scale `full`
    // already is that height; a gap fit can only make it smaller.
    let final = if fit < 1 {
      measure([#block(sticky: true, lead)#probe#group], width: width).height - 1pt
    } else {
      full
    }
    [#metadata((event: "group", room: room.pt(), full: full.pt(), final: final.pt(), fit: fit, page: start.page)) <handbook-figure-fit>]
    if final <= height { block(breakable: false, above: 0pt, group) } else { group }
  }
}

#let handbook-fit-table(it, radius) = context {
  // A local table show-set passes the caption reservation through native styles.
  let inset = block.inset
  let bottom = if type(inset) == dictionary { inset.at("bottom", default: inset.at("y", default: inset.at("rest", default: 0pt))) } else { inset }
  let reserve = if type(bottom) == relative { bottom.length + bottom.ratio * handbook-body-height() } else { bottom }
  set block(inset: 0pt)
  let full = measure(it, width: handbook-body-width()).height
  let budget = handbook-float-budget.get()
  let limit = (if budget == none { handbook-body-height() } else { budget }) - reserve
  // Reserve the caption below every fragment; reclaim it for the real caption.
  // Keep this padding outside the clipped surface so row corners stay rounded.
  let breakable = full > limit
  block(inset: (bottom: reserve), below: 0pt, breakable: breakable,
    align(center, block(radius: radius, clip: true, breakable: breakable, it)))
  // A weak negative block spacing collapses against the caption gap.
  v(-reserve, weak: false)
}

#let handbook-fit-float(it) = context {
  let full = measure(it, width: handbook-body-width()).height
  let budget = handbook-float-budget.get()
  let limit = if budget == none { handbook-body-height() } else { budget }
  let reserve = calc.max(0pt, full - measure(it.body, width: handbook-body-width()).height)
  show table: set block(inset: (bottom: reserve))
  let name = if it.has("label") { str(it.label) } else { "unlabelled" }
  block(breakable: full > limit)[#context [#metadata((event: "start", name: name, height: full.pt(), body: limit.pt(), page: counter(page).get().first())) <handbook-table-fit>]#it#context [#metadata((event: "end", name: name, page: counter(page).get().first())) <handbook-table-fit>]]
}
