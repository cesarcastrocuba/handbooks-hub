# WP1 evidence

Desktop Word: **not opened**. No publication, tag, release or deployment dispatched.

## Completed focused checks

- Fresh local venv created with python3 -m venv .venv; requirements-dev.txt installed successfully.
- Extraction boundary 2ee437c: two focused DOCX helper tests passed.
- Native field/validator fixtures: 23 tests passed.
- Design conformance: 12 tests passed, scanning every toolkit Python module except design.py.
- Copied-template tests: 18 passed, including both real seven-file build paths and initialization.
- LibreOffice cached-list smoke: passed. Its PDF has populated Contents, List of Tables and
  List of Figures. The real fixture contains an original programmatically generated PNG.
- Independent SDK: .NET 10.0.115, DocumentFormat.OpenXml 3.3.0, OpenXmlValidator Office2019:
  **0 errors** for the real figure-build DOCX. The published v0.4.1 baseline reports 125 errors.
  No Word rendering behavior is inferred from this schema check.

## Final candidate verification

Runtime candidate: 3311565. The final evidence commit changes this Markdown file only.

| Command / boundary | Result |
| --- | --- |
| Activate .venv, then make full | 333 tests passed in 90.885 s; VERIFY 5 checks, 0 problems; VERIFY (full) 6 checks, 0 problems |
| python3 -m unittest discover -s tools/tests -p test_build.py -v | 24 passed in 61.476 s, including the LibreOffice smoke; no skips |
| Original figure fixture built twice from the same source commit | Both seven-file builds passed; DOCX bytes identical |
| sha256sum -c SHA256SUMS.txt in the fixture release directory | All six entries OK |
| OpenXmlValidator Office2019, final generated DOCX | 0 errors |
| Chromium 1440px, generated tables.html | Header bottom rule 1px; list border-top, padding-top and margin-top all 0px |
| git diff --check | Passed |

Fixture source commit: be02735856ff23e5529f84d98daed843242280cf (temporary original test book,
version 1.0.0-preview). Both builds use toolkit 0.9.2 at runtime candidate 3311565.
Repeated DOCX SHA256: 0481642721b91a68cb94bd89d6bf4f9ee7816d3578d54cb7a4f8512841c70eca.

Local evidence (temporary files, not committed artifacts):

- /tmp/wp1-full-candidate.log and /tmp/wp1-build-candidate.log
- /tmp/wp1-candidate-evidence.log and /tmp/wp1-candidate-evidence-dist/
- /tmp/wp1-sdk-final.log and /tmp/wp1-openxml/
- /tmp/wp1-tables-final.png (visually inspected, one rule)

The SDK check was run as:

    dotnet run --project /tmp/wp1-openxml -- /tmp/wp1-candidate-evidence-dist/book.docx

The throwaway project targets net10.0 and references DocumentFormat.OpenXml 3.3.0. Its program is:

    using DocumentFormat.OpenXml;
    using DocumentFormat.OpenXml.Packaging;
    using DocumentFormat.OpenXml.Validation;

    using var document = WordprocessingDocument.Open(args[0], false);
    var errors = new OpenXmlValidator(FileFormatVersions.Office2019) { MaxNumberOfErrors = 0 }
        .Validate(document).ToList();
    foreach (var error in errors)
        Console.WriteLine($"{error.Part?.Uri} {error.Path?.XPath}: {error.Description}");
    Console.WriteLine($"OpenXmlValidator Office2019: {errors.Count} errors");
    return errors.Count == 0 ? 0 : 1;

The fixture helper generates an original PNG, commits its canonical sources into a temporary
book, then invokes build_book twice without modifying that commit. This avoids changing either
the published sample or the reference handbook.

## Development checks and limits

Earlier development runs exposed the first-page image relocation and duplicate figure-caption
paragraph properties; both were corrected before candidate verification. A relative PATH used
for an initial venv invocation made subprocess test interpreters unavailable in temporary working
directories; the final commands activate the venv as specified. Template builds initially rejected
the old release pin against the new builder; temporary runtime fixtures now name the current
builder while the actual released pin remains separately tested.

Desktop Word, macOS Word and Windows font substitution: not run. No claim is made about the Word
field-update prompt or exact font fallback chosen by a viewer. The optional SDK check is evidence,
not a new toolkit dependency.

Deviations from the brief: none. The first-page Image filter is the bounded fix required to make
the requested real figure build pass; it does not migrate the HTML architecture. Font fallbacks
use single-name alternate chains because altName describes one alternate font, not a CSS list.
The coordinator still owns the template/release pin bump and independent review.
