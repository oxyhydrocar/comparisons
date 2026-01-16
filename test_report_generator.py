import pytest
from unittest.mock import Mock, patch

from report_generator import ReportGenerator


@pytest.fixture
def mock_processor():
    """Create a mock processor with default attributes for testing."""
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
def test_reportgenerator_generate_summary_report_basic(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_summary_report builds the expected report with basic values."""
    mock_processor.records = [Mock(), Mock(), Mock()]
    mock_processor.get_total_sales.return_value = 1234.56
    mock_processor.get_average_sale.return_value = 411.52

    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.generate_summary_report()

    lines = report.split("\n")
    assert lines[0] == "=" * 50
    assert lines[1] == "SALES SUMMARY REPORT"
    assert lines[2] == "=" * 50
    assert lines[3] == "Total Records: 3"
    assert lines[4] == "Total Sales: $1,234.56"
    assert lines[5] == "Average Sale: $411.52"
    assert lines[6] == "=" * 50

    mock_processor.get_total_sales.assert_called_once()
    mock_processor.get_average_sale.assert_called_once()
    assert len(lines) == 7


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_zero_records(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_summary_report when there are zero records."""
    mock_processor.records = []
    mock_processor.get_total_sales.return_value = 0.0
    mock_processor.get_average_sale.return_value = 0.0
    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.generate_summary_report()
    lines = report.split("\n")

    assert "Total Records: 0" in lines
    assert "Total Sales: $0.00" in lines
    assert "Average Sale: $0.00" in lines


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_multiple_regions(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_regional_report with multiple regions and records."""
    record_a1 = Mock()
    record_a1.amount = 100.0
    record_a2 = Mock()
    record_a2.amount = 200.0
    record_b1 = Mock()
    record_b1.amount = 50.0

    mock_processor.group_by_region.return_value = {
        "North": [record_a1, record_a2],
        "South": [record_b1],
    }

    def fake_format_currency(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = fake_format_currency

    report = report_generator_instance.generate_regional_report()
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "REGIONAL SALES REPORT"
    assert lines[2] == "=" * 50

    assert "Region: North" in report
    assert "  Records: 2" in report
    assert "  Total Sales: $300.00" in report
    assert "  Average: $150.00" in report

    assert "Region: South" in report
    assert "  Records: 1" in report
    assert "  Total Sales: $50.00" in report
    assert "  Average: $50.00" in report

    mock_processor.group_by_region.assert_called_once()


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_empty_region(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_regional_report handles a region with zero records."""
    mock_processor.group_by_region.return_value = {
        "EmptyRegion": [],
    }

    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.generate_regional_report()
    assert "Region: EmptyRegion" in report
    assert "  Records: 0" in report
    assert "  Total Sales: $0.00" in report
    assert "  Average: $0.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_default_limit(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_top_products_report with default limit and multiple products."""
    mock_processor.get_top_products.return_value = [
        ("Product A", 1000.0),
        ("Product B", 750.5),
        ("Product C", 500.25),
    ]

    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.generate_top_products_report()
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "TOP 5 PRODUCTS BY SALES"
    assert lines[2] == "=" * 50
    assert "1. Product A: $1,000.00" in lines
    assert "2. Product B: $750.50" in lines
    assert "3. Product C: $500.25" in lines
    assert lines[-1] == "=" * 50

    mock_processor.get_top_products.assert_called_once_with(5)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_custom_limit_empty(mock_format_currency, mock_processor, report_generator_instance):
    """Test generate_top_products_report with custom limit and no products."""
    mock_processor.get_top_products.return_value = []
    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=3)
    lines = report.split("\n")

    assert lines[1] == "TOP 3 PRODUCTS BY SALES"
    assert lines[2] == "=" * 50
    assert lines[-1] == "=" * 50
    assert len(lines) == 4
    mock_processor.get_top_products.assert_called_once_with(3)


def test_reportgenerator_apply_advanced_filter_valid_expression(report_generator_instance, mock_processor):
    """Test apply_advanced_filter filters records correctly with a valid expression."""
    record1 = Mock()
    record1.amount = 100
    record2 = Mock()
    record2.amount = 200
    record3 = Mock()
    record3.amount = 50

    mock_processor.records = [record1, record2, record3]

    filter_expression = "record.amount > 100"

    result = report_generator_instance.apply_advanced_filter(filter_expression)

    assert result == [record2]


def test_reportgenerator_apply_advanced_filter_uses_eval_context(report_generator_instance, mock_processor):
    """Test apply_advanced_filter that eval has access to 'record' variable only."""
    record1 = Mock()
    record1.amount = 10
    record2 = Mock()
    record2.amount = 20
    mock_processor.records = [record1, record2]

    filter_expression = "record.amount == 20"

    result = report_generator_instance.apply_advanced_filter(filter_expression)

    assert result == [record2]


def test_reportgenerator_apply_advanced_filter_invalid_expression_silently_ignored(report_generator_instance, mock_processor):
    """Test apply_advanced_filter silently ignores exceptions from eval."""
    record1 = Mock()
    record1.amount = 10
    mock_processor.records = [record1]

    filter_expression = "1 / 0"

    result = report_generator_instance.apply_advanced_filter(filter_expression)

    assert result == []


def test_reportgenerator_apply_advanced_filter_expression_raises_for_some_records(report_generator_instance, mock_processor):
    """Test apply_advanced_filter continues processing when some records cause eval errors."""
    record1 = Mock()
    record1.amount = 10
    record2 = Mock()
    delattr(record2, "amount")
    record3 = Mock()
    record3.amount = 30

    mock_processor.records = [record1, record2, record3]

    filter_expression = "record.amount > 20"

    result = report_generator_instance.apply_advanced_filter(filter_expression)

    assert result == [record3]


@patch("report_generator.format_currency")
@patch("report_generator.BusinessCalculator")
def test_reportgenerator_calculate_growth_report_basic(mock_business_calculator, mock_format_currency, report_generator_instance):
    """Test calculate_growth_report builds the expected report and uses BusinessCalculator."""
    mock_business_calculator.calculate_compound_growth_rate.return_value = 12.3456
    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    region = "North"
    start_value = 1000.0
    end_value = 2000.0
    periods = 3

    report = report_generator_instance.calculate_growth_report(
        region=region,
        start_value=start_value,
        end_value=end_value,
        periods=periods,
    )

    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        start_value, end_value, periods
    )

    lines = report.split("\n")
    assert lines[0] == "=" * 50
    assert lines[1] == f"GROWTH ANALYSIS - {region}"
    assert lines[2] == "=" * 50
    assert lines[3] == "Starting Value: $1,000.00"
    assert lines[4] == "Ending Value: $2,000.00"
    assert lines[5] == f"Periods: {periods}"
    assert lines[6] == "Growth Rate: 12.35%"
    assert lines[7] == "=" * 50


@patch("report_generator.format_currency")
@patch("report_generator.BusinessCalculator")
def test_reportgenerator_calculate_growth_report_zero_periods(mock_business_calculator, mock_format_currency, report_generator_instance):
    """Test calculate_growth_report when BusinessCalculator returns negative or edge growth."""
    mock_business_calculator.calculate_compound_growth_rate.return_value = -5.0
    mock_format_currency.side_effect = lambda x: f"${x:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region="TestRegion",
        start_value=500.0,
        end_value=400.0,
        periods=1,
    )

    assert "Growth Rate: -5.00%" in report
    mock_business_calculator.calculate_compound_growth_rate.assert_called_once()