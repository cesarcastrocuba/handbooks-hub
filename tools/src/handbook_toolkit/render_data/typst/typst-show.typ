// Portions adapted from the typst-show partial of Quarto.
// Copyright (c) 2020-2024 Posit Software, PBC. MIT License:
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// Handbook print layout: replaces the Quarto orange-book book layout.
//
// The reference handbook renders its print edition with Quarto's plain
// `article` layout: a simple title block, an explicit Contents outline and
// unindented, justified paragraphs. orange-book adds a framed cover, odd-page
// chapter breaks, a bracketed outline and first-line paragraph indents, so it
// is not imported here. Quarto's book filter still emits `part` and
// `appendices` calls, so compatible definitions are provided below.

#set text(font: ("Liberation Sans",), size: 10pt, fill: rgb("#161616"), lang: "en")
#show raw: set text(font: ("JetBrains Mono",))

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
  font: ("Liberation Sans",),
  fontsize: 10pt,
  heading-family: ("Liberation Sans",),
  codefont: ("JetBrains Mono",),
  sectionnumbering: handbook-numbering,
  toc: false,
  doc,
)
