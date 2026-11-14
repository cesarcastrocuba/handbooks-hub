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
    issues.extend(_callout_contrast_issues(tokens))
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
    for name, callout in tokens.get("callout", {}).items():
        for part in ("accent", "tint"):
            declarations.append(
                f"--callout-{name}-{part}: {callout[part][scheme]};"
            )
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


# Geometry inherited from the released book layout; palette and type roles remain tokens.
BOOK_METRICS = {'book-metric-0': '1rem',
 'book-metric-1': '1.25rem',
 'book-metric-2': '0.94rem',
 'book-metric-3': '0.45rem',
 'book-metric-4': '0.9rem',
 'book-metric-5': '1px',
 'book-metric-6': '0.55rem',
 'book-metric-7': '0.75rem',
 'book-metric-8': '0.5rem',
 'book-metric-9': '1.1rem',
 'book-metric-10': '0.4rem',
 'book-metric-11': '1300px',
 'book-metric-12': '56px',
 'book-metric-13': '1.02rem',
 'book-metric-14': '-.01em',
 'book-metric-15': '.2rem',
 'book-metric-16': '.55rem',
 'book-metric-17': '.84rem',
 'book-metric-18': '.8rem',
 'book-metric-19': '1.4rem',
 'book-metric-20': '1.2rem',
 'book-metric-21': '2rem',
 'book-metric-22': '4vw',
 'book-metric-23': '3rem',
 'book-metric-24': '62ch',
 'book-metric-25': '.68rem',
 'book-metric-26': '.1em',
 'book-metric-27': '.82rem',
 'book-metric-28': '2px',
 'book-metric-29': '.45rem',
 'book-metric-30': '4px',
 'book-metric-31': '1.35rem',
 'book-metric-32': '.7rem',
 'book-metric-33': '22rem',
 'book-metric-34': '.35rem',
 'book-metric-35': '1.5rem',
 'book-metric-36': '600px'}


def book_layout_css() -> str:
    """Expand the packaged layout using central design measurements."""
    css = resource_files("handbook_toolkit").joinpath("render_data/html/handbook.css").read_text()
    for name, value in BOOK_METRICS.items():
        css = css.replace("{{" + name + "}}", value)
    return css


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
    for name, callout in tokens.get("callout", {}).items():
        for part in ("accent", "tint"):
            lines.append(
                f'#let hb-callout-{name}-{part} = rgb("{callout[part]["print"]}")'
            )
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
        "canvas": colour["canvas"],
        "stripe": colour["table_stripe"],
        "on_solid": colour["on_solid"],
        "accent_solid": colour["accent_solid"],
        **{f"callout_{kind}_{part}": values[part]["print"]
           for kind, values in tokens["callout"].items() for part in ("accent", "tint")},
    }



def docx_callout_styles() -> dict[str, dict[str, str]]:
    """Names shared by the reference generator and staged Pandoc filter."""
    return {kind: {part: f"Callout {kind.title()} {part.title()}"
                   for part in ("title", "body")}
            for kind in load_tokens()["callout"]}


def book_scss(scheme: str) -> str:
    """Generate deterministic Bootstrap/Quarto defaults for the same base theme."""
    tokens = load_tokens()
    colors = {name: values[scheme] for name, values in tokens["color"].items()}
    variables = {"navbar-padding-y": "1rem" if scheme == "dark" else "0.5rem",
                 "border-color": colors["chrome_rule"],
                 "body-bg": colors["canvas"], "body-color": colors["text"],
                 "link-color": colors["accent"], "navbar-bg": colors["canvas"],
                 "navbar-fg": colors["text"], "sidebar-bg": colors["canvas"],
                 "sidebar-fg": colors["text"], "headings-color": colors["heading"],
                 "font-family-sans-serif": '"Handbook Sans"',
                 "font-family-monospace": '"Handbook Mono"',
                 "headings-font-family": '"Handbook Serif"'}
    for kind, roles in tokens["callout"].items():
        if kind != "review":
            variables["callout-color-" + kind] = roles["accent"][scheme]
    return ("/*-- scss:defaults --*/\n" +
            "\n".join(f"${name}: {value};" for name, value in sorted(variables.items())) +
            "\n/*-- scss:rules --*/\n")


READING_METRICS = {"focus-width": "3px", "focus-offset": "3px", "progress-height": "3px",
                   "cover-space": "1rem", "cover-radius": "6px", "reveal-distance": "8px",
                   "favicon-viewbox": "0 0 64 64"}


def reading_css() -> str:
    """Expand the packaged reading controls from central geometry and motion tokens."""
    css = resource_files("handbook_toolkit").joinpath("render_data/html/reading.css").read_text()
    tokens = load_tokens()
    values = dict(READING_METRICS)
    values.update({"motion-fast": str(tokens["motion"]["fast_ms"]) + "ms",
                   "motion-normal": str(tokens["motion"]["normal_ms"]) + "ms",
                   "motion-ease": tokens["motion"]["easing"]})
    for name, value in values.items():
        css = css.replace("{{" + name + "}}", value)
    return css


def favicon_svg() -> str:
    """Render the toolkit's original book mark from approved light palette roles."""
    svg = resource_files("handbook_toolkit").joinpath("render_data/html/favicon.svg").read_text()
    colors = load_tokens()["color"]
    for role in ("accent_solid", "on_solid"):
        svg = svg.replace("{{" + role + "}}", colors[role]["light"])
    return svg.replace("{{viewbox}}", READING_METRICS["favicon-viewbox"])


def example_figure_svg() -> str:
    """Generate original template artwork with portable, token-derived print colors."""
    svg = resource_files("handbook_toolkit").joinpath("render_data/figures/section-structure.svg").read_text()
    for role in ("canvas", "text"):
        svg = svg.replace("{{" + role + "}}", load_tokens()["color"][role]["print"])
    return svg


def _callout_contrast_issues(tokens: dict[str, Any]) -> list[Issue]:
    """Callout titles use their accent on their tint, including small web titles."""
    issues = []
    for name, role in tokens["callout"].items():
        for scheme in SCHEMES:
            ratio = contrast_ratio(role["accent"][scheme], role["tint"][scheme])
            if ratio < MINIMUM_TEXT_CONTRAST:
                issues.append(Issue(f"$.callout.{name}.{scheme}",
                                    f"title contrast {ratio:.2f}:1 is below the required {MINIMUM_TEXT_CONTRAST}:1"))
    return issues
