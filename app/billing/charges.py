from __future__ import annotations


def apply_discount(amount: float, rate: float) -> float:
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount * (1 - rate)
