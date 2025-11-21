"""Tests for unit handling within formula blocks."""

import pytest

from notebook.document import Document, FormulaBlock


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
