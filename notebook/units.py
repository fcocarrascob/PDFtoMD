"""Math utilities for expression evaluation."""

from __future__ import annotations

import math


def math_env() -> dict[str, object]:
    """Safe math helpers exposed to expression evaluation."""

    def _sqrt(value):
        """Numeric sqrt using exponent for all values."""
        try:
            return value ** 0.5
        except Exception:
            return math.sqrt(value)

    return {
        "sqrt": _sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
    }
