"""Native Typst measurement and Word keep chains."""

from pathlib import Path
import json, re, shutil, subprocess, tempfile, unittest
import xml.etree.ElementTree as ET
from handbook_toolkit.docx_tables import keep_rows
from handbook_toolkit.docx_xml import W


class TableFitTests(unittest.TestCase):
    def test_word_short_rows_and_caption_chain(self):
        t = ET.Element(W + "tbl")
        for i in range(3):
            r = ET.SubElement(t, W + "tr")
            c = ET.SubElement(r, W + "tc")
            ET.SubElement(c, W + "p")
        caption = ET.Element(W + "p")
        keep_rows(t, caption, True)
        self.assertTrue(
            all(r.find(W + "trPr/" + W + "cantSplit") is not None for r in t)
        )
        self.assertTrue(
            all(
                p.find(W + "pPr/" + W + "keepNext") is not None for p in t.iter(W + "p")
            )
        )

    @unittest.skipUnless(shutil.which("quarto"), "Quarto Typst required")
    def test_measured_short_moves_whole_and_tall_breaks_with_its_caption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = (
                Path(__file__).resolve().parents[1]
                / "src/handbook_toolkit/render_data/typst/table-fit.typ"
            )
            script = """#set page(paper:"a4",margin:(x:2.2cm,y:2.4cm))
#set table(inset:6pt)
#import "HELPER": handbook-fit-table, handbook-fit-float
#show table: it => handbook-fit-table(it, 2pt)
#show figure.where(kind:table): set block(breakable:true)
#show figure.where(kind:table): handbook-fit-float
#v(23cm)
#figure(table(columns:1,table.header[SHORTHEADER],[SHORTFIRST],[SHORTLAST]),caption:[SHORTCAPTION]) <short>
#pagebreak()
#figure(table(columns:1,table.header[LONGHEADER],..range(100).map(i=>[LONGROW#i])),caption:[LONGCAPTION]) <long>
""".replace("HELPER", helper.as_posix())
            path = root / "test.typ"
            path.write_text(script)
            subprocess.run(
                [
                    "quarto",
                    "typst",
                    "compile",
                    str(path),
                    str(root / "test.pdf"),
                    "--root",
                    "/",
                ],
                check=True,
                capture_output=True,
            )
            result = subprocess.run(
                [
                    "quarto",
                    "typst",
                    "query",
                    str(path),
                    "<handbook-table-fit>",
                    "--field",
                    "value",
                    "--root",
                    "/",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            values = json.loads(
                next(
                    line
                    for line in (result.stdout + "\n" + result.stderr).splitlines()
                    if line.startswith("[")
                )
            )
            for name, fit in [("short", True), ("long", False)]:
                events = [e for e in values if e["name"] == name]
                self.assertEqual(events[0]["height"] <= events[0]["body"], fit)
                self.assertEqual(events[0]["page"] == events[-1]["page"], fit)
            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(root / "test.pdf"), "-"], text=True
            ).split("\f")
            containing = lambda s: [i for i, p in enumerate(pages) if s in p]
            self.assertEqual(containing("SHORTFIRST"), containing("SHORTCAPTION"))
            self.assertEqual(containing("LONGROW99"), containing("LONGCAPTION"))
            self.assertGreater(len(containing("LONGHEADER")), 1)
