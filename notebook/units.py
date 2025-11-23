"""Shared unit registry utilities."""

from __future__ import annotations

import math
from functools import lru_cache

from pint import UnitRegistry

# Common units to surface in the UI quick-pick.
DEFAULT_COMMON_UNITS: list[str] = [
    "mm",
    "cm",
    "m",
    "km",
    "in",
    "ft",
    "N",
    "kN",
    "MN",
    "Pa",
    "kPa",
    "MPa",
    "GPa",
    "kg",
    "g",
    "ton",
    "s",
    "min",
    "hr",
    "deg",
    "rad",
]


def build_common_units(preset: list[str] | None = None) -> list[str]:
    """Return a sanitized list of units, falling back to sensible defaults."""

    items = preset or DEFAULT_COMMON_UNITS
    normalized: list[str] = []
    for entry in items:
        unit = entry.strip()
        if not unit:
            continue
        if unit in normalized:
            continue
        normalized.append(unit)
    return normalized or DEFAULT_COMMON_UNITS


# Mutable list that can be repopulated at runtime from user preferences.
COMMON_UNITS: list[str] = build_common_units()


def math_env() -> dict[str, object]:
    """Safe math helpers exposed to expression evaluation."""

    def _sqrt(value):
        """Pint-friendly sqrt: uses exponent for quantities, falls back to math.sqrt."""

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


@lru_cache(maxsize=1)
def get_unit_registry() -> UnitRegistry:
    """Return a singleton :class:`pint.UnitRegistry` instance."""

    registry = UnitRegistry()
    return registry

