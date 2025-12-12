import sys
import types
from unittest.mock import Mock, patch
import pytest

# Inject stub modules to satisfy imports within report_generator
utils = types.ModuleType("utils")
def _default_format_currency(value):
    return f"${value:,.2f}"
utils.format_currency = _default_format_currency

calculator = types.ModuleType("calculator")
class _DefaultBusinessCalculator:
    @staticmethod
    def calculate_compound_growth_rate(start_value, end_value, periods):
        return 0.0
calculator.BusinessCalculator = _DefaultBusinessCalculator

sys.modules["utils"] = utils
sys.modules["calculator"] = calculator

from report_generator import ReportGenerator


class Record:
    def __init__(self, region, amount):
        self.region = region
        self.amount = amount


@pytest.fixture
def processor_mock():
    """Create a mock processor with default attributes and methods."""
    mock = Mock()
    mock.records = []
    mock.get_total_sales.return_value = 0.0
    mock.get_average_sale.return_value = 0.0
    mock.group_by_region.return_value = {}
    mock.get_top_products.return_value = []
    return mock


@pytest.fixture
def report_generator(processor_mock):
    """Instantiate ReportGenerator with a mocked processor."""
    return ReportGenerator(processor=processor_mock)


def test_reportgenerator_init_sets_processor(processor_mock):
    """Ensure __init__ stores the provided processor."""
    rg = ReportGenerator(processor_mock)
    assert rg.processor is processor_mock


def test_reportgenerator_generate_summary_report_formats_and_counts(report_generator, processor_mock):
    """Verify summary report includes counts and formatted sales values."""
    processor_mock.records = [1, 2, 3, 4]
    processor_mock.get_total_sales.return_value = 1234.56
    processor_mock.get_average_sale.return_value = 308.64

    with patch("report_generator.format_currency") as mock_fmt:
        mock_fmt.side_effect = lambda v: f"CURR[{v}]"

        report = report_generator.generate_summary_report()

        # Ensure formatting was called with correct numbers
        assert mock_fmt.call_count == 2
        mock_fmt.assert_any_call(1234.56)
        mock_fmt.assert_any_call(308.64)

    assert "SALES SUMMARY REPORT" in report
    assert "Total Records: 4" in report
    assert "Total Sales: CURR[1234.56]" in report
    assert "Average Sale: CURR[308.64]" in report
    assert report.startswith("=" * 50)
    assert report.endswith("=" * 50)


def test_reportgenerator_generate_regional_report_multiple_regions_including_empty(report_generator, processor_mock):
    """Validate regional report aggregates totals, counts, and averages per region and handles empty region list."""
    emea_records = [Record("EMEA", 100.0), Record("EMEA", 200.0)]
    apac_records = [Record("APAC", 50.0)]
    empty_records = []

    processor_mock.group_by_region.return_value = {
        "EMEA": emea_records,
        "APAC": apac_records,
        "LATAM": empty_records,
    }

    with patch("report_generator.format_currency") as mock_fmt:
        mock_fmt.side_effect = lambda v: f"F[{v}]"
        text = report_generator.generate_regional_report()

    assert "REGIONAL SALES REPORT" in text

    # EMEA: total 300.0, count 2, avg 150.0
    assert "\nRegion: EMEA" in text
    assert "Records: 2" in text
    assert "Total Sales: F[300.0]" in text
    assert "Average: F[150.0]" in text

    # APAC: total 50.0, count 1, avg 50.0
    assert "\nRegion: APAC" in text
    assert "Records: 1" in text
    assert "Total Sales: F[50.0]" in text
    assert "Average: F[50.0]" in text

    # LATAM: total 0, count 0, avg 0
    assert "\nRegion: LATAM" in text
    assert "Records: 0" in text
    assert "Total Sales: F[0]" in text
    assert "Average: F[0]" in text

    assert text.endswith("=" * 50)


def test_reportgenerator_generate_regional_report_empty_input(report_generator, processor_mock):
    """Ensure regional report with no groups still renders header and footer."""
    processor_mock.group_by_region.return_value = {}

    with patch("report_generator.format_currency") as mock_fmt:
        mock_fmt.side_effect = lambda v: f"F[{v}]"
        text = report_generator.generate_regional_report()

    assert "REGIONAL SALES REPORT" in text
    # No "Region:" lines should appear
    assert "Region:" not in text.split("\n", 4)[-1]  # quick scan to ensure no region sections
    assert text.endswith("=" * 50)


def test_reportgenerator_generate_top_products_report_default_limit_and_formatting(report_generator, processor_mock):
    """Check top products report uses default limit and formats currency for each product."""
    processor_mock.get_top_products.return_value = [
        ("Product A", 500.0),
        ("Product B", 400.5),
        ("Product C", 100.25),
    ]

    with patch("report_generator.format_currency") as mock_fmt:
        mock_fmt.side_effect = lambda v: f"${v}"
        text = report_generator.generate_top_products_report()

    assert "TOP 5 PRODUCTS BY SALES" in text  # default limit is 5 in header
    assert "1. Product A: $500.0" in text
    assert "2. Product B: $400.5" in text
    assert "3. Product C: $100.25" in text
    assert text.endswith("=" * 50)

    # Ensure formatting called for each product's sales
    assert mock_fmt.call_count == 3
    mock_fmt.assert_any_call(500.0)
    mock_fmt.assert_any_call(400.5)
    mock_fmt.assert_any_call(100.25)


def test_reportgenerator_generate_top_products_report_custom_limit(report_generator, processor_mock):
    """Verify custom limit is reflected in the header and only that many items are listed."""
    processor_mock.get_top_products.return_value = [
        ("Product X", 10.0),
        ("Product Y", 20.0),
        ("Product Z", 30.0),
        ("Product W", 40.0),
    ]

    with patch("report_generator.format_currency") as mock_fmt:
        mock_fmt.side_effect = lambda v: f"CUR[{v}]"
        text = report_generator.generate_top_products_report(limit=2)

    assert "TOP 2 PRODUCTS BY SALES" in text
    assert "1. Product X: CUR[10.0]" in text
    assert "2. Product Y: CUR[20.0]" in text
    assert "3." not in text


def test_reportgenerator_apply_advanced_filter_valid_expression_filters_correctly(report_generator, processor_mock):
    """apply_advanced_filter should return records matching eval expression."""
    r1 = Record("EMEA", 150)
    r2 = Record("EMEA", 90)
    r3 = Record("APAC", 200)
    processor_mock.records = [r1, r2, r3]

    expr = "record.amount > 100 and record.region == 'EMEA'"
    filtered = report_generator.apply_advanced_filter(expr)

    assert filtered == [r1]


def test_reportgenerator_apply_advanced_filter_invalid_expression_suppresses_exceptions(report_generator, processor_mock):
    """Invalid expressions should be caught and result in no filtered records."""
    r1 = Record("EMEA", 150)
    processor_mock.records = [r1]

    expr = "nonexistent > 0"  # NameError
    filtered = report_generator.apply_advanced_filter(expr)

    assert filtered == []


def test_reportgenerator_calculate_growth_report_uses_business_calculator_and_formats(report_generator):
    """Growth report should call BusinessCalculator and format values correctly."""
    with patch("report_generator.format_currency") as mock_fmt, \
         patch("report_generator.BusinessCalculator") as mock_calc:

        mock_fmt.side_effect = lambda v: f"F[{v}]"
        instance = mock_calc.return_value  # Not used; static method is accessed on class
        mock_calc.calculate_compound_growth_rate.return_value = 12.3456

        text = report_generator.calculate_growth_report(
            region="EMEA",
            start_value=1000.0,
            end_value=2000.0,
            periods=4
        )

        mock_calc.calculate_compound_growth_rate.assert_called_once_with(1000.0, 2000.0, 4)
        # Check formatted values and percent rounded to 2 decimals
        assert "GROWTH ANALYSIS - EMEA" in text
        assert "Starting Value: F[1000.0]" in text
        assert "Ending Value: F[2000.0]" in text
        assert "Periods: 4" in text
        assert "Growth Rate: 12.35%" in text
        assert text.endswith("=" * 50)