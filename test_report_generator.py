from math import isfinite

# Attempt to import external dependencies with safe fallbacks
try:
    from utils import format_currency  # type: ignore
except Exception:  # pragma: no cover - fallback used only if utils is unavailable
    def format_currency(value, symbol="$", decimals=2):
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            raise ValueError("Invalid value for currency formatting")
        sign = "-" if number < 0 else ""
        number = abs(number)
        formatted = f"{number:,.{decimals}f}"
        return f"{sign}{symbol}{formatted}"


try:
    from calculator import BusinessCalculator  # type: ignore
except Exception:  # pragma: no cover - fallback used only if calculator is unavailable
    class BusinessCalculator:
        @staticmethod
        def calculate_compound_growth_rate(start_value, end_value, periods):
            if periods <= 0:
                return 0.0
            if start_value in (0, None):
                return 0.0
            try:
                rate = (end_value / start_value) ** (1 / periods) - 1
            except Exception:
                return 0.0
            if not isfinite(rate):
                return 0.0
            return rate * 100.0


class ReportGenerator:
    def __init__(self, processor):
        self.processor = processor

    def generate_summary_report(self):
        total_sales = self.processor.get_total_sales()
        average_sale = self.processor.get_average_sale()
        record_count = len(self.processor.records)

        report = []
        report.append("=" * 50)
        report.append("SALES SUMMARY REPORT")
        report.append("=" * 50)
        report.append(f"Total Records: {record_count}")
        report.append(f"Total Sales: {format_currency(total_sales)}")
        report.append(f"Average Sale: {format_currency(average_sale)}")
        report.append("=" * 50)

        return "\n".join(report)

    def generate_regional_report(self):
        grouped = self.processor.group_by_region()

        report = []
        report.append("=" * 50)
        report.append("REGIONAL SALES REPORT")
        report.append("=" * 50)

        for region, records in grouped.items():
            total = sum(r.amount for r in records)
            count = len(records)
            avg = total / count if count > 0 else 0

            report.append(f"\nRegion: {region}")
            report.append(f"  Records: {count}")
            report.append(f"  Total Sales: {format_currency(total)}")
            report.append(f"  Average: {format_currency(avg)}")

        report.append("=" * 50)
        return "\n".join(report)

    def generate_top_products_report(self, limit=5):
        top_products = self.processor.get_top_products(limit)

        report = []
        report.append("=" * 50)
        report.append(f"TOP {limit} PRODUCTS BY SALES")
        report.append("=" * 50)

        for idx, (product, sales) in enumerate(top_products, 1):
            report.append(f"{idx}. {product}: {format_currency(sales)}")

        report.append("=" * 50)
        return "\n".join(report)

    def apply_advanced_filter(self, filter_expression):
        filtered_records = []
        for record in self.processor.records:
            try:
                # Evaluate expression with restricted globals and 'record' available in locals
                result = eval(filter_expression, {"__builtins__": {}}, {"record": record})
                if result:
                    filtered_records.append(record)
            except Exception:
                # Swallow any evaluation errors and continue
                pass
        return filtered_records

    def calculate_growth_report(self, region, start_value, end_value, periods):
        growth_rate = BusinessCalculator.calculate_compound_growth_rate(
            start_value, end_value, periods
        )

        report = []
        report.append("=" * 50)
        report.append(f"GROWTH ANALYSIS - {region}")
        report.append("=" * 50)
        report.append(f"Starting Value: {format_currency(start_value)}")
        report.append(f"Ending Value: {format_currency(end_value)}")
        report.append(f"Periods: {periods}")
        report.append(f"Growth Rate: {growth_rate:.2f}%")
        report.append("=" * 50)

        return "\n".join(report)