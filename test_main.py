from data_processor import SalesRecord, DataProcessor
from report_generator import ReportGenerator
from calculator import BusinessCalculator
from utils import format_currency


def create_sample_data():
    sample_records = [
        SalesRecord(
            record_id=1,
            product="Laptop",
            amount=1200.00,
            date="2024-01-15",
            region="North",
        ),
        SalesRecord(
            record_id=2,
            product="Mouse",
            amount=25.00,
            date="2024-01-16",
            region="South",
        ),
        SalesRecord(
            record_id=3,
            product="Keyboard",
            amount=75.00,
            date="2024-01-17",
            region="East",
        ),
        SalesRecord(
            record_id=4,
            product="Monitor",
            amount=350.00,
            date="2024-01-18",
            region="West",
        ),
        SalesRecord(
            record_id=5,
            product="Laptop",
            amount=1150.00,
            date="2024-01-19",
            region="North",
        ),
        SalesRecord(
            record_id=6,
            product="Mouse",
            amount=30.00,
            date="2024-01-20",
            region="South",
        ),
        SalesRecord(
            record_id=7,
            product="Headphones",
            amount=120.00,
            date="2024-01-21",
            region="East",
        ),
        SalesRecord(
            record_id=8,
            product="Webcam",
            amount=80.00,
            date="2024-01-22",
            region="West",
        ),
        SalesRecord(
            record_id=9,
            product="Laptop",
            amount=1300.00,
            date="2024-01-23",
            region="South",
        ),
        SalesRecord(
            record_id=10,
            product="Monitor",
            amount=400.00,
            date="2024-01-24",
            region="North",
        ),
    ]
    return sample_records


def demonstrate_sorting():
    print("\n--- Demonstrating Record Sorting ---")
    records = create_sample_data()
    processor = DataProcessor(records)

    sorted_records = processor.sort_by_amount()

    print("\nRecords sorted by amount:")
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
    print(
        f"Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): {growth_rate:.2f}%"
    )

    break_even = BusinessCalculator.calculate_break_even_point(5000, 50, 30)
    print(
        f"Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): {break_even:.0f} units"
    )


def demonstrate_parallel_processing():
    print("\n--- Parallel Processing Demo ---")
    records = create_sample_data()
    processor = DataProcessor(records)

    high_value_records = processor.process_records_parallel(100)

    print(f"\nFound {len(high_value_records)} records above $100:")
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