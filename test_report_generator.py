import pytest
from unittest.mock import Mock, patch

from report_generator import ReportGenerator


@pytest.fixture
def mock_processor():
    """Create a mock processor with basic attributes and methods."""
    processor = Mock()
    processor.records = []
    processor.get_total_sales = Mock(return_value=0.0)
    processor.get_average_sale = Mock(return_value=0.0)
    processor.group_by_region = Mock(return_value={})
    processor.get_top_products = Mock(return_value=[])
    return processor


@pytest.fixture
def report_generator_instance(mock_processor):
    """Create a ReportGenerator instance with a mocked processor."""
    return ReportGenerator(processor=mock_processor)


def test_reportgenerator_init_stores_processor(mock_processor):
    """Test that ReportGenerator initialization stores the processor."""
    rg = ReportGenerator(processor=mock_processor)
    assert rg.processor is mock_processor


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_basic(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_summary_report with standard processor values."""
    mock_processor.records = [1, 2, 3]
    mock_processor.get_total_sales.return_value = 300.0
    mock_processor.get_average_sale.return_value = 100.0

    # format_currency will return a formatted string based on input
    def format_side_effect(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = format_side_effect

    report = report_generator_instance.generate_summary_report()

    assert "SALES SUMMARY REPORT" in report
    assert "Total Records: 3" in report
    assert "Total Sales: $300.00" in report
    assert "Average Sale: $100.00" in report
    assert report.startswith("=" * 50)
    assert report.endswith("=" * 50)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_zero_records(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_summary_report when there are zero records."""
    mock_processor.records = []
    mock_processor.get_total_sales.return_value = 0.0
    mock_processor.get_average_sale.return_value = 0.0

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_summary_report()

    assert "Total Records: 0" in report
    assert "Total Sales: $0.00" in report
    assert "Average Sale: $0.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_multiple_regions(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report with multiple regions and records."""
    class Record:
        def __init__(self, amount):
            self.amount = amount

    grouped = {
        "North": [Record(100.0), Record(200.0)],
        "South": [Record(50.0)],
    }
    mock_processor.group_by_region.return_value = grouped

    def format_side_effect(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = format_side_effect

    report = report_generator_instance.generate_regional_report()

    assert "REGIONAL SALES REPORT" in report
    assert "Region: North" in report
    assert "Records: 2" in report
    assert "Total Sales: $300.00" in report
    assert "Average: $150.00" in report
    assert "Region: South" in report
    assert "Records: 1" in report
    assert "Total Sales: $50.00" in report
    assert "Average: $50.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_empty_groups(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report when no regions are returned."""
    mock_processor.group_by_region.return_value = {}

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_regional_report()

    assert "REGIONAL SALES REPORT" in report
    # No 'Region:' lines should be present beyond the header block
    assert "Region:" not in report.split("REGIONAL SALES REPORT")[-1]


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_zero_records_in_region(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report when a region has zero records."""
    grouped = {
        "EmptyRegion": [],
    }
    mock_processor.group_by_region.return_value = grouped

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_regional_report()

    assert "Region: EmptyRegion" in report
    assert "Records: 0" in report
    assert "Total Sales: $0.00" in report
    assert "Average: $0.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_default_limit(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report with default limit."""
    mock_processor.get_top_products.return_value = [
        ("Product A", 1000.0),
        ("Product B", 800.0),
    ]

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report()

    assert "TOP 5 PRODUCTS BY SALES" in report
    assert "1. Product A: $1,000.00" in report
    assert "2. Product B: $800.00" in report
    # Ensure enumeration starts at 1 and increments
    assert "3." not in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_custom_limit(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report with custom limit and more products."""
    mock_processor.get_top_products.return_value = [
        ("P1", 10.0),
        ("P2", 20.0),
        ("P3", 30.0),
    ]

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=3)

    assert "TOP 3 PRODUCTS BY SALES" in report
    assert "1. P1: $10.00" in report
    assert "2. P2: $20.00" in report
    assert "3. P3: $30.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_empty(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report when get_top_products returns empty list."""
    mock_processor.get_top_products.return_value = []

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=2)

    assert "TOP 2 PRODUCTS BY SALES" in report
    # No product lines should exist between header and footer besides separators
    lines = report.splitlines()
    product_lines = [line for line in lines if line and line[0].isdigit()]
    assert product_lines == []


def test_reportgenerator_apply_advanced_filter_valid_expression(report_generator_instance, mock_processor):
    """Test apply_advanced_filter with a valid filter_expression."""
    # Records will be simple objects with attributes
    class Record:
        def __init__(self, amount, region):
            self.amount = amount
            self.region = region

    r1 = Record(100, "North")
    r2 = Record(50, "South")
    r3 = Record(200, "North")
    mock_processor.records = [r1, r2, r3]

    # Expression is evaluated in the context where 'record' is defined in the loop
    expression = "record.amount > 80 and record.region == 'North'"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    assert len(filtered) == 2
    assert r1 in filtered
    assert r3 in filtered
    assert r2 not in filtered


def test_reportgenerator_apply_advanced_filter_invalid_expression(report_generator_instance, mock_processor):
    """Test apply_advanced_filter silently ignores exceptions from eval."""
    class Record:
        def __init__(self, amount):
            self.amount = amount

    r1 = Record(100)
    mock_processor.records = [r1]

    # This expression will raise a NameError (undefined variable 'x')
    expression = "x > 10"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    # Since exception is swallowed, result should be empty
    assert filtered == []


def test_reportgenerator_apply_advanced_filter_expression_raises_for_some_records(report_generator_instance, mock_processor):
    """Test apply_advanced_filter when expression fails for some records but not others."""
    class Record:
        def __init__(self, amount, flag):
            self.amount = amount
            self.flag = flag

    r1 = Record(100, True)
    r2 = Record(200, False)
    # For r2, accessing record.nonexistent will raise AttributeError
    mock_processor.records = [r1, r2]

    expression = "record.flag and record.amount > 50 and record.nonexistent == 1"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    # r1 will raise AttributeError; r2 will also raise before any True result
    assert filtered == []


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_basic(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report with normal values."""
    mock_business_calculator.calculate_compound_growth_rate.return_value = 5.1234

    def format_side_effect(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = format_side_effect

    report = report_generator_instance.calculate_growth_report(
        region="North",
        start_value=1000.0,
        end_value=1200.0,
        periods=2,
    )

    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        1000.0, 1200.0, 2
    )

    assert "GROWTH ANALYSIS - North" in report
    assert "Starting Value: $1,000.00" in report
    assert "Ending Value: $1,200.00" in report
    assert "Periods: 2" in report
    # Growth rate formatted to 2 decimal places with percent sign
    assert "Growth Rate: 5.12%" in report


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_zero_periods(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report when BusinessCalculator returns negative or zero growth."""
    mock_business_calculator.calculate_compound_growth_rate.return_value = 0.0

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region="Global",
        start_value=500.0,
        end_value=500.0,
        periods=1,
    )

    assert "GROWTH ANALYSIS - Global" in report
    assert "Starting Value: $500.00" in report
    assert "Ending Value: $500.00" in report
    assert "Growth Rate: 0.00%" in report


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_negative_growth(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report with negative growth rate."""
    mock_business_calculator.calculate_compound_growth_rate.return_value = -3.4567

    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region="DeclineRegion",
        start_value=1000.0,
        end_value=900.0,
        periods=1,
    )

    assert "GROWTH ANALYSIS - DeclineRegion" in report
    assert "Starting Value: $1,000.00" in report
    assert "Ending Value: $900.00" in report
    assert "Growth Rate: -3.46%" in report