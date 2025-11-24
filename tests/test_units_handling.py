"""Tests for numeric calculations within formula blocks."""

import pytest

from notebook.document import Document, FormulaBlock


def test_assignment_with_numeric_value() -> None:
    """Assignments with numeric values should be evaluated and stored."""

    block = FormulaBlock("M = 3500")
    block.evaluate()

    assert block.numeric_value == pytest.approx(3500)
    assert block.result == "3500.00"

    doc = Document([block])
    html = doc.to_html()

    assert "3500.00" in html


def test_formula_uses_previous_numeric_values() -> None:
    """Expressions that combine numeric variables should propagate values."""

    l_block = FormulaBlock("L = 3.5")
    b_block = FormulaBlock("B = 4.0")
    p_block = FormulaBlock("P = B * L")

    doc = Document([l_block, b_block, p_block])
    html = doc.to_html()

    assert p_block.numeric_value == pytest.approx(14.0)
    assert "14.00" in html


def test_invalid_expression_does_not_block_following_cells() -> None:
    """An evaluation error should be surfaced but not prevent later evaluations."""

    bad_block = FormulaBlock("X = 5 / 0")
    good_block = FormulaBlock("Y = 2 + 2")

    doc = Document([bad_block, good_block])
    context = doc.evaluate()

    assert bad_block.evaluation_status == "error"
    assert good_block.numeric_value == 4
    assert len(context.errors) >= 1
    assert any(var.name == "Y" and var.numeric_value == 4 for var in context.variables)

    html = doc.to_html()
    assert "Errores de evaluación" in html
    assert "Registro de evaluación" in html


def test_numeric_expressions_with_functions() -> None:
    """Mathematical functions should work correctly with numeric values."""

    block = FormulaBlock("result = 2 * sqrt(16)")
    block.evaluate()

    assert block.numeric_value == pytest.approx(8.0)
    assert block.result == "8.00"


def test_multiple_operations() -> None:
    """Complex numeric expressions should be evaluated correctly."""

    a_block = FormulaBlock("a = 10")
    b_block = FormulaBlock("b = 5")
    c_block = FormulaBlock("c = (a + b) * 2")

    doc = Document([a_block, b_block, c_block])
    doc.evaluate()

    assert c_block.numeric_value == pytest.approx(30.0)
    assert c_block.result == "30.00"


def test_division_and_multiplication() -> None:
    """Division and multiplication should work correctly."""

    block = FormulaBlock("result = 100 / 4 * 2")
    block.evaluate()

    assert block.numeric_value == pytest.approx(50.0)
    assert block.result == "50.00"
