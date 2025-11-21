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


def test_invalid_unit_reports_error() -> None:
    """Unknown units should surface an error message and avoid registration."""

    bad_block = FormulaBlock("F = 10 fooUnit")
    doc = Document([bad_block])
    html = doc.to_html()

    assert bad_block.error_message
    assert "fooUnit" in bad_block.error_message
    assert "Error" in html


def test_literal_expression_with_units_is_evaluated() -> None:
    """Expressions con varias unidades sin variables previas deben evaluarse."""

    block = FormulaBlock("D = 3 m + 4 cm")
    doc = Document([block])
    html = doc.to_html()

    assert block.error_message is None
    assert block.numeric_value == pytest.approx(3.04)
    assert block.units == "m"
    assert "3.04" in html
