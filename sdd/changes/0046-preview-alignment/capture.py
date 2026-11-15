"""Capture the supplied concept and running branch previews without modifying their styles."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

SELECTORS = {
    'body': 'body', 'h1': 'h1', 'h2': 'main section.level2 h2',
    'card title': '.book h2', 'button': '.btn', 'tag': '.tag', 'format': '.fmt',
    'filter': '[data-filter]', 'summary': '.summary', 'links': '.links a',
    'guide': '.guide-card', 'book card': '.book', 'cover': '.cover',
    'table': 'table', 'cell': 'tbody td', 'header': 'thead th',
}
PREVIEW = {
    'body': 'body', 'h1': '.top h1', 'h2': 'h2.section',
    'card title': '.mock-details h3', 'button': '.btn', 'tag': '.tags span',
    'format': '.formats span', 'summary': '.mock-details p',
    'links': '.mock-actions a', 'table': '.mock-prose table',
    'cell': '.mock-prose tbody td', 'header': '.mock-prose thead th',
}
STYLE = '''e => {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return {font:s.fontSize, line:s.lineHeight, weight:s.fontWeight,
        radius:s.borderRadius, padding:s.padding, color:s.color,
        background:s.backgroundColor, border:s.borderBottom,
        height:r.height, width:r.width};
}'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.venv/inspection-final'))
    parser.add_argument('--chrome', type=Path, default=(
        Path.home() / '.cache/ms-playwright/chromium-1223/chrome-linux/chrome'))
    parser.add_argument('--sample-site', type=Path,
                        help='Optional unpacked sample site, captured through local file URLs.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sites = [
        ('preview', 'http://127.0.0.1:8765/'),
        ('portal', 'http://127.0.0.1:8766/'),
        ('design', 'http://127.0.0.1:8766/design.html'),
        ('chapter', 'http://127.0.0.1:8767/manuscript/chapters/01-example.html'),
    ]
    if args.sample_site:
        chapter = args.sample_site / 'manuscript/chapters/ch01-why-handbooks-fail.html'
        sites.append(('sample-chapter', chapter.resolve().as_uri()))
    report = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(args.chrome), args=['--headless=new', '--no-sandbox'])
        report['chromium'] = browser.version
        for width in (1280, 390):
            for scheme in ('light', 'dark'):
                context = browser.new_context(
                    viewport={'width': width, 'height': 1000}, color_scheme=scheme)
                page = context.new_page()
                for name, url in sites:
                    page.goto(url)
                    page.evaluate('document.fonts.ready')
                    page.wait_for_timeout(600)
                    key = f'{name}-{width}-{scheme}'
                    report[key] = {}
                    if name == 'preview':
                        frame = page.locator(f'.frame[data-theme="{scheme}"]')
                        frame.first.scroll_into_view_if_needed()
                        for index, label in ((0, 'portal'), (1, 'book')):
                            frame.nth(index).screenshot(
                                path=str(args.output / f'{key}-{label}-frame.png'))
                    page.screenshot(path=str(args.output / f'{key}.png'), full_page=True)
                    if name == 'sample-chapter':
                        page.locator('main table').first.screenshot(
                            path=str(args.output / f'sample-table-{width}-{scheme}.png'))
                    for label, selector in (PREVIEW if name == 'preview' else SELECTORS).items():
                        if name == 'preview' and label not in ('body', 'h1', 'h2'):
                            selector = f'.frame[data-theme="{scheme}"] {selector}'
                        locator = page.locator(selector)
                        if locator.count():
                            report[key][label] = locator.first.evaluate(STYLE)
                    report[key]['overflow'] = page.evaluate(
                        '({viewport:innerWidth,document:document.documentElement.scrollWidth})')
                context.close()
        browser.close()
    (args.output / 'computed.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
