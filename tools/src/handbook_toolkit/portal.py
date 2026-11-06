"""Generate the static handbook catalog; no manuscript content is mirrored."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import shutil
import tempfile

from .catalog import validate_catalog
from .validation import load_document, load_packaged_schema

CATEGORIES = {"architecture", "authoring", "cloud", "data", "engineering",
              "governance", "publishing", "security"}

STYLE = """
:root{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#142b3d;background:#f3f6f7;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}a{color:#075e63;text-underline-offset:4px}a:hover{text-decoration-thickness:2px}
button,select{font:inherit}button,a,select{touch-action:manipulation}:focus-visible{outline:3px solid #0c757c;outline-offset:4px}
.skip{position:absolute;left:1rem;top:-5rem;background:white;padding:1rem;z-index:2}.skip:focus{top:1rem}
.wrap{max-width:1120px;margin:auto;padding:0 1.5rem}nav{display:flex;justify-content:space-between;align-items:center;min-height:80px;border-bottom:1px solid #ccd8dc;gap:1rem}
.brand{font-weight:800;font-size:1.15rem;color:#142b3d;text-decoration:none}.brand span{color:#087077}
header{padding:4.5rem 0 3rem;background:linear-gradient(150deg,#e9f3f2,#f3f6f7 75%)}.eyebrow{font-size:.75rem;text-transform:uppercase;letter-spacing:.13em;font-weight:750;color:#075e63}
h1{font-size:clamp(2.4rem,6vw,4.2rem);line-height:1.08;letter-spacing:-.045em;max-width:850px;margin:.8rem 0 1.2rem}
.intro{max-width:650px;font-size:1.1rem;color:#405b6c;line-height:1.7}.statusline{font-size:.9rem;color:#405b6c;margin-top:2rem}
main{padding:2rem 0 4rem}h2{font-size:1.45rem;letter-spacing:-.02em}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;margin:1.5rem 0}
.filters{display:flex;gap:.5rem;flex-wrap:wrap}button,select{border:1px solid #b0c4ca;background:#fff;color:#173c48;border-radius:999px;min-height:44px;padding:.55rem .9rem}
button{cursor:pointer}button[aria-pressed=true]{background:#075e63;color:white;border-color:#075e63}.sort{display:flex;gap:.6rem;align-items:center;font-size:.88rem}
.results{color:#405b6c;font-size:.9rem;margin:1rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));gap:1.2rem}
.book{display:flex;flex-direction:column;background:#fff;border:1px solid #d0dcdf;border-radius:18px;padding:1.5rem;box-shadow:0 4px 16px #142b3d05}
.book h3{font-size:1.25rem;line-height:1.35;margin:.7rem 0}.summary{color:#405b6c;line-height:1.65;flex-grow:1}.tags{display:flex;gap:.4rem;flex-wrap:wrap}
.tag{font-size:.72rem;background:#eaf2f3;color:#315563;padding:.25rem .55rem;border-radius:5px}.version{font-family:ui-monospace,monospace;font-size:.8rem;color:#405b6c;margin-top:1rem}
.links{display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem}.read{font-weight:750}.assets{font-size:.82rem;display:flex;gap:.9rem;flex-wrap:wrap;margin-top:1rem}
.empty{background:#fff;border:1px dashed #9cb5bd;border-radius:20px;padding:3.5rem 2rem;text-align:center}.empty h3{font-size:1.5rem;margin:0 0 1rem}.empty p{max-width:550px;margin:auto;color:#405b6c;line-height:1.7}
.planned{margin:2rem 0;color:#405b6c;font-size:.9rem;line-height:1.8}.archived{color:#794514;font-weight:650;font-size:.8rem}footer{border-top:1px solid #ccd8dc;padding:2rem 0;color:#405b6c;font-size:.85rem;line-height:1.8}
[hidden]{display:none!important}@media(max-width:600px){header{padding-top:2.5rem}.wrap{padding:0 1rem}nav{font-size:.88rem}.sort{width:100%}.empty{padding:2rem 1rem}}
"""

SCRIPT = """
const grid=document.querySelector('.grid');
if(grid){
 const cards=Array.from(grid.querySelectorAll('.book'));
 let category='all';
 function update(){
  const mode=document.querySelector('#sort').value;
  cards.sort((a,b)=>mode==='latest'?b.dataset.date.localeCompare(a.dataset.date)||a.dataset.title.localeCompare(b.dataset.title,'en'):mode==='za'?b.dataset.title.localeCompare(a.dataset.title,'en'):a.dataset.title.localeCompare(b.dataset.title,'en'));
  let shown=0;
  for(const card of cards){card.hidden=category!=='all'&&!card.dataset.categories.split(' ').includes(category);if(!card.hidden)shown++;grid.append(card);}
  document.querySelector('#results').textContent=`Showing ${shown} of ${cards.length} handbooks`;
 }
 for(const button of document.querySelectorAll('[data-filter]')){
  button.addEventListener('click',()=>{category=button.dataset.filter;for(const item of document.querySelectorAll('[data-filter]'))item.setAttribute('aria-pressed',String(item===button));update();});
 }
 document.querySelector('#sort').addEventListener('change',update);
}
"""


def _card(book: dict) -> str:
    release = book["latest_release"]
    tags = "".join(f'<span class="tag">{escape(category.title())}</span>' for category in book["categories"])
    archived = '<span class="archived">Archived handbook</span>' if book["status"] == "archived" else ''
    return f'''<article class="book" data-title="{escape(book['title'], quote=True)}" data-date="{release['published_at']}" data-categories="{' '.join(book['categories'])}">
<div class="tags">{tags}</div>{archived}<h3>{escape(book['title'])}</h3><p class="summary">{escape(book['summary'])}</p>
<div class="version">v{release['version']} · <time datetime="{release['published_at']}">{release['published_at']}</time></div>
<div class="links"><a class="read" href="{escape(book['reading_url'], quote=True)}">Read handbook →</a><a href="{escape(release['url'], quote=True)}">Release downloads</a></div>
<div class="assets"><a href="{escape(release['manifest_url'], quote=True)}">Manifest</a><a href="{escape(release['checksums_url'], quote=True)}">Checksums</a></div></article>'''


def build_portal(catalog: Path, output: Path) -> Path:
    """Build a fresh static directory from a validated catalog; never fetch drafts.

    This offline build checks structure. Release bytes and URLs must independently
    verify before the catalog update is accepted and this directory is deployed.
    """
    result = validate_catalog(catalog, load_packaged_schema("catalog.schema.json"))
    if not result.ok:
        raise ValueError("invalid catalog: " + "; ".join(map(str, result.issues)))
    books = sorted(load_document(catalog)["books"], key=lambda book: book["title"].casefold())
    categories = sorted({category for book in books for category in book["categories"]})
    unknown = set(categories) - CATEGORIES
    if unknown:
        raise ValueError("unknown catalog categories: " + ", ".join(sorted(unknown)))
    published = sum(book["status"] == "published" for book in books)
    archived = len(books) - published
    if books:
        buttons = '<button type="button" data-filter="all" aria-controls="book-grid" aria-pressed="true">All topics</button>'
        buttons += "".join(f'<button type="button" data-filter="{category}" aria-controls="book-grid" aria-pressed="false">{category.title()}</button>' for category in categories)
        content = f'''<div class="toolbar"><div class="filters" role="group" aria-label="Filter by topic">{buttons}</div>
<label class="sort" for="sort">Sort by <select id="sort"><option value="az">Title A–Z</option><option value="za">Title Z–A</option><option value="latest">Latest release</option></select></label></div>
<p class="results" id="results" aria-live="polite">Showing {len(books)} of {len(books)} handbooks</p><div class="grid" id="book-grid">{''.join(_card(book) for book in books)}</div>'''
    else:
        content = '''<div class="empty"><h3>The first handbook is being prepared.</h3><p>Handbooks appear here after an approved release and artifact verification. Each book will have its own reading site, source repository and downloadable editions.</p></div>'''
    planned = sorted(CATEGORIES - set(categories))
    if planned:
        content += '<p class="planned"><strong>Planned topics:</strong> ' + " · ".join(category.title() for category in planned) + '. Topics become filters when a released handbook is available.</p>'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Independent technical handbooks, maintained in public and published as verified releases."><title>Handbook Hub — Open technical knowledge</title><style>{STYLE}</style></head>
<body><a class="skip" href="#library">Skip to handbooks</a><nav class="wrap" aria-label="Main navigation"><a class="brand" href="./">Handbook<span>Hub</span></a><a href="https://github.com/cesarcastrocuba/handbooks-hub">Contribute on GitHub</a></nav>
<header><div class="wrap"><p class="eyebrow">Independent books · Shared standards</p><h1>Knowledge worth keeping.<br>Handbooks worth sharing.</h1><p class="intro">Practical technical knowledge, maintained in public. Read online, download an edition, or contribute to the next release.</p><p class="statusline">{published} published · {archived} archived · Verified release downloads</p></div></header>
<main id="library" class="wrap"><h2>Explore the library</h2>{content}</main><footer><div class="wrap">Each handbook owns its source, review process and releases. This catalog links to approved editions; it does not mirror manuscript content.<br>Content: CC BY-SA 4.0 · Platform code: MIT · <a href="https://github.com/cesarcastrocuba/handbooks-hub">Source and contribution guide</a></div></footer><script>{SCRIPT}</script></body></html>'''
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".portal-", dir=output.parent))
    try:
        (staged / "index.html").write_text(page, encoding="utf-8")
        staged.rename(output)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return output / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the static approved-release handbook catalog")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build_portal(args.catalog, args.output))
    except (OSError, ValueError) as error:
        parser.exit(1, f"portal build failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
