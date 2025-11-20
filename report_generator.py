from utils import format_currency
from calculator import BusinessCalculator

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
                if eval(filter_expression):
                    filtered_records.append(record)
            except:
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
