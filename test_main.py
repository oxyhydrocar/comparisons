import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from main import (
    Sale,
    create_sample_data,
    demonstrate_sorting,
    demonstrate_reports,
    demonstrate_calculations,
    demonstrate_parallel_processing,
    main,
)


@pytest.fixture
def small_sales():
    """Provide a small, deterministic set of sales for sorting and reporting tests."""
    return [
        Sale(1, "North", "Gadget", 1, 100.0, date(2024, 1, 2)),     # rev 100
        Sale(2, "East", "Widget", 5, 10.0, date(2024, 1, 1)),       # rev 50
        Sale(3, "South", "Widget", 3, 20.0, date(2024, 1, 3)),      # rev 60
        Sale(4, "North", "Doohickey", 2, 25.0, date(2024, 1, 1)),   # rev 50
        Sale(5, "East", "Widget", 7, 10.0, date(2024, 1, 5)),       # rev 70
        Sale(6, "West", "Gadget", 2, 60.0, date(2024, 1, 4)),       # rev 120
    ]


@pytest.fixture
def stats_sales():
    """Provide a simple dataset for calculation tests."""
    return [
        Sale(1, "North", "Widget", 1, 10.0, date(2024, 1, 1)),  # rev 10
        Sale(2, "North", "Widget", 2, 10.0, date(2024, 1, 2)),  # rev 20
        Sale(3, "South", "Widget", 3, 10.0, date(2024, 1, 3)),  # rev 30
    ]


@pytest.fixture
def dummy_executors(monkeypatch):
    """Monkeypatch ProcessPoolExecutor and ThreadPoolExecutor to run tasks synchronously, and skip sleep."""

    class DummyExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def map(self, fn, iterable):
            for item in iterable:
                yield fn(item)

    monkeypatch.setattr("main.cf.ProcessPoolExecutor", DummyExecutor)
    monkeypatch.setattr("main.cf.ThreadPoolExecutor", DummyExecutor)
    monkeypatch.setattr("main.time.sleep", lambda *_args, **_kwargs: None)


@pytest.mark.parametrize("n", [0, 1, 5])
def test_create_sample_data_sizes(n):
    """Test create_sample_data returns the correct number of items for various sizes."""
    data = create_sample_data(n=n, seed=123)
    assert len(data) == n


def test_create_sample_data_reproducible():
    """Test create_sample_data is reproducible with a fixed seed."""
    data1 = create_sample_data(n=10, seed=123)
    data2 = create_sample_data(n=10, seed=123)
    assert data1 == data2


def test_sale_revenue_property():
    """Test Sale.revenue property computes units * unit_price correctly."""
    s = Sale(1, "North", "Widget", 3, 10.0, date(2024, 1, 1))
    assert s.revenue == 30.0


def test_demonstrate_sorting_with_empty():
    """Test demonstrate_sorting handles an empty iterable."""
    result = demonstrate_sorting([])
    assert result["by_revenue_desc"] == []
    assert result["by_region_date"] == []
    assert result["by_product_units_desc"] == []


def test_demonstrate_sorting_expected_order(small_sales, capsys):
    """Test demonstrate_sorting returns correctly ordered lists."""
    result = demonstrate_sorting(small_sales)

    by_revenue_ids = [s.id for s in result["by_revenue_desc"]]
    assert by_revenue_ids == [6, 1, 5, 3, 2, 4]

    by_region_date_ids = [s.id for s in result["by_region_date"]]
    assert by_region_date_ids == [2, 5, 4, 1, 3, 6]

    by_product_units_desc_ids = [s.id for s in result["by_product_units_desc"]]
    assert by_product_units_desc_ids == [4, 6, 1, 5, 2, 3]

    # Ensure prints do not cause errors and include expected headers
    captured = capsys.readouterr().out
    assert "Top 5 by revenue desc:" in captured
    assert "First 5 by (region, date):" in captured
    assert "First 5 by product asc, units desc:" in captured


def test_demonstrate_reports_correct_totals(small_sales, capsys):
    """Test demonstrate_reports aggregates revenue by region and product correctly."""
    result = demonstrate_reports(small_sales)
    rev_by_region = result["revenue_by_region"]
    rev_by_product = result["revenue_by_product"]

    assert rev_by_region == {
        "North": 150.0,
        "East": 120.0,
        "South": 60.0,
        "West": 120.0,
    }
    assert rev_by_product == {
        "Gadget": 220.0,
        "Widget": 180.0,
        "Doohickey": 50.0,
    }

    captured = capsys.readouterr().out
    assert "Revenue by region:" in captured
    assert "Revenue by product (top 3):" in captured


def test_demonstrate_calculations_basic_stats(stats_sales, capsys):
    """Test demonstrate_calculations returns correct statistics."""
    result = demonstrate_calculations(stats_sales)
    assert result["revenue_sum"] == 60.0
    assert result["revenue_mean"] == 20.0
    assert result["revenue_median"] == 20.0
    # population stdev of [10,20,30] is sqrt(200/3)
    assert result["revenue_stdev"] == pytest.approx((200 / 3) ** 0.5, rel=1e-12)
    assert result["unit_price_mean"] == 10.0
    assert result["units_mean"] == 2.0
    assert result["units_median"] == 2

    captured = capsys.readouterr().out
    assert "Calculations:" in captured
    assert "revenue_sum" in captured


def test_demonstrate_parallel_processing_aggregates_by_region_with_dummy_executors(dummy_executors):
    """Test parallel processing aggregates revenue by region using dummy executors."""
    sales = [
        Sale(1, "North", "W", 1, 10.0, date(2024, 1, 1)),  # rev 10
        Sale(2, "North", "W", 1, 20.0, date(2024, 1, 2)),  # rev 20
        Sale(3, "South", "W", 1, 15.0, date(2024, 1, 3)),  # rev 15
    ]
    result = demonstrate_parallel_processing(sales, workers=2)
    assert result == {"North": 30.0, "South": 15.0}


def test_demonstrate_parallel_processing_raises_with_zero_workers():
    """Test demonstrate_parallel_processing raises ValueError with zero workers (real executor)."""
    sales = [
        Sale(1, "North", "W", 1, 10.0, date(2024, 1, 1)),
    ]
    with pytest.raises(ValueError):
        demonstrate_parallel_processing(sales, workers=0)


def test_main_runs_sorting_only(capsys):
    """Test main runs only the sorting demo when specified."""
    main(["--size", "5", "--seed", "1", "--demo", "sorting"])
    out = capsys.readouterr().out
    assert "Top 5 by revenue desc:" in out


def test_main_all_demo_calls_parallel_with_workers(monkeypatch):
    """Test main('all') calls demonstrate_parallel_processing with provided workers."""
    called = {"ok": False}

    def fake_parallel(sales, workers):
        called["ok"] = True
        called["workers"] = workers
        return {"North": 1.0}

    with patch("main.demonstrate_parallel_processing", side_effect=fake_parallel) as mocked:
        main(["--size", "3", "--seed", "1", "--demo", "all", "--workers", "2"])
        assert called["ok"] is True
        assert called["workers"] == 2
        assert mocked.call_count == 1


def test_main_invalid_demo_raises_systemexit():
    """Test main raises SystemExit when invalid demo choice is provided."""
    with pytest.raises(SystemExit):
        main(["--demo", "invalid"])


def test_main_unknown_arg_raises_systemexit():
    """Test main raises SystemExit when an unknown argument is provided."""
    with pytest.raises(SystemExit):
        main(["--unknown-flag"])