"""Tests for unit handling within formula blocks."""

import pytest

from notebook.document import Document, FormulaBlock, NotebookOptions


def test_assignment_with_units_formats_quantity() -> None:
    """Assignments with units should be compacted and rendered with units."""

    block = FormulaBlock("M = 3500 N*m")
    block.evaluate()

    assert block.numeric_value == pytest.approx(3.5)
    assert block.units == "kN·m"
    assert block.result == "3.50 kN·m"

    doc = Document([block])
    html = doc.to_html()

    assert "3.50 kN·m" in html
    assert "kN·m" in html


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


def test_compact_units_can_be_disabled() -> None:
    """Users can keep original unit products instead of compacting them."""

    compact_opts = NotebookOptions(simplify_units=True)
    compact_block = FormulaBlock("R = 3 MPa * 4 mm")
    Document([compact_block]).evaluate(options=compact_opts)

    assert compact_block.units == "kN/m"
    assert compact_block.numeric_value == pytest.approx(12.0)

    keep_opts = NotebookOptions(simplify_units=False)
    keep_block = FormulaBlock("R = 3 MPa * 4 mm")
    Document([keep_block]).evaluate(options=keep_opts)

    assert keep_block.units == "MPa·mm"
    assert keep_block.numeric_value == pytest.approx(12.0)


def test_target_units_support_powers_and_divisions() -> None:
    """Unit conversion handles powers without losing units."""

    block = FormulaBlock("sigma = 500 N / (2 mm^2)")
    options = NotebookOptions(target_unit="MPa", simplify_units=False)
    Document([block]).evaluate(options=options)

    assert block.units == "MPa"
    assert block.numeric_value == pytest.approx(250.0)


def test_invalid_target_unit_reports_spanish_message() -> None:
    """Invalid target units surface a friendly Spanish message."""

    block = FormulaBlock("F = 10 N")
    options = NotebookOptions(target_unit="nope")
    context = Document([block]).evaluate(options=options)

    assert block.evaluation_status == "error"
    assert "Unidad" in (block.result or "")
    assert len(context.errors) == 1
