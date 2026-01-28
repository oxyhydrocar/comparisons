from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterable, List, Dict, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


@dataclass(frozen=True)
class SalesRecord:
    id: str
    product: str
    region: str
    amount: float
    date: datetime = field(compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product": self.product,
            "region": self.region,
            "amount": self.amount,
            "date": self.date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SalesRecord":
        # id
        rec_id = str(data.get("id", ""))
        # product and region
        product = str(data.get("product", ""))
        region = str(data.get("region", ""))
        # amount
        try:
            amount_val = float(data.get("amount", 0.0))
        except (TypeError, ValueError):
            amount_val = 0.0
        # date
        d = data.get("date", None)
        if isinstance(d, datetime):
            date_val = d
        elif isinstance(d, str):
            try:
                date_val = datetime.fromisoformat(d)
            except ValueError:
                date_val = datetime.min
        else:
            date_val = datetime.min

        return cls(id=rec_id, product=product, region=region, amount=amount_val, date=date_val)


class DataProcessor:
    def __init__(self, records: Iterable[SalesRecord]):
        self.records: List[SalesRecord] = list(records)

    def sort_by_amount(self, descending: bool = False) -> List[SalesRecord]:
        return sorted(self.records, key=lambda r: r.amount, reverse=descending)

    def filter_by_region(self, region: str) -> List[SalesRecord]:
        return [record for record in self.records if record.region == region]

    def filter_by_product(self, product: str) -> List[SalesRecord]:
        return [record for record in self.records if record.product == product]

    def get_total_sales(self, records: Optional[Iterable[SalesRecord]] = None) -> float:
        recs = list(records) if records is not None else self.records
        return sum(r.amount for r in recs)

    def get_average_sale(self, records: Optional[Iterable[SalesRecord]] = None) -> float:
        recs = list(records) if records is not None else self.records
        if not recs:
            return 0.0
        return self.get_total_sales(recs) / len(recs)

    def group_by_region(self) -> Dict[str, List[SalesRecord]]:
        grouped: Dict[str, List[SalesRecord]] = {}
        for record in self.records:
            grouped.setdefault(record.region, []).append(record)
        return grouped

    def get_top_products(self, n: int = 5, by: str = "revenue") -> List[Tuple[str, float]]:
        if by not in {"revenue", "count"}:
            raise ValueError("Invalid 'by' argument; must be 'revenue' or 'count'")

        aggregates: Dict[str, float] = {}
        if by == "revenue":
            for r in self.records:
                aggregates[r.product] = aggregates.get(r.product, 0.0) + r.amount
        else:  # by == "count"
            for r in self.records:
                aggregates[r.product] = aggregates.get(r.product, 0.0) + 1.0

        sorted_items = sorted(aggregates.items(), key=lambda kv: kv[1], reverse=True)
        return sorted_items[:n]

    def process_records_parallel(
        self,
        func: Callable[[SalesRecord], Any],
        max_workers: Optional[int] = None,
        use_processes: bool = False,
    ) -> List[Any]:
        if not self.records:
            return []

        Executor = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        results: List[Optional[Any]] = [None] * len(self.records)
        with Executor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(func, record): idx for idx, record in enumerate(self.records)
            }
            for fut in as_completed(list(future_to_index.keys())):
                idx = future_to_index[fut]
                results[idx] = fut.result()

        # results list is filled in order by index; mypy: ensure no None remains
        return [res for res in results if res is not None]