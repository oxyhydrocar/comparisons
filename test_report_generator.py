import pytest
from types import SimpleNamespace
from collections import OrderedDict
from unittest.mock import Mock

from report_generator import ReportGenerator


@pytest.fixture
def mock_processor():
    """Provide a generic processor mock with default attributes."""
    p = Mock()
    p.records = []
    p.get_total_sales = Mock(return_value=0)
    p.get_average_sale = Mock(return_value=0)
    p.group_by_region = Mock(return_value={})
    p.get_top_products = Mock(return_value=[])
    return p


@pytest.fixture
def report_generator(mock_processor):
    """Create a ReportGenerator instance with a mocked processor."""
    return ReportGenerator(mock_processor)


def test_reportgenerator_init_stores_processor(mock_processor):
    """Ensure the processor dependency is stored on initialization."""
    rg = ReportGenerator(mock_processor)
    assert rg.processor is mock_processor


def test_reportgenerator_generate_summary_report_basic(report_generator, mock_processor, monkeypatch):
    """Validate summary report content and currency formatting calls."""
    mock_processor.get_total_sales.return_value = 1500
    mock_processor.get_average_sale.return_value = 150
    mock_processor.records = [1] * 10

    fake_currency = Mock(side_effect=lambda v: f"${v}")
    monkeypatch.setattr("report_generator.format_currency", fake_currency)

    report = report_generator.generate_summary_report()

    lines = report.splitlines()
    assert lines[0] == "=" * 50
    assert "SALES SUMMARY REPORT" in lines[1]
    assert lines[-1] == "=" * 50
    assert "Total Records: 10" in report
    assert "Total Sales: $1500" in report
    assert "Average Sale: $150" in report

    assert fake_currency.call_count == 2
    assert fake_currency.call_args_list[0].args[0] == 1500
    assert fake_currency.call_args_list[1].args[0] == 150


def test_reportgenerator_generate_regional_report_with_data(report_generator, mock_processor, monkeypatch):
    """Generate regional report and verify aggregation and formatting."""
    class Rec:
        def __init__(self, amount):
            self.amount = amount

    grouped = OrderedDict()
    grouped["NA"] = [Rec(100), Rec(50)]
    grouped["EU"] = [Rec(200)]
    mock_processor.group_by_region.return_value = grouped

    monkeypatch.setattr("report_generator.format_currency", lambda v: f"C({v})")

    report = report_generator.generate_regional_report()

    assert "REGIONAL SALES REPORT" in report
    # NA section
    assert "\nRegion: NA" in report
    assert "  Records: 2" in report
    assert "  Total Sales: C(150)" in report
    assert "  Average: C(75.0)" in report
    # EU section
    assert "\nRegion: EU" in report
    assert "  Records: 1" in report
    assert "  Total Sales: C(200)" in report
    assert "  Average: C(200.0)" in report


def test_reportgenerator_generate_regional_report_handles_empty_region(report_generator, mock_processor, monkeypatch):
    """Ensure regional report handles regions with zero records."""
    mock_processor.group_by_region.return_value = {"APAC": []}
    monkeypatch.setattr("report_generator.format_currency", lambda v: f"C({v})")

    report = report_generator.generate_regional_report()

    assert "Region: APAC" in report
    assert "  Records: 0" in report
    assert "  Total Sales: C(0)" in report
    assert "  Average: C(0)" in report


def test_reportgenerator_generate_top_products_report_limit_and_calls(report_generator, mock_processor, monkeypatch):
    """Validate top products report with custom limit and call to processor."""
    mock_processor.get_top_products.return_value = [("A", 300), ("B", 250)]
    monkeypatch.setattr("report_generator.format_currency", lambda v: f"${v}")

    report = report_generator.generate_top_products_report(limit=2)

    assert "TOP 2 PRODUCTS BY SALES" in report
    assert "1. A: $300" in report
    assert "2. B: $250" in report
    mock_processor.get_top_products.assert_called_once_with(2)


def test_reportgenerator_generate_top_products_report_empty(report_generator, mock_processor, monkeypatch):
    """Ensure top products report handles empty product list."""
    mock_processor.get_top_products.return_value = []
    monkeypatch.setattr("report_generator.format_currency", lambda v: f"${v}")

    report = report_generator.generate_top_products_report()

    assert "TOP 5 PRODUCTS BY SALES" in report
    assert "1. " not in report  # No items enumerated


def test_reportgenerator_apply_advanced_filter_selects_matching(report_generator, mock_processor):
    """Filter records using a valid expression referencing record fields."""
    mock_processor.records = [
        SimpleNamespace(region="NA", amount=120, product="X"),
        SimpleNamespace(region="EU", amount=80, product="Y"),
        SimpleNamespace(region="NA", amount=90, product="Z"),
    ]

    expr = "record.region == 'NA' and record.amount > 100"
    filtered = report_generator.apply_advanced_filter(expr)

    assert len(filtered) == 1
    assert filtered[0].region == "NA"
    assert filtered[0].amount == 120


def test_reportgenerator_apply_advanced_filter_ignores_exceptions(report_generator, mock_processor):
    """Ensure records causing eval errors are ignored without raising."""
    mock_processor.records = [
        SimpleNamespace(region="NA"),  # missing amount -> AttributeError
        SimpleNamespace(region="NA", amount=120),
        SimpleNamespace(region="EU", amount="oops"),  # TypeError
    ]

    expr = "record.amount > 100"
    filtered = report_generator.apply_advanced_filter(expr)

    assert len(filtered) == 1
    assert filtered[0].amount == 120


def test_reportgenerator_apply_advanced_filter_invalid_expression_returns_empty(report_generator, mock_processor):
    """Invalid filter expressions are caught and result in empty output."""
    mock_processor.records = [
        SimpleNamespace(region="NA", amount=120),
        SimpleNamespace(region="EU", amount=80),
    ]

    expr = "undefined_var > 5"  # NameError each iteration
    filtered = report_generator.apply_advanced_filter(expr)

    assert filtered == []


def test_reportgenerator_calculate_growth_report_formats_output_and_calls_calc(report_generator, monkeypatch):
    """Validate growth report formatting and calculator invocation."""
    monkeypatch.setattr("report_generator.format_currency", lambda v: f"${v}")
    calc_mock = Mock(return_value=12.3456)
    monkeypatch.setattr(
        "report_generator.BusinessCalculator.calculate_compound_growth_rate",
        calc_mock,
    )

    report = report_generator.calculate_growth_report("NA", 1000, 2000, 4)

    assert "GROWTH ANALYSIS - NA" in report
    assert "Starting Value: $1000" in report
    assert "Ending Value: $2000" in report
    assert "Periods: 4" in report
    assert "Growth Rate: 12.35%" in report

    calc_mock.assert_called_once_with(1000, 2000, 4)