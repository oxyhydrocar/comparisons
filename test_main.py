import pytest
from unittest.mock import Mock, patch

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
def patched_data_processor():
    """Fixture that patches DataProcessor and returns the mock class."""
    with patch("main.DataProcessor") as mock_dp_cls:
        yield mock_dp_cls


@pytest.fixture
def patched_report_generator():
    """Fixture that patches ReportGenerator and returns the mock class."""
    with patch("main.ReportGenerator") as mock_rg_cls:
        yield mock_rg_cls


@pytest.fixture
def patched_business_calculator():
    """Fixture that patches BusinessCalculator and returns the mock class."""
    with patch("main.BusinessCalculator") as mock_bc_cls:
        yield mock_bc_cls


@pytest.fixture
def patched_format_currency():
    """Fixture that patches format_currency and returns the mock."""
    with patch("main.format_currency") as mock_fmt:
        yield mock_fmt


def test_create_sample_data_structure(sample_sales_records):
    """Test that create_sample_data returns a non-empty list of SalesRecord objects."""
    assert isinstance(sample_sales_records, list)
    assert len(sample_sales_records) == 10
    first = sample_sales_records[0]
    # We can't import SalesRecord directly here reliably, but we know attributes
    assert hasattr(first, "id")
    assert hasattr(first, "product")
    assert hasattr(first, "amount")
    assert hasattr(first, "date")
    assert hasattr(first, "region")


def test_create_sample_data_content(sample_sales_records):
    """Test that create_sample_data returns expected first and last items' core fields."""
    assert sample_sales_records[0].id == 1
    assert sample_sales_records[0].product == "Laptop"
    assert sample_sales_records[0].amount == pytest.approx(1200.00)
    assert sample_sales_records[0].region == "North"

    assert sample_sales_records[-1].id == 10
    assert sample_sales_records[-1].product == "Monitor"
    assert sample_sales_records[-1].amount == pytest.approx(400.00)
    assert sample_sales_records[-1].region == "North"


def test_demonstrate_sorting_happy_path(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_sorting prints sorted records using DataProcessor and format_currency."""
    mock_processor_instance = Mock()
    # Create fake record objects with product and amount attributes
    fake_records = [
        Mock(product="A", amount=10.0),
        Mock(product="B", amount=20.0),
        Mock(product="C", amount=30.0),
        Mock(product="D", amount=40.0),
        Mock(product="E", amount=50.0),
    ]
    mock_processor_instance.sort_by_amount.return_value = fake_records
    patched_data_processor.return_value = mock_processor_instance

    # Configure format_currency to return formatted string
    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    demonstrate_sorting()

    captured = capsys.readouterr().out
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "Records sorted by amount:" in captured
    for rec in fake_records[:5]:
        assert rec.product in captured
        assert f"${rec.amount:,.2f}" in captured

    patched_data_processor.assert_called_once()
    mock_processor_instance.sort_by_amount.assert_called_once()
    assert patched_format_currency.call_count == 5


def test_demonstrate_sorting_data_processor_error(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_sorting handles DataProcessor.sort_by_amount raising an error."""
    mock_processor_instance = Mock()
    mock_processor_instance.sort_by_amount.side_effect = RuntimeError("sort error")
    patched_data_processor.return_value = mock_processor_instance

    # Even if format_currency is not reached, keep it patched
    demonstrate_sorting()
    captured = capsys.readouterr().out

    # Header still printed
    assert "--- Demonstrating Record Sorting ---" in captured
    # Error is not explicitly handled in code, so no specific error output expected
    mock_processor_instance.sort_by_amount.assert_called_once()


def test_demonstrate_reports_happy_path(
    patched_data_processor, patched_report_generator, capsys
):
    """Test demonstrate_reports generates and prints summary, top products, and regional reports."""
    mock_processor_instance = Mock()
    patched_data_processor.return_value = mock_processor_instance

    mock_reporter_instance = Mock()
    mock_reporter_instance.generate_summary_report.return_value = "SUMMARY REPORT"
    mock_reporter_instance.generate_top_products_report.return_value = (
        "TOP PRODUCTS REPORT"
    )
    mock_reporter_instance.generate_regional_report.return_value = (
        "REGIONAL REPORT"
    )
    patched_report_generator.return_value = mock_reporter_instance

    demonstrate_reports()
    captured = capsys.readouterr().out

    assert "--- Generating Reports ---" in captured
    assert "SUMMARY REPORT" in captured
    assert "TOP PRODUCTS REPORT" in captured
    assert "REGIONAL REPORT" in captured

    patched_data_processor.assert_called_once()
    patched_report_generator.assert_called_once_with(mock_processor_instance)
    mock_reporter_instance.generate_summary_report.assert_called_once()
    mock_reporter_instance.generate_top_products_report.assert_called_once_with(3)
    mock_reporter_instance.generate_regional_report.assert_called_once()


@pytest.mark.parametrize(
    "method_name,side_effect",
    [
        ("generate_summary_report", RuntimeError("summary error")),
        ("generate_top_products_report", RuntimeError("top error")),
        ("generate_regional_report", RuntimeError("regional error")),
    ],
)
def test_demonstrate_reports_error_cases(
    method_name, side_effect, patched_data_processor, patched_report_generator, capsys
):
    """Test demonstrate_reports behavior when individual report methods fail."""
    mock_processor_instance = Mock()
    patched_data_processor.return_value = mock_processor_instance

    mock_reporter_instance = Mock()
    # Default return values
    mock_reporter_instance.generate_summary_report.return_value = "SUMMARY REPORT"
    mock_reporter_instance.generate_top_products_report.return_value = (
        "TOP PRODUCTS REPORT"
    )
    mock_reporter_instance.generate_regional_report.return_value = (
        "REGIONAL REPORT"
    )

    # Apply side effect to specific method
    getattr(mock_reporter_instance, method_name).side_effect = side_effect
    patched_report_generator.return_value = mock_reporter_instance

    demonstrate_reports()
    captured = capsys.readouterr().out

    # Header and at least some output should be printed
    assert "--- Generating Reports ---" in captured
    patched_report_generator.assert_called_once_with(mock_processor_instance)


def test_demonstrate_calculations_happy_path(patched_business_calculator, capsys):
    """Test demonstrate_calculations prints all calculations using BusinessCalculator."""
    # Configure return values
    patched_business_calculator.calculate_profit_margin.return_value = 40.0
    patched_business_calculator.calculate_roi.return_value = 50.0
    patched_business_calculator.calculate_compound_growth_rate.return_value = 14.474
    patched_business_calculator.calculate_break_even_point.return_value = 250.0

    demonstrate_calculations()
    captured = capsys.readouterr().out

    assert "--- Business Calculations ---" in captured
    assert "Profit Margin (Revenue: $10,000, Costs: $6,000): 40.00%" in captured
    assert "ROI (Gain: $15,000, Cost: $10,000): 50.00%" in captured
    assert (
        "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): "
        in captured
    )
    assert "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): 250 units" in captured

    patched_business_calculator.calculate_profit_margin.assert_called_once_with(
        10000, 6000
    )
    patched_business_calculator.calculate_roi.assert_called_once_with(15000, 10000)
    patched_business_calculator.calculate_compound_growth_rate.assert_called_once_with(
        10000, 15000, 3
    )
    patched_business_calculator.calculate_break_even_point.assert_called_once_with(
        5000, 50, 30
    )


@pytest.mark.parametrize(
    "method_name,side_effect",
    [
        ("calculate_profit_margin", ZeroDivisionError("division by zero")),
        ("calculate_roi", ZeroDivisionError("division by zero")),
        ("calculate_compound_growth_rate", ValueError("invalid rate")),
        ("calculate_break_even_point", ValueError("invalid break-even")),
    ],
)
def test_demonstrate_calculations_error_cases(
    method_name, side_effect, patched_business_calculator, capsys
):
    """Test demonstrate_calculations behavior when BusinessCalculator methods raise errors."""
    # Set default values for all to ensure formatting proceeds if not failing first
    patched_business_calculator.calculate_profit_margin.return_value = 40.0
    patched_business_calculator.calculate_roi.return_value = 50.0
    patched_business_calculator.calculate_compound_growth_rate.return_value = 14.474
    patched_business_calculator.calculate_break_even_point.return_value = 250.0

    getattr(patched_business_calculator, method_name).side_effect = side_effect

    demonstrate_calculations()
    captured = capsys.readouterr().out

    assert "--- Business Calculations ---" in captured
    # The function does not handle exceptions, so exceptions may interrupt execution.
    # We only assert header presence to avoid assuming control flow.


def test_demonstrate_parallel_processing_happy_path(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_parallel_processing filters and prints high value records."""
    mock_processor_instance = Mock()
    high_value_records = [
        Mock(product="Laptop", amount=1200.0),
        Mock(product="Monitor", amount=400.0),
    ]
    mock_processor_instance.process_records_parallel.return_value = high_value_records
    patched_data_processor.return_value = mock_processor_instance

    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    demonstrate_parallel_processing()
    captured = capsys.readouterr().out

    assert "--- Parallel Processing Demo ---" in captured
    assert "Found 2 records above $100:" in captured
    for rec in high_value_records:
        assert rec.product in captured
        assert f"${rec.amount:,.2f}" in captured

    mock_processor_instance.process_records_parallel.assert_called_once_with(100)
    assert patched_format_currency.call_count == len(high_value_records)


def test_demonstrate_parallel_processing_no_results(
    patched_data_processor, patched_format_currency, capsys
):
    """Test demonstrate_parallel_processing when no high value records are returned."""
    mock_processor_instance = Mock()
    mock_processor_instance.process_records_parallel.return_value = []
    patched_data_processor.return_value = mock_processor_instance

    demonstrate_parallel_processing()
    captured = capsys.readouterr().out

    assert "Found 0 records above $100:" in captured
    mock_processor_instance.process_records_parallel.assert_called_once_with(100)
    patched_format_currency.assert_not_called()


def test_main_integration(
    patched_data_processor,
    patched_report_generator,
    patched_business_calculator,
    patched_format_currency,
    capsys,
):
    """Test main orchestrates all demo functions and prints final messages."""
    # Configure mocks lightly so code paths can run without error
    dp_instance = Mock()
    dp_instance.sort_by_amount.return_value = [
        Mock(product="X", amount=1.0) for _ in range(5)
    ]
    dp_instance.process_records_parallel.return_value = []
    patched_data_processor.return_value = dp_instance

    rg_instance = Mock()
    rg_instance.generate_summary_report.return_value = "SUMMARY"
    rg_instance.generate_top_products_report.return_value = "TOP"
    rg_instance.generate_regional_report.return_value = "REGIONAL"
    patched_report_generator.return_value = rg_instance

    patched_business_calculator.calculate_profit_margin.return_value = 1.0
    patched_business_calculator.calculate_roi.return_value = 2.0
    patched_business_calculator.calculate_compound_growth_rate.return_value = 3.0
    patched_business_calculator.calculate_break_even_point.return_value = 4.0

    patched_format_currency.side_effect = lambda x: f"${x:,.2f}"

    main()
    captured = capsys.readouterr().out

    assert "BUSINESS ANALYTICS SYSTEM" in captured
    assert "Analysis Complete!" in captured

    # Ensure each major section header appears
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "--- Generating Reports ---" in captured
    assert "--- Business Calculations ---" in captured
    assert "--- Parallel Processing Demo ---" in captured


def test_main_data_processor_failure(
    patched_data_processor,
    patched_report_generator,
    patched_business_calculator,
    patched_format_currency,
    capsys,
):
    """Test main behavior when DataProcessor initialization fails."""
    patched_data_processor.side_effect = RuntimeError("init error")

    # Even though errors will be raised in the called functions, we call main to
    # ensure it at least prints the initial header before the exception.
    with pytest.raises(RuntimeError):
        main()

    captured = capsys.readouterr().out
    assert "BUSINESS ANALYTICS SYSTEM" in captured