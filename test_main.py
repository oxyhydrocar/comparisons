import sys
import types
import pytest
from unittest.mock import patch, MagicMock

# Inject stub modules before importing 'main' to satisfy external dependencies.
if 'data_processor' not in sys.modules:
    data_processor = types.ModuleType('data_processor')

    class SalesRecord:
        def __init__(self, record_id, product, amount, date, region):
            self.record_id = record_id
            self.product = product
            self.amount = amount
            self.date = date
            self.region = region

    class DataProcessor:
        def __init__(self, records):
            self.records = records

        def sort_by_amount(self):
            return sorted(self.records, key=lambda r: r.amount)

        def process_records_parallel(self, threshold):
            # Simulate filtering of records above a threshold
            return [r for r in self.records if r.amount > threshold]

    data_processor.SalesRecord = SalesRecord
    data_processor.DataProcessor = DataProcessor
    sys.modules['data_processor'] = data_processor

if 'report_generator' not in sys.modules:
    report_generator = types.ModuleType('report_generator')

    class ReportGenerator:
        def __init__(self, processor):
            self.processor = processor

        def generate_summary_report(self):
            return "SUMMARY REPORT"

        def generate_top_products_report(self, n):
            return f"TOP {n} PRODUCTS REPORT"

        def generate_regional_report(self):
            return "REGIONAL REPORT"

    report_generator.ReportGenerator = ReportGenerator
    sys.modules['report_generator'] = report_generator

if 'calculator' not in sys.modules:
    calculator = types.ModuleType('calculator')

    class BusinessCalculator:
        @staticmethod
        def calculate_profit_margin(revenue, costs):
            if revenue == 0:
                return 0.0
            return (revenue - costs) / revenue * 100.0

        @staticmethod
        def calculate_roi(gain, cost):
            if cost == 0:
                return 0.0
            return (gain - cost) / cost * 100.0

        @staticmethod
        def calculate_compound_growth_rate(start, end, periods):
            if start <= 0 or periods <= 0:
                return 0.0
            return ((end / start) ** (1 / periods) - 1) * 100.0

        @staticmethod
        def calculate_break_even_point(fixed_costs, price_per_unit, variable_cost_per_unit):
            contribution = price_per_unit - variable_cost_per_unit
            if contribution == 0:
                return float('inf')
            return fixed_costs / contribution

    calculator.BusinessCalculator = BusinessCalculator
    sys.modules['calculator'] = calculator

if 'utils' not in sys.modules:
    utils = types.ModuleType('utils')

    def format_currency(amount):
        return f"${amount:,.2f}"

    utils.format_currency = format_currency
    sys.modules['utils'] = utils

from main import (
    create_sample_data,
    demonstrate_sorting,
    demonstrate_reports,
    demonstrate_calculations,
    demonstrate_parallel_processing,
    main,
)


@pytest.fixture
def sample_records():
    """Provide sample sales records from create_sample_data()."""
    return create_sample_data()


def test_create_sample_data_returns_expected_records(sample_records):
    """Test that create_sample_data returns 10 valid SalesRecord instances with expected attributes."""
    from data_processor import SalesRecord  # use stub to validate type
    assert isinstance(sample_records, list)
    assert len(sample_records) == 10
    assert all(isinstance(r, SalesRecord) for r in sample_records)
    first = sample_records[0]
    assert (first.record_id, first.product, first.amount, first.date, first.region) == (
        1, "Laptop", 1200.00, "2024-01-15", "North"
    )


@pytest.mark.parametrize(
    "index,product,amount",
    [
        (1, "Mouse", 25.00),
        (2, "Keyboard", 75.00),
        (3, "Monitor", 350.00),
        (5, "Mouse", 30.00),
        (9, "Monitor", 400.00),
    ],
)
def test_create_sample_data_contains_expected_values_by_index(index, product, amount):
    """Parametrized test verifying selected records at specific indices contain expected values."""
    records = create_sample_data()
    r = records[index - 1]  # index is 1-based in data
    assert r.product == product
    assert r.amount == amount


def test_demonstrate_sorting_prints_sorted_top_five(capsys):
    """Test demonstrate_sorting prints top five records sorted by amount and formatted correctly."""
    demonstrate_sorting()
    out = capsys.readouterr().out
    assert "--- Demonstrating Record Sorting ---" in out
    assert "Records sorted by amount:" in out
    # Validate first five lines correspond to lowest amounts
    expected_lines = [
        "Mouse: $25.00",
        "Mouse: $30.00",
        "Keyboard: $75.00",
        "Webcam: $80.00",
        "Headphones: $120.00",
    ]
    for line in expected_lines:
        assert line in out


def test_demonstrate_sorting_raises_when_processor_fails():
    """Test demonstrate_sorting propagates exceptions when DataProcessor.sort_by_amount fails."""
    with patch("main.DataProcessor.sort_by_amount", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            demonstrate_sorting()


def test_demonstrate_reports_prints_reports_and_calls_methods(capsys):
    """Test demonstrate_reports prints outputs from report generator and calls methods with expected args."""
    mock_reporter = MagicMock()
    mock_reporter.generate_summary_report.return_value = "MOCK SUMMARY"
    mock_reporter.generate_top_products_report.return_value = "MOCK TOP"
    mock_reporter.generate_regional_report.return_value = "MOCK REGIONAL"

    with patch("main.ReportGenerator", return_value=mock_reporter) as rg_cls:
        demonstrate_reports()
        out = capsys.readouterr().out

    # Ensure ReportGenerator constructed once
    rg_cls.assert_called_once()
    # Ensure the three methods were invoked with expected params
    mock_reporter.generate_summary_report.assert_called_once_with()
    mock_reporter.generate_top_products_report.assert_called_once_with(3)
    mock_reporter.generate_regional_report.assert_called_once_with()
    # Validate printed outputs
    assert "--- Generating Reports ---" in out
    assert "MOCK SUMMARY" in out
    assert "MOCK TOP" in out
    assert "MOCK REGIONAL" in out


def test_demonstrate_reports_raises_when_generator_fails():
    """Test demonstrate_reports propagates exceptions raised by ReportGenerator methods."""
    mock_reporter = MagicMock()
    mock_reporter.generate_summary_report.side_effect = ValueError("no summary")
    with patch("main.ReportGenerator", return_value=mock_reporter):
        with pytest.raises(ValueError):
            demonstrate_reports()


def test_demonstrate_calculations_prints_expected_values(capsys):
    """Test demonstrate_calculations prints computed business metrics correctly."""
    demonstrate_calculations()
    out = capsys.readouterr().out
    assert "--- Business Calculations ---" in out
    assert "Profit Margin (Revenue: $10,000, Costs: $6,000): 40.00%" in out
    assert "ROI (Gain: $15,000, Cost: $10,000): 50.00%" in out
    # Growth rate: approximately 14.47%
    assert "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): 14.47%" in out
    assert "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): 250 units" in out


@pytest.mark.parametrize(
    "method_name,args,exc",
    [
        ("calculate_profit_margin", (10000, 6000), ValueError("bad pm")),
        ("calculate_roi", (15000, 10000), RuntimeError("bad roi")),
        ("calculate_compound_growth_rate", (10000, 15000, 3), ZeroDivisionError("bad cagr")),
        ("calculate_break_even_point", (5000, 50, 30), ArithmeticError("bad bep")),
    ],
)
def test_demonstrate_calculations_raises_when_calculator_fails(method_name, args, exc):
    """Parametrized test ensuring demonstrate_calculations propagates exceptions from BusinessCalculator methods."""
    path = f"main.BusinessCalculator.{method_name}"
    with patch(path, side_effect=exc):
        with pytest.raises(type(exc)):
            demonstrate_calculations()


def test_demonstrate_parallel_processing_filters_and_prints(capsys):
    """Test demonstrate_parallel_processing prints correct count and includes expected filtered records."""
    demonstrate_parallel_processing()
    out = capsys.readouterr().out
    assert "--- Parallel Processing Demo ---" in out
    # For threshold 100, expect 6 records: 120, 350, 1150, 1200, 1300, 400
    assert "Found 6 records above $100:" in out
    # Ensure some specific lines exist
    assert "Headphones: $120.00" in out
    assert "Monitor: $350.00" in out
    assert "Laptop: $1,150.00" in out
    assert "Laptop: $1,200.00" in out
    assert "Laptop: $1,300.00" in out
    assert "Monitor: $400.00" in out


def test_demonstrate_parallel_processing_raises_when_processor_fails():
    """Test demonstrate_parallel_processing propagates exceptions when DataProcessor.process_records_parallel fails."""
    with patch("main.DataProcessor.process_records_parallel", side_effect=RuntimeError("pp fail")):
        with pytest.raises(RuntimeError):
            demonstrate_parallel_processing()


def test_main_prints_headers_and_runs_all_sections(capsys):
    """Test main prints section headers and completion message."""
    main()
    out = capsys.readouterr().out
    assert "BUSINESS ANALYTICS SYSTEM" in out
    assert "--- Demonstrating Record Sorting ---" in out
    assert "--- Generating Reports ---" in out
    assert "--- Business Calculations ---" in out
    assert "--- Parallel Processing Demo ---" in out
    assert "Analysis Complete!" in out

