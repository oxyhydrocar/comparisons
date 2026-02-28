from __future__ import annotations

from .charges import apply_discount


def total_after_discount(amount: float, rate: float) -> float:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if rate < 0 or rate >= 1:
        raise ValueError("rate must be between 0 and 1")
    return apply_discount(amount, rate)
