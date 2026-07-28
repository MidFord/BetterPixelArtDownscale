"""Deterministic integer interval distribution used by the legacy API."""

from __future__ import annotations

import math


def distributive(values):
    values = list(values)
    if not values:
        return []
    distinct = list(dict.fromkeys(values))
    return [distinct[index % len(distinct)] for index in range(len(values))]


def sumative(values):
    return sum(values)


def create_pattern(value: int, reacher: int) -> list[int]:
    """Split ``value`` into ``reacher`` stable, evenly distributed integers.

    This is equivalent to measuring consecutive intervals on an integer raster.
    The result always has the requested length and exact sum, without accumulating
    rounding drift at the final element.
    """

    value = int(value)
    reacher = int(reacher)
    if value < 0:
        raise ValueError("value must be non-negative")
    if reacher <= 0:
        raise ValueError("reacher must be positive")
    return [
        math.floor((index + 1) * value / reacher)
        - math.floor(index * value / reacher)
        for index in range(reacher)
    ]


def inside_range(value, reach, tolerance):
    return reach - tolerance <= value <= reach + tolerance


def incolor(x, y, t):
    return all(inside_range(a, b, t) for a, b in zip(x, y))


def identify_color(colors, color, t):
    for index, candidate in enumerate(colors):
        if incolor(candidate, color, t):
            return True, index
    return False, -1


def square_value(value, size):
    if size <= 0:
        raise ValueError("size must be positive")
    y, x = divmod(value, size)
    return x, y
