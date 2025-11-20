import pytest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from report_generator import ReportGenerator


@pytest.fixture
def sample_records():
    """Provide a set of sample records for testing."""
    return [
        SimpleNamespace(amount=100.0, region="NA", product="P1"),
        SimpleNamespace(amount=200.0, region="EMEA", product="P2"),
        SimpleNamespace(amount=50.0, region="NA", product="P3"),
    ]


@pytest.fixture
def mock_processor(sample_records):
    """Create a mocked processor with predictable behavior."""
    proc = Mock()
    proc.records = list(sample_records)

    total = sum(r.amount for r in sample_records)
    avg = total / len(sample_records)

    proc.get_total_sales.return_value = total
    proc.get_average_sale.return_value = avg
    proc.group_by_region.return_value = {
        "NA": [sample_records[0], sample_records[2]],
        "EMEA": [sample_records[1]],
    }

    base_top = [("P2", 500.0), ("P1", 300.0), ("P3", 100.0), ("P4", 50.0)]

    def get_top_products(limit=5):
        return base_top[:limit]

    proc.get_top_products.side_effect = get_top_products

    return proc


@pytest.fixture
def report_generator(mock_processor):
    """Create a ReportGenerator instance with a mocked processor."""
    return ReportGenerator(mock_processor)


@pytest.fixture
def patch_format_currency():
    """Patch format_currency within report_generator module for consistent output."""
    with patch("report_generator.format_currency", side_effect=lambda x: f"${x}") as mock_fmt:
        yield mock_fmt


def test_reportgenerator_init_stores_processor():
    """Test that ReportGenerator stores the processor reference on initialization."""
    proc = Mock()
    rg = ReportGenerator(proc)
    assert rg.processor is proc


def test_reportgenerator_generate_summary_report_basic(report_generator, mock_processor, patch_format_currency):
    """Test generate_summary_report outputs correct lines and uses format_currency."""
    patch_format_currency.reset_mock()
    result = report_generator.generate_summary_report()

    total = mock_processor.get_total_sales.return_value
    avg = mock_processor.get_average_sale.return_value
    count = len(mock_processor.records)

    expected = "\n".join([
        "=" * 50,
        "SALES SUMMARY REPORT",
        "=" * 50,
        f"Total Records: {count}",
        f"Total Sales: ${total}",
        f"Average Sale: ${avg}",
        "=" * 50,
    ])

    assert result == expected
    mock_processor.get_total_sales.assert_called_once()
    mock_processor.get_average_sale.assert_called_once()
    assert patch_format_currency.call_count == 2
    patch_format_currency.assert_any_call(total)
    patch_format_currency.assert_any_call(avg)


def test_reportgenerator_generate_summary_report_zero_records(patch_format_currency):
    """Test generate_summary_report with zero records and zero totals."""
    proc = Mock()
    proc.records = []
    proc.get_total_sales.return_value = 0
    proc.get_average_sale.return_value = 0
    rg = ReportGenerator(proc)

    result = rg.generate_summary_report()

    expected = "\n".join([
        "=" * 50,
        "SALES SUMMARY REPORT",
        "=" * 50,
        "Total Records: 0",
        "Total Sales: $0",
        "Average Sale: $0",
        "=" * 50,
    ])

    assert result == expected


def test_reportgenerator_generate_regional_report_includes_all_regions_and_calculations(
    report_generator, mock_processor, patch_format_currency, sample_records
):
    """Test generate_regional_report aggregates, averages, and formatting per region, including empty regions."""
    # Include an empty region to test avg/total=0
    mock_processor.group_by_region.return_value = {
        "NA": [sample_records[0], sample_records[2]],
        "EMEA": [sample_records[1]],
        "APAC": [],
    }

    result = report_generator.generate_regional_report()

    expected_lines = [
        "=" * 50,
        "REGIONAL SALES REPORT",
        "=" * 50,
        "",  # blank line due to leading \n in "Region:" line
        "Region: NA",
        "  Records: 2",
        "  Total Sales: $150.0",
        "  Average: $75.0",
        "",
        "Region: EMEA",
        "  Records: 1",
        "  Total Sales: $200.0",
        "  Average: $200.0",
        "",
        "Region: APAC",
        "  Records: 0",
        "  Total Sales: $0",
        "  Average: $0",
        "=" * 50,
    ]
    expected = "\n".join(expected_lines)

    assert result == expected
    mock_processor.group_by_region.assert_called_once()


def test_reportgenerator_generate_top_products_report_respects_limit_and_formatting(
    report_generator, mock_processor, patch_format_currency
):
    """Test generate_top_products_report respects limit, ordering, and uses format_currency."""
    result = report_generator.generate_top_products_report(limit=3)

    expected = "\n".join([
        "=" * 50,
        "TOP 3 PRODUCTS BY SALES",
        "=" * 50,
        "1. P2: $500.0",
        "2. P1: $300.0",
        "3. P3: $100.0",
        "=" * 50,
    ])

    assert result == expected
    mock_processor.get_top_products.assert_called_once_with(3)


def test_reportgenerator_generate_top_products_report_default_limit(report_generator, mock_processor, patch_format_currency):
    """Test generate_top_products_report with default limit (5)."""
    # Our mock returns 4 items total; default limit is 5, so expect only 4 lines
    result = report_generator.generate_top_products_report()

    expected = "\n".join([
        "=" * 50,
        "TOP 5 PRODUCTS BY SALES",
        "=" * 50,
        "1. P2: $500.0",
        "2. P1: $300.0",
        "3. P3: $100.0",
        "4. P4: $50.0",
        "=" * 50,
    ])

    assert result == expected
    mock_processor.get_top_products.assert_called_with(5)


def test_reportgenerator_generate_top_products_report_empty_list(report_generator, mock_processor, patch_format_currency):
    """Test generate_top_products_report when processor returns no products."""
    mock_processor.get_top_products.return_value = []

    result = report_generator.generate_top_products_report(limit=2)

    expected = "\n".join([
        "=" * 50,
        "TOP 2 PRODUCTS BY SALES",
        "=" * 50,
        "=" * 50,
    ])

    assert result == expected
    mock_processor.get_top_products.assert_called_once_with(2)


def test_reportgenerator_apply_advanced_filter_filters_records(report_generator, sample_records):
    """Test apply_advanced_filter returns records that match expression."""
    expr = 'record.amount >= 100 and record.region in ("NA", "EMEA")'
    filtered = report_generator.apply_advanced_filter(expr)
    assert filtered == [sample_records[0], sample_records[1]]


def test_reportgenerator_apply_advanced_filter_ignores_exceptions(report_generator):
    """Test apply_advanced_filter silently ignores bad expressions and returns an empty list."""
    expr = "record.nonexistent_field > 0"
    filtered = report_generator.apply_advanced_filter(expr)
    assert filtered == []


def test_reportgenerator_calculate_growth_report_formats_output_and_calls_calculator(
    report_generator, patch_format_currency
):
    """Test calculate_growth_report formats values, percentage, and delegates to BusinessCalculator."""
    with patch("report_generator.BusinessCalculator") as mock_bc:
        mock_bc.calculate_compound_growth_rate.return_value = 12.3456

        result = report_generator.calculate_growth_report(
            region="EMEA", start_value=1000, end_value=2000, periods=4
        )

        expected = "\n".join([
            "=" * 50,
            "GROWTH ANALYSIS - EMEA",
            "=" * 50,
            "Starting Value: $1000",
            "Ending Value: $2000",
            "Periods: 4",
            "Growth Rate: 12.35%",
            "=" * 50,
        ])

        assert result == expected
        mock_bc.calculate_compound_growth_rate.assert_called_once_with(1000, 2000, 4)