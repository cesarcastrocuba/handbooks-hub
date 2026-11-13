"""The packaged semantic design tokens that every renderer must consume.

Colour, type, spacing and contrast rules live in ``design/tokens.json`` so the portal, the book
HTML, the Typst/PDF edition and the DOCX edition cannot drift into separate visual systems. The
module only reads and validates data: it renders nothing, so a caller can adopt the contract
without changing any output.
"""

from __future__ import annotations

from importlib.resources import files as resource_files
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .validation import Issue, load_packaged_schema

SCHEMES: tuple[str, ...] = ("light", "dark", "print")
"""Every surface family a colour role must serve."""

MINIMUM_TEXT_CONTRAST = 4.5
"""WCAG 2.2 AA floor for normal text; token pairs may not declare a lower bound."""

TOKENS_SCHEMA = "design-tokens.schema.json"


def load_tokens(path: Path | None = None) -> dict[str, Any]:
    """Load the packaged tokens, or an explicit file for tests and tooling."""

    if path is None:
        resource = resource_files("handbook_toolkit").joinpath("design", "tokens.json")
        try:
            text = resource.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"packaged design tokens are unreadable: {exc}") from exc
        label = "packaged design tokens"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read design tokens {path}: {exc}") from exc
        label = str(path)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} are not a JSON object")
    return data


def validate_tokens(
    tokens: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[Issue]:
    """Return deterministic issues for a token document; an empty list means valid.

    Validation covers shape, colour syntax, role references and the declared contrast floors. It
    does not inspect rendered output: phase 1 conformance tests compare generated resources with
    these values.
    """

    schema = schema if schema is not None else load_packaged_schema(TOKENS_SCHEMA)
    validator = Draft202012Validator(schema)
    issues = [
        Issue(_pointer(error.absolute_path), error.message)
        for error in sorted(
            validator.iter_errors(tokens),
            key=lambda error: (list(error.absolute_path), error.message),
        )
    ]
    if issues:
        return sorted(issues)
    issues.extend(_reference_issues(tokens))
    issues.extend(_contrast_issues(tokens))
    return sorted(issues)


def relative_luminance(value: str) -> float:
    """Return the WCAG relative luminance of a ``#RRGGBB`` colour."""

    digits = value.strip().lstrip("#")
    if len(digits) != 6:
        raise ValueError(f"expected a #RRGGBB colour, got {value!r}")
    try:
        channels = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    except ValueError as exc:
        raise ValueError(f"expected a #RRGGBB colour, got {value!r}") from exc
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG contrast ratio between two ``#RRGGBB`` colours."""

    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _pointer(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _reference_issues(tokens: dict[str, Any]) -> list[Issue]:
    roles = set(tokens["color"])
    issues = []
    for index, pair in enumerate(tokens["contrast"]):
        for field in ("foreground", "background"):
            if pair[field] not in roles:
                issues.append(
                    Issue(
                        f"$.contrast[{index}].{field}",
                        f"unknown colour role: {pair[field]}",
                    )
                )
    return issues


def _contrast_issues(tokens: dict[str, Any]) -> list[Issue]:
    issues = []
    colours = tokens["color"]
    for index, pair in enumerate(tokens["contrast"]):
        minimum = pair["minimum"]
        if minimum < MINIMUM_TEXT_CONTRAST:
            issues.append(
                Issue(
                    f"$.contrast[{index}].minimum",
                    f"{minimum}:1 is below the {MINIMUM_TEXT_CONTRAST}:1 text floor",
                )
            )
        foreground = colours.get(pair["foreground"], {})
        background = colours.get(pair["background"], {})
        for scheme in pair["schemes"]:
            if scheme not in foreground or scheme not in background:
                continue
            ratio = contrast_ratio(foreground[scheme], background[scheme])
            if ratio + 1e-9 < minimum:
                issues.append(
                    Issue(
                        f"$.contrast[{index}].{scheme}",
                        f"{pair['name']} is {ratio:.2f}:1, below the required {minimum}:1",
                    )
                )
    return issues


# Web font assets, relative to ``render_data/fonts``. Each tuple is
# (CSS family, relative path, weight, style).
WEB_FONTS: tuple[tuple[str, str, int, str], ...] = (
    ("Handbook Sans", "source-sans3/HandbookSans-Regular.woff2", 400, "normal"),
    ("Handbook Sans", "source-sans3/HandbookSans-Bold.woff2", 700, "normal"),
    ("Handbook Sans", "source-sans3/HandbookSans-Italic.woff2", 400, "italic"),
    ("Handbook Sans", "source-sans3/HandbookSans-BoldItalic.woff2", 700, "italic"),
    ("Handbook Serif", "source-serif4/HandbookSerif-Regular.woff2", 400, "normal"),
    ("Handbook Serif", "source-serif4/HandbookSerif-Semibold.woff2", 600, "normal"),
    ("Handbook Serif", "source-serif4/HandbookSerif-Bold.woff2", 700, "normal"),
    ("Handbook Mono", "jetbrains-mono/HandbookMono-Regular.woff2", 400, "normal"),
    ("Handbook Mono", "jetbrains-mono/HandbookMono-Bold.woff2", 700, "normal"),
    ("Handbook Mono", "jetbrains-mono/HandbookMono-Italic.woff2", 400, "italic"),
)

LEGACY_ALIASES = (
    "--paper: var(--canvas);",
    "--ink: var(--text);",
    "--line: var(--border);",
    "--accent-ink: var(--on-solid);",
    "--soft: var(--surface);",
    "--shelf: var(--border);",
    "--warn: {warn};",
)
"""Portal variable names kept during the migration to semantic roles."""

BOOTSTRAP_ALIASES = (
    "--bs-body-bg: var(--canvas);",
    "--bs-body-color: var(--text);",
    "--bs-heading-color: var(--heading);",
    "--bs-link-color: var(--accent);",
    "--bs-link-hover-color: var(--accent);",
    "--bs-link-color-rgb: var(--accent-rgb);",
    "--bs-link-hover-color-rgb: var(--accent-rgb);",
    "--bs-border-color: var(--border);",
    "--bs-body-font-family: var(--font-sans);",
    "--bs-body-font-size: var(--body-size);",
    "--bs-body-line-height: var(--body-line);",
)
"""Quarto's Bootstrap layer reads these names; mapping them keeps its chrome on brand."""


def font_assets() -> dict[str, bytes]:
    """Return the packaged WOFF2 files keyed by their path below ``render_data/fonts``."""

    package = resource_files("handbook_toolkit").joinpath("render_data", "fonts")
    return {relative: package.joinpath(*relative.split("/")).read_bytes()
            for _family, relative, _weight, _style in WEB_FONTS}


def font_licenses() -> dict[str, bytes]:
    """Return the OFL license files that must travel with the web fonts."""

    package = resource_files("handbook_toolkit").joinpath("render_data", "fonts")
    return {
        "source-sans3/OFL.txt": package.joinpath("source-sans3", "OFL.txt").read_bytes(),
        "source-serif4/OFL.txt": package.joinpath("source-serif4", "OFL.txt").read_bytes(),
        "jetbrains-mono/OFL.txt": package.joinpath("jetbrains-mono", "OFL.txt").read_bytes(),
    }


def font_face_css(prefix: str) -> str:
    """Return ``@font-face`` rules whose URLs are relative to *prefix* (same origin only)."""

    comment = (
        "/* Web fonts: Handbook Sans (Source Sans 3 subset, SIL OFL 1.1, "
        f"{prefix}source-sans3/OFL.txt); Handbook Serif (Source Serif 4 subset, SIL OFL 1.1, "
        f"{prefix}source-serif4/OFL.txt); Handbook Mono (JetBrains Mono subset, SIL OFL 1.1, "
        f"{prefix}jetbrains-mono/OFL.txt). */"
    )
    rules = []
    for family, relative, weight, style in WEB_FONTS:
        rules.append(
            '@font-face{font-family:"%s";src:url("%s%s") format("woff2");'
            "font-weight:%d;font-style:%s;font-display:swap}"
            % (family, prefix, relative, weight, style)
        )
    return comment + "\n" + "\n".join(rules)


def css_variables(scheme: str) -> str:
    """Return the semantic custom properties for one scheme."""

    tokens = load_tokens()
    declarations = [f"--{role.replace('_', '-')}: {values[scheme]};"
                    for role, values in tokens["color"].items()]
    body = tokens["type"]["body"]
    code = tokens["type"]["code"]
    def rgb(value: str) -> str:
        value = value.lstrip("#")
        return f"{int(value[0:2], 16)}, {int(value[2:4], 16)}, {int(value[4:6], 16)}"

    declarations += [
        f"--font-sans: {body['web_family']};",
        f"--font-display: {tokens['type']['display']['web_family']};",
        f"--font-mono: {code['web_family']};",
        f"--accent-rgb: {rgb(tokens['color']['accent'][scheme])};",
        f"--accent-solid-rgb: {rgb(tokens['color']['accent_solid'][scheme])};",
        f"--body-size: {body['web_size_px']}px;",
        f"--body-line: {body['line_height']};",
        f"--display-size: {tokens['type']['display']['web_size_px']}px;",
        f"--code-size: {code['web_size_px']}px;",
        f"--measure: {body['measure_ch']}ch;",
        f"--space-unit: {tokens['space']['unit_px']}px;",
        f"--section: {tokens['space']['section_px']}px;",
        f"--control-radius: {tokens['radius']['control_px']}px;",
        f"--card-radius: {tokens['radius']['card_px']}px;",
    ]
    return "\n".join(declarations)


def _aliases(scheme: str) -> str:
    warn = {"light": "#8A4B12", "dark": "#E7B071", "print": "#8A4B12"}[scheme]
    return "\n".join(alias.format(warn=warn) for alias in LEGACY_ALIASES)


BOOK_CHROME = """

/* Book chrome. The reading site uses Quarto's Bootstrap shell; these rules keep that shell on the
   same canvas, type and accent as the content. */
#quarto-header .navbar,
#quarto-header .navbar[data-bs-theme="dark"] {
  background: var(--canvas) !important;
  color: var(--text) !important;
  min-height: 56px;
  border-bottom: 1px solid var(--border);
  box-shadow: none;
  --bs-navbar-color: var(--text);
  --bs-navbar-hover-color: var(--accent);
  --bs-navbar-active-color: var(--accent);
  --bs-navbar-brand-color: var(--heading);
  --bs-navbar-brand-hover-color: var(--accent);
}
#quarto-header .navbar .navbar-brand,
#quarto-header .navbar .navbar-title {
  color: var(--heading) !important;
  font-family: var(--font-display);
  font-size: 1.02rem;
  letter-spacing: -.01em;
}
#quarto-header .navbar .nav-link,
#quarto-header .navbar .dropdown-toggle {
  color: var(--text) !important;
  font-size: .84rem;
}
#quarto-header .navbar .nav-link:hover,
#quarto-header .navbar .nav-link.active {
  color: var(--accent) !important;
}
#quarto-header .quarto-secondary-nav,
#quarto-header .quarto-page-breadcrumbs {
  background: var(--canvas);
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font-size: .8rem;
}
#title-block-header {
  background: linear-gradient(160deg, var(--surface), var(--canvas) 78%);
  border-bottom: 1px solid var(--border);
  padding: 2.2rem 0 1.8rem;
  margin-bottom: 2rem;
}
#title-block-header .title {
  color: var(--heading);
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.08;
}
#title-block-header .subtitle {
  color: var(--muted);
  font-size: 1rem;
  max-width: 62ch;
}
#title-block-header .quarto-title-meta-heading {
  color: var(--muted);
  font-size: .68rem;
  letter-spacing: .1em;
  text-transform: uppercase;
}
#title-block-header .quarto-title-meta-contents {
  color: var(--text);
  font-size: .82rem;
}
#quarto-sidebar,
#quarto-margin-sidebar,
#TOC,
.sidebar-navigation {
  background: var(--canvas) !important;
  color: var(--text);
}
#quarto-sidebar {
  border-right: 1px solid var(--border);
}
.sidebar-title,
#toc-title {
  color: var(--muted);
  font-size: .68rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  font-weight: 700;
}
.sidebar-navigation a,
#TOC a,
.sidebar-item-text {
  color: var(--text);
  font-size: .82rem;
}
.sidebar-navigation a:hover,
#TOC a:hover {
  color: var(--accent);
}
.sidebar-navigation a.active,
#TOC a.active,
.sidebar-item-container .active {
  color: var(--accent) !important;
  border-left: 2px solid var(--accent);
  padding-left: .55rem;
  font-weight: 600;
}
#quarto-document-content h1,
#quarto-document-content h2,
#quarto-document-content h3,
#quarto-document-content h4,
#quarto-document-content .title {
  color: var(--heading);
  font-family: var(--font-display);
}
#quarto-document-content a,
#quarto-document-content .nav-link,
#quarto-document-content .quarto-xref {
  color: var(--accent);
}
#quarto-document-content table thead th {
  background: var(--accent-solid) !important;
  color: var(--on-solid) !important;
  border-color: var(--accent-solid) !important;
  font-weight: 600;
}
#quarto-document-content table caption,
#quarto-document-content .quarto-float-caption,
#quarto-document-content figcaption {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: .8rem;
  font-style: italic;
  text-align: center;
  padding-top: .45rem;
}
.callout.callout-style-simple {
  border-left-width: 4px;
  border-left-style: solid;
  background: var(--surface);
}
.callout-note.callout { border-left-color: #0065B3; background: color-mix(in srgb, #0065B3 7%, var(--surface)); }
.callout-tip.callout { border-left-color: #107C10; background: color-mix(in srgb, #107C10 7%, var(--surface)); }
.callout-warning.callout { border-left-color: #D83B01; background: color-mix(in srgb, #D83B01 7%, var(--surface)); }
.callout-important.callout { border-left-color: #5C2D91; background: color-mix(in srgb, #5C2D91 7%, var(--surface)); }
.callout-note .callout-title { color: #0065B3; }
.callout-tip .callout-title { color: #107C10; }
.callout-warning .callout-title { color: #D83B01; }
.callout-important .callout-title { color: #5C2D91; }
.page-navigation a { color: var(--accent); }
.list-of-tables {
  margin: 2rem 0;
  padding-top: 1.4rem;
  border-top: 1px solid var(--border);
}
.list-of-tables h2 {
  font-family: var(--font-display);
  color: var(--heading);
  font-size: 1.35rem;
  margin: 0 0 .7rem;
}
.list-of-tables ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
  gap: .35rem 1.5rem;
}
.list-of-tables li { font-size: .8rem; color: var(--text); }
.list-of-tables a { color: var(--accent); text-decoration: none; }
.list-of-tables a:hover { text-decoration: underline; }
"""
def portal_theme_css() -> str:
    """Return the portal stylesheet preamble: same-origin fonts plus both schemes."""

    light = (
        f":root{{\n{css_variables('light')}\n{_aliases('light')}\n}}\n"
        "body{font-family:var(--font-sans);font-size:var(--body-size);color:var(--text);"
        "background:var(--canvas);line-height:var(--body-line)}"
    )
    dark = f":root{{\n{css_variables('dark')}\n{_aliases('dark')}\n}}"
    return (
        font_face_css("fonts/")
        + "\n"
        + light
        + "\n@media(prefers-color-scheme:dark){\n"
        + dark
        + "\n}"
    )


def book_theme_css() -> str:
    """Return the book stylesheet preamble for Quarto's light/dark toggle.

    Quarto puts ``quarto-light``/``quarto-dark`` on ``<body>``; the media query keeps a
    no-JavaScript reader on the operating-system preference.
    """

    light = f":root{{\n{css_variables('light')}\n{chr(10).join(BOOTSTRAP_ALIASES)}\n}}"
    return (
        font_face_css("../fonts/")
        + "\n"
        + light
        + "\nbody.quarto-dark{\n"
        + css_variables("dark")
        + "\n"
        + "\n".join(BOOTSTRAP_ALIASES)
        + "\n}\n@media(prefers-color-scheme:dark){body:not(.quarto-light){\n"
        + css_variables("dark")
        + "\n"
        + "\n".join(BOOTSTRAP_ALIASES)
        + "\n}}"
        + BOOK_CHROME
    )


def typst_preamble() -> str:
    """Return Typst constants for the print scheme; included before the theme file."""

    tokens = load_tokens()
    colour = {role: values["print"] for role, values in tokens["color"].items()}
    lines = [
        '// Generated from design/tokens.json. Do not edit.',
        f'#let hb-font = ("{tokens["type"]["brand"]["text_family"]}",)',
        f'#let hb-display-font = ("{tokens["type"]["brand"]["display_family"]}",)',
        f'#let hb-code-font = ("{tokens["type"]["code"]["print_family"]}",)',
    ]
    for role, value in colour.items():
        name = role.replace("_", "-")
        lines.append(f'#let hb-{name} = rgb("{value}")')
    return "\n".join(lines) + "\n"


def docx_values() -> dict[str, str]:
    """Return the DOCX style values: metric-compatible family names and print colours."""

    tokens = load_tokens()
    brand = tokens["type"]["brand"]
    colour = {role: values["print"] for role, values in tokens["color"].items()}
    return {
        "body_font": brand["docx_text_family"],
        "display_font": brand["docx_display_family"],
        "code_font": tokens["type"]["code"]["print_family"],
        "ink": colour["text"],
        "muted": colour["muted"],
        "accent": colour["accent"],
        "rule": colour["border"],
        "heading": colour["heading"],
    }

