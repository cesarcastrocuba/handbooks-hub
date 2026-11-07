// Handbook print layout: replaces the Quarto orange-book book layout.
//
// The reference handbook renders its print edition with Quarto's plain
// `article` layout: a simple title block, an explicit Contents outline and
// unindented, justified paragraphs. orange-book adds a framed cover, odd-page
// chapter breaks, a bracketed outline and first-line paragraph indents, so it
// is not imported here. Quarto's book filter still emits `part` and
// `appendices` calls, so compatible definitions are provided below.

#set text(font: ("Selawik", "Liberation Sans", "DejaVu Sans"), size: 10pt, fill: rgb("#161616"), lang: "en")
#show raw: set text(font: ("Cascadia Code", "DejaVu Sans Mono"))

// A book part is an unnumbered, outlined level-1 heading.
#let part(title) = heading(level: 1, numbering: none)[#title]

// Appendices keep their own literal labels ("Appendix A — …", "A.1 …"), which
// Quarto marks as unnumbered; the state is kept for appendix-aware numbering.
#let appendices(title, hide-parent: false, body) = {
  state("appendix-state", none).update(title)
  body
}

#show: doc => article(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  authors: (
$for(by-author)$
$if(it.name.literal)$
    ( name: [$it.name.literal$],
      affiliation: [],
      email: [] ),
$endif$
$endfor$
    ),
$endif$
$if(date)$
  date: [$date$],
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
  font: ("Selawik", "Liberation Sans", "DejaVu Sans"),
  fontsize: 10pt,
  heading-family: ("Selawik", "Liberation Sans", "DejaVu Sans"),
  codefont: ("Cascadia Code", "DejaVu Sans Mono"),
  sectionnumbering: handbook-numbering,
  toc: false,
  doc,
)
