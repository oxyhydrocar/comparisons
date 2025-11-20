import pytest
from unittest.mock import Mock, patch, call
from types import SimpleNamespace

from report_generator import ReportGenerator


@pytest.fixture
def processor_mock():
    """Create a processor mock with required interface for ReportGenerator."""
    mock = Mock()
    mock.get_total_sales = Mock(return_value=0)
    mock.get_average_sale = Mock(return_value=0)
    mock.group_by_region = Mock(return_value={})
    mock.get_top_products = Mock(return_value=[])
    mock.records = []
    return mock


@pytest.fixture
def report_generator(processor_mock):
    """Create a ReportGenerator instance with a mocked processor."""
    return ReportGenerator(processor=processor_mock)


@pytest.fixture
def currency_patcher():
    """Patch format_currency to a deterministic formatter that prefixes with $ and two decimals."""
    with patch('report_generator.format_currency', side_effect=lambda x: f"${x:,.2f}") as mock_fmt:
        yield mock_fmt


def make_record(amount, region="NA"):
    """Helper to create a simple record object with amount and region attributes."""
    return SimpleNamespace(amount=amount, region=region)


def test_reportgenerator_init_stores_processor(processor_mock):
    """Test that ReportGenerator stores the processor dependency."""
    rg = ReportGenerator(processor_mock)
    assert rg.processor is processor_mock


def test_reportgenerator_generate_summary_report_builds_expected(report_generator, processor_mock, currency_patcher):
    """Test generate_summary_report builds the correct string with formatted values."""
    processor_mock.get_total_sales.return_value = 1234.56
    processor_mock.get_average_sale.return_value = 123.45
    processor_mock.records = [1, 2, 3]  # only length matters

    expected = "\n".join([
        "=" * 50,
        "SALES SUMMARY REPORT",
        "=" * 50,
        "Total Records: 3",
        "Total Sales: $1,234.56",
        "Average Sale: $123.45",
        "=" * 50,
    ])

    result = report_generator.generate_summary_report()

    assert result == expected
    processor_mock.get_total_sales.assert_called_once()
    processor_mock.get_average_sale.assert_called_once()
    # format_currency should be called for total and average
    assert currency_patcher.call_args_list == [call(1234.56), call(123.45)]


def test_reportgenerator_generate_summary_report_zero_values(report_generator, processor_mock, currency_patcher):
    """Test generate_summary_report with zero records and zero sales."""
    processor_mock.get_total_sales.return_value = 0
    processor_mock.get_average_sale.return_value = 0
    processor_mock.records = []

    expected = "\n".join([
        "=" * 50,
        "SALES SUMMARY REPORT",
        "=" * 50,
        "Total Records: 0",
        "Total Sales: $0.00",
        "Average Sale: $0.00",
        "=" * 50,
    ])

    result = report_generator.generate_summary_report()

    assert result == expected
    assert currency_patcher.call_args_list == [call(0), call(0)]


def test_reportgenerator_generate_regional_report_with_data(report_generator, processor_mock, currency_patcher):
    """Test generate_regional_report aggregates and formats per region, including empty region group."""
    na_records = [make_record(100, "NA"), make_record(50, "NA")]
    emea_records = []  # edge case: empty region list
    processor_mock.group_by_region.return_value = {"NA": na_records, "EMEA": emea_records}

    expected = "\n".join([
        "=" * 50,
        "REGIONAL SALES REPORT",
        "=" * 50,
        "\nRegion: NA",
        "  Records: 2",
        "  Total Sales: $150.00",
        "  Average: $75.00",
        "\nRegion: EMEA",
        "  Records: 0",
        "  Total Sales: $0.00",
        "  Average: $0.00",
        "=" * 50,
    ])

    result = report_generator.generate_regional_report()

    assert result == expected
    # format_currency should be called for NA total and average, EMEA total and average
    assert currency_patcher.call_args_list == [call(150), call(75.0), call(0), call(0)]


def test_reportgenerator_generate_regional_report_empty_group(report_generator, processor_mock, currency_patcher):
    """Test generate_regional_report handles no regions gracefully."""
    processor_mock.group_by_region.return_value = {}

    expected = "\n".join([
        "=" * 50,
        "REGIONAL SALES REPORT",
        "=" * 50,
        "=" * 50,
    ])
    result = report_generator.generate_regional_report()

    assert result == expected
    assert "Region:" not in result
    currency_patcher.assert_not_called()


def test_reportgenerator_generate_top_products_report_default_limit(report_generator, processor_mock, currency_patcher):
    """Test generate_top_products_report with default limit and fewer products returned."""
    processor_mock.get_top_products.return_value = [
        ("Widget A", 1000.0),
        ("Widget B", 500.5),
        ("Widget C", 100),
    ]
    expected = "\n".join([
        "=" * 50,
        "TOP 5 PRODUCTS BY SALES",
        "=" * 50,
        "1. Widget A: $1,000.00",
        "2. Widget B: $500.50",
        "3. Widget C: $100.00",
        "=" * 50,
    ])

    result = report_generator.generate_top_products_report()

    assert result == expected
    processor_mock.get_top_products.assert_called_once_with(5)
    assert currency_patcher.call_args_list == [call(1000.0), call(500.5), call(100)]


def test_reportgenerator_generate_top_products_report_custom_limit(report_generator, processor_mock, currency_patcher):
    """Test generate_top_products_report with a custom limit and verifies header and calls."""
    processor_mock.get_top_products.return_value = [
        ("Prod X", 2000.0),
        ("Prod Y", 1500.25),
    ]
    expected = "\n".join([
        "=" * 50,
        "TOP 2 PRODUCTS BY SALES",
        "=" * 50,
        "1. Prod X: $2,000.00",
        "2. Prod Y: $1,500.25",
        "=" * 50,
    ])

    result = report_generator.generate_top_products_report(limit=2)

    assert result == expected
    processor_mock.get_top_products.assert_called_once_with(2)
    assert currency_patcher.call_args_list == [call(2000.0), call(1500.25)]


def test_reportgenerator_generate_top_products_report_empty(report_generator, processor_mock, currency_patcher):
    """Test generate_top_products_report when no products are returned."""
    processor_mock.get_top_products.return_value = []

    expected = "\n".join([
        "=" * 50,
        "TOP 5 PRODUCTS BY SALES",
        "=" * 50,
        "=" * 50,
    ])
    result = report_generator.generate_top_products_report()

    assert result == expected
    currency_patcher.assert_not_called()


def test_reportgenerator_apply_advanced_filter_valid_expression(report_generator, processor_mock):
    """Test apply_advanced_filter returns records matching a valid expression."""
    processor_mock.records = [
        make_record(50, "NA"),
        make_record(200, "NA"),
        make_record(300, "EU"),
    ]
    expr = 'record.amount > 100 and record.region == "NA"'

    result = report_generator.apply_advanced_filter(expr)

    assert len(result) == 1
    assert result[0].amount == 200 and result[0].region == "NA"


def test_reportgenerator_apply_advanced_filter_invalid_expression_returns_empty(report_generator, processor_mock):
    """Test apply_advanced_filter swallows errors and returns empty for invalid expression."""
    processor_mock.records = [
        make_record(10, "NA"),
        make_record(20, "EU"),
    ]
    expr = 'record.unknown_attr > 0'  # AttributeError for all records

    result = report_generator.apply_advanced_filter(expr)

    assert result == []


def test_reportgenerator_apply_advanced_filter_partial_errors(report_generator, processor_mock):
    """Test apply_advanced_filter continues despite errors for some records."""
    processor_mock.records = [
        make_record(10, "NA"),   # will cause ZeroDivisionError
        make_record(20, "EU"),   # will evaluate to 1/10 => True
        make_record(20, "NA"),   # will evaluate to 1/10 => True
    ]
    expr = '1 / (record.amount - 10)'

    result = report_generator.apply_advanced_filter(expr)

    assert len(result) == 2
    assert all(r.amount == 20 for r in result)


def test_reportgenerator_calculate_growth_report_builds_expected(report_generator, currency_patcher):
    """Test calculate_growth_report builds the expected string and calls BusinessCalculator."""
    start_value = 1000.0
    end_value = 2000.0
    periods = 12

    with patch('report_generator.BusinessCalculator.calculate_compound_growth_rate', return_value=12.3456) as calc_mock:
        expected = "\n".join([
            "=" * 50,
            "GROWTH ANALYSIS - NA",
            "=" * 50,
            "Starting Value: $1,000.00",
            "Ending Value: $2,000.00",
            "Periods: 12",
            "Growth Rate: 12.35%",
            "=" * 50,
        ])

        result = report_generator.calculate_growth_report(region="NA", start_value=start_value, end_value=end_value, periods=periods)

        assert result == expected
        calc_mock.assert_called_once_with(start_value, end_value, periods)


def test_reportgenerator_generate_regional_report_precision(report_generator, processor_mock, currency_patcher):
    """Test generate_regional_report computes average with floating values accurately."""
    records = [make_record(33.33), make_record(66.67)]
    processor_mock.group_by_region.return_value = {"NA": records}

    expected = "\n".join([
        "=" * 50,
        "REGIONAL SALES REPORT",
        "=" * 50,
        "\nRegion: NA",
        "  Records: 2",
        "  Total Sales: $100.00",
        "  Average: $50.00",
        "=" * 50,
    ])

    result = report_generator.generate_regional_report()
    assert result == expected