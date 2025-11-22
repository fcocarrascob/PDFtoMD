import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebook.document import TextBlock


def test_textblock_escapes_script_tag():
    block = TextBlock("<script>alert('x')</script> keep text")

    html_output = block.to_html()

    assert "<script" not in html_output
    assert "alert('x')" in html_output
    assert "&lt;script&gt;" in html_output


def test_textblock_renders_markdown_and_sanitizes():
    raw = """# Heading

- safe item
- <script>alert('bad')</script>

Inline `code` and [danger](javascript:alert('boom')).
"""
    block = TextBlock(raw)

    html_output = block.to_html()

    assert "<h1>Heading</h1>" in html_output
    assert "<ul>" in html_output and "<li>safe item</li>" in html_output
    assert "<code>code</code>" in html_output
    assert "javascript:" not in html_output
    assert "<script" not in html_output
