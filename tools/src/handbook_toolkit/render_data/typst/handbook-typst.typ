// Technical Handbook Platform — Typst styling for book publishing
// Derived from Solutions Architecture Handbook visual language.
// Clean headings, themed alert boxes with accent borders, visible links,
// gray-headed tables, and running headers/footers with document title and license.

// Typography -----------------------------------------------------------------
#set text(font: hb-font, size: 9.5pt, fill: hb-text, lang: "en")
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
//
// The function stays plain: a `context` function cannot be resolved when Typst
// assembles the PDF bookmarks, which then lose the number and keep only the
// separating space (issue #99). Appendix headings are literal "Appendix A — …"
// and "A.1 …" text staged as unnumbered headings (change 0060), so no state
// lookup is needed here.
#let handbook-numbering(..nums) = {
  let parts = nums.pos()
  if parts.len() == 1 {
    numbering("1.", parts.first())
  } else {
    numbering("1.1", ..parts)
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
  counter(figure.where(kind: "quarto-float-tbl")).update(0)
  counter(figure.where(kind: "quarto-float-fig")).update(0)
  counter(figure.where(kind: table)).update(0)
  counter(figure.where(kind: image)).update(0)
  it
}

// Table and figure numbers follow the chapter, as they do in HTML and DOCX.
// Front matter has no chapter number, so its floats use 0.N continuous numbering.
// Appendices use lettered counters (A.1, B.1...).
#let handbook-front-tbl = counter("handbook-front-tbl")
#let handbook-front-fig = counter("handbook-front-fig")

#show figure.where(kind: "quarto-float-tbl"): it => context {
  let is-bm = it.has("label") and str(it.label).starts-with("tbl-bm-")
  let is-front = it.has("label") and str(it.label).starts-with("tbl-0-")
  let is-app = it.has("label") and str(it.label).matches(regex("^tbl-[a-z]+-[0-9]+$")).len() > 0
  if is-bm {
    let num-str = "BM." + str(it.label).slice("tbl-bm-".len())
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else if is-front {
    let num-str = "0." + str(it.label).slice("tbl-0-".len())
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else if is-app {
    let parts = str(it.label).split("-")
    let num-str = upper(parts.at(1)) + "." + parts.at(2)
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else {
    let ch = counter(heading).get().first()
    if ch == 0 {
      handbook-front-tbl.step()
    }
    it
  }
}
#show figure.where(kind: "quarto-float-fig"): it => context {
  let is-bm = it.has("label") and str(it.label).starts-with("fig-bm-")
  let is-front = it.has("label") and str(it.label).starts-with("fig-0-")
  let is-app = it.has("label") and str(it.label).matches(regex("^fig-[a-z]+-[0-9]+$")).len() > 0
  if is-bm {
    let num-str = "BM." + str(it.label).slice("fig-bm-".len())
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else if is-front {
    let num-str = "0." + str(it.label).slice("fig-0-".len())
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else if is-app {
    let parts = str(it.label).split("-")
    let num-str = upper(parts.at(1)) + "." + parts.at(2)
    show figure.caption: c => align(center)[#text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#c.supplement #num-str: #c.body]]
    it
  } else {
    let ch = counter(heading).get().first()
    if ch == 0 {
      handbook-front-fig.step()
    }
    it
  }
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
    let num-str = if it.element.has("label") and str(it.element.label).starts-with("tbl-bm-") {
      "BM." + str(it.element.label).slice("tbl-bm-".len())
    } else if it.element.has("label") and str(it.element.label).starts-with("fig-bm-") {
      "BM." + str(it.element.label).slice("fig-bm-".len())
    } else if it.element.has("label") and str(it.element.label).starts-with("tbl-0-") {
      "0." + str(it.element.label).slice("tbl-0-".len())
    } else if it.element.has("label") and str(it.element.label).starts-with("fig-0-") {
      "0." + str(it.element.label).slice("fig-0-".len())
    } else if it.element.has("label") and str(it.element.label).matches(regex("^(tbl|fig)-[a-z]+-[0-9]+$")).len() > 0 {
      let parts = str(it.element.label).split("-")
      upper(parts.at(1)) + "." + parts.at(2)
    } else if ch == 0 {
      let f_num = if is-tbl { handbook-front-tbl.at(loc).first() + 1 } else { handbook-front-fig.at(loc).first() + 1 }
      "0." + str(f_num)
    } else if app-start != none and ch >= app-start {
      let app-idx = ch - app-start + 1
      numbering("A.1", app-idx, num)
    } else {
      numbering("1.1", ch, num)
    }
    link(
      loc,
      it.indented([#sup #num-str], it.inner()),
    )
  } else {
    it
  }
}

#show ref: it => {
  let el = it.element
  if el != none and el.func() == figure and el.has("label") {
    let lbl = str(el.label)
    if lbl.matches(regex("^(tbl|fig)-[a-z]+-[0-9]+$")).len() > 0 {
      let parts = lbl.split("-")
      let is-tbl = el.kind == "quarto-float-tbl" or el.kind == table
      let sup = if el.supplement != auto { el.supplement } else if is-tbl { [Table] } else { [Figure] }
      let num-str = upper(parts.at(1)) + "." + parts.at(2)
      link(el.location(), [#sup #num-str])
    } else {
      it
    }
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
#import "handbook-render/typst/table-fit.typ": handbook-fit-table, handbook-fit-float, handbook-float-group, handbook-figure-group
#show table: it => handbook-fit-table(it, hb-card-radius)

// Figures -------------------------------------------------------------------
// A figure stays right after the text that introduces it (Owner decision
// 2026-11-23, as in the Word edition); handbook-figure-group only scales one that
// nearly fits the gap in front of it.

// Captions -------------------------------------------------------------------
#show figure.caption: it => align(center)[
  #text(style: "italic", font: hb-font, size: 9pt, fill: hb-muted)[#it.supplement #it.counter.display(it.numbering): #it.body]
]
#show figure.where(kind: "quarto-float-tbl"): set figure.caption(position: bottom)
#show figure.where(kind: "quarto-float-tbl"): set block(breakable: true)
#show figure.where(kind: "quarto-float-tbl"): handbook-fit-float

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
  // "Review Checklist" is tested before "Decision": a checklist title such as
  // "Architecture Review Checklist — Decisions" contains both.
  let (accent, tint) = if "Common Pitfall" in label {
    (hb-callout-warning-accent, hb-callout-warning-tint)
  } else if "Review Checklist" in label {
    (hb-callout-review-accent, hb-callout-review-tint)
  } else if "Decision" in label {
    (hb-callout-important-accent, hb-callout-important-tint)
  } else if "Key Takeaway" in label {
    (hb-callout-tip-accent, hb-callout-tip-tint)
  } else if "When to Use" in label {
    (hb-callout-note-accent, hb-callout-note-tint)
  } else {
    (hb-callout-note-accent, hb-callout-note-tint)
  }
  // A callout is never split across pages (Owner decision 2026-11-23); a
  // pitfall and its decision are separate boxes, so a pitfall can end a page.
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
