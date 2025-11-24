"""Regression tests for rendering and evaluation pipeline."""

import json
from pathlib import Path
import sys

import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebook.document import Document, FormulaBlock


def load_fixture(name: str) -> dict:
    here = Path(__file__).parent
    with open(here / f"{name}.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_assignment_renders_fraction():
    payload = {
        "version": 1,
        "blocks": [
            {"type": "FormulaBlock", "raw": "fc = 30"},
            {"type": "FormulaBlock", "raw": "b = 300"},
            {"type": "FormulaBlock", "raw": "k = 1/(2*0.85*fc*b)"},
        ],
    }
    doc = Document.from_dict(payload)
    context = doc.evaluate()

    k_block = next(b for b in doc.blocks if isinstance(b, FormulaBlock) and b.variable_name == "k")
    assert k_block.latex
    assert "\\frac" in k_block.latex
    assert "fc" in k_block.latex and "b" in k_block.latex
    assert context.errors == []


def test_mul_symbol_used_between_symbols_and_numbers():
    block = FormulaBlock("y = 3*phi*fc*b")
    block.evaluate()

    assert "\\cdot" in block.latex
    # Should not collapse symbols; expect separators between each factor.
    assert "phi" in block.latex and "fc" in block.latex and "b" in block.latex


def test_arrays_render_in_table():
    doc = Document(
        [
            FormulaBlock("arr = linspace(0, 4, 3)"),
        ]
    )
    html = doc.to_html()

    assert "<h3>Arrays</h3>" in html
    assert "arr" in html
    # values should be formatted with two decimals
    assert "0.00" in html and "4.00" in html
