from __future__ import annotations

import argparse
import concurrent.futures as cf
from dataclasses import dataclass
from datetime import date, timedelta
import random
import sys
import time
from typing import Iterable, List, Dict, Any


@dataclass(eq=True, frozen=True)
class Sale:
    id: int
    region: str
    product: str
    units: int
    unit_price: float
    date: date

    @property
    def revenue(self) -> float:
        return self.units * self.unit_price


def create_sample_data(n: int = 100, seed: int | None = None) -> List[Sale]:
    rng = random.Random(seed)
    regions = ["North", "East", "South", "West"]
    products = ["Widget", "Gadget", "Doohickey"]
    base_date = date(2024, 1, 1)

    data: List[Sale] = []
    for i in range(1, n + 1):
        region = rng.choice(regions)
        product = rng.choice(products)
        units = rng.randint(1, 10)
        # Keep prices reasonable and deterministic
        unit_price = round(rng.uniform(5.0, 120.0), 2)
        d = base_date + timedelta(days=rng.randint(0, 30))
        data.append(Sale(i, region, product, units, unit_price, d))
    return data


def demonstrate_sorting(sales: Iterable[Sale]) -> Dict[str, List[Sale]]:
    sales_list = list(sales)

    # Sorts
    by_revenue_desc = sorted(sales_list, key=lambda s: s.revenue, reverse=True)
    by_region_date = sorted(sales_list, key=lambda s: (s.region, s.date))
    by_product_units_desc = sorted(sales_list, key=lambda s: (s.product, -s.units))

    # Prints
    print("Top 5 by revenue desc:")
    for s in by_revenue_desc[:5]:
        print(f"  id={s.id} region={s.region} product={s.product} revenue={s.revenue:.2f}")

    print("First 5 by (region, date):")
    for s in by_region_date[:5]:
        print(f"  id={s.id} region={s.region} date={s.date.isoformat()}")

    print("First 5 by product asc, units desc:")
    for s in by_product_units_desc[:5]:
        print(f"  id={s.id} product={s.product} units={s.units}")

    return {
        "by_revenue_desc": by_revenue_desc,
        "by_region_date": by_region_date,
        "by_product_units_desc": by_product_units_desc,
    }


def demonstrate_reports(sales: Iterable[Sale]) -> Dict[str, Dict[str, float]]:
    sales_list = list(sales)

    revenue_by_region: Dict[str, float] = {}
    revenue_by_product: Dict[str, float] = {}

    for s in sales_list:
        revenue_by_region[s.region] = revenue_by_region.get(s.region, 0.0) + s.revenue
        revenue_by_product[s.product] = revenue_by_product.get(s.product, 0.0) + s.revenue

    print("Revenue by region:")
    for region, rev in sorted(revenue_by_region.items()):
        print(f"  {region}: {rev:.2f}")

    print("Revenue by product (top 3):")
    top_products = sorted(revenue_by_product.items(), key=lambda kv: kv[1], reverse=True)[:3]
    for product, rev in top_products:
        print(f"  {product}: {rev:.2f}")

    return {
        "revenue_by_region": revenue_by_region,
        "revenue_by_product": revenue_by_product,
    }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _median(values: List[float]) -> float | int:
    if not values:
        return 0.0
    sv = sorted(values)
    n = len(sv)
    mid = n // 2
    if n % 2 == 1:
        return sv[mid]
    return (sv[mid - 1] + sv[mid]) / 2


def demonstrate_calculations(sales: Iterable[Sale]) -> Dict[str, Any]:
    sales_list = list(sales)
    revenues = [s.revenue for s in sales_list]
    unit_prices = [s.unit_price for s in sales_list]
    units_list = [s.units for s in sales_list]

    revenue_sum = sum(revenues)
    revenue_mean = _mean(revenues)
    revenue_median = _median(revenues)

    # Population standard deviation
    if revenues:
        variance = sum((x - revenue_mean) ** 2 for x in revenues) / len(revenues)
        revenue_stdev = variance ** 0.5
    else:
        revenue_stdev = 0.0

    unit_price_mean = _mean(unit_prices)
    units_mean = _mean([float(u) for u in units_list])
    units_median = _median(units_list)

    print("Calculations:")
    print(f"  revenue_sum = {revenue_sum:.2f}")
    print(f"  revenue_mean = {revenue_mean:.2f}")
    print(f"  revenue_median = {revenue_median}")
    print(f"  revenue_stdev = {revenue_stdev:.6f}")
    print(f"  unit_price_mean = {unit_price_mean:.2f}")
    print(f"  units_mean = {units_mean:.2f}")
    print(f"  units_median = {units_median}")

    return {
        "revenue_sum": revenue_sum,
        "revenue_mean": revenue_mean,
        "revenue_median": revenue_median,
        "revenue_stdev": revenue_stdev,
        "unit_price_mean": unit_price_mean,
        "units_mean": units_mean,
        "units_median": units_median,
    }


def demonstrate_parallel_processing(sales: Iterable[Sale], workers: int = 4) -> Dict[str, float]:
    if workers <= 0:
        raise ValueError("workers must be > 0")

    sales_list = list(sales)

    def compute(s: Sale) -> tuple[str, float]:
        # simulate small workload
        time.sleep(0.001)
        return s.region, s.revenue

    totals: Dict[str, float] = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for region, revenue in ex.map(compute, sales_list):
            totals[region] = totals.get(region, 0.0) + revenue

    print("Parallel processing complete. Aggregated revenue by region:")
    for region, rev in sorted(totals.items()):
        print(f"  {region}: {rev:.2f}")

    return totals


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sales analytics demos")
    parser.add_argument("--size", type=int, default=100, help="Number of sample sales to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--demo",
        choices=["sorting", "reports", "calculations", "parallel", "all"],
        default="all",
        help="Which demo to run",
    )
    parser.add_argument("--workers", type=int, default=4, help="Workers for parallel demo")

    args = parser.parse_args(argv)

    sales = create_sample_data(n=args.size, seed=args.seed)

    if args.demo == "sorting":
        demonstrate_sorting(sales)
    elif args.demo == "reports":
        demonstrate_reports(sales)
    elif args.demo == "calculations":
        demonstrate_calculations(sales)
    elif args.demo == "parallel":
        demonstrate_parallel_processing(sales, workers=args.workers)
    elif args.demo == "all":
        demonstrate_sorting(sales)
        demonstrate_reports(sales)
        demonstrate_calculations(sales)
        demonstrate_parallel_processing(sales, workers=args.workers)


if __name__ == "__main__":
    main(sys.argv[1:])