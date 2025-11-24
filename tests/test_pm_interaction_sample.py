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
        ("Pn1_kN", 236.691, 1e-5),
        ("Mn1_kNm", 12.246622, 1e-6),
        ("Pn4_kN", 473.3820000000001, 1e-6),
        ("Mn4_kNm", 101.1240925408703, 1e-6),
        ("Pn5_kN", 710.073, 1e-6),
        ("Mn5_kNm", 177.93032204087027, 1e-6),
        ("Pn6_kN", 986.2125, 1e-6),
        ("Mn6_kNm", 252.28088241587028, 1e-6),
        ("Pn2_kN", 1.048866, 1e-6),
        ("Mn2_kNm", 266.863485, 1e-6),
        ("Pn3_kN", 1.3806975, 1e-7),
        ("Mn3_kNm", 329.994427, 1e-6),
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
