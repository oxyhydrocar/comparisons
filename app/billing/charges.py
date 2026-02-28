from __future__ import annotations


def apply_discount(amount: float, rate: float) -> float:
    return amount * (1 - rate)
