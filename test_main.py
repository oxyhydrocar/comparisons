import sys
import types
import importlib
import pytest


@pytest.fixture
def setup_main_with_stubs(monkeypatch):
    """Fixture to install stub modules for external dependencies and import main."""
    # Create stub modules
    data_processor = types.ModuleType("data_processor")
    report_generator = types.ModuleType("report_generator")
    calculator = types.ModuleType("calculator")
    utils = types.ModuleType("utils")

    # utils.format_currency
    def format_currency(value):
        return "${:,.2f}".format(value)

    utils.format_currency = format_currency

    # data_processor stubs
    class SalesRecord:
        def __init__(self, id, product, amount, date, region):
            self.id = id
            self.product = product
            self.amount = amount
            self.date = date
            self.region = region

    class DataProcessor:
        def __init__(self, records):
            self.records = records

        def sort_by_amount(self):
            return sorted(self.records, key=lambda r: r.amount, reverse=True)

        def process_records_parallel(self, threshold):
            return [r for r in self.records if r.amount > threshold]

    data_processor.SalesRecord = SalesRecord
    data_processor.DataProcessor = DataProcessor

    # report_generator stubs
    class ReportGenerator:
        def __init__(self, processor):
            self.processor = processor

        def generate_summary_report(self):
            from utils import format_currency as fmt
            total = sum(r.amount for r in self.processor.records)
            return f"Summary: {len(self.processor.records)} records, Total: {fmt(total)}"

        def generate_top_products_report(self, n):
            from utils import format_currency as fmt
            totals = {}
            for r in self.processor.records:
                totals[r.product] = totals.get(r.product, 0) + r.amount
            ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:n]
            lines = [f"Top {n} Products by Revenue:"]
            for i, (prod, total) in enumerate(ranked, start=1):
                lines.append(f"{i}. {prod}: {fmt(total)}")
            return "\n".join(lines)

        def generate_regional_report(self):
            from utils import format_currency as fmt
            totals = {}
            for r in self.processor.records:
                totals[r.region] = totals.get(r.region, 0) + r.amount
            lines = ["Regional Revenue Report:"]
            for region, total in sorted(totals.items()):
                lines.append(f"{region}: {fmt(total)}")
            return "\n".join(lines)

    report_generator.ReportGenerator = ReportGenerator

    # calculator stubs
    class BusinessCalculator:
        @staticmethod
        def calculate_profit_margin(revenue, costs):
            if revenue == 0:
                raise ZeroDivisionError("Revenue cannot be zero")
            return (revenue - costs) / revenue * 100.0

        @staticmethod
        def calculate_roi(gain, cost):
            if cost == 0:
                raise ZeroDivisionError("Cost cannot be zero")
            return (gain - cost) / cost * 100.0

        @staticmethod
        def calculate_compound_growth_rate(start, end, periods):
            if start <= 0 or periods <= 0:
                raise ValueError("Invalid input")
            return ((end / start) ** (1.0 / periods) - 1.0) * 100.0

        @staticmethod
        def calculate_break_even_point(fixed_cost, price, variable_cost):
            margin = price - variable_cost
            if margin <= 0:
                raise ValueError("No contribution margin")
            return fixed_cost / margin

    calculator.BusinessCalculator = BusinessCalculator

    # Inject stubs into sys.modules
    monkeypatch.setitem(sys.modules, "data_processor", data_processor)
    monkeypatch.setitem(sys.modules, "report_generator", report_generator)
    monkeypatch.setitem(sys.modules, "calculator", calculator)
    monkeypatch.setitem(sys.modules, "utils", utils)

    # Import or reload main
    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    else:
        importlib.import_module("main")

    return sys.modules["main"]


def test_create_sample_data_returns_expected_length_and_sum(setup_main_with_stubs):
    """Test create_sample_data returns 10 records with the correct total amount."""
    from main import create_sample_data

    records = create_sample_data()
    assert len(records) == 10
    total = sum(r.amount for r in records)
    assert total == pytest.approx(4730.0)
    products = {r.product for r in records}
    assert products == {"Laptop", "Mouse", "Keyboard", "Monitor", "Headphones", "Webcam"}


@pytest.mark.parametrize(
    "product,expected_count",
    [
        ("Laptop", 3),
        ("Monitor", 2),
        ("Mouse", 2),
        ("Keyboard", 1),
        ("Headphones", 1),
        ("Webcam", 1),
    ],
)
def test_create_sample_data_product_counts(setup_main_with_stubs, product, expected_count):
    """Test create_sample_data includes expected count of each product."""
    from main import create_sample_data

    records = create_sample_data()
    count = sum(1 for r in records if r.product == product)
    assert count == expected_count


def test_demonstrate_sorting_prints_top5_correctly(setup_main_with_stubs, capsys):
    """Test demonstrate_sorting prints the top 5 records sorted by amount with currency formatting."""
    from main import demonstrate_sorting

    demonstrate_sorting()
    out = capsys.readouterr().out

    assert "--- Demonstrating Record Sorting ---" in out
    assert "Records sorted by amount:" in out

    expected_lines = [
        "  Laptop: $1,300.00",
        "  Laptop: $1,200.00",
        "  Laptop: $1,150.00",
        "  Monitor: $400.00",
        "  Monitor: $350.00",
    ]
    # Extract only the printed record lines
    record_lines = [line.strip("\n") for line in out.splitlines() if line.strip().startswith(("Laptop:", "Monitor:", "Mouse:", "Keyboard:", "Headphones:", "Webcam:")) or line.strip().startswith(("",)) and line.strip().startswith("Laptop") is False]
    # Simpler: find expected lines in order
    idx = -1
    for line in expected_lines:
        new_idx = out.find(line, idx + 1)
        assert new_idx != -1, f"Expected line not found: {line}"
        idx = new_idx


def test_demonstrate_reports_outputs_expected_strings(setup_main_with_stubs, capsys):
    """Test demonstrate_reports prints summary, top products, and regional reports with expected content."""
    from main import demonstrate_reports

    demonstrate_reports()
    out = capsys.readouterr().out

    assert "--- Generating Reports ---" in out
    assert "Summary: 10 records, Total: $4,730.00" in out

    assert "Top 3 Products by Revenue:" in out
    assert "1. Laptop: $3,650.00" in out
    assert "2. Monitor: $750.00" in out
    assert "3. Headphones: $120.00" in out

    assert "Regional Revenue Report:" in out
    assert "East: $195.00" in out
    assert "North: $2,750.00" in out
    assert "South: $1,355.00" in out
    assert "West: $430.00" in out


def test_demonstrate_calculations_prints_expected_values(setup_main_with_stubs, capsys):
    """Test demonstrate_calculations prints correct computed values."""
    from main import demonstrate_calculations

    demonstrate_calculations()
    out = capsys.readouterr().out

    assert "--- Business Calculations ---" in out
    assert "Profit Margin (Revenue: $10,000, Costs: $6,000): 40.00%" in out
    assert "ROI (Gain: $15,000, Cost: $10,000): 50.00%" in out
    assert "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): 14.47%" in out
    assert "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): 250 units" in out


def test_demonstrate_parallel_processing_shows_count_and_items(setup_main_with_stubs, capsys):
    """Test demonstrate_parallel_processing prints count and items above threshold."""
    from main import demonstrate_parallel_processing

    demonstrate_parallel_processing()
    out = capsys.readouterr().out

    assert "--- Parallel Processing Demo ---" in out
    assert "Found 6 records above $100:" in out
    # Verify some expected items are present
    assert "Laptop: $1,300.00" in out
    assert "Laptop: $1,200.00" in out
    assert "Laptop: $1,150.00" in out
    assert "Monitor: $400.00" in out
    assert "Monitor: $350.00" in out
    assert "Headphones: $120.00" in out


def test_main_invokes_demos_and_prints_banners(setup_main_with_stubs, monkeypatch, capsys):
    """Test main prints banners and invokes demonstration functions."""
    main_mod = setup_main_with_stubs

    def fake_sorting():
        print("DEMO_SORTING_CALLED")

    def fake_reports():
        print("DEMO_REPORTS_CALLED")

    def fake_calculations():
        print("DEMO_CALCULATIONS_CALLED")

    def fake_parallel():
        print("DEMO_PARALLEL_CALLED")

    monkeypatch.setattr(main_mod, "demonstrate_sorting", fake_sorting)
    monkeypatch.setattr(main_mod, "demonstrate_reports", fake_reports)
    monkeypatch.setattr(main_mod, "demonstrate_calculations", fake_calculations)
    monkeypatch.setattr(main_mod, "demonstrate_parallel_processing", fake_parallel)

    from main import main as entry

    entry()
    out = capsys.readouterr().out

    assert "BUSINESS ANALYTICS SYSTEM" in out
    assert "DEMO_SORTING_CALLED" in out
    assert "DEMO_REPORTS_CALLED" in out
    assert "DEMO_CALCULATIONS_CALLED" in out
    assert "DEMO_PARALLEL_CALLED" in out
    assert "Analysis Complete!" in out


def test_demonstrate_sorting_raises_when_sort_fails(setup_main_with_stubs, monkeypatch):
    """Test demonstrate_sorting propagates exceptions from DataProcessor.sort_by_amount."""
    import main

    def boom(_self):
        raise RuntimeError("sort failed")

    monkeypatch.setattr(main.DataProcessor, "sort_by_amount", boom)

    from main import demonstrate_sorting

    with pytest.raises(RuntimeError):
        demonstrate_sorting()


def test_demonstrate_reports_raises_when_summary_fails(setup_main_with_stubs, monkeypatch):
    """Test demonstrate_reports propagates exceptions from ReportGenerator.generate_summary_report."""
    import main

    def boom(_self):
        raise ValueError("report failed")

    monkeypatch.setattr(main.ReportGenerator, "generate_summary_report", boom)

    from main import demonstrate_reports

    with pytest.raises(ValueError):
        demonstrate_reports()


def test_demonstrate_parallel_processing_handles_empty_result(setup_main_with_stubs, monkeypatch, capsys):
    """Test demonstrate_parallel_processing prints zero count when no records match."""
    import main

    def empty(_self, threshold):
        return []

    monkeypatch.setattr(main.DataProcessor, "process_records_parallel", empty)

    from main import demonstrate_parallel_processing

    demonstrate_parallel_processing()
    out = capsys.readouterr().out
    assert "Found 0 records above $100:" in out


def test_demonstrate_calculations_raises_on_error(setup_main_with_stubs, monkeypatch):
    """Test demonstrate_calculations propagates errors from BusinessCalculator."""
    import main

    def boom(_revenue, _costs):
        raise ZeroDivisionError("bad revenue")

    monkeypatch.setattr(main.BusinessCalculator, "calculate_profit_margin", staticmethod(boom))

    from main import demonstrate_calculations

    with pytest.raises(ZeroDivisionError):
        demonstrate_calculations()