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

#let handbook-fit-table(it, radius) = context {
  let full = measure(it, width: handbook-body-width()).height
  let limit = handbook-body-height()
  align(center, block(radius: radius, clip: true, sticky: true, breakable: full > limit, it))
}

#let handbook-fit-float(it) = context {
  let full = measure(it, width: handbook-body-width()).height
  let limit = handbook-body-height()
  let name = if it.has("label") { str(it.label) } else { "unlabelled" }
  block(breakable: full > limit)[#context [#metadata((event: "start", name: name, height: full.pt(), body: limit.pt(), page: counter(page).get().first())) <handbook-table-fit>]#it#context [#metadata((event: "end", name: name, page: counter(page).get().first())) <handbook-table-fit>]]
}
