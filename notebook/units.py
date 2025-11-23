"""Shared unit registry utilities."""

from __future__ import annotations

import math
from functools import lru_cache

from pint import Quantity, UnitRegistry

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

    return {
        "sqrt": math.sqrt,
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


def validate_unit(unit_text: str) -> str:
    """Return a cleaned unit string or raise a friendly error."""

    cleaned = unit_text.strip()
    if not cleaned:
        raise ValueError("La unidad no puede estar vacía.")
    ureg = get_unit_registry()
    try:
        # ``Unit`` will raise if the text cannot be parsed.
        ureg.Unit(cleaned)
    except Exception as exc:  # pylint: disable=broad-except
        raise ValueError(f"Unidad inválida: {cleaned}") from exc
    return cleaned


def _smart_compact(quantity: Quantity, ureg: UnitRegistry, simplify: bool) -> Quantity:
    """Return a compacted quantity honoring domain-specific preferences."""

    if not simplify:
        return quantity

    try:
        if quantity.check("[pressure] * [length]"):
            quantity = quantity.to(ureg.newton / ureg.meter)
        elif quantity.check("[pressure]"):
            quantity = quantity.to(ureg.pascal)
    except Exception:  # pragma: no cover - defensive
        pass

    try:
        quantity = quantity.to_compact()
    except Exception:  # pragma: no cover - fallback keeps existing units
        pass
    return quantity


def format_units(units) -> str:
    """Format pint units using a compact, human-friendly style."""

    text = f"{units:~P}".replace(" ", "")
    if text.lower() == "dimensionless":
        return ""
    return text


def normalize_quantity(
    quantity: Quantity, *, target_unit: str | None, simplify: bool
) -> tuple[float, str, Quantity]:
    """Normalize a quantity and return (magnitude, formatted units, normalized quantity)."""

    ureg = get_unit_registry()
    normalized = quantity

    if target_unit:
        unit_name = validate_unit(target_unit)
        try:
            normalized = normalized.to(unit_name)
        except Exception as exc:  # pylint: disable=broad-except
            raise ValueError(f"No se pudo convertir a {unit_name}: {exc}") from exc

    normalized = _smart_compact(normalized, ureg, simplify)

    units_text = format_units(normalized.units)
    return float(normalized.magnitude), units_text, normalized

