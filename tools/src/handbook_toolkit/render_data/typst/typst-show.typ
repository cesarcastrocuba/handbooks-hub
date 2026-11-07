#import "@preview/orange-book:0.7.1": book, part, chapter, appendices

#set text(font: ("Selawik", "Liberation Sans", "DejaVu Sans"), size: 10pt, fill: rgb("#161616"), lang: "en")
#show raw: set text(font: ("Cascadia Code", "DejaVu Sans Mono"))

#show: book.with(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
$endif$
$if(date)$
  date: "$date$",
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
  main-color: rgb("#161616"),
  margin: (x: 2.2cm, top: 2.2cm, bottom: 2.2cm),
  heading-style: 0,
  padded-heading-number: false,
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
  supplement-chapter: "Chapter",
)

// Headings matching Solutions Architecture Handbook:
// Level 1: bold 21pt, #161616 (near-black / negro), no colored boxes
#show heading.where(level: 1): it => {
  v(1.5em)
  text(size: 21pt, weight: "bold", fill: rgb("#161616"))[#it.body]
  v(1em)
}

// Level 2: bold 14pt, #161616 (near-black / negro), light gray bottom border #e1dfdd
#show heading.where(level: 2): it => {
  v(1.2em)
  block(
    width: 100%,
    stroke: (bottom: 0.6pt + rgb("#e1dfdd")),
    inset: (bottom: 4pt),
    text(size: 14pt, weight: "bold", fill: rgb("#161616"))[#it.body]
  )
  v(0.6em)
}

#show heading.where(level: 3): it => {
  v(1em)
  text(size: 11.5pt, weight: "bold", fill: rgb("#161616"))[#it.body]
  v(0.5em)
}

#show heading.where(level: 4): it => {
  v(0.8em)
  text(size: 10.5pt, weight: "bold", fill: rgb("#605e5c"))[#it.body]
  v(0.4em)
}
