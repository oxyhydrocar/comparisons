import pytest
from unittest.mock import Mock, patch

from report_generator import ReportGenerator


@pytest.fixture
def mock_processor():
    """Create a mock processor with default attributes and methods."""
    processor = Mock()
    processor.records = []
    processor.get_total_sales.return_value = 0.0
    processor.get_average_sale.return_value = 0.0
    processor.group_by_region.return_value = {}
    processor.get_top_products.return_value = []
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
    """Test generate_summary_report builds the expected summary with formatted values."""
    mock_processor.records = [1, 2, 3]
    mock_processor.get_total_sales.return_value = 300.50
    mock_processor.get_average_sale.return_value = 100.17
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_summary_report()

    lines = report.split("\n")
    assert lines[0] == "=" * 50
    assert lines[1] == "SALES SUMMARY REPORT"
    assert lines[2] == "=" * 50
    assert lines[3] == "Total Records: 3"
    assert lines[4] == "Total Sales: $300.50"
    assert lines[5] == "Average Sale: $100.17"
    assert lines[6] == "=" * 50

    mock_processor.get_total_sales.assert_called_once()
    mock_processor.get_average_sale.assert_called_once()
    mock_format_currency.assert_any_call(300.50)
    mock_format_currency.assert_any_call(100.17)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_zero_records(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_summary_report when there are zero records."""
    mock_processor.records = []
    mock_processor.get_total_sales.return_value = 0.0
    mock_processor.get_average_sale.return_value = 0.0
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_summary_report()

    lines = report.split("\n")
    assert "Total Records: 0" in lines
    assert "Total Sales: $0.00" in lines
    assert "Average Sale: $0.00" in lines


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_multiple_regions(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report with multiple regions and records."""
    Record = Mock
    r1 = Record()
    r1.amount = 100.0
    r2 = Record()
    r2.amount = 200.0
    r3 = Record()
    r3.amount = 50.0

    mock_processor.group_by_region.return_value = {
        "North": [r1, r2],
        "South": [r3],
    }

    def fc(val):
        return f"${val:,.2f}"

    mock_format_currency.side_effect = fc

    report = report_generator_instance.generate_regional_report()
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "REGIONAL SALES REPORT"
    assert lines[2] == "=" * 50

    report_text = "\n".join(lines)
    assert "\nRegion: North" in report_text
    assert "Records: 2" in report_text
    assert "Total Sales: $300.00" in report_text
    assert "Average: $150.00" in report_text

    assert "\nRegion: South" in report_text
    assert "Records: 1" in report_text
    assert "Total Sales: $50.00" in report_text
    assert "Average: $50.00" in report_text

    assert report_text.strip().endswith("=" * 50)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_empty_region(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report when regions have no records (avg should be formatted from 0)."""
    mock_processor.group_by_region.return_value = {
        "EmptyRegion": [],
    }
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_regional_report()
    report_text = report

    assert "\nRegion: EmptyRegion" in report_text
    assert "Records: 0" in report_text
    assert "Total Sales: $0.00" in report_text
    assert "Average: $0.00" in report_text


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_default_limit(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report with default limit value."""
    mock_processor.get_top_products.return_value = [
        ("Product A", 300.0),
        ("Product B", 200.5),
    ]
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report()
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "TOP 5 PRODUCTS BY SALES"
    assert "1. Product A: $300.00" in lines
    assert "2. Product B: $200.50" in lines
    assert lines[-1] == "=" * 50

    mock_processor.get_top_products.assert_called_once_with(5)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_custom_limit(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report with a custom limit."""
    mock_processor.get_top_products.return_value = [
        ("Product X", 1000.0),
    ]
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=1)
    assert "TOP 1 PRODUCTS BY SALES" in report
    assert "1. Product X: $1,000.00" in report
    mock_processor.get_top_products.assert_called_once_with(1)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_no_products(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report when there are no products."""
    mock_processor.get_top_products.return_value = []
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=3)
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "TOP 3 PRODUCTS BY SALES"
    # Only header and footer with no product lines in between (3 empty product slots not generated)
    assert lines[-1] == "=" * 50


def test_reportgenerator_apply_advanced_filter_simple_condition(report_generator_instance, mock_processor):
    """Test apply_advanced_filter with a simple eval condition using record attributes."""
    Record = Mock
    r1 = Record()
    r1.amount = 100
    r1.region = "North"
    r2 = Record()
    r2.amount = 50
    r2.region = "South"
    r3 = Record()
    r3.amount = 200
    r3.region = "North"

    mock_processor.records = [r1, r2, r3]

    # Note: filter_expression is evaluated in scope where 'record' is defined in loop
    expression = "record.amount > 80 and record.region == 'North'"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    assert len(filtered) == 2
    assert r1 in filtered
    assert r3 in filtered
    assert r2 not in filtered


def test_reportgenerator_apply_advanced_filter_invalid_expression(report_generator_instance, mock_processor):
    """Test apply_advanced_filter silently ignores errors in eval and returns unfiltered subset."""
    Record = Mock
    r1 = Record()
    r1.amount = 100
    mock_processor.records = [r1]

    # This expression will raise NameError because 'unknown' is not defined.
    expression = "unknown + 1"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    assert filtered == []


def test_reportgenerator_apply_advanced_filter_expression_raises_for_some_records(report_generator_instance, mock_processor):
    """Test apply_advanced_filter where eval fails for some records but passes for others."""
    Record = Mock
    r1 = Record()
    r1.amount = 100
    r2 = Record()
    # r2 has no 'amount' attribute and will cause AttributeError in eval
    mock_processor.records = [r1, r2]

    expression = "record.amount > 50"

    filtered = report_generator_instance.apply_advanced_filter(expression)

    assert filtered == [r1]


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_basic(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report produces correct formatted report and uses BusinessCalculator."""
    start_value = 1000.0
    end_value = 2000.0
    periods = 4
    region = "North"

    mock_business_calculator.calculate_compound_growth_rate.return_value = 18.9205
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region=region,
        start_value=start_value,
        end_value=end_value,
        periods=periods,
    )

    lines = report.split("\n")
    assert lines[0] == "=" * 50
    assert lines[1] == f"GROWTH ANALYSIS - {region}"
    assert lines[2] == "=" * 50
    assert lines[3] == "Starting Value: $1,000.00"
    assert lines[4] == "Ending Value: $2,000.00"
    assert lines[5] == f"Periods: {periods}"
    assert lines[6] == "Growth Rate: 18.92%"
    assert lines[7] == "=" * 50

    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        start_value, end_value, periods
    )
    mock_format_currency.assert_any_call(start_value)
    mock_format_currency.assert_any_call(end_value)


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_zero_periods(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report when BusinessCalculator returns negative/edge growth."""
    start_value = 1000.0
    end_value = 1000.0
    periods = 0
    region = "TestRegion"

    mock_business_calculator.calculate_compound_growth_rate.return_value = 0.0
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region=region,
        start_value=start_value,
        end_value=end_value,
        periods=periods,
    )

    assert "Growth Rate: 0.00%" in report
    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        start_value, end_value, periods
    )