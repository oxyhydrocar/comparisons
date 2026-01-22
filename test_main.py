import pytest
from unittest.mock import Mock, patch, call
from main import (
    create_sample_data,
    demonstrate_sorting,
    demonstrate_reports,
    demonstrate_calculations,
    demonstrate_parallel_processing,
    main,
)


@pytest.fixture
def sample_sales_records():
    """Fixture returning the sample sales records created by create_sample_data."""
    return create_sample_data()


@pytest.fixture
def patched_data_processor():
    """Fixture to patch DataProcessor in main module."""
    with patch("main.DataProcessor") as mock_dp_cls:
        yield mock_dp_cls


@pytest.fixture
def patched_report_generator():
    """Fixture to patch ReportGenerator in main module."""
    with patch("main.ReportGenerator") as mock_rg_cls:
        yield mock_rg_cls


@pytest.fixture
def patched_business_calculator():
    """Fixture to patch BusinessCalculator in main module."""
    with patch("main.BusinessCalculator") as mock_bc_cls:
        yield mock_bc_cls


@pytest.fixture
def patched_format_currency():
    """Fixture to patch format_currency in main module."""
    with patch("main.format_currency") as mock_fmt:
        yield mock_fmt


def test_create_sample_data_length_and_type(sample_sales_records):
    """Test create_sample_data returns a list of 10 SalesRecord-like objects."""
    assert isinstance(sample_sales_records, list)
    assert len(sample_sales_records) == 10
    # We can't import SalesRecord here (comes from another module),
    # but we can check attributes that must exist.
    first = sample_sales_records[0]
    assert hasattr(first, "id")
    assert hasattr(first, "product")
    assert hasattr(first, "amount")
    assert hasattr(first, "date")
    assert hasattr(first, "region")


@pytest.mark.parametrize(
    "index,expected_product,expected_amount",
    [
        (0, "Laptop", 1200.00),
        (1, "Mouse", 25.00),
        (9, "Monitor", 400.00),
    ],
)
def test_create_sample_data_contents(sample_sales_records, index, expected_product, expected_amount):
    """Test that create_sample_data returns expected records at specific positions."""
    record = sample_sales_records[index]
    assert record.product == expected_product
    assert record.amount == pytest.approx(expected_amount)


def test_demonstrate_sorting_happy_path(patched_data_processor, patched_format_currency, capsys):
    """Test demonstrate_sorting calls DataProcessor.sort_by_amount and formats output."""
    # Configure DataProcessor mock instance
    dp_instance = patched_data_processor.return_value

    # Create mock records with required attributes
    mock_records = []
    for i in range(5):
        rec = Mock()
        rec.product = f"Product{i}"
        rec.amount = 100.0 + i
        mock_records.append(rec)

    # sort_by_amount returns at least 5 records
    dp_instance.sort_by_amount.return_value = mock_records

    # format_currency just returns a formatted string
    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    demonstrate_sorting()

    # Ensure DataProcessor was instantiated with sample data
    assert patched_data_processor.called is True

    # Ensure sort_by_amount was called exactly once
    dp_instance.sort_by_amount.assert_called_once()

    # Capture printed output
    captured = capsys.readouterr().out

    # Verify that header and first few records are printed
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "Records sorted by amount:" in captured
    for i in range(5):
        assert f"Product{i}: ${100.0 + i:,.2f}" in captured


def test_demonstrate_sorting_handles_empty_sort_result(patched_data_processor, patched_format_currency, capsys):
    """Test demonstrate_sorting when sort_by_amount returns an empty list."""
    dp_instance = patched_data_processor.return_value
    dp_instance.sort_by_amount.return_value = []

    demonstrate_sorting()

    captured = capsys.readouterr().out
    # Still prints headers even if no data
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "Records sorted by amount:" in captured
    # No calls to format_currency because no records
    patched_format_currency.assert_not_called()


def test_demonstrate_reports_happy_path(patched_data_processor, patched_report_generator, capsys):
    """Test demonstrate_reports uses ReportGenerator to create and print three reports."""
    rg_instance = patched_report_generator.return_value
    rg_instance.generate_summary_report.return_value = "SUMMARY REPORT"
    rg_instance.generate_top_products_report.return_value = "TOP PRODUCTS REPORT"
    rg_instance.generate_regional_report.return_value = "REGIONAL REPORT"

    demonstrate_reports()

    # Ensure DataProcessor and ReportGenerator are instantiated
    assert patched_data_processor.called is True
    patched_report_generator.assert_called_once()
    # Ensure reports are generated with expected arguments
    rg_instance.generate_summary_report.assert_called_once()
    rg_instance.generate_top_products_report.assert_called_once_with(3)
    rg_instance.generate_regional_report.assert_called_once()

    captured = capsys.readouterr().out
    assert "--- Generating Reports ---" in captured
    assert "SUMMARY REPORT" in captured
    assert "TOP PRODUCTS REPORT" in captured
    assert "REGIONAL REPORT" in captured


def test_demonstrate_reports_handles_report_exceptions(
    patched_data_processor, patched_report_generator, capsys
):
    """Test demonstrate_reports does not crash when report generation raises an error."""
    rg_instance = patched_report_generator.return_value
    rg_instance.generate_summary_report.side_effect = Exception("summary error")
    rg_instance.generate_top_products_report.return_value = "TOP PRODUCTS REPORT"
    rg_instance.generate_regional_report.return_value = "REGIONAL REPORT"

    # Function doesn't handle exceptions explicitly, so we expect it to propagate.
    with pytest.raises(Exception) as excinfo:
        demonstrate_reports()
    assert "summary error" in str(excinfo.value)


def test_demonstrate_calculations_happy_path(patched_business_calculator, capsys):
    """Test demonstrate_calculations calls BusinessCalculator methods and prints results."""
    # Configure return values for the static methods
    patched_business_calculator.calculate_profit_margin.return_value = 40.0
    patched_business_calculator.calculate_roi.return_value = 50.0
    patched_business_calculator.calculate_compound_growth_rate.return_value = 14.47
    patched_business_calculator.calculate_break_even_point.return_value = 250.0

    demonstrate_calculations()

    # Verify each calculation called with the correct arguments
    patched_business_calculator.calculate_profit_margin.assert_called_once_with(10000, 6000)
    patched_business_calculator.calculate_roi.assert_called_once_with(15000, 10000)
    patched_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        10000, 15000, 3
    )
    patched_business_calculator.calculate_break_even_point.assert_called_once_with(
        5000, 50, 30
    )

    captured = capsys.readouterr().out
    assert "--- Business Calculations ---" in captured
    assert "Profit Margin" in captured
    assert "ROI" in captured
    assert "Compound Growth Rate" in captured
    assert "Break-even Point" in captured
    # Check formatted numbers were used (two decimals / no decimals)
    assert "40.00%" in captured
    assert "50.00%" in captured
    assert "14.47%" in captured
    assert "250" in captured


@pytest.mark.parametrize(
    "method_name,params",
    [
        ("calculate_profit_margin", (10000, 6000)),
        ("calculate_roi", (15000, 10000)),
        ("calculate_compound_growth_rate", (10000, 15000, 3)),
        ("calculate_break_even_point", (5000, 50, 30)),
    ],
)
def test_demonstrate_calculations_raises_from_calculator(
    patched_business_calculator, method_name, params
):
    """Test demonstrate_calculations propagates exceptions from BusinessCalculator."""
    getattr(patched_business_calculator, method_name).side_effect = ValueError("calc error")

    with pytest.raises(ValueError) as excinfo:
        demonstrate_calculations()
    assert "calc error" in str(excinfo.value)


def test_demonstrate_parallel_processing_happy_path(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_parallel_processing processes records and prints high value items."""
    dp_instance = patched_data_processor.return_value

    # Create mock records that are returned by process_records_parallel
    high_value_records = []
    for i in range(3):
        rec = Mock()
        rec.product = f"HV{i}"
        rec.amount = 200.0 + i * 50
        high_value_records.append(rec)

    dp_instance.process_records_parallel.return_value = high_value_records
    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    demonstrate_parallel_processing()

    # DataProcessor instantiated and process_records_parallel called
    assert patched_data_processor.called is True
    dp_instance.process_records_parallel.assert_called_once_with(100)

    captured = capsys.readouterr().out
    assert "--- Parallel Processing Demo ---" in captured
    assert "Found 3 records above $100:" in captured
    for i, rec in enumerate(high_value_records):
        assert f"{rec.product}: ${rec.amount:,.2f}" in captured


def test_demonstrate_parallel_processing_empty_result(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_parallel_processing with no high value records."""
    dp_instance = patched_data_processor.return_value
    dp_instance.process_records_parallel.return_value = []

    demonstrate_parallel_processing()

    captured = capsys.readouterr().out
    assert "Found 0 records above $100:" in captured
    patched_format_currency.assert_not_called()


def test_main_happy_path(
    patched_data_processor,
    patched_report_generator,
    patched_business_calculator,
    patched_format_currency,
    capsys,
):
    """Test main orchestrates all demo functions and prints overall banners."""
    # Setup minimal return values so that inner functions run without error
    dp_instance = patched_data_processor.return_value
    dp_instance.sort_by_amount.return_value = []
    dp_instance.process_records_parallel.return_value = []

    rg_instance = patched_report_generator.return_value
    rg_instance.generate_summary_report.return_value = "SUMMARY"
    rg_instance.generate_top_products_report.return_value = "TOP"
    rg_instance.generate_regional_report.return_value = "REGION"

    patched_business_calculator.calculate_profit_margin.return_value = 40.0
    patched_business_calculator.calculate_roi.return_value = 50.0
    patched_business_calculator.calculate_compound_growth_rate.return_value = 10.0
    patched_business_calculator.calculate_break_even_point.return_value = 100.0

    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    main()

    captured = capsys.readouterr().out
    # Check global banners
    assert "BUSINESS ANALYTICS SYSTEM" in captured
    assert "Analysis Complete!" in captured
    # Check that each section header appears
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "--- Generating Reports ---" in captured
    assert "--- Business Calculations ---" in captured
    assert "--- Parallel Processing Demo ---" in captured


def test_main_propagates_error_from_inner_function(
    patched_data_processor,
    patched_report_generator,
    patched_business_calculator,
    patched_format_currency,
):
    """Test main propagates exceptions raised by one of the inner demonstration functions."""
    # Cause DataProcessor.sort_by_amount (used in demonstrate_sorting) to raise
    dp_instance = patched_data_processor.return_value
    dp_instance.sort_by_amount.side_effect = RuntimeError("sorting failure")

    with pytest.raises(RuntimeError) as excinfo:
        main()
    assert "sorting failure" in str(excinfo.value)