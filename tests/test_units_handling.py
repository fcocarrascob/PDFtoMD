"""Tests for unit handling within formula blocks."""

import pytest

from notebook.document import Document, FormulaBlock


def test_assignment_with_units_formats_quantity() -> None:
    """Assignments with units should be compacted and rendered with units."""

    block = FormulaBlock("M = 3500 N*m")
    block.evaluate()

    assert block.numeric_value == pytest.approx(3.5)
    assert block.units == "kN*m"
    assert block.result == "3.50 kN*m"

    doc = Document([block])
    html = doc.to_html()

    assert "3.50 kN*m" in html
    assert "kN*m" in html


def test_formula_uses_previous_quantity_units() -> None:
    """Expressions that combine quantities should propagate and format units."""

    l_block = FormulaBlock("L = 3 MPa")
    b_block = FormulaBlock("B = 4 mm")
    p_block = FormulaBlock("P = B * L")

    doc = Document([l_block, b_block, p_block])
    html = doc.to_html()

    assert p_block.numeric_value == pytest.approx(12.0)
    assert p_block.units == "kN/m"
    assert "12.00 kN/m" in html


def test_invalid_units_do_not_block_following_cells() -> None:
    """A unit error should be surfaced but not prevent later evaluations."""

    bad_block = FormulaBlock("X = 5 foobar")
    good_block = FormulaBlock("Y = 2 + 2")

    doc = Document([bad_block, good_block])
    context = doc.evaluate()

    assert bad_block.evaluation_status == "error"
    assert good_block.numeric_value == 4
    assert len(context.errors) == 1
    assert any(var.name == "Y" and var.numeric_value == 4 for var in context.variables)

    html = doc.to_html()
    assert "Errores de evaluación" in html
    assert "Registro de evaluación" in html
