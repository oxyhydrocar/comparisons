import pytest
from unittest.mock import patch, MagicMock
from main import (
    create_sample_data,
    demonstrate_sorting,
    demonstrate_reports,
    demonstrate_calculations,
    demonstrate_parallel_processing,
    main,
)


@pytest.fixture
def simple_records():
    """Provide a simple set of record-like objects with product and amount attributes."""
    class SimpleRecord:
        def __init__(self, product, amount):
            self.product = product
            self.amount = amount

    return [
        SimpleRecord("A", 10.0),
        SimpleRecord("B", 200.0),
        SimpleRecord("C", 150.0),
        SimpleRecord("D", 300.0),
        SimpleRecord("E", 50.0),
        SimpleRecord("F", 400.0),
    ]


@pytest.fixture
def patched_create_sample_data():
    """Patch main.create_sample_data to return a small deterministic dataset."""
    with patch("main.create_sample_data") as mock_create:
        mock_create.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        yield mock_create


def test_create_sample_data_structure_and_calls():
    """Test create_sample_data returns 10 records and SalesRecord called with expected arguments."""
    with patch("main.SalesRecord") as mock_sales_record:
        def mk_record(*args, **kwargs):
            # Represent each SalesRecord call as a dict capturing args for testing
            return {"args": args, "kwargs": kwargs}

        mock_sales_record.side_effect = mk_record
        records = create_sample_data()

        assert isinstance(records, list)
        assert len(records) == 10
        assert mock_sales_record.call_count == 10

        # Validate a few known entries by index
        first = records[0]["args"]
        second = records[1]["args"]
        last = records[-1]["args"]

        assert first[0] == 1
        assert first[1] == "Laptop"
        assert first[2] == pytest.approx(1200.00)
        assert first[3] == "2024-01-15"
        assert first[4] == "North"

        assert second[0] == 2
        assert second[1] == "Mouse"
        assert second[2] == pytest.approx(25.00)
        assert second[3] == "2024-01-16"
        assert second[4] == "South"

        assert last[0] == 10
        assert last[1] == "Monitor"
        assert last[2] == pytest.approx(400.00)
        assert last[3] == "2024-01-24"
        assert last[4] == "North"


def test_demonstrate_sorting_prints_top_five(simple_records, capsys):
    """Test demonstrate_sorting prints records sorted by amount and uses only top 5."""
    # Prepare sorted records for the processor to return
    sorted_records = sorted(simple_records, key=lambda r: r.amount)

    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls, \
         patch("main.format_currency") as mock_currency:

        mock_create.return_value = ["placeholder"]  # ensure DataProcessor called with our list
        mock_currency.side_effect = lambda amount: f"${amount:,.2f}"

        mock_processor = MagicMock()
        mock_processor.sort_by_amount.return_value = sorted_records
        mock_proc_cls.return_value = mock_processor

        demonstrate_sorting()
        out = capsys.readouterr().out

        # Verify banner
        assert "--- Demonstrating Record Sorting ---" in out
        assert "Records sorted by amount:" in out

        # Verify top five lines are present and formatted
        expected_lines = [
            f"  {sorted_records[i].product}: ${sorted_records[i].amount:,.2f}"
            for i in range(5)
        ]
        for line in expected_lines:
            assert line in out

        # Ensure the 6th item is not printed
        not_expected_line = f"  {sorted_records[5].product}: ${sorted_records[5].amount:,.2f}"
        assert not_expected_line not in out

        # Ensure DataProcessor constructed with create_sample_data return
        mock_proc_cls.assert_called_once_with(mock_create.return_value)
        mock_processor.sort_by_amount.assert_called_once()


def test_demonstrate_sorting_raises_on_processor_error(capsys):
    """Test demonstrate_sorting propagates exceptions from DataProcessor.sort_by_amount."""
    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls:
        mock_create.return_value = ["data"]
        mock_processor = MagicMock()
        mock_processor.sort_by_amount.side_effect = RuntimeError("sort error")
        mock_proc_cls.return_value = mock_processor

        with pytest.raises(RuntimeError):
            demonstrate_sorting()


def test_demonstrate_reports_prints_all_reports(capsys):
    """Test demonstrate_reports prints summary, top products, and regional reports."""
    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls, \
         patch("main.ReportGenerator") as mock_report_gen_cls:

        data = [{"id": 1}]
        mock_create.return_value = data

        mock_processor = MagicMock()
        mock_proc_cls.return_value = mock_processor

        mock_reporter = MagicMock()
        mock_reporter.generate_summary_report.return_value = "SUMMARY REPORT"
        mock_reporter.generate_top_products_report.return_value = "TOP PRODUCTS REPORT"
        mock_reporter.generate_regional_report.return_value = "REGIONAL REPORT"
        mock_report_gen_cls.return_value = mock_reporter

        demonstrate_reports()
        out = capsys.readouterr().out

        assert "--- Generating Reports ---" in out
        assert "SUMMARY REPORT" in out
        assert "TOP PRODUCTS REPORT" in out
        assert "REGIONAL REPORT" in out

        mock_proc_cls.assert_called_once_with(data)
        mock_report_gen_cls.assert_called_once_with(mock_processor)
        mock_reporter.generate_summary_report.assert_called_once()
        mock_reporter.generate_top_products_report.assert_called_once_with(3)
        mock_reporter.generate_regional_report.assert_called_once()


def test_demonstrate_reports_raises_on_report_error():
    """Test demonstrate_reports propagates errors from reporter generation methods."""
    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls, \
         patch("main.ReportGenerator") as mock_report_gen_cls:

        mock_create.return_value = [{"id": 1}]
        mock_proc_cls.return_value = MagicMock()

        mock_reporter = MagicMock()
        mock_reporter.generate_summary_report.side_effect = ValueError("report error")
        mock_report_gen_cls.return_value = mock_reporter

        with pytest.raises(ValueError):
            demonstrate_reports()


@pytest.mark.parametrize(
    "pm,roi,cgr,be",
    [
        (40.0, 50.0, 14.473, 250.0),
        (33.3333, 20.0, 7.5, 1000.49),
    ],
)
def test_demonstrate_calculations_prints_formatted(pm, roi, cgr, be, capsys):
    """Test demonstrate_calculations prints correctly formatted calculator results."""
    with patch("main.BusinessCalculator") as mock_calc:
        mock_calc.calculate_profit_margin.return_value = pm
        mock_calc.calculate_roi.return_value = roi
        mock_calc.calculate_compound_growth_rate.return_value = cgr
        mock_calc.calculate_break_even_point.return_value = be

        demonstrate_calculations()
        out = capsys.readouterr().out

        assert "--- Business Calculations ---" in out

        assert f"Profit Margin (Revenue: $10,000, Costs: $6,000): {pm:.2f}%" in out
        assert f"ROI (Gain: $15,000, Cost: $10,000): {roi:.2f}%" in out
        assert f"Compound Growth Rate (Start: $10,000, End: $15,000, 3 periods): {cgr:.2f}%" in out
        assert f"Break-even Point (Fixed: $5,000, Price: $50, Variable: $30): {be:.0f} units" in out

        mock_calc.calculate_profit_margin.assert_called_once_with(10000, 6000)
        mock_calc.calculate_roi.assert_called_once_with(15000, 10000)
        mock_calc.calculate_compound_growth_rate.assert_called_once_with(10000, 15000, 3)
        mock_calc.calculate_break_even_point.assert_called_once_with(5000, 50, 30)


def test_demonstrate_calculations_raises_on_error():
    """Test demonstrate_calculations propagates exceptions from BusinessCalculator."""
    with patch("main.BusinessCalculator") as mock_calc:
        mock_calc.calculate_profit_margin.side_effect = ZeroDivisionError("division by zero")

        with pytest.raises(ZeroDivisionError):
            demonstrate_calculations()


def test_demonstrate_parallel_processing_prints_records(capsys):
    """Test demonstrate_parallel_processing prints count and records above threshold."""
    class Rec:
        def __init__(self, product, amount):
            self.product = product
            self.amount = amount

    returned_records = [Rec("X", 150.0), Rec("Y", 200.0), Rec("Z", 1000.0)]

    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls, \
         patch("main.format_currency") as mock_currency:

        data = [{"id": "a"}]
        mock_create.return_value = data

        mock_processor = MagicMock()
        mock_processor.process_records_parallel.return_value = returned_records
        mock_proc_cls.return_value = mock_processor

        mock_currency.side_effect = lambda amt: f"${amt:,.2f}"

        demonstrate_parallel_processing()
        out = capsys.readouterr().out

        assert "--- Parallel Processing Demo ---" in out
        assert f"Found {len(returned_records)} records above $100:" in out
        for rec in returned_records:
            assert f"  {rec.product}: ${rec.amount:,.2f}" in out

        mock_proc_cls.assert_called_once_with(data)
        mock_processor.process_records_parallel.assert_called_once_with(100)


def test_demonstrate_parallel_processing_raises_on_error():
    """Test demonstrate_parallel_processing propagates exceptions from process_records_parallel."""
    with patch("main.create_sample_data") as mock_create, \
         patch("main.DataProcessor") as mock_proc_cls:
        mock_create.return_value = ["data"]
        mock_processor = MagicMock()
        mock_processor.process_records_parallel.side_effect = RuntimeError("parallel error")
        mock_proc_cls.return_value = mock_processor

        with pytest.raises(RuntimeError):
            demonstrate_parallel_processing()


def test_main_calls_all_sections_in_order(capsys):
    """Test main prints banners and calls all demonstration functions."""
    with patch("main.demonstrate_sorting") as mock_sorting, \
         patch("main.demonstrate_reports") as mock_reports, \
         patch("main.demonstrate_calculations") as mock_calcs, \
         patch("main.demonstrate_parallel_processing") as mock_parallel:

        main()
        out = capsys.readouterr().out

        # Check banners and footers
        assert "BUSINESS ANALYTICS SYSTEM" in out
        assert "Analysis Complete!" in out

        mock_sorting.assert_called_once()
        mock_reports.assert_called_once()
        mock_calcs.assert_called_once()
        mock_parallel.assert_called_once()


def test_main_propagates_exception_from_subroutine(capsys):
    """Test main propagates exceptions raised by any demonstration function."""
    with patch("main.demonstrate_sorting") as mock_sorting, \
         patch("main.demonstrate_reports") as mock_reports, \
         patch("main.demonstrate_calculations") as mock_calcs, \
         patch("main.demonstrate_parallel_processing") as mock_parallel:

        mock_sorting.side_effect = RuntimeError("fail")

        with pytest.raises(RuntimeError):
            main()

        out = capsys.readouterr().out
        # Header should still be printed before the failure
        assert "BUSINESS ANALYTICS SYSTEM" in out
        assert "Analysis Complete!" not in out