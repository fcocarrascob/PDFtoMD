"""Numeric-only evaluation helpers (no units)."""

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from notebook.document import Document, FormulaBlock


def test_function_and_call_numeric_only() -> None:
    doc = Document(
        [
            FormulaBlock("f(x) = x**2 + 3*x + 2"),
            FormulaBlock("f(2)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    assert doc.blocks[1].result == "12.00"
    assert doc.blocks[1].numeric_value == 12.0


def test_linspace_and_sweep_numeric_only() -> None:
    doc = Document(
        [
            FormulaBlock("f(x) = x**2"),
            FormulaBlock("xs = linspace(0, 6, 4)"),
            FormulaBlock("f_vals = sweep(f, xs)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    assert context.arrays["xs"].values == [0, 2, 4, 6]
    assert context.arrays["f_vals"].values == [0, 4, 16, 36]


def test_comprehension_and_range_numeric_only() -> None:
    doc = Document(
        [
            FormulaBlock("xs = [i for i in range(5)]"),
            FormulaBlock("total = sum(xs)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    assert context.arrays["xs"].values == [0, 1, 2, 3, 4]
    total_block = context.variables[-1]
    assert total_block.name == "total"
    assert total_block.numeric_value == 10


def test_arange_decimal_step_numeric_only() -> None:
    doc = Document(
        [
            FormulaBlock("arr4 = arange(0, 5, 0.5)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    expected = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    arr_record = context.arrays["arr4"]
    assert arr_record.values == pytest.approx(expected)


def test_sweep_with_array_literal() -> None:
    doc = Document(
        [
            FormulaBlock("g(x) = 2*x + 1"),
            FormulaBlock("vals = [0, 1, 2]"),
            FormulaBlock("out = sweep(g, vals)"),
            FormulaBlock("out_sum = sum(out)"),
            FormulaBlock("out_max = max(out)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    assert context.arrays["out"].values == [1, 3, 5]
    assert context.numeric_values["out_sum"] == pytest.approx(9.0)
    assert context.numeric_values["out_max"] == pytest.approx(5.0)


def test_multiline_conditional_piecewise() -> None:
    doc = Document(
        [
            FormulaBlock("x = -1"),
            FormulaBlock(
                """
if x > 0:
    10
elif x > -2:
    20
else:
    30
"""
            ),
        ]
    )

    context = doc.evaluate()

    assert not context.errors
    assert doc.blocks[1].numeric_value == 20
    assert doc.blocks[1].result == "20.00"


def test_multiline_conditional_with_equality_branch() -> None:
    doc = Document(
        [
            FormulaBlock("x = -3"),
            FormulaBlock(
                """
if x > 0:
    10
elif x == -3:
    30
else:
    -5
"""
            ),
        ]
    )

    context = doc.evaluate()

    assert not context.errors
    assert doc.blocks[1].numeric_value == 30
    assert doc.blocks[1].result == "30.00"


def test_logical_operators_in_conditionals() -> None:
    doc = Document(
        [
            FormulaBlock("a = 5"),
            FormulaBlock("b = -3"),
            FormulaBlock("result = 1 if And(a > 0, Not(b > 0)) else 0"),
        ]
    )

    context = doc.evaluate()

    assert not context.errors
    assert context.numeric_values["result"] == 1
    assert doc.blocks[2].result == "1.00"
