"""Real opt-in glossary/Index publication boundary."""

from pathlib import Path
import posixpath
import re
import subprocess
import tempfile
import unittest
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import yaml
from test_build import make_book, commit_all, build_book, BUILD_AVAILABLE
from test_glossary_index import GLOSSARY, LONG
from html_support import Document
from handbook_toolkit.docx_fields import bookmark_name
from handbook_toolkit.docx_xml import W


@unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo required")
class GlossaryBuildTests(unittest.TestCase):
    def test_glossary_and_final_index_resolve_in_all_editions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _ = make_book(root, chapter=True)
            descriptor = repo / "book.yaml"
            book = yaml.safe_load(descriptor.read_text())
            book["manuscript"]["glossary"] = "terms.qmd"
            descriptor.write_text(yaml.safe_dump(book))
            reading = repo / "manuscript/book.yml"
            order = yaml.safe_load(reading.read_text())
            order["appendices"] = ["terms.qmd"]
            reading.write_text(yaml.safe_dump(order))
            (repo / "manuscript/terms.qmd").write_text(
                GLOSSARY + "\n: Fixture terminology.\n"
            )
            chapter = repo / "manuscript/chapters/pilot.qmd"
            chapter.write_text(
                chapter.read_text().replace(
                    "**Example.** A labeled example.",
                    "**Example.** Latency is useful. See [latency](#gl-latency).",
                )
            )
            output = root / "dist"
            build_book(repo, commit_all(repo), output, mode="chapter")
            with ZipFile(output / "book-html.zip") as archive:
                files = set(archive.namelist())
                docs = {
                    n: Document(archive.read(n).decode()).root
                    for n in files
                    if n.endswith(".html")
                }
                self.assertIn("analytic-index.html", docs)
                index = docs["analytic-index.html"].find("main")[0]
                self.assertTrue(
                    any(
                        "#gl-latency" in a.attrs.get("href", "")
                        for a in index.find("a")
                    )
                )
                for name, doc in docs.items():
                    for a in doc.find("a"):
                        u = urlsplit(a.attrs.get("href", ""))
                        if u.scheme or u.netloc or not u.fragment:
                            continue
                        target = (
                            posixpath.normpath(
                                posixpath.join(posixpath.dirname(name), unquote(u.path))
                            )
                            if u.path
                            else name
                        )
                        self.assertIn(target, docs, (name, a.attrs))
                        self.assertTrue(
                            any(
                                n.attrs.get("id") == unquote(u.fragment)
                                for n in docs[target].walk()
                            ),
                            (name, a.attrs),
                        )
                # Only the deliberate link appears in the prose chapter.
                body = docs["manuscript/chapters/pilot.html"].find("main")[0]
                self.assertEqual(
                    sum("#gl-" in a.attrs.get("href", "") for a in body.find("a")), 1
                )
            with ZipFile(output / "book.docx") as z:
                doc = ET.fromstring(z.read("word/document.xml"))
            bookmarks = {n.get(W + "name") for n in doc.iter(W + "bookmarkStart")}
            anchors = {
                n.get(W + "anchor")
                for n in doc.iter(W + "hyperlink")
                if n.get(W + "anchor")
            }
            self.assertFalse(anchors - bookmarks)
            self.assertIn(
                bookmark_name("gl-" + LONG.lower().replace(" ", "-")), bookmarks
            )
            tables = [
                t
                for t in doc.iter(W + "tbl")
                if any("Locations" == "".join(n.itertext()) for n in t.iter(W + "t"))
            ]
            self.assertEqual(len(tables), 1)
            self.assertTrue(
                all(
                    r.find(W + "trPr/" + W + "cantSplit") is not None
                    for r in tables[0].findall(W + "tr")
                )
            )
            headings = [
                "".join(p.itertext())
                for p in doc.iter(W + "p")
                if p.find(W + "pPr/" + W + "pStyle") is not None
                and p.find(W + "pPr/" + W + "pStyle").get(W + "val") == "Heading1"
            ]
            self.assertEqual(headings[-1], "Index")
            destinations = subprocess.check_output(
                ["pdfinfo", "-dests", str(output / "book.pdf")], text=True
            )
            # Pandoc/Typst table-span links use direct PDF page destinations.
            glossary_page = re.search(
                r'^\s*(\d+).*"sec_app_a"', destinations, re.M
            ).group(1)
            xml = subprocess.check_output(
                ["pdftohtml", "-xml", "-i", "-stdout", str(output / "book.pdf")],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            parsed = ET.fromstring(xml)
            pages = {p.get("number") for p in parsed.iter("page")}
            targets = {
                a.get("href").rsplit("#", 1)[1]
                for a in parsed.iter("a")
                if "#" in a.get("href", "")
            }
            self.assertFalse(targets - pages)
            self.assertIn(glossary_page, targets)
