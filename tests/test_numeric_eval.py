"""Numeric-only evaluation helpers (no units)."""

import pytest

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
    assert doc.blocks[1].result == "12"
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
    assert context.objects["xs"] == [0, 2, 4, 6]
    assert context.objects["f_vals"] == [0, 4, 16, 36]


def test_comprehension_and_range_numeric_only() -> None:
    doc = Document(
        [
            FormulaBlock("xs = [i for i in range(5)]"),
            FormulaBlock("total = sum(xs)"),
        ]
    )
    context = doc.evaluate()

    assert not context.errors
    assert context.objects["xs"] == [0, 1, 2, 3, 4]
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
