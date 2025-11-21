"""Shared unit registry utilities."""

from __future__ import annotations

from functools import lru_cache

from pint import UnitRegistry


@lru_cache(maxsize=1)
def get_unit_registry() -> UnitRegistry:
    """Return a singleton :class:`pint.UnitRegistry` instance."""

    registry = UnitRegistry()
    registry.default_format = "~P"
    return registry

