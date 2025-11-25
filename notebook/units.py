"""Math utilities for expression evaluation."""

from __future__ import annotations

import math
from typing import Callable, Iterable


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
    # Convert num to int in case it's passed as a float
    num = int(num)

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


def sweep(func: Callable[[float], float], xs: Iterable[float]) -> list[float]:
    """
    Apply a scalar function to each value in an iterable and return a list.

    Args:
        func: Callable that acepta un valor y retorna un valor (numérico).
        xs: Iterable de valores de entrada.
    """
    results = []
    for x in xs:
        try:
            results.append(func(x))
        except Exception:
            # Propaga el error para que se registre en el bloque si algo falla.
            raise
    return results


def imap(func: Callable[[float], float], xs: Iterable[float]) -> list[float]:
    """
    Map a unary function over an iterable and return a list (Python map amigable).
    """
    results = []
    for x in xs:
        results.append(func(x))
    return results


def imap2(func: Callable[[float, float], float], xs: Iterable[float], ys: Iterable[float]) -> list[float]:
    """
    Map a binary function over two iterables in paralelo (tipo zip) y retornar lista.
    """
    results = []
    for x, y in zip(xs, ys):
        results.append(func(x, y))
    return results


def irange(*args: int) -> list[int]:
    """
    Return a list version of range (so se ve el contenido).
    """
    try:
        return list(range(*args))
    except TypeError as exc:
        raise exc


def isum(xs: Iterable[float]) -> float:
    """Sum helper that siempre retorna float."""
    return float(sum(xs))


def imean(xs: Iterable[float]) -> float:
    """Mean helper sobre iterables numéricos."""
    xs_list = list(xs)
    if not xs_list:
        return 0.0
    return float(sum(xs_list) / len(xs_list))


def math_env() -> dict[str, object]:
    """Safe math helpers exposed to expression evaluation."""

    def _sqrt(value):
        """Numeric sqrt using exponent for all values."""
        try:
            return value ** 0.5
        except Exception:
            return math.sqrt(value)

    def _and(*args):
        if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
            args = tuple(args[0])  # Accept single iterable argument
        return all(bool(arg) for arg in args)

    def _or(*args):
        if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
            args = tuple(args[0])  # Accept single iterable argument
        return any(bool(arg) for arg in args)

    def _not(arg):
        return not bool(arg)

    return {
        "sqrt": _sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "range": range,
        "linspace": linspace,
        "arange": arange,
        "sweep": sweep,
        "imap": imap,
        "imap2": imap2,
        "irange": irange,
        "isum": isum,
        "imean": imean,
        "And": _and,
        "Or": _or,
        "Not": _not,
    }
