"""Math utilities for expression evaluation."""

from __future__ import annotations

import math


def linspace(start: float, stop: float, num: int = 50) -> list[float]:
    """
    Generate evenly spaced values between start and stop.

    Args:
        start: Starting value
        stop: Ending value
        num: Number of values to generate (default 50)

    Returns:
        List of evenly spaced values
    """
    if num <= 0:
        return []
    if num == 1:
        return [start]

    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


def arange(start: float, stop: float, step: float = 1.0) -> list[float]:
    """
    Generate values with fixed step increment.

    Args:
        start: Starting value
        stop: Ending value (exclusive)
        step: Step size (default 1.0)

    Returns:
        List of values with fixed step
    """
    if step == 0:
        raise ValueError("step cannot be zero")

    result = []
    current = start

    if step > 0:
        while current < stop:
            result.append(current)
            current += step
    else:
        while current > stop:
            result.append(current)
            current += step

    return result


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
        "linspace": linspace,
        "arange": arange,
    }
