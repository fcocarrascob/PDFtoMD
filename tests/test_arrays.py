"""Tests for array generation with linspace and arange."""

import pytest

from notebook.document import Document, FormulaBlock
from notebook.units import linspace, arange


def test_linspace_basic() -> None:
    """linspace should generate evenly spaced values."""

    result = linspace(0, 10, 5)

    assert len(result) == 5
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(10.0)
    assert result[2] == pytest.approx(5.0)


def test_linspace_single_value() -> None:
    """linspace with num=1 should return just the start value."""

    result = linspace(5, 10, 1)

    assert len(result) == 1
    assert result[0] == pytest.approx(5.0)


def test_linspace_empty() -> None:
    """linspace with num=0 should return empty list."""

    result = linspace(0, 10, 0)

    assert result == []


def test_linspace_negative() -> None:
    """linspace with num<0 should return empty list."""

    result = linspace(0, 10, -5)

    assert result == []


def test_linspace_reverse() -> None:
    """linspace should work with reverse order (stop < start)."""

    result = linspace(10, 0, 5)

    assert len(result) == 5
    assert result[0] == pytest.approx(10.0)
    assert result[-1] == pytest.approx(0.0)
    assert result[2] == pytest.approx(5.0)


def test_arange_basic() -> None:
    """arange should generate values with fixed step."""

    result = arange(0, 10, 1)

    assert len(result) == 10
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(9.0)


def test_arange_fractional_step() -> None:
    """arange should work with fractional steps."""

    result = arange(0, 5, 0.5)

    assert len(result) == 10
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(4.5)


def test_arange_negative_step() -> None:
    """arange should work with negative step."""

    result = arange(10, 0, -1)

    assert len(result) == 10
    assert result[0] == pytest.approx(10.0)
    assert result[-1] == pytest.approx(1.0)


def test_arange_zero_step_error() -> None:
    """arange with step=0 should raise ValueError."""

    with pytest.raises(ValueError, match="step cannot be zero"):
        arange(0, 10, 0)


def test_arange_empty_positive_step() -> None:
    """arange with start > stop and positive step should return empty."""

    result = arange(10, 0, 1)

    assert result == []


def test_arange_empty_negative_step() -> None:
    """arange with start < stop and negative step should return empty."""

    result = arange(0, 10, -1)

    assert result == []


def test_linspace_in_formula_block() -> None:
    """linspace should work within FormulaBlock."""

    block = FormulaBlock("x = linspace(0, 10, 5)")
    block.evaluate()

    assert block.is_array is True
    assert block.array_values is not None
    assert len(block.array_values) == 5
    assert block.array_values[0] == pytest.approx(0.0)
    assert block.array_values[-1] == pytest.approx(10.0)


def test_arange_in_formula_block() -> None:
    """arange should work within FormulaBlock."""

    block = FormulaBlock("y = arange(0, 10, 2)")
    block.evaluate()

    assert block.is_array is True
    assert block.array_values is not None
    assert len(block.array_values) == 5
    assert block.array_values[0] == pytest.approx(0.0)
    assert block.array_values[-1] == pytest.approx(8.0)


def test_array_in_document() -> None:
    """Arrays should be registered in document context."""

    block1 = FormulaBlock("arr1 = linspace(0, 5, 3)")
    block2 = FormulaBlock("arr2 = arange(0, 10, 2.5)")

    doc = Document([block1, block2])
    context = doc.evaluate()

    assert len(context.arrays) == 2
    assert "arr1" in context.arrays
    assert "arr2" in context.arrays
    assert len(context.arrays["arr1"].values) == 3
    assert len(context.arrays["arr2"].values) == 4


def test_array_compact_display() -> None:
    """Small arrays (<=5 elements) should show all values."""

    block = FormulaBlock("small = linspace(0, 4, 5)")
    block.evaluate()

    assert "Array: [" in block.result
    assert "..." not in block.result


def test_array_truncated_display() -> None:
    """Large arrays (>5 elements) should show truncated values."""

    block = FormulaBlock("large = linspace(0, 100, 50)")
    block.evaluate()

    assert "Array (50 values):" in block.result
    assert "..." in block.result


def test_array_with_variables() -> None:
    """Arrays can use previously defined variables."""

    start = FormulaBlock("start = 0")
    stop = FormulaBlock("stop = 10")
    arr = FormulaBlock("arr = linspace(start, stop, 5)")

    doc = Document([start, stop, arr])
    doc.evaluate()

    assert arr.is_array is True
    assert arr.array_values is not None
    assert len(arr.array_values) == 5
    assert arr.array_values[0] == pytest.approx(0.0)
    assert arr.array_values[-1] == pytest.approx(10.0)


def test_array_with_expressions() -> None:
    """Arrays can use expressions for parameters."""

    block = FormulaBlock("arr = linspace(2*3, 5**2, 10)")
    block.evaluate()

    assert block.is_array is True
    assert block.array_values is not None
    assert len(block.array_values) == 10
    assert block.array_values[0] == pytest.approx(6.0)
    assert block.array_values[-1] == pytest.approx(25.0)


def test_multiple_arrays_independent() -> None:
    """Multiple arrays should be stored independently."""

    arr1 = FormulaBlock("x = linspace(0, 5, 3)")
    arr2 = FormulaBlock("y = linspace(10, 20, 4)")
    arr3 = FormulaBlock("z = arange(0, 10, 3)")

    doc = Document([arr1, arr2, arr3])
    context = doc.evaluate()

    assert len(context.arrays) == 3
    assert len(context.arrays["x"].values) == 3
    assert len(context.arrays["y"].values) == 4
    assert len(context.arrays["z"].values) == 4


def test_array_latex_rendering() -> None:
    """Array definitions should render LaTeX properly."""

    block = FormulaBlock("arr = linspace(0, 10, 5)")
    block.evaluate()

    assert block.latex is not None
    assert "arr" in block.latex
