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

#show heading: set text(font: hb-display-font)
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
  counter(figure.where(kind: "quarto-float-tbl")).update(0)
  it
}

// Table numbers follow the chapter, as they do in HTML and DOCX. Front matter
// has no chapter number, so its tables keep the flat number.
#set figure(numbering: n => {
  let chapter = counter(heading).get().first()
  if chapter == 0 { numbering("1", n) } else { numbering("1.1", chapter, n) }
})

// Contents -------------------------------------------------------------------

// Tables ---------------------------------------------------------------------
#set table(
  stroke: 0.5pt + hb-border,
  inset: (x: 7pt, y: 6pt),
  fill: (_, y) => if y == 0 { hb-accent-solid } else if calc.even(y) { hb-table-stripe } else { none },
)
#show table.cell.where(y: 0): set text(fill: hb-on-solid, weight: "bold")
#show table.cell: set block(breakable: false)
#show table.cell: set text(hyphenate: false)
#show table: it => align(center, it)

// Captions -------------------------------------------------------------------
#show figure.caption: it => align(center)[
  #text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#it.supplement #it.counter.display(it.numbering): #it.body]
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
    (hb-callout-warning-accent, hb-callout-warning-tint)
  } else if "Decision" in label {
    (hb-callout-important-accent, hb-callout-important-tint)
  } else if "Key Takeaway" in label {
    (hb-callout-tip-accent, hb-callout-tip-tint)
  } else if "Review Checklist" in label {
    (hb-callout-review-accent, hb-callout-review-tint)
  } else if "When to Use" in label {
    (hb-callout-note-accent, hb-callout-note-tint)
  } else {
    (hb-callout-note-accent, hb-callout-note-tint)
  }
  block(
    width: 100%,
    breakable: false,
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
    // Tables inside a callout use the box tint, never the alternating stripe.
    #set table(fill: (_, y) => if y == 0 { hb-accent-solid } else { none })
    #body
  ]
}
