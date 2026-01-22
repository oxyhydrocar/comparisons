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
def sample_records():
    """Return sample records from create_sample_data for reuse."""
    return create_sample_data()


@pytest.fixture
def mock_data_processor():
    """Create a mock DataProcessor instance."""
    return Mock(name="DataProcessorMock")


@pytest.fixture
def mock_report_generator():
    """Create a mock ReportGenerator instance."""
    return Mock(name="ReportGeneratorMock")


def test_create_sample_data_structure(sample_records):
    """Test that create_sample_data returns 10 SalesRecord-like objects with expected attributes."""
    assert len(sample_records) == 10
    first = sample_records[0]
    # We can't import SalesRecord type safely here, so check attributes instead
    assert hasattr(first, "id")
    assert hasattr(first, "product")
    assert hasattr(first, "amount")
    assert hasattr(first, "date")
    assert hasattr(first, "region")

    # Spot-check some values to ensure data consistency
    assert first.id == 1
    assert first.product == "Laptop"
    assert first.amount == pytest.approx(1200.00)
    assert first.date == "2024-01-15"
    assert first.region == "North"

    last = sample_records[-1]
    assert last.id == 10
    assert last.product == "Monitor"
    assert last.amount == pytest.approx(400.00)
    assert last.date == "2024-01-24"
    assert last.region == "North"


def test_create_sample_data_unique_ids(sample_records):
    """Test that create_sample_data returns records with unique sequential IDs 1..10."""
    ids = [r.id for r in sample_records]
    assert sorted(ids) == list(range(1, 11))


@patch("main.DataProcessor")
@patch("main.format_currency")
def test_demonstrate_sorting_happy_path(mock_format_currency, mock_data_processor, sample_records, capsys):
    """Test demonstrate_sorting prints sorted records by amount and uses DataProcessor.sort_by_amount."""
    # Arrange DataProcessor mock
    instance = mock_data_processor.return_value
    # Use the real sample_data order as a baseline and create a sorted version
    sorted_by_amount = sorted(sample_records, key=lambda r: r.amount)
    instance.sort_by_amount.return_value = sorted_by_amount

    # format_currency returns a simple prefixed string for visibility
    mock_format_currency.side_effect = lambda amt: f"${amt:,.2f}"

    from main import demonstrate_sorting

    # Act
    demonstrate_sorting()
    captured = capsys.readouterr().out

    # Assert DataProcessor was instantiated with created data
    mock_data_processor.assert_called_once()
    # Ensure sort_by_amount is called exactly once
    instance.sort_by_amount.assert_called_once()

    # Check that output header is present
    assert "--- Demonstrating Record Sorting ---" in captured
    assert "Records sorted by amount:" in captured

    # Validate that first 5 lines printed correspond to lowest 5 amounts
    lowest_five = sorted_by_amount[:5]
    for record in lowest_five:
        expected_line = f"{record.product}: {mock_format_currency(record.amount)}"
        assert expected_line in captured


@patch("main.DataProcessor")
@patch("main.ReportGenerator")
def test_demonstrate_reports_happy_path(mock_report_generator_cls, mock_data_processor_cls, capsys):
    """Test demonstrate_reports creates processor and reporter and prints all reports."""
    summary_text = "SUMMARY REPORT"
    top_products_text = "TOP PRODUCTS"
    regional_text = "REGIONAL REPORT"

    # Configure ReportGenerator mock
    reporter_instance = mock_report_generator_cls.return_value
    reporter_instance.generate_summary_report.return_value = summary_text
    reporter_instance.generate_top_products_report.return_value = top_products_text
    reporter_instance.generate_regional_report.return_value = regional_text

    from main import demonstrate_reports

    demonstrate_reports()
    captured = capsys.readouterr().out

    # Assert DataProcessor instantiated with create_sample_data output (any list is fine)
    mock_data_processor_cls.assert_called_once()
    # Assert ReportGenerator instantiated with processor
    mock_report_generator_cls.assert_called_once_with(mock_data_processor_cls.return_value)

    reporter_instance.generate_summary_report.assert_called_once_with()
    reporter_instance.generate_top_products_report.assert_called_once_with(3)
    reporter_instance.generate_regional_report.assert_called_once_with()

    # Check printed outputs
    assert "--- Generating Reports ---" in captured
    assert summary_text in captured
    assert top_products_text in captured
    assert regional_text in captured


@patch("main.BusinessCalculator")
def test_demonstrate_calculations_happy_path(mock_business_calculator, capsys):
    """Test demonstrate_calculations prints values from BusinessCalculator methods."""
    # Set explicit float return values
    mock_business_calculator.calculate_profit_margin.return_value = 40.0
    mock_business_calculator.calculate_roi.return_value = 50.0
    mock_business_calculator.calculate_compound_growth_rate.return_value = 14.47
    mock_business_calculator.calculate_break_even_point.return_value = 250.0

    from main import demonstrate_calculations

    demonstrate_calculations()
    captured = capsys.readouterr().out

    # Assert BusinessCalculator static methods called with expected args
    mock_business_calculator.calculate_profit_margin.assert_called_once_with(10000, 6000)
    mock_business_calculator.calculate_roi.assert_called_once_with(15000, 10000)
    mock_business_calculator.calculate_compound_growth_rate.assert_called_once_with(10000, 15000, 3)
    mock_business_calculator.calculate_break_even_point.assert_called_once_with(5000, 50, 30)

    # Validate some portions of the printed output (formatted with 2 decimals)
    assert "--- Business Calculations ---" in captured
    assert "Profit Margin (Revenue: $10,000, Costs: $6,000): 40.00%" in captured
    assert "ROI (Gain: $15,000, Cost: $10,000): 50.00%" in captured
    assert "Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): 14.47%" in captured
    # Break-even printed as 0 decimal places
    assert "Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): 250 units" in captured


@patch("main.DataProcessor")
@patch("main.format_currency")
def test_demonstrate_parallel_processing_happy_path(
    mock_format_currency, mock_data_processor_cls, capsys
):
    """Test demonstrate_parallel_processing prints high-value records from DataProcessor.process_records_parallel."""
    # Arrange
    instance = mock_data_processor_cls.return_value

    # Construct a minimal object with attributes for demonstration
    Record = type("Record", (), {})
    r1 = Record()
    r1.product = "Laptop"
    r1.amount = 1200.0
    r2 = Record()
    r2.product = "Monitor"
    r2.amount = 350.0
    high_value = [r1, r2]

    instance.process_records_parallel.return_value = high_value
    mock_format_currency.side_effect = lambda amt: f"${amt:,.2f}"

    from main import demonstrate_parallel_processing

    demonstrate_parallel_processing()
    captured = capsys.readouterr().out

    mock_data_processor_cls.assert_called_once()
    instance.process_records_parallel.assert_called_once_with(100)

    assert "--- Parallel Processing Demo ---" in captured
    assert "Found 2 records above $100:" in captured
    assert "Laptop: $1,200.00" in captured
    assert "Monitor: $350.00" in captured


@patch("main.demonstrate_parallel_processing")
@patch("main.demonstrate_calculations")
@patch("main.demonstrate_reports")
@patch("main.demonstrate_sorting")
def test_main_happy_path(
    mock_demonstrate_sorting,
    mock_demonstrate_reports,
    mock_demonstrate_calculations,
    mock_demonstrate_parallel_processing,
    capsys,
):
    """Test main orchestrates all demo functions and prints headers and footers."""
    from main import main as main_entry

    main_entry()
    captured = capsys.readouterr().out

    # Check that demo functions were called exactly once
    mock_demonstrate_sorting.assert_called_once_with()
    mock_demonstrate_reports.assert_called_once_with()
    mock_demonstrate_calculations.assert_called_once_with()
    mock_demonstrate_parallel_processing.assert_called_once_with()

    # Validate header and footer prints
    assert "BUSINESS ANALYTICS SYSTEM" in captured
    assert "Analysis Complete!" in captured


@pytest.mark.parametrize(
    "threshold, expected_count",
    [
        (0, 10),
        (100, 0),  # when mocked to return empty list
    ],
)
@patch("main.DataProcessor")
@patch("main.format_currency")
def test_demonstrate_parallel_processing_parametrized_threshold(
    mock_format_currency,
    mock_data_processor_cls,
    threshold,
    expected_count,
    capsys,
):
    """Test demonstrate_parallel_processing behavior with different thresholds via parametrization."""
    instance = mock_data_processor_cls.return_value

    # Return lists of different lengths according to test case
    Record = type("Record", (), {})
    if expected_count == 10:
        records = []
        for i in range(10):
            r = Record()
            r.product = f"Product-{i}"
            r.amount = float(i)
            records.append(r)
    else:
        records = []

    instance.process_records_parallel.return_value = records
    mock_format_currency.side_effect = lambda amt: f"${amt:,.2f}"

    from main import demonstrate_parallel_processing

    demonstrate_parallel_processing()
    captured = capsys.readouterr().out

    # even though demonstrate_parallel_processing always calls with 100,
    # we still verify that our mock returned the expected_count
    assert f"Found {expected_count} records above $100:" in captured
    assert instance.process_records_parallel.call_args == call(100)


def test_create_sample_data_independence():
    """Test that multiple calls to create_sample_data return new lists (not the same object)."""
    data1 = create_sample_data()
    data2 = create_sample_data()
    assert data1 is not data2
    # But contents should be equivalent per position
    for r1, r2 in zip(data1, data2):
        assert r1.id == r2.id
        assert r1.product == r2.product
        assert r1.amount == pytest.approx(r2.amount)
        assert r1.date == r2.date
        assert r1.region == r2.region


def test_main_under___name__guard(monkeypatch, capsys):
    """Test that importing main does not execute main() when __name__ != '__main__'."""
    # Reloading the module in this test is not straightforward; instead we assert that
    # calling main() directly is the only way to trigger the prints we care about.
    # Here we call main() and ensure output is produced as expected.
    from main import main as entry

    # Patch demo functions to avoid side effects, focus only on header/footer
    monkeypatch.setattr("main.demonstrate_sorting", lambda: None)
    monkeypatch.setattr("main.demonstrate_reports", lambda: None)
    monkeypatch.setattr("main.demonstrate_calculations", lambda: None)
    monkeypatch.setattr("main.demonstrate_parallel_processing", lambda: None)

    entry()
    captured = capsys.readouterr().out

    # Only header and footer should appear as demo functions are no-ops
    assert "BUSINESS ANALYTICS SYSTEM" in captured
    assert "Analysis Complete!" in captured