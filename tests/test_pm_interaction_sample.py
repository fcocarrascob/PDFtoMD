"""Ensure the P–M sample notebook evaluates successfully."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebook.document import Document  # noqa: E402


SAMPLE_PATH = ROOT / "pm_interaccion_simple.json"


@pytest.mark.parametrize(
    "name, expected, rel",  # pylint: disable=invalid-name
    [
        ("Pn1_kN", 718.5903915890277, 1e-9),
        ("Mn1_kNm", 149.9367815089145, 1e-9),
        ("Pn2_kN", 1.2200338989619288, 1e-12),
        ("Mn2_kNm", 183.34626086281375, 1e-9),
        ("Pn3_kN", 1.5224341836407342, 1e-12),
        ("Mn3_kNm", 217.3979634101835, 1e-9),
        ("Pn4_kN", 1.5028113270575545, 1e-12),
        ("Mn4_kNm", 226.22841926438863, 1e-9),
        ("Pn_balance_kN", 1.5070619887834, 1e-12),
        ("Mn_balance_kNm", 231.22861619584995, 1e-9),
        ("Pn_comp_kN", 1.6916656253012532, 1e-12),
        ("Mn_comp_kNm", 257.23425630203656, 1e-9),
    ],
)
def test_pm_sample_computes_expected_values(name: str, expected: float, rel: float) -> None:
    """Load the demo notebook and validate the interaction points."""

    doc = Document.load(SAMPLE_PATH)
    context = doc.evaluate()

    # Only parse warnings are acceptable for the conversion helpers.
    assert all(err["type"] == "ParseWarning" for err in context.errors)

    values = {record.name: record.numeric_value for record in context.variables}
    assert values[name] == pytest.approx(expected, rel=rel)
