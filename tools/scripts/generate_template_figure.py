#!/usr/bin/env python3
"""Regenerate the original template illustration from its packaged source and design tokens."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from handbook_toolkit.design import example_figure_svg

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[2] / 'template/book/manuscript/images/section-structure.svg'
    target.write_text(example_figure_svg(), encoding='utf-8')
