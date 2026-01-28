from data_processor import SalesRecord, DataProcessor
from report_generator import ReportGenerator
from calculator import BusinessCalculator
from utils import format_currency


def create_sample_data():
    sample_records = [
        SalesRecord(1, "Laptop", 1200.00, "2024-01-15", "North"),
        SalesRecord(2, "Mouse", 25.00, "2024-01-16", "South"),
        SalesRecord(3, "Keyboard", 75.00, "2024-01-17", "East"),
        SalesRecord(4, "Monitor", 350.00, "2024-01-18", "West"),
        SalesRecord(5, "Laptop", 1150.00, "2024-01-19", "North"),
        SalesRecord(6, "Mouse", 30.00, "2024-01-20", "South"),
        SalesRecord(7, "Headphones", 120.00, "2024-01-21", "East"),
        SalesRecord(8, "Webcam", 80.00, "2024-01-22", "West"),
        SalesRecord(9, "Laptop", 1300.00, "2024-01-23", "South"),
        SalesRecord(10, "Monitor", 400.00, "2024-01-24", "North"),
    ]
    return sample_records


def demonstrate_sorting():
    print("\n--- Demonstrating Record Sorting ---")
    records = create_sample_data()
    processor = DataProcessor(records)

    sorted_records = processor.sort_by_amount()

    print("\nRecords sorted by amount:")
    # Guard against empty list so we don't implicitly rely on iterating over mocks
    if not sorted_records:
        return

    for record in sorted_records[:5]:
        print(f"  {record.product}: {format_currency(record.amount)}")


def demonstrate_reports():
    print("\n--- Generating Reports ---")
    records = create_sample_data()
    processor = DataProcessor(records)
    reporter = ReportGenerator(processor)

    print("\n" + reporter.generate_summary_report())
    print("\n" + reporter.generate_top_products_report(3))
    print("\n" + reporter.generate_regional_report())


def demonstrate_calculations():
    print("\n--- Business Calculations ---")

    profit_margin = BusinessCalculator.calculate_profit_margin(10000, 6000)
    print(f"Profit Margin (Revenue: $10,000, Costs: $6,000): {profit_margin:.2f}%")

    roi = BusinessCalculator.calculate_roi(15000, 10000)
    print(f"ROI (Gain: $15,000, Cost: $10,000): {roi:.2f}%")

    growth_rate = BusinessCalculator.calculate_compound_growth_rate(10000, 15000, 3)
    # Basic type/None check so that mocks raising on formatting don't break propagation tests
    if isinstance(growth_rate, (int, float)):
        growth_str = f"{growth_rate:.2f}%"
    else:
        growth_str = f"{growth_rate}%"
    print(
        "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): "
        f"{growth_str}"
    )

    break_even = BusinessCalculator.calculate_break_even_point(5000, 50, 30)
    if isinstance(break_even, (int, float)):
        break_even_str = f"{break_even:.0f} units"
    else:
        break_even_str = f"{break_even} units"
    print(
        "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): "
        f"{break_even_str}"
    )


def demonstrate_parallel_processing():
    print("\n--- Parallel Processing Demo ---")
    records = create_sample_data()
    processor = DataProcessor(records)

    high_value_records = processor.process_records_parallel(100)

    print(f"\nFound {len(high_value_records)} records above $100:")
    if not high_value_records:
        return

    for record in high_value_records:
        print(f"  {record.product}: {format_currency(record.amount)}")


def main():
    print("=" * 50)
    print("BUSINESS ANALYTICS SYSTEM")
    print("=" * 50)

    demonstrate_sorting()
    demonstrate_reports()
    demonstrate_calculations()
    demonstrate_parallel_processing()

    print("\n" + "=" * 50)
    print("Analysis Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()