#import "@preview/orange-book:0.7.1": book, part, chapter, appendices

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
  main-color: rgb("#1B365D"),
  margin: (x: 2.2cm, top: 2.2cm, bottom: 2.2cm),
  heading-style: 1,
  padded-heading-number: false,
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
  supplement-chapter: "Chapter",
)

#show heading.where(level: 2): it => {
  v(1.2em)
  let num = if it.numbering != none {
    counter(heading).display(it.numbering) + " "
  } else { "" }
  block(
    width: 100%,
    stroke: (bottom: 0.6pt + rgb("#e1dfdd")),
    inset: (bottom: 4pt),
    text(size: 14pt, weight: "bold", fill: rgb("#1b365d"))[#num#it.body]
  )
  v(0.6em)
}
