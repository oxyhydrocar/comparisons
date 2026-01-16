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
    """Fixture that returns the sample sales records from create_sample_data."""
    return create_sample_data()


@pytest.fixture
def mock_data_processor_class():
    """Fixture that patches DataProcessor class in main module."""
    with patch("main.DataProcessor") as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_report_generator_class():
    """Fixture that patches ReportGenerator class in main module."""
    with patch("main.ReportGenerator") as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_business_calculator_class():
    """Fixture that patches BusinessCalculator class in main module."""
    with patch("main.BusinessCalculator") as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_format_currency():
    """Fixture that patches format_currency function in main module."""
    with patch("main.format_currency") as mock_func:
        yield mock_func


def test_create_sample_data_structure(sample_sales_records):
    """Test that create_sample_data returns a list of 10 SalesRecord-like objects."""
    assert isinstance(sample_sales_records, list)
    assert len(sample_sales_records) == 10

    first = sample_sales_records[0]
    # We don't have SalesRecord class here, but we can check attributes by duck-typing
    assert hasattr(first, "id")
    assert hasattr(first, "product")
    assert hasattr(first, "amount")
    assert hasattr(first, "date")
    assert hasattr(first, "region")


@pytest.mark.parametrize(
    "index,expected_product,expected_amount,expected_region",
    [
        (0, "Laptop", 1200.00, "North"),
        (1, "Mouse", 25.00, "South"),
        (9, "Monitor", 400.00, "North"),
    ],
)
def test_create_sample_data_contents(
    index, expected_product, expected_amount, expected_region
):
    """Test that specific records in create_sample_data have expected values."""
    records = create_sample_data()
    record = records[index]
    assert record.product == expected_product
    assert record.region == expected_region
    assert record.amount == pytest.approx(expected_amount)


def test_demonstrate_sorting_happy_path(
    mock_data_processor_class, mock_format_currency, capsys
):
    """Test demonstrate_sorting prints sorted records using DataProcessor and format_currency."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance

    # Create fake records with product and amount attributes
    fake_records = []
    for i in range(5):
        rec = Mock()
        rec.product = f"Product{i}"
        rec.amount = 100 + i
        fake_records.append(rec)

    mock_processor_instance.sort_by_amount.return_value = fake_records
    mock_format_currency.side_effect = lambda x: f"${x:.2f}"

    demonstrate_sorting()

    # Ensure DataProcessor was instantiated with sample data
    assert mock_data_processor_class.call_count == 1
    mock_processor_instance.sort_by_amount.assert_called_once()

    # Check printed output
    captured = capsys.readouterr()
    out = captured.out

    assert "--- Demonstrating Record Sorting ---" in out
    assert "Records sorted by amount:" in out
    for i in range(5):
        assert f"Product{i}: ${100 + i:.2f}" in out


def test_demonstrate_sorting_processor_error(
    mock_data_processor_class, mock_format_currency, capsys
):
    """Test demonstrate_sorting handles exception from DataProcessor.sort_by_amount."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance
    mock_processor_instance.sort_by_amount.side_effect = RuntimeError("sort failed")

    # Even if an exception occurs, function does not handle it; test that it propagates
    with pytest.raises(RuntimeError):
        demonstrate_sorting()


def test_demonstrate_reports_happy_path(
    mock_data_processor_class, mock_report_generator_class, capsys
):
    """Test demonstrate_reports uses ReportGenerator to print three reports."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance

    mock_reporter_instance = Mock()
    mock_report_generator_class.return_value = mock_reporter_instance

    mock_reporter_instance.generate_summary_report.return_value = "SUMMARY"
    mock_reporter_instance.generate_top_products_report.return_value = "TOP PRODUCTS"
    mock_reporter_instance.generate_regional_report.return_value = "REGIONAL"

    demonstrate_reports()

    # Ensure DataProcessor and ReportGenerator were instantiated correctly
    mock_data_processor_class.assert_called_once()
    mock_report_generator_class.assert_called_once_with(mock_processor_instance)

    mock_reporter_instance.generate_summary_report.assert_called_once()
    mock_reporter_instance.generate_top_products_report.assert_called_once_with(3)
    mock_reporter_instance.generate_regional_report.assert_called_once()

    captured = capsys.readouterr()
    out = captured.out

    assert "--- Generating Reports ---" in out
    assert "SUMMARY" in out
    assert "TOP PRODUCTS" in out
    assert "REGIONAL" in out


def test_demonstrate_reports_report_generator_error(
    mock_data_processor_class, mock_report_generator_class
):
    """Test demonstrate_reports propagates exceptions from ReportGenerator methods."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance

    mock_reporter_instance = Mock()
    mock_report_generator_class.return_value = mock_reporter_instance

    mock_reporter_instance.generate_summary_report.side_effect = ValueError(
        "bad summary"
    )

    with pytest.raises(ValueError):
        demonstrate_reports()


def test_demonstrate_calculations_happy_path(
    mock_business_calculator_class, capsys
):
    """Test demonstrate_calculations prints calculated business metrics."""
    mock_business_calculator_class.calculate_profit_margin.return_value = 40.0
    mock_business_calculator_class.calculate_roi.return_value = 50.0
    mock_business_calculator_class.calculate_compound_growth_rate.return_value = 14.47
    mock_business_calculator_class.calculate_break_even_point.return_value = 250.0

    demonstrate_calculations()

    # Verify calls with correct arguments
    mock_business_calculator_class.calculate_profit_margin.assert_called_once_with(
        10000, 6000
    )
    mock_business_calculator_class.calculate_roi.assert_called_once_with(15000, 10000)
    mock_business_calculator_class.calculate_compound_growth_rate.assert_called_once_with(
        10000, 15000, 3
    )
    mock_business_calculator_class.calculate_break_even_point.assert_called_once_with(
        5000, 50, 30
    )

    captured = capsys.readouterr()
    out = captured.out

    assert "--- Business Calculations ---" in out
    assert "Profit Margin (Revenue: $10,000, Costs: $6,000): 40.00%" in out
    assert "ROI (Gain: $15,000, Cost: $10,000): 50.00%" in out
    assert (
        "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): 14.47%" in out
    )
    assert (
        "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): 250 units" in out
    )


@pytest.mark.parametrize(
    "method_name,exception",
    [
        ("calculate_profit_margin", ZeroDivisionError("division by zero")),
        ("calculate_roi", ValueError("invalid roi")),
        ("calculate_compound_growth_rate", OverflowError("overflow")),
        ("calculate_break_even_point", RuntimeError("calc error")),
    ],
)
def test_demonstrate_calculations_error_propagation(
    mock_business_calculator_class, method_name, exception
):
    """Test demonstrate_calculations propagates exceptions from BusinessCalculator."""
    getattr(mock_business_calculator_class, method_name).side_effect = exception

    with pytest.raises(type(exception)):
        demonstrate_calculations()


def test_demonstrate_parallel_processing_happy_path(
    mock_data_processor_class, mock_format_currency, capsys
):
    """Test demonstrate_parallel_processing filters and prints high value records."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance

    # Create fake high value records
    high_value_records = []
    for i in range(3):
        rec = Mock()
        rec.product = f"HV{i}"
        rec.amount = 200 + i * 50
        high_value_records.append(rec)

    mock_processor_instance.process_records_parallel.return_value = high_value_records
    mock_format_currency.side_effect = lambda x: f"${x:.2f}"

    demonstrate_parallel_processing()

    mock_data_processor_class.assert_called_once()
    mock_processor_instance.process_records_parallel.assert_called_once_with(100)

    captured = capsys.readouterr()
    out = captured.out

    assert "--- Parallel Processing Demo ---" in out
    assert "Found 3 records above $100:" in out
    for i, rec in enumerate(high_value_records):
        assert f"{rec.product}: ${rec.amount:.2f}" in out


def test_demonstrate_parallel_processing_processor_error(
    mock_data_processor_class, capsys
):
    """Test demonstrate_parallel_processing propagates exceptions from DataProcessor."""
    mock_processor_instance = Mock()
    mock_data_processor_class.return_value = mock_processor_instance
    mock_processor_instance.process_records_parallel.side_effect = RuntimeError(
        "parallel error"
    )

    with pytest.raises(RuntimeError):
        demonstrate_parallel_processing()


def test_main_happy_path(
    mocker,
    mock_data_processor_class,
    mock_report_generator_class,
    mock_business_calculator_class,
    mock_format_currency,
    capsys,
):
    """Test main orchestrates all demonstration functions and prints headers/footers."""
    # Patch demonstration functions to isolate main
    mock_sort = mocker.patch("main.demonstrate_sorting")
    mock_reports = mocker.patch("main.demonstrate_reports")
    mock_calcs = mocker.patch("main.demonstrate_calculations")
    mock_parallel = mocker.patch("main.demonstrate_parallel_processing")

    main()

    # Ensure each demonstration function is called once
    mock_sort.assert_called_once()
    mock_reports.assert_called_once()
    mock_calcs.assert_called_once()
    mock_parallel.assert_called_once()

    captured = capsys.readouterr()
    out = captured.out

    assert "BUSINESS ANALYTICS SYSTEM" in out
    assert "Analysis Complete!" in out


def test_main_demonstration_error_propagation(mocker):
    """Test main propagates exceptions from demonstration functions."""
    mock_sort = mocker.patch("main.demonstrate_sorting")
    mock_sort.side_effect = RuntimeError("demo error")

    with pytest.raises(RuntimeError):
        main()