// Technical Handbook Platform — Learn-style Typst styling for book publishing
// Derived from Solutions Architecture Handbook visual language.
// Clean headings, themed alert boxes with accent borders, visible links,
// gray-headed tables, and running headers/footers with document title and license.

// Typography -----------------------------------------------------------------
#set text(font: ("Selawik", "Liberation Sans", "DejaVu Sans"), size: 10pt, fill: rgb("#161616"), lang: "en")
#set par(leading: 0.65em, spacing: 1.05em)
#show raw: set text(font: ("Cascadia Code", "DejaVu Sans Mono"))
#show raw.where(block: true): set text(size: 8.8pt)

#show raw.where(block: true): set block(
  fill: rgb("#f5f5f5"),
  stroke: 0.5pt + rgb("#e1dfdd"),
  inset: 8pt,
  radius: 2pt,
  width: 100%,
)

// Links: Microsoft Learn blue
#show link: set text(fill: rgb("#0065b3"))

#show emph: it => text(font: ("Liberation Sans", "DejaVu Sans"), style: "italic", it.body)

// Running headers & footers --------------------------------------------------
#set page(
  margin: (x: 2.2cm, top: 2.2cm, bottom: 2.2cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 8.5pt, fill: rgb("#605E5C"))
      #grid(
        columns: (1fr, auto),
        align: (left, right),
        [#document.title],
        [Practitioner reference]
      )
      #v(-4pt)
      #line(length: 100%, stroke: 0.4pt + rgb("#E1DFDD"))
    ]
  },
  footer: context [
    #set text(size: 8.5pt, fill: rgb("#605E5C"))
    #line(length: 100%, stroke: 0.4pt + rgb("#E1DFDD"))
    #v(2pt)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      [Licensed under CC BY-SA 4.0],
      [Page #counter(page).display("1 of 1", both: true)]
    )
  ]
)

// Headings -------------------------------------------------------------------
#show heading.where(level: 1): set text(size: 21pt, weight: "bold", fill: rgb("#161616"))
#show heading.where(level: 2): set text(size: 14pt, weight: "bold", fill: rgb("#161616"))
#show heading.where(level: 3): set text(size: 11.5pt, weight: "bold", fill: rgb("#161616"))
#show heading.where(level: 4): set text(size: 10.5pt, weight: "bold", fill: rgb("#605E5C"))

#show heading.where(level: 1): set block(above: 0pt, below: 12pt)
#show heading.where(level: 2): set block(
  above: 17pt, below: 7pt,
  stroke: (bottom: 0.6pt + rgb("#E1DFDD")),
  inset: (bottom: 3pt),
)
#show heading.where(level: 3): set block(above: 13pt, below: 4pt)
#show heading.where(level: 4): set block(above: 10pt, below: 3pt)

// Tables ---------------------------------------------------------------------
#set table(
  stroke: 0.5pt + rgb("#E1DFDD"),
  inset: (x: 7pt, y: 6pt),
  fill: (_, y) => if y == 0 { rgb("#F2F2F2") } else { white },
)
#show table.cell.where(y: 0): set text(fill: rgb("#161616"), weight: "bold")
#show table.cell: set block(breakable: false)
#show table.cell: set text(hyphenate: false)
#show table: it => align(center, it)

// Captions -------------------------------------------------------------------
#show figure.caption: it => align(center)[
  #text(style: "italic", font: ("Liberation Sans", "DejaVu Sans"), size: 9pt, fill: rgb("#605E5C"))[#it.body]
]
#show figure.where(kind: "quarto-float-tbl"): set figure.caption(position: bottom)
#show figure.where(kind: "quarto-float-tbl"): set block(breakable: true)

// Callouts / Themed Alert Boxes ---------------------------------------------
#let callout(
  body: [],
  title: "Callout",
  background_color: rgb("#dddddd"),
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
      top: 0.5pt + rgb("#E1DFDD"),
      right: 0.5pt + rgb("#E1DFDD"),
      bottom: 0.5pt + rgb("#E1DFDD"),
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
