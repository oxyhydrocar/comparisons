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
    """Create a ReportGenerator instance for testing."""
    return ReportGenerator(processor=mock_processor)


def test_reportgenerator_init_stores_processor(mock_processor):
    """Test that ReportGenerator initialization stores the processor."""
    rg = ReportGenerator(processor=mock_processor)
    assert rg.processor is mock_processor


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_basic(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_summary_report returns correctly formatted report."""
    mock_processor.records = [1, 2, 3]
    mock_processor.get_total_sales.return_value = 150.5
    mock_processor.get_average_sale.return_value = 50.1666667

    def format_side_effect(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = format_side_effect

    report = report_generator_instance.generate_summary_report()

    lines = report.split("\n")
    assert lines[0] == "=" * 50
    assert lines[1] == "SALES SUMMARY REPORT"
    assert lines[2] == "=" * 50
    assert lines[3] == "Total Records: 3"
    assert lines[4] == "Total Sales: $150.50"
    assert lines[5] == "Average Sale: $50.17"
    assert lines[6] == "=" * 50

    mock_processor.get_total_sales.assert_called_once()
    mock_processor.get_average_sale.assert_called_once()
    mock_format_currency.assert_any_call(150.5)
    mock_format_currency.assert_any_call(50.1666667)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_summary_report_zero_records(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_summary_report handles zero records."""
    mock_processor.records = []
    mock_processor.get_total_sales.return_value = 0.0
    mock_processor.get_average_sale.return_value = 0.0
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_summary_report()

    assert "Total Records: 0" in report
    assert "Total Sales: $0.00" in report
    assert "Average Sale: $0.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_basic(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report with multiple regions and records."""
    Record = lambda amount: Mock(amount=amount)  # simple record object
    mock_processor.group_by_region.return_value = {
        "North": [Record(100.0), Record(200.0)],
        "South": [Record(50.0)],
    }

    def format_side_effect(value):
        return f"${value:,.2f}"

    mock_format_currency.side_effect = format_side_effect

    report = report_generator_instance.generate_regional_report()
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "REGIONAL SALES REPORT"
    assert lines[2] == "=" * 50

    assert "Region: North" in report
    assert "Records: 2" in report
    assert "Total Sales: $300.00" in report
    assert "Average: $150.00" in report

    assert "Region: South" in report
    assert "Records: 1" in report
    assert "Total Sales: $50.00" in report
    assert "Average: $50.00" in report

    # Ensure no division by zero happened and currency called correctly
    mock_format_currency.assert_any_call(300.0)
    mock_format_currency.assert_any_call(150.0)
    mock_format_currency.assert_any_call(50.0)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_regional_report_empty_group(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_regional_report with a region that has zero records."""
    mock_processor.group_by_region.return_value = {"EmptyRegion": []}
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_regional_report()

    assert "Region: EmptyRegion" in report
    assert "Records: 0" in report
    assert "Total Sales: $0.00" in report
    assert "Average: $0.00" in report


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_basic(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report formats top products correctly."""
    mock_processor.get_top_products.return_value = [
        ("Product A", 1000.0),
        ("Product B", 500.5),
    ]
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.generate_top_products_report(limit=2)
    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "TOP 2 PRODUCTS BY SALES"
    assert lines[2] == "=" * 50
    assert lines[3] == "1. Product A: $1,000.00"
    assert lines[4] == "2. Product B: $500.50"
    assert lines[5] == "=" * 50

    mock_processor.get_top_products.assert_called_once_with(2)


@patch("report_generator.format_currency")
def test_reportgenerator_generate_top_products_report_default_limit(mock_format_currency, report_generator_instance, mock_processor):
    """Test generate_top_products_report uses default limit when not provided."""
    mock_processor.get_top_products.return_value = []
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report_generator_instance.generate_top_products_report()
    mock_processor.get_top_products.assert_called_once_with(5)


def test_reportgenerator_apply_advanced_filter_basic(report_generator_instance, mock_processor):
    """Test apply_advanced_filter filters records using eval expression."""
    Record = lambda region, amount: Mock(region=region, amount=amount)
    records = [
        Record("North", 100),
        Record("South", 50),
        Record("North", 200),
    ]
    mock_processor.records = records

    # filter_expression is evaluated in the context where 'record' is defined
    # but in the method, eval is called without specifying locals/globals
    # so it relies on 'record' defined in the for loop
    filtered = report_generator_instance.apply_advanced_filter("record.region == 'North' and record.amount > 100")

    assert len(filtered) == 1
    assert filtered[0].amount == 200


def test_reportgenerator_apply_advanced_filter_invalid_expression(report_generator_instance, mock_processor):
    """Test apply_advanced_filter silently ignores invalid expressions."""
    Record = lambda amount: Mock(amount=amount)
    mock_processor.records = [Record(10), Record(20)]

    # This expression will raise an exception inside eval due to NameError (undefined var)
    filtered = report_generator_instance.apply_advanced_filter("undefined_var > 0")

    # On exception, method should just continue; result should be empty
    assert filtered == []


def test_reportgenerator_apply_advanced_filter_expression_raises_runtime_error(report_generator_instance, mock_processor):
    """Test apply_advanced_filter ignores runtime errors triggered by expression."""
    Record = lambda amount: Mock(amount=amount)
    mock_processor.records = [Record(0), Record(1)]

    # Division by zero for first record, but second would be fine;
    # however, any exception is caught and ignored, so no records are added.
    filtered = report_generator_instance.apply_advanced_filter("1 / record.amount > 0")

    assert filtered == []


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_basic(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report formats growth analysis correctly."""
    start_value = 1000.0
    end_value = 2000.0
    periods = 2
    growth_rate = 41.421356237  # arbitrary number for testing

    mock_business_calculator.calculate_compound_growth_rate.return_value = growth_rate
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region="North",
        start_value=start_value,
        end_value=end_value,
        periods=periods,
    )

    lines = report.split("\n")

    assert lines[0] == "=" * 50
    assert lines[1] == "GROWTH ANALYSIS - North"
    assert lines[2] == "=" * 50
    assert lines[3] == "Starting Value: $1,000.00"
    assert lines[4] == "Ending Value: $2,000.00"
    assert lines[5] == f"Periods: {periods}"
    # growth rate formatted to 2 decimals with percent sign
    assert lines[6] == f"Growth Rate: {growth_rate:.2f}%"
    assert lines[7] == "=" * 50

    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        start_value, end_value, periods
    )
    mock_format_currency.assert_any_call(start_value)
    mock_format_currency.assert_any_call(end_value)


@patch("report_generator.BusinessCalculator")
@patch("report_generator.format_currency")
def test_reportgenerator_calculate_growth_report_zero_periods(mock_format_currency, mock_business_calculator, report_generator_instance):
    """Test calculate_growth_report behavior when BusinessCalculator returns inf or raises for zero periods."""
    start_value = 1000.0
    end_value = 2000.0
    periods = 0

    mock_business_calculator.calculate_compound_growth_rate.return_value = float("inf")
    mock_format_currency.side_effect = lambda v: f"${v:,.2f}"

    report = report_generator_instance.calculate_growth_report(
        region="All",
        start_value=start_value,
        end_value=end_value,
        periods=periods,
    )

    assert "GROWTH ANALYSIS - All" in report
    assert "Starting Value: $1,000.00" in report
    assert "Ending Value: $2,000.00" in report
    assert "Periods: 0" in report
    # Just ensure the inf was formatted; exact string will be 'inf%'
    assert "Growth Rate: inf%" in report


def test_reportgenerator_apply_advanced_filter_uses_current_record(report_generator_instance, mock_processor):
    """Test apply_advanced_filter ensures expression refers to current record only."""
    Record = lambda amount: Mock(amount=amount)
    mock_processor.records = [Record(10), Record(20), Record(30)]

    # Expression ensures only records with amount >= 20 are selected
    filtered = report_generator_instance.apply_advanced_filter("record.amount >= 20")

    assert len(filtered) == 2
    assert filtered[0].amount == 20
    assert filtered[1].amount == 30