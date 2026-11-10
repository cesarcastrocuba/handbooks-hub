"""Generate the static handbook library; no manuscript content is mirrored."""

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

HUB_URL = "https://github.com/cesarcastrocuba/handbooks-hub"
TEMPLATE_URL = "https://github.com/cesarcastrocuba/handbooks-template"
GUIDE_URL = f"{HUB_URL}/blob/main/docs/author-guide.md"
LISTING_URL = f"{HUB_URL}/issues/new?template=request-listing.yml"
WITHDRAWAL_URL = f"{HUB_URL}/issues/new?template=request-withdrawal.yml"

# Label of each downloadable edition, in the order the buttons are shown.
FORMATS = {"pdf": "PDF", "html": "HTML", "docx": "DOCX", "markdown": "Markdown", "source": "Source"}

STYLE = """
:root{--paper:#f6f1e7;--surface:#fffdf8;--ink:#1d2a2c;--muted:#55666a;--line:#ddd3c0;--accent:#0b5d5f;--accent-ink:#fff;--soft:#ebe3d2;--shelf:#b9a37c;--warn:#8a4b12;
font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper);font-synthesis:none;color-scheme:light dark}
@media(prefers-color-scheme:dark){:root{--paper:#141a1b;--surface:#1c2526;--ink:#ebe6da;--muted:#a3b0b0;--line:#33403f;--accent:#6fcfc6;--accent-ink:#0c1a1a;--soft:#243030;--shelf:#5b4c33;--warn:#e7b071}}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;line-height:1.6}a{color:var(--accent);text-underline-offset:4px}a:hover{text-decoration-thickness:2px}
h1,h2,h3{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-weight:700;letter-spacing:-.01em;text-wrap:balance}
button,select,input{font:inherit}button,a,select,input{touch-action:manipulation}:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:4px}
.skip{position:absolute;left:1rem;top:-5rem;background:var(--surface);padding:1rem;z-index:3}.skip:focus{top:1rem}
.wrap{max-width:1120px;margin:auto;padding:0 1.5rem}
nav{display:flex;justify-content:space-between;align-items:center;min-height:72px;gap:1rem;flex-wrap:wrap;padding-top:.5rem;padding-bottom:.5rem}
.brand{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-weight:700;font-size:1.3rem;color:var(--ink);text-decoration:none}.brand span{color:var(--accent)}
.menu{display:flex;gap:1.2rem;flex-wrap:wrap;font-size:.92rem}.menu a{color:var(--ink);text-decoration:none;padding:.6rem 0}.menu a:hover{color:var(--accent);text-decoration:underline}
header{border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:linear-gradient(160deg,var(--soft),var(--paper) 70%);padding:4rem 0 3.5rem}
.eyebrow{font-size:.75rem;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--accent);margin:0}
h1{font-size:clamp(2.3rem,6vw,4rem);line-height:1.08;max-width:860px;margin:.8rem 0 1.2rem}
.intro{max-width:640px;font-size:1.1rem;color:var(--muted);margin:0}
.cta{display:flex;gap:.8rem;flex-wrap:wrap;margin:1.8rem 0 0}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:.6rem 1.1rem;border-radius:8px;border:1px solid var(--accent);font-weight:650;text-decoration:none}
.btn.primary{background:var(--accent);color:var(--accent-ink)}.btn:hover{text-decoration:underline}
.statusline{font-size:.9rem;color:var(--muted);margin:1.8rem 0 0}
main section{padding:3.5rem 0;border-bottom:1px solid var(--line)}main section:last-child{border-bottom:0}
h2{font-size:clamp(1.6rem,3.5vw,2.1rem);margin:0 0 .5rem}.lede{color:var(--muted);max-width:700px;margin:0 0 1.5rem}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;margin:1.5rem 0 .5rem}
.filters{display:flex;gap:.5rem;flex-wrap:wrap}
button,select,input[type=search]{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;min-height:44px;padding:.5rem .95rem}
button{cursor:pointer}button[aria-pressed=true]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.tools{display:flex;gap:.8rem;align-items:center;flex-wrap:wrap;font-size:.9rem}.tools label{display:flex;gap:.5rem;align-items:center}
.results{color:var(--muted);font-size:.9rem;margin:.8rem 0 1.2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,31rem),1fr));gap:1.5rem}
.book{display:grid;grid-template-columns:9.5rem 1fr;gap:1.4rem;background:var(--surface);border:1px solid var(--line);border-bottom:6px solid var(--shelf);border-radius:12px;padding:1.4rem}
.cover{--tone:#0f5c5c;aspect-ratio:3/4;align-self:start;display:flex;flex-direction:column;justify-content:space-between;padding:.9rem .8rem .8rem 1.2rem;border-radius:3px 8px 8px 3px;color:#fff;
background:linear-gradient(90deg,#0004 0 .45rem,#fff2 .45rem .55rem,#0000 .55rem),linear-gradient(155deg,#fff2,#0000 55%),var(--tone);box-shadow:3px 4px 10px #0003}
.cover[data-tone=architecture]{--tone:#3b4a7a}.cover[data-tone=authoring]{--tone:#0f5c5c}.cover[data-tone=cloud]{--tone:#1f5f8b}.cover[data-tone=data]{--tone:#5a3f7a}
.cover[data-tone=engineering]{--tone:#7a4a1f}.cover[data-tone=governance]{--tone:#5c2f3f}.cover[data-tone=publishing]{--tone:#2f5c3a}.cover[data-tone=security]{--tone:#6b2d2d}
.cover-kicker{font-size:.62rem;text-transform:uppercase;letter-spacing:.14em;opacity:.85}
.cover-title{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-weight:700;font-size:1rem;line-height:1.25;overflow-wrap:anywhere}
.cover-foot{font-family:ui-monospace,monospace;font-size:.68rem;opacity:.85}
.details{display:flex;flex-direction:column;min-width:0}.book h3{font-size:1.3rem;line-height:1.3;margin:.5rem 0}
.summary{color:var(--muted);margin:0;flex-grow:1}.tags{display:flex;gap:.4rem;flex-wrap:wrap}
.tag{font-size:.72rem;background:var(--soft);color:var(--ink);padding:.2rem .55rem;border-radius:5px}
.version{font-family:ui-monospace,monospace;font-size:.8rem;color:var(--muted);margin-top:.9rem}
.links{display:flex;gap:1rem;flex-wrap:wrap;align-items:center;margin-top:.9rem}.read{font-weight:700}
.formats{display:flex;gap:.45rem;flex-wrap:wrap;margin-top:.9rem}
.fmt{display:inline-flex;align-items:center;min-height:36px;padding:.25rem .7rem;border:1px solid var(--line);border-radius:6px;background:var(--paper);font-size:.82rem;font-weight:650;text-decoration:none}
.fmt:hover{border-color:var(--accent);text-decoration:underline}
.assets{font-size:.8rem;display:flex;gap:.9rem;flex-wrap:wrap;margin-top:.8rem}
.archived{color:var(--warn);font-weight:650;font-size:.8rem;margin-top:.4rem}
.empty{background:var(--surface);border:1px dashed var(--shelf);border-radius:16px;padding:3.5rem 2rem;text-align:center}.empty h3{font-size:1.5rem;margin:0 0 1rem}.empty p{max-width:550px;margin:auto;color:var(--muted)}
.planned{margin:1.8rem 0 0;color:var(--muted);font-size:.9rem}
.flow{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(11.5rem,1fr));gap:1rem;counter-reset:step}
.flow li{counter-increment:step;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1.1rem 1.1rem 1.2rem}
.flow li::before{content:counter(step);display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;background:var(--accent);color:var(--accent-ink);font-weight:700;font-size:.9rem;margin-bottom:.7rem}
.flow strong{display:block;font-size:1.02rem;margin-bottom:.25rem}.flow span{color:var(--muted);font-size:.92rem;display:block}
.parts{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1rem;margin:0 0 1.5rem;padding:0;list-style:none}
.parts li{border-left:4px solid var(--accent);background:var(--surface);padding:.9rem 1rem;border-radius:0 10px 10px 0}.parts strong{display:block}.parts span{color:var(--muted);font-size:.92rem}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,22rem),1fr));gap:2rem}
.two h3{font-size:1.2rem;margin:0 0 .6rem}.steps{margin:0;padding-left:1.3rem}.steps li{margin:.45rem 0}.steps li::marker{color:var(--accent);font-weight:700}
.note{background:var(--soft);border-radius:10px;padding:1rem 1.2rem;margin:1.5rem 0 0;font-size:.95rem}
details{border-bottom:1px solid var(--line);padding:.3rem 0}summary{cursor:pointer;font-weight:650;padding:.8rem 0;min-height:44px}details p{margin:0 0 1rem;color:var(--muted);max-width:760px}
footer{border-top:1px solid var(--line);padding:2rem 0;color:var(--muted);font-size:.85rem}
[hidden]{display:none!important}
@media(max-width:600px){header{padding:2.5rem 0}.wrap{padding:0 1rem}.book{grid-template-columns:6.5rem 1fr;gap:1rem;padding:1rem}.cover{padding:.6rem .5rem .5rem .9rem}.cover-title{font-size:.8rem}.tools{width:100%}.tools input{flex:1;min-width:0}.empty{padding:2rem 1rem}main section{padding:2.5rem 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

SCRIPT = """
const grid=document.querySelector('.grid');
if(grid){
 const cards=Array.from(grid.querySelectorAll('.book'));
 const search=document.querySelector('#search');
 let category='all';
 function update(){
  const mode=document.querySelector('#sort').value;
  const words=search.value.toLowerCase().split(/\\s+/).filter(Boolean);
  cards.sort((a,b)=>mode==='latest'?b.dataset.date.localeCompare(a.dataset.date)||a.dataset.title.localeCompare(b.dataset.title,'en'):mode==='za'?b.dataset.title.localeCompare(a.dataset.title,'en'):a.dataset.title.localeCompare(b.dataset.title,'en'));
  let shown=0;
  for(const card of cards){
   const text=card.querySelector('.details').textContent.toLowerCase();
   card.hidden=(category!=='all'&&!card.dataset.categories.split(' ').includes(category))||!words.every(word=>text.includes(word));
   if(!card.hidden)shown++;grid.append(card);
  }
  document.querySelector('#results').textContent=`Showing ${shown} of ${cards.length} handbooks`;
 }
 for(const button of document.querySelectorAll('[data-filter]')){
  button.addEventListener('click',()=>{category=button.dataset.filter;for(const item of document.querySelectorAll('[data-filter]'))item.setAttribute('aria-pressed',String(item===button));update();});
 }
 document.querySelector('#sort').addEventListener('change',update);
 search.addEventListener('input',update);
}
"""

GUIDE = f"""
<section id="how-it-works" aria-labelledby="how-title"><h2 id="how-title">How the platform works</h2>
<p class="lede">Every handbook lives in its own repository and is built by the same pinned toolkit. The hub lists a book only after its release has been verified and approved.</p>
<ul class="parts">
<li><strong>Book repository</strong><span>Owns the manuscript, its reviews and its releases. Nothing is copied into the hub.</span></li>
<li><strong>Toolkit</strong><span>One versioned tool validates the manuscript and builds every edition the same way for every book.</span></li>
<li><strong>Release</strong><span>Built once from an approved commit: HTML, PDF, DOCX, Markdown and sources, with a manifest and checksums.</span></li>
<li><strong>Catalog and portal</strong><span>The catalog records approved releases. This page is generated from it and links to the exact published files.</span></li>
</ul>
<ol class="flow" aria-label="From manuscript to library">
<li><strong>Write</strong><span>Authors write chapters in Quarto Markdown in the book repository.</span></li>
<li><strong>Check</strong><span>Automatic checks validate structure, references and the editorial profile.</span></li>
<li><strong>Release</strong><span>The book publishes a verified release and its reading site.</span></li>
<li><strong>Review</strong><span>A reviewer who did not write the change verifies the published bytes.</span></li>
<li><strong>List</strong><span>The hub owner approves the catalog change and this library updates itself.</span></li>
</ol></section>
<section id="create" aria-labelledby="create-title"><h2 id="create-title">Create your handbook in 5 steps</h2>
<p class="lede">You need a GitHub account and a topic you know well. The template brings the structure, the checks and the release workflow.</p>
<ol class="flow">
<li><strong>Use the template</strong><span>Open the template repository and choose <em>Use this template</em> to create your own book repository.</span></li>
<li><strong>Initialize</strong><span>Run the <em>Initialize book</em> workflow with your title, identifier, author and license. It prepares a branch for you to review and merge.</span></li>
<li><strong>Write</strong><span>Add chapters under <code>manuscript/</code>. Every push runs the checks and tells you what to fix.</span></li>
<li><strong>Release</strong><span>Run the release workflow on an approved commit. It builds, verifies and publishes every edition and the reading site.</span></li>
<li><strong>Request listing</strong><span>Open a listing request in the hub. After review and owner approval your book appears here.</span></li>
</ol>
<p class="cta"><a class="btn primary" href="{TEMPLATE_URL}">Open the handbook template</a><a class="btn" href="{GUIDE_URL}">Read the author guide</a></p></section>
<section id="publishing" aria-labelledby="publishing-title"><h2 id="publishing-title">How a book is published and withdrawn</h2>
<p class="lede">Nothing reaches this library without a person approving it, and anything listed can be withdrawn through the same reviewed path.</p>
<div class="two"><div><h3>Publishing</h3><ol class="steps">
<li>The author releases a version from an approved commit of the book.</li>
<li>The author opens a <a href="{LISTING_URL}">listing request</a> with the repository and the release tag.</li>
<li>A catalog change is prepared and the published files are verified against the manifest and checksums.</li>
<li>A reviewer who did not prepare the change checks it.</li>
<li>The hub owner merges the change. The library is rebuilt and deployed automatically.</li>
</ol></div><div><h3>Withdrawal</h3><ol class="steps">
<li>Anyone can open a <a href="{WITHDRAWAL_URL}">withdrawal request</a> stating the book and the reason.</li>
<li>If the release is defective or infringing, the catalog entry is removed first so readers stop being sent to it.</li>
<li>If a corrected release exists, the catalog moves to it before the old one is removed.</li>
<li>The hub owner approves the change, and the release files are deleted while the version tag is kept as a record.</li>
</ol></div></div>
<p class="note"><strong>Why the owner gate?</strong> Checksums prove that the files are the ones that were built. They do not prove that the content was reviewed. That decision stays with a person and is recorded.</p></section>
<section id="contribute" aria-labelledby="contribute-title"><h2 id="contribute-title">Contribute to an existing book</h2>
<p class="lede">Each handbook accepts corrections and proposals in its own repository.</p>
<ol class="steps">
<li>Open the reading site of the book and follow its link to the source repository.</li>
<li>Open an issue for an error or a proposal, or send a pull request with the change.</li>
<li>The book's checks run on your pull request, and a maintainer reviews it.</li>
<li>Accepted changes appear in the next release of the book and then in this library.</li>
</ol>
<p class="note">To improve the toolkit, the template or this portal, contribute to the <a href="{HUB_URL}">hub repository</a>.</p></section>
<section id="faq" aria-labelledby="faq-title"><h2 id="faq-title">Questions and answers</h2>
<details><summary>Which formats does a handbook have?</summary><p>A reading site, and downloadable PDF, DOCX, HTML and Markdown editions with the sources. Older releases may offer fewer formats; each card shows what its release provides.</p></details>
<details><summary>Can an AI tool read a handbook?</summary><p>Yes. Releases built with the current toolkit include one Markdown file with the whole book in reading order. The file <a href="llms.txt">llms.txt</a> on this site lists every handbook and its Markdown edition.</p></details>
<details><summary>What does "verified release" mean?</summary><p>Before a book is listed, its published files are downloaded and compared with the manifest and checksums of the release, and the reading site is compared with the released HTML.</p></details>
<details><summary>Who decides what is listed?</summary><p>The hub owner approves every catalog change after a review by someone who did not prepare it. Authors keep full control of their own repository.</p></details>
<details><summary>Under which license are the books published?</summary><p>Content defaults to CC BY-SA 4.0 and code to MIT. Each book states its own license and third-party notices.</p></details>
<details><summary>Does the hub host my manuscript?</summary><p>No. Your repository holds the manuscript and the releases. The hub stores only the catalog entry that points to your approved release.</p></details>
<details><summary>What does it cost?</summary><p>Nothing. The platform uses public repositories, their release pages and static sites.</p></details>
</section>"""


def _card(book: dict) -> str:
    release = book["latest_release"]
    tags = "".join(f'<span class="tag">{escape(category.title())}</span>' for category in book["categories"])
    archived = '<span class="archived">Archived handbook</span>' if book["status"] == "archived" else ''
    title = escape(book["title"])
    assets = release.get("assets", {})
    formats = "".join(
        f'<a class="fmt" href="{escape(assets[role], quote=True)}" aria-label="Download {escape(book["title"], quote=True)} as {label}">{label}</a>'
        for role, label in FORMATS.items() if role in assets
    )
    if formats:
        formats = f'<div class="formats">{formats}</div>'
    return f'''<article class="book" data-title="{escape(book['title'], quote=True)}" data-date="{release['published_at']}" data-categories="{' '.join(book['categories'])}">
<div class="cover" data-tone="{book['categories'][0]}" aria-hidden="true"><span class="cover-kicker">{escape(book['categories'][0])}</span><span class="cover-title">{title}</span><span class="cover-foot">v{release['version']}</span></div>
<div class="details"><div class="tags">{tags}</div>{archived}<h3>{title}</h3><p class="summary">{escape(book['summary'])}</p>
<div class="version">v{release['version']} · <time datetime="{release['published_at']}">{release['published_at']}</time></div>
<div class="links"><a class="read" href="{escape(book['reading_url'], quote=True)}">Read handbook →</a><a href="{escape(release['url'], quote=True)}">Release downloads</a></div>{formats}
<div class="assets"><a href="{escape(release['manifest_url'], quote=True)}">Manifest</a><a href="{escape(release['checksums_url'], quote=True)}">Checksums</a></div></div></article>'''


def _one_line(text: str) -> str:
    return " ".join(text.replace("[", "(").replace("]", ")").split())


def llms_text(books: list[dict]) -> str:
    """Return the ``llms.txt`` index: one link per handbook, to its Markdown edition when it has one."""

    lines = [
        "# Handbook Hub",
        "",
        "> Independent technical handbooks published as verified releases. Each entry links to the whole "
        "book as one Markdown file when its release provides one, and otherwise to its reading site.",
        "",
        "## Handbooks",
        "",
    ]
    if not books:
        lines.append("No handbook is listed yet.")
    for book in books:
        release = book["latest_release"]
        markdown = release.get("assets", {}).get("markdown")
        edition = "Markdown edition" if markdown else "reading site"
        lines.append(
            f"- [{_one_line(book['title'])}]({markdown or book['reading_url']}): "
            f"{_one_line(book['summary'])} Version {release['version']}, {edition}."
        )
    lines += ["", "## Optional", "", f"- [Author guide]({GUIDE_URL}): how to create and publish a handbook.", ""]
    return "\n".join(lines)


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
<div class="tools"><label for="search">Search <input type="search" id="search" autocomplete="off" aria-controls="book-grid"></label>
<label for="sort">Sort by <select id="sort"><option value="az">Title A–Z</option><option value="za">Title Z–A</option><option value="latest">Latest release</option></select></label></div></div>
<p class="results" id="results" aria-live="polite">Showing {len(books)} of {len(books)} handbooks</p><div class="grid" id="book-grid">{''.join(_card(book) for book in books)}</div>'''
    else:
        content = '''<div class="empty"><h3>The first handbook is being prepared.</h3><p>Handbooks appear here after an approved release and artifact verification. Each book will have its own reading site, source repository and downloadable editions.</p></div>'''
    planned = sorted(CATEGORIES - set(categories))
    if planned:
        content += '<p class="planned"><strong>Planned topics:</strong> ' + " · ".join(category.title() for category in planned) + '. Topics become filters when a released handbook is available.</p>'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A library of independent technical handbooks, maintained in public and published as verified releases."><title>Handbook Hub — An open library of technical handbooks</title><style>{STYLE}</style></head>
<body><a class="skip" href="#library">Skip to handbooks</a><nav class="wrap" aria-label="Main navigation"><a class="brand" href="./">Handbook<span>Hub</span></a>
<div class="menu"><a href="#library">Library</a><a href="#how-it-works">How it works</a><a href="#create">Create a handbook</a><a href="#publishing">Publishing</a><a href="#faq">FAQ</a><a href="{HUB_URL}">GitHub</a></div></nav>
<header><div class="wrap"><p class="eyebrow">Independent books · Shared standards</p><h1>Knowledge worth keeping.<br>Handbooks worth sharing.</h1><p class="intro">An open library of practical technical handbooks. Read online, download an edition, or write the next one.</p>
<p class="cta"><a class="btn primary" href="#library">Browse the library</a><a class="btn" href="#create">Create your handbook</a></p><p class="statusline">{published} published · {archived} archived · Verified release downloads</p></div></header>
<main class="wrap"><section id="library" aria-labelledby="library-title"><h2 id="library-title">Explore the library</h2>{content}</section>{GUIDE}</main>
<footer><div class="wrap">Each handbook owns its source, review process and releases. This catalog links to approved editions; it does not mirror manuscript content.<br>Content: CC BY-SA 4.0 · Platform code: MIT · <a href="{HUB_URL}">Source and contribution guide</a> · <a href="llms.txt">llms.txt</a></div></footer><script>{SCRIPT}</script></body></html>'''
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".portal-", dir=output.parent))
    try:
        (staged / "index.html").write_text(page, encoding="utf-8")
        (staged / "llms.txt").write_text(llms_text(books), encoding="utf-8")
        staged.rename(output)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return output / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the static approved-release handbook library")
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
