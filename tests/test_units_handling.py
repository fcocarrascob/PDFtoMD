"""Tests for unit handling within formula blocks."""

import pytest

from notebook.document import Document, FormulaBlock
from notebook.document import NotebookOptions


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


def test_units_not_duplicated_in_variable_table_or_log() -> None:
    """The unit should appear only once per value in tables and logs."""

    block = FormulaBlock("M = 3 MPa·mm")
    options = NotebookOptions(simplify_units=False)
    doc = Document([block])

    html = doc.to_html(options=options)

    # Result should keep the original unit string when compaction is disabled.
    assert "3.00 MPa·mm" in html

    # Variable table should show numeric value without appending the unit again.
    assert "<td>3.00 MPa·mm</td>" not in html
    assert "<td>3.00</td><td>MPa·mm</td>" in html.replace("\n", "")

    # Evaluation log should list the unit only once per entry.
    assert "<td>MPa·mm</td>" in html
