// Technical Handbook Platform — Typst styling for book publishing
// Derived from Solutions Architecture Handbook visual language.
// Clean headings, themed alert boxes with accent borders, visible links,
// gray-headed tables, and running headers/footers with document title and license.

// Typography -----------------------------------------------------------------
#set text(font: hb-font, size: 10pt, fill: hb-text, lang: "en")
// Paragraphs are justified and never indented, as in the reference handbook.
#set par(leading: 0.65em, spacing: 1.05em, first-line-indent: 0pt, justify: true)
#show raw: set text(font: hb-code-font)
#show raw.where(block: true): set text(size: 8.8pt)

#show raw.where(block: true): set block(
  fill: hb-surface,
  stroke: 0.5pt + hb-border,
  inset: 8pt,
  radius: 2pt,
  width: 100%,
)

// Links: accessible blue
#show link: set text(fill: hb-accent)

#show emph: it => text(font: hb-font, style: "italic", it.body)

// Running headers & footers --------------------------------------------------
// Defaults (overridden by generated book-data.typ when present)
#let handbook-title = ""
#let handbook-license = "CC BY-SA 4.0"
#let handbook-running-header = "Practitioner reference"

#set page(
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 8.5pt, fill: hb-muted)
      #grid(
        columns: (1fr, auto),
        align: (left, right),
        [#handbook-title],
        [#handbook-running-header]
      )
      #v(-4pt)
      #line(length: 100%, stroke: 0.4pt + hb-border)
    ]
  },
  footer: context [
    #set text(size: 8.5pt, fill: hb-muted)
    #line(length: 100%, stroke: 0.4pt + hb-border)
    #v(2pt)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      [Licensed under #handbook-license],
      [Page #counter(page).display("1 of 1", both: true)]
    )
  ]
)

// Headings -------------------------------------------------------------------
// Chapters read "1. Title" and sections "1.1 Title", matching the DOCX and the
// reference handbook. Front matter, appendices and references arrive from
// Quarto as unnumbered headings and keep their literal labels. The layout in
// typst-show.typ passes this function to `article` as its section numbering.
#let handbook-numbering(..nums) = {
  let parts = nums.pos()
  if parts.len() == 1 { numbering("1.", ..parts) } else { numbering("1.1", ..parts) }
}
#set heading(numbering: handbook-numbering)

#show heading.where(level: 1): set text(size: 21pt, weight: "bold", fill: hb-text)
#show heading.where(level: 2): set text(size: 14pt, weight: "bold", fill: hb-text)
#show heading.where(level: 3): set text(size: 11.5pt, weight: "bold", fill: hb-text)
#show heading.where(level: 4): set text(size: 10.5pt, weight: "bold", fill: hb-text)

#show heading.where(level: 1): set block(above: 0pt, below: 12pt)
#show heading.where(level: 2): set block(
  above: 17pt, below: 7pt,
  stroke: (bottom: 0.6pt + hb-border),
  inset: (bottom: 3pt),
)
#show heading.where(level: 3): set block(above: 13pt, below: 4pt)
#show heading.where(level: 4): set block(above: 10pt, below: 3pt)

// Every front-matter page, chapter and appendix starts on a new page.
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  it
}

// Contents -------------------------------------------------------------------
// Document Control sits on its own page after the Contents and is not listed,
// as in the reference handbook.
#show outline.entry: it => {
  let body = it.element.body
  if it.element.func() == heading and body.has("text") and body.text == "Document Control" {
    none
  } else {
    it
  }
}

// Tables ---------------------------------------------------------------------
#set table(
  stroke: 0.5pt + hb-border,
  inset: (x: 7pt, y: 6pt),
  fill: (_, y) => if y == 0 { hb-accent-solid } else { white },
)
#show table.cell.where(y: 0): set text(fill: hb-on-solid, weight: "bold")
#show table.cell: set block(breakable: false)
#show table.cell: set text(hyphenate: false)
#show table: it => align(center, it)

// Captions -------------------------------------------------------------------
#show figure.caption: it => align(center)[
  #text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#it.body]
]
#show figure.where(kind: "quarto-float-tbl"): set figure.caption(position: bottom)
#show figure.where(kind: "quarto-float-tbl"): set block(breakable: true)

// Callouts / Themed Alert Boxes ---------------------------------------------
#let callout(
  body: [],
  title: "Callout",
  background_color: hb-border,
  icon: none,
  icon_color: black,
  body_background_color: white,
) = {
  let label = repr(title)
  let (accent, tint) = if "Common Pitfall" in label {
    (rgb("#D83B01"), rgb("#FDF3F0"))
  } else if "Decision" in label {
    (rgb("#5C2D91"), rgb("#F5F0FA"))
  } else if "Key Takeaway" in label {
    (rgb("#107C10"), rgb("#F1FAF1"))
  } else if "When to Use" in label {
    (rgb("#0065B3"), rgb("#EFF6FC"))
  } else {
    (rgb("#0065B3"), rgb("#F4F9F9"))
  }
  block(
    width: 100%,
    breakable: true,
    fill: tint,
    stroke: (
      left: 4pt + accent,
      top: 0.5pt + hb-border,
      right: 0.5pt + hb-border,
      bottom: 0.5pt + hb-border,
    ),
    inset: (left: 10pt, right: 10pt, top: 8pt, bottom: 8pt),
    above: 10pt,
    below: 10pt,
  )[
    #if "Note" not in label [
      #text(weight: "bold", fill: accent)[#title]
      #v(3pt)
    ]
    #body
  ]
}
