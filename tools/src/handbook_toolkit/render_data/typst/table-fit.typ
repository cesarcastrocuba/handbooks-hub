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
#let handbook-float-group(lead: [], body: []) = context {
  let previous = handbook-float-budget.get()
  let leading = measure([#block(sticky: true, lead)#block(height: 1pt)[#rect(width: 1pt, height: 1pt)]], width: handbook-body-width()).height - 1pt
  handbook-float-budget.update(handbook-body-height() - leading)
  block(breakable: true)[#block(sticky: true, lead)#body]
  handbook-float-budget.update(previous)
}

#let handbook-caption-reserve = state("handbook-caption-reserve", 0pt)

#let handbook-fit-table(it, radius) = context {
  let reserve = handbook-caption-reserve.get()
  let full = measure(it, width: handbook-body-width()).height
  let budget = handbook-float-budget.get()
  let limit = (if budget == none { handbook-body-height() } else { budget }) - reserve
  // Reserve the caption below every fragment; reclaim it for the real caption.
  // Keep this padding outside the clipped surface so row corners stay rounded.
  block(inset: (bottom: reserve), below: 0pt, breakable: full > limit,
    align(center, block(radius: radius, clip: true, breakable: full > limit, it)))
  // A weak negative block spacing collapses against the caption gap.
  v(-reserve, weak: false)
}

#let handbook-fit-float(it) = context {
  let full = measure(it, width: handbook-body-width()).height
  let budget = handbook-float-budget.get()
  let limit = if budget == none { handbook-body-height() } else { budget }
  let previous = handbook-caption-reserve.get()
  let reserve = calc.max(0pt, full - measure(it.body, width: handbook-body-width()).height)
  handbook-caption-reserve.update(reserve)
  let name = if it.has("label") { str(it.label) } else { "unlabelled" }
  block(breakable: full > limit)[#context [#metadata((event: "start", name: name, height: full.pt(), body: limit.pt(), page: counter(page).get().first())) <handbook-table-fit>]#it#context [#metadata((event: "end", name: name, page: counter(page).get().first())) <handbook-table-fit>]]
  handbook-caption-reserve.update(previous)
}
