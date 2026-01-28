import pytest
from datetime import datetime
import time
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from data_processor import SalesRecord, DataProcessor


def slow_double_amount(record: SalesRecord) -> float:
    """Helper function for parallel processing tests; sleeps variably to reorder completions."""
    # Make the first record significantly slower to encourage out-of-order completion
    sleep_time = 0.1 if record.id == "1" else 0.01
    time.sleep(sleep_time)
    return record.amount * 2.0


def just_return_id(record: SalesRecord) -> str:
    """Helper function to return record id for parallel processing tests."""
    return record.id


@pytest.fixture
def sample_records():
    """Create a list of sample SalesRecord instances."""
    return [
        SalesRecord(id="1", product="Widget", region="North", amount=100.0, date=datetime(2023, 1, 10, 8, 30)),
        SalesRecord(id="2", product="Gadget", region="South", amount=150.5, date=datetime(2023, 2, 20, 9, 45)),
        SalesRecord(id="3", product="Widget", region="North", amount=75.25, date=datetime(2023, 3, 15, 12, 0)),
        SalesRecord(id="4", product="Gizmo", region="East", amount=200.0, date=datetime(2023, 4, 5, 16, 20)),
        SalesRecord(id="5", product="Gadget", region="West", amount=50.0, date=datetime(2023, 5, 1, 10, 10)),
    ]


@pytest.fixture
def data_processor(sample_records):
    """Create a DataProcessor with sample records."""
    return DataProcessor(records=sample_records)


@pytest.fixture
def empty_data_processor():
    """Create a DataProcessor with no records."""
    return DataProcessor(records=[])


def test_salesrecord_init_and_attributes():
    """Test SalesRecord initialization with valid data and attribute assignment."""
    dt = datetime(2024, 5, 1, 15, 30)
    rec = SalesRecord(id="abc", product="Thing", region="EMEA", amount=123.45, date=dt)
    assert rec.id == "abc"
    assert rec.product == "Thing"
    assert rec.region == "EMEA"
    assert rec.amount == pytest.approx(123.45)
    assert rec.date == dt


def test_salesrecord_frozen_immutability():
    """Test that SalesRecord is immutable (frozen dataclass)."""
    rec = SalesRecord(id="1", product="Widget", region="North", amount=10.0, date=datetime(2023, 1, 1))
    with pytest.raises(FrozenInstanceError):
        rec.amount = 20.0  # type: ignore


def test_salesrecord_to_dict_isoformat():
    """Test SalesRecord.to_dict returns ISO 8601 formatted date string."""
    dt = datetime(2024, 5, 1, 15, 30, 45)
    rec = SalesRecord(id="1", product="Widget", region="North", amount=10.5, date=dt)
    d = rec.to_dict()
    assert d["id"] == "1"
    assert d["product"] == "Widget"
    assert d["region"] == "North"
    assert d["amount"] == pytest.approx(10.5)
    assert d["date"] == dt.isoformat()


def test_salesrecord_from_dict_with_datetime():
    """Test SalesRecord.from_dict accepts a datetime instance for date."""
    dt = datetime(2022, 8, 9, 7, 6, 5)
    rec = SalesRecord.from_dict({"id": 123, "product": "X", "region": "Y", "amount": "42.7", "date": dt})
    assert rec.id == "123"
    assert rec.product == "X"
    assert rec.region == "Y"
    assert rec.amount == pytest.approx(42.7)
    assert rec.date == dt


def test_salesrecord_from_dict_with_iso_string():
    """Test SalesRecord.from_dict parses ISO 8601 date string."""
    iso_str = "2023-06-01T12:34:56"
    rec = SalesRecord.from_dict({"id": "a", "product": "P", "region": "R", "amount": 1.0, "date": iso_str})
    assert rec.date == datetime.fromisoformat(iso_str)


def test_salesrecord_from_dict_with_date_only_string():
    """Test SalesRecord.from_dict parses YYYY-MM-DD date-only string."""
    date_only = "2023-06-01"
    rec = SalesRecord.from_dict({"id": "a", "product": "P", "region": "R", "amount": 1.0, "date": date_only})
    assert rec.date == datetime(2023, 6, 1)


def test_salesrecord_from_dict_with_missing_date_defaults_min():
    """Test SalesRecord.from_dict uses datetime.min when date is missing or invalid type."""
    rec = SalesRecord.from_dict({"id": "1", "product": "P", "region": "R", "amount": 0.0, "date": None})
    assert rec.date == datetime.min


def test_dataprocessor_init_accepts_iterable(sample_records):
    """Test DataProcessor initialization accepts iterable and stores as list."""
    gen = (r for r in sample_records)
    dp = DataProcessor(records=gen)
    assert isinstance(dp.records, list)
    assert len(dp.records) == len(sample_records)
    # Ensure same objects were captured
    assert [r.id for r in dp.records] == [r.id for r in sample_records]


def test_dataprocessor_sort_by_amount_ascending(data_processor):
    """Test sort_by_amount returns records sorted by amount ascending by default."""
    sorted_recs = data_processor.sort_by_amount()
    amounts = [r.amount for r in sorted_recs]
    assert amounts == [pytest.approx(v) for v in [50.0, 75.25, 100.0, 150.5, 200.0]]


def test_dataprocessor_sort_by_amount_descending(data_processor):
    """Test sort_by_amount returns records sorted by amount descending when specified."""
    sorted_recs = data_processor.sort_by_amount(descending=True)
    amounts = [r.amount for r in sorted_recs]
    assert amounts == [pytest.approx(v) for v in [200.0, 150.5, 100.0, 75.25, 50.0]]


def test_dataprocessor_filter_by_region(data_processor):
    """Test filter_by_region returns only records with matching region."""
    north = data_processor.filter_by_region("North")
    assert all(r.region == "North" for r in north)
    assert [r.id for r in north] == ["1", "3"]


def test_dataprocessor_filter_by_product(data_processor):
    """Test filter_by_product returns only records with matching product."""
    gadgets = data_processor.filter_by_product("Gadget")
    assert all(r.product == "Gadget" for r in gadgets)
    assert [r.id for r in gadgets] == ["2", "5"]


def test_dataprocessor_get_total_sales_default(data_processor):
    """Test get_total_sales computes total for all records by default."""
    total = data_processor.get_total_sales()
    assert total == pytest.approx(575.75)


def test_dataprocessor_get_total_sales_subset(data_processor):
    """Test get_total_sales can compute total for a provided subset of records."""
    subset = data_processor.filter_by_region("North")
    total = data_processor.get_total_sales(subset)
    expected = subset[0].amount + subset[1].amount
    assert total == pytest.approx(expected)


def test_dataprocessor_get_average_sale_default(data_processor):
    """Test get_average_sale computes average for all records by default."""
    avg = data_processor.get_average_sale()
    assert avg == pytest.approx(575.75 / 5)


def test_dataprocessor_get_average_sale_subset(data_processor):
    """Test get_average_sale computes average for a provided subset of records."""
    subset = data_processor.filter_by_product("Gadget")
    avg = data_processor.get_average_sale(subset)
    expected = (subset[0].amount + subset[1].amount) / 2
    assert avg == pytest.approx(expected)


def test_dataprocessor_get_average_sale_empty(empty_data_processor):
    """Test get_average_sale returns 0.0 when there are no records."""
    assert empty_data_processor.get_average_sale() == pytest.approx(0.0)


def test_dataprocessor_group_by_region(data_processor):
    """Test group_by_region returns a dict grouping records by region."""
    grouped = data_processor.group_by_region()
    assert set(grouped.keys()) == {"North", "South", "East", "West"}
    assert [r.id for r in grouped["North"]] == ["1", "3"]
    assert [r.id for r in grouped["South"]] == ["2"]
    assert [r.id for r in grouped["East"]] == ["4"]
    assert [r.id for r in grouped["West"]] == ["5"]


def test_dataprocessor_group_by_region_empty(empty_data_processor):
    """Test group_by_region returns empty dict for no records."""
    assert empty_data_processor.group_by_region() == {}


def test_dataprocessor_get_top_products_by_revenue_limit(data_processor):
    """Test get_top_products by revenue with a limit."""
    top2 = data_processor.get_top_products(n=2, by="revenue")
    assert top2[0][0] == "Gadget"
    assert top2[0][1] == pytest.approx(200.5)
    assert top2[1][0] == "Gizmo"
    assert top2[1][1] == pytest.approx(200.0)


def test_dataprocessor_get_top_products_by_count(data_processor):
    """Test get_top_products when aggregated by count."""
    top = data_processor.get_top_products(n=2, by="count")
    assert top[0][0] == "Widget"
    assert top[0][1] == pytest.approx(2.0)
    assert top[1][0] == "Gadget"
    assert top[1][1] == pytest.approx(2.0)


def test_dataprocessor_get_top_products_invalid_by_raises(data_processor):
    """Test get_top_products raises ValueError for invalid 'by' argument."""
    with pytest.raises(ValueError):
        data_processor.get_top_products(n=3, by="invalid")


def test_dataprocessor_process_records_parallel_threads_order_preserved():
    """Test process_records_parallel with threads preserves original order of results."""
    records = [
        SalesRecord(id="1", product="P", region="R", amount=1.0, date=datetime(2023, 1, 1)),
        SalesRecord(id="2", product="P", region="R", amount=2.5, date=datetime(2023, 1, 2)),
        SalesRecord(id="3", product="P", region="R", amount=3.25, date=datetime(2023, 1, 3)),
    ]
    dp = DataProcessor(records=records)
    results = dp.process_records_parallel(func=slow_double_amount, max_workers=3, use_processes=False)
    expected = [r.amount * 2.0 for r in records]
    assert results == [pytest.approx(v) for v in expected]


def test_dataprocessor_process_records_parallel_empty(empty_data_processor):
    """Test process_records_parallel returns empty list when there are no records."""
    results = empty_data_processor.process_records_parallel(func=just_return_id)
    assert results == []


def test_dataprocessor_process_records_parallel_processes_mocked(sample_records):
    """Test process_records_parallel uses ProcessPoolExecutor when use_processes=True, with mocked executor."""
    created_executors = []

    class DummyFuture:
        def __init__(self, result):
            self._result = result

        def result(self):
            return self._result

    class DummyExecutor:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers
            self.submissions = []
            created_executors.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, func, rec):
            res = func(rec)
            fut = DummyFuture(res)
            self.submissions.append(fut)
            return fut

    def dummy_as_completed(futures):
        # Return futures in reverse order to simulate arbitrary completion order
        return list(futures)[::-1]

    dp = DataProcessor(records=sample_records[:3])
    with patch("data_processor.ProcessPoolExecutor", new=DummyExecutor), patch("data_processor.as_completed", new=dummy_as_completed):
        results = dp.process_records_parallel(func=just_return_id, max_workers=3, use_processes=True)

    # Ensure executor was created with passed max_workers
    assert created_executors and created_executors[-1].max_workers == 3
    # Ensure results align with original order of records
    assert results == [r.id for r in sample_records[:3]]