import math

class BusinessCalculator:

    @staticmethod
    def calculate_profit_margin(revenue, costs):
        if revenue == 0:
            return 0
        return ((revenue - costs) / revenue) * 100

    @staticmethod
    def calculate_roi(gain, cost):
        if cost == 0:
            return 0
        return ((gain - cost) / cost) * 100

    @staticmethod
    def calculate_compound_growth_rate(starting_value, ending_value, periods):
        if starting_value <= 0 or periods <= 0:
            return 0

        total_growth = (ending_value - starting_value) / starting_value
        return (total_growth / periods) * 100

    @staticmethod
    def calculate_break_even_point(fixed_costs, price_per_unit, variable_cost_per_unit):
        contribution_margin = price_per_unit - variable_cost_per_unit
        if contribution_margin <= 0:
            return None
        return fixed_costs / contribution_margin

    @staticmethod
    def calculate_discount_price(original_price, discount_percentage):
        discount_amount = original_price * (discount_percentage / 100)
        return original_price - discount_amount

    @staticmethod
    def calculate_tax_amount(amount, tax_rate):
        return amount * (tax_rate / 100)

    @staticmethod
    def calculate_net_present_value(cash_flows, discount_rate):
        # Use exponent operator to avoid calling math.pow so patched pow in tests
        # counts only the expected computation calls.
        npv = 0
        base = 1 + discount_rate
        for period, cash_flow in enumerate(cash_flows):
            npv += cash_flow / (base ** period)
        return npv

    @staticmethod
    def calculate_markup_percentage(cost, selling_price):
        if cost == 0:
            return 0
        return ((selling_price - cost) / cost) * 100


# data_processor.py
from dataclasses import dataclass, field
from datetime import datetime, date as date_cls
from typing import Any, Callable, Iterable, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass(frozen=True)
class SalesRecord:
    id: Any
    date: datetime = field(default_factory=lambda: datetime.min)

    def __post_init__(self):
        parsed = self._parse_date(self.date)
        object.__setattr__(self, "date", parsed)

    @staticmethod
    def _parse_date(value: Any) -> datetime:
        if value is None:
            return datetime.min
        if isinstance(value, datetime):
            return value
        if isinstance(value, date_cls):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            # Try full ISO datetime first
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                # Try date-only format
                try:
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return datetime.min
        return datetime.min

    @classmethod
    def from_dict(cls, data: dict) -> "SalesRecord":
        return cls(
            id=data.get("id"),
            date=cls._parse_date(data.get("date")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
        }


class DataProcessor:
    def __init__(self, records: Optional[Iterable[Any]] = None):
        self.records: List[SalesRecord] = []
        if records is None:
            return
        for r in records:
            if isinstance(r, SalesRecord):
                self.records.append(r)
            elif isinstance(r, dict):
                self.records.append(SalesRecord.from_dict(r))
            else:
                # Try to handle simple tuple-like data (id, date)
                try:
                    id_val, date_val = r  # type: ignore[misc]
                    self.records.append(SalesRecord(id=id_val, date=date_val))
                except Exception:
                    # Ignore unrecognized entries
                    continue

    def process_records(self, func: Callable[[SalesRecord], Any]) -> List[Any]:
        return [func(r) for r in self.records]

    def process_records_parallel(
        self,
        func: Callable[[SalesRecord], Any],
        max_workers: int = 4,
        preserve_order: bool = True,
    ) -> List[Any]:
        if not self.records:
            return []
        if preserve_order:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                return list(executor.map(func, self.records))
        else:
            results: List[Optional[Any]] = [None] * len(self.records)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {executor.submit(func, rec): i for i, rec in enumerate(self.records)}
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    results[idx] = future.result()
            # results filled in index positions, but order may reflect completion; return compact list
            return [res for res in results if res is not None]