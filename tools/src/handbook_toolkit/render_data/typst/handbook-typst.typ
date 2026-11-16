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
#let handbook-appendix-state = state("handbook-appendix-start", none)

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
#let handbook-numbering(..nums) = context {
  let parts = nums.pos()
  let ch = parts.first()
  let app-start = handbook-appendix-state.get()
  if app-start != none and ch >= app-start {
    let app-idx = ch - app-start + 1
    if parts.len() == 1 {
      numbering("A.", app-idx)
    } else {
      numbering("A.1", app-idx, ..parts.slice(1))
    }
  } else {
    if parts.len() == 1 {
      numbering("1.", ch)
    } else {
      numbering("1.1", ..parts)
    }
  }
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
  if it.numbering != none {
    counter(figure.where(kind: "quarto-float-tbl")).update(0)
    counter(figure.where(kind: "quarto-float-fig")).update(0)
    counter(figure.where(kind: table)).update(0)
    counter(figure.where(kind: image)).update(0)
  }
  it
}

// Table and figure numbers follow the chapter, as they do in HTML and DOCX.
// Front matter has no chapter number, so its floats use 0.N continuous numbering.
// Appendices use lettered counters (A.1, B.1...).
#let handbook-front-tbl = counter("handbook-front-tbl")
#let handbook-front-fig = counter("handbook-front-fig")

#show figure.where(kind: "quarto-float-tbl"): it => context {
  let ch = counter(heading).get().first()
  if ch == 0 {
    handbook-front-tbl.step()
  }
  it
}
#show figure.where(kind: "quarto-float-fig"): it => context {
  let ch = counter(heading).get().first()
  if ch == 0 {
    handbook-front-fig.step()
  }
  it
}

#show figure.where(kind: "quarto-float-tbl"): set figure(numbering: n => context {
  let chapter = counter(heading).get().first()
  let app-start = handbook-appendix-state.get()
  if chapter == 0 {
    "0." + str(handbook-front-tbl.get().first())
  } else if app-start != none and chapter >= app-start {
    let app-idx = chapter - app-start + 1
    numbering("A.1", app-idx, n)
  } else {
    numbering("1.1", chapter, n)
  }
})

#show figure.where(kind: "quarto-float-fig"): set figure(numbering: n => context {
  let chapter = counter(heading).get().first()
  let app-start = handbook-appendix-state.get()
  if chapter == 0 {
    "0." + str(handbook-front-fig.get().first())
  } else if app-start != none and chapter >= app-start {
    let app-idx = chapter - app-start + 1
    numbering("A.1", app-idx, n)
  } else {
    numbering("1.1", chapter, n)
  }
})

#set figure(numbering: n => context {
  let chapter = counter(heading).get().first()
  let app-start = handbook-appendix-state.get()
  if chapter == 0 {
    "0." + str(n)
  } else if app-start != none and chapter >= app-start {
    let app-idx = chapter - app-start + 1
    numbering("A.1", app-idx, n)
  } else {
    numbering("1.1", chapter, n)
  }
})

// Outline entry for figures and tables in List of Figures / List of Tables
#show outline.entry: it => {
  if it.element.func() == figure {
    let loc = it.element.location()
    let ch = counter(heading).at(loc).first()
    let num = it.element.counter.at(loc).first()
    let app-start = handbook-appendix-state.at(loc)
    let is-tbl = it.element.kind == "quarto-float-tbl" or it.element.kind == table
    let sup = if it.element.supplement != auto { it.element.supplement } else if is-tbl { "Table" } else { "Figure" }
    let num-str = if ch == 0 {
      let f_num = if is-tbl { handbook-front-tbl.at(loc).first() + 1 } else { handbook-front-fig.at(loc).first() + 1 }
      "0." + str(f_num)
    } else if app-start != none and ch >= app-start {
      let app-idx = ch - app-start + 1
      numbering("A.1", app-idx, num)
    } else {
      numbering("1.1", ch, num)
    }
    let pg = counter(page).at(loc).first()
    link(loc)[
      #sup #num-str #h(0.5em) #it.element.caption.body #box(width: 1fr, it.fill) #pg
    ]
  } else {
    it
  }
}

// Contents -------------------------------------------------------------------

// Tables ---------------------------------------------------------------------
#set table(
  stroke: (x: none, y: 0.5pt + hb-border),
  inset: (x: 7pt, y: 6pt),
  fill: (_, y) => if y == 0 { hb-accent-solid } else { hb-surface },
)
#show table.cell.where(y: 0): set text(fill: hb-on-solid, weight: "bold")
#show table.cell: set block(breakable: false)
#show table.cell: set text(hyphenate: false)
#show table.cell: set par(justify: false)
#show table: it => align(center, block(radius: hb-card-radius, clip: true, breakable: true)[#it])

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
    // Data tables keep the shared surface inside callouts.
    #set table(fill: (_, y) => if y == 0 { hb-accent-solid } else { hb-surface })
    #body
  ]
}
