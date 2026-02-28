import pytest
from unittest.mock import patch, call
from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sample_records():
    """Create a sample list of SalesRecord instances for testing."""
    return [
        SalesRecord(record_id=1, product="A", amount=50.0, date="2021-01-01", region="US"),
        SalesRecord(record_id=2, product="B", amount=20.0, date="2021-01-02", region="EU"),
        SalesRecord(record_id=3, product="A", amount=75.0, date="2021-01-03", region="US"),
        SalesRecord(record_id=4, product="C", amount=50.0, date="2021-01-04", region="APAC"),
        SalesRecord(record_id=5, product="B", amount=10.0, date="2021-01-05", region="US"),
        SalesRecord(record_id=6, product="A", amount=120.0, date="2021-01-06", region="EU"),
        SalesRecord(record_id=7, product="D", amount=5.0, date="2021-01-07", region="US"),
    ]


@pytest.fixture
def processor(sample_records):
    """Create a DataProcessor instance with sample records."""
    return DataProcessor(records=sample_records)


@pytest.fixture
def empty_processor():
    """Create a DataProcessor instance with no records."""
    return DataProcessor(records=[])


@pytest.fixture
def ten_records():
    """Create 10 records for chunking/threading tests."""
    return [
        SalesRecord(record_id=i, product="X", amount=float(i), date=f"2021-01-{i:02d}", region="R")
        for i in range(10)
    ]


def test_salesrecord_init_and_to_dict():
    """Test SalesRecord initialization and to_dict output."""
    rec = SalesRecord(record_id=42, product="Widget", amount=99.5, date="2024-01-01", region="NA")
    assert rec.record_id == 42
    assert rec.product == "Widget"
    assert rec.amount == 99.5
    assert rec.date == "2024-01-01"
    assert rec.region == "NA"

    d = rec.to_dict()
    assert d == {
        "record_id": 42,
        "product": "Widget",
        "amount": 99.5,
        "date": "2024-01-01",
        "region": "NA",
    }


def test_salesrecord_from_dict_success():
    """Test SalesRecord.from_dict uses utils.v correctly and returns a populated record."""
    data = {
        "record_id": "101",
        "product": "Gadget",
        "amount": "123.45",
        "date": "2023-06-15",
        "region": "EU",
    }

    values = {
        ("record_id", "i"): 101,
        ("product", "s"): "Gadget",
        ("amount", "f"): 123.45,
        ("date", "s"): "2023-06-15",
        ("region", "s"): "EU",
    }

    def v_side_effect(d, key, typ):
        # Return the mapped value regardless of input types
        return values[(key, typ)]

    with patch("data_processor.v", side_effect=v_side_effect) as mock_v:
        rec = SalesRecord.from_dict(data)

        # Validate call sequence and argument correctness
        assert mock_v.call_args_list == [
            call(data, "record_id", "i"),
            call(data, "product", "s"),
            call(data, "amount", "f"),
            call(data, "date", "s"),
            call(data, "region", "s"),
        ]

        # Validate result
        assert rec.record_id == 101
        assert rec.product == "Gadget"
        assert rec.amount == 123.45
        assert rec.date == "2023-06-15"
        assert rec.region == "EU"


def test_salesrecord_from_dict_raises_on_v_error():
    """Test SalesRecord.from_dict propagates errors from utils.v."""
    with patch("data_processor.v", side_effect=ValueError("bad input")):
        with pytest.raises(ValueError):
            SalesRecord.from_dict({"record_id": None, "product": None, "amount": None, "date": None, "region": None})


def test_dataprocessor_init_and_records_reference(sample_records):
    """Test DataProcessor initialization keeps reference to original list."""
    dp = DataProcessor(records=sample_records)
    assert dp.records is sample_records


def test_dataprocessor_sort_by_amount_ascending_and_stable(processor, sample_records):
    """Test sorting by amount ascending and stability for equal amounts."""
    original_order_ids = [r.record_id for r in processor.records]
    sorted_records = processor.sort_by_amount()

    # Ensure it's a new list
    assert sorted_records is not processor.records

    # Verify ascending order
    sorted_amounts = [r.amount for r in sorted_records]
    assert sorted_amounts == sorted(sorted_amounts)

    # Verify stability for equal amounts (records 1 and 4 both 50.0)
    ids_in_sorted = [r.record_id for r in sorted_records]
    assert ids_in_sorted.index(1) < ids_in_sorted.index(4)

    # Original list not mutated
    assert [r.record_id for r in processor.records] == original_order_ids


def test_dataprocessor_filter_by_region_matches_and_no_match(processor):
    """Test filtering by region returns correct records and handles no matches."""
    us = processor.filter_by_region("US")
    assert [r.record_id for r in us] == [1, 3, 5, 7]

    none = processor.filter_by_region("NA")
    assert none == []


def test_dataprocessor_filter_by_product(processor):
    """Test filtering by product returns correct records."""
    a = processor.filter_by_product("A")
    assert [r.record_id for r in a] == [1, 3, 6]


def test_dataprocessor_get_total_sales(processor):
    """Test total sales sum across all records."""
    assert processor.get_total_sales() == 330.0


def test_dataprocessor_get_average_sale_non_empty_and_empty(processor, empty_processor):
    """Test average sale for non-empty and empty processors."""
    assert processor.get_average_sale() == pytest.approx(330.0 / 7)
    assert empty_processor.get_average_sale() == 0


def test_dataprocessor_group_by_region(processor, empty_processor):
    """Test grouping records by region."""
    grouped = processor.group_by_region()
    assert set(grouped.keys()) == {"US", "EU", "APAC"}
    assert [r.record_id for r in grouped["US"]] == [1, 3, 5, 7]
    assert [r.record_id for r in grouped["EU"]] == [2, 6]
    assert [r.record_id for r in grouped["APAC"]] == [4]

    assert empty_processor.group_by_region() == {}


def test_dataprocessor_get_top_products_default_and_custom_limit(processor):
    """Test computing top products by total amount with default and custom limits."""
    # Totals: A=245, C=50, B=30, D=5
    default_top = processor.get_top_products()
    assert default_top == [("A", 245.0), ("C", 50.0), ("B", 30.0), ("D", 5.0)]
    assert len(default_top) == 4  # fewer than default limit 5

    top2 = processor.get_top_products(limit=2)
    assert top2 == [("A", 245.0), ("C", 50.0)]


def test_dataprocessor_process_records_parallel_threshold(processor):
    """Test parallel processing filters records strictly greater than threshold."""
    # Threshold at 50 should include amounts > 50 only
    results = processor.process_records_parallel(threshold=50.0)
    result_ids = sorted([r.record_id for r in results])
    assert result_ids == [3, 6]  # 75.0 and 120.0


def test_dataprocessor_process_records_parallel_includes_all_and_thread_count(ten_records):
    """Test parallel processing uses expected number of threads and processes all chunks."""
    dp = DataProcessor(records=ten_records)
    expected_chunk_size = len(ten_records) // 4  # 10 // 4 = 2
    assert expected_chunk_size == 2
    expected_threads = len(ten_records) // expected_chunk_size  # 10 / 2 = 5
    assert expected_threads == 5

    class FakeThread:
        def __init__(self, target=None, args=()):
            self._target = target
            self._args = args

        def start(self):
            # Execute synchronously to make behavior deterministic
            if self._target:
                self._target(*self._args)

        def join(self):
            return

    constructed = []

    def constructor(target=None, args=()):
        t = FakeThread(target=target, args=args)
        constructed.append(t)
        return t

    with patch("data_processor.threading.Thread", side_effect=constructor) as thread_ctor:
        results = dp.process_records_parallel(threshold=-1.0)

        # All records should be included
        assert sorted([r.record_id for r in results]) == list(range(10))

        # Expected number of threads constructed
        assert thread_ctor.call_count == expected_threads
        assert len(constructed) == expected_threads


def test_dataprocessor_process_records_parallel_empty_records_no_threads():
    """Test parallel processing with no records creates no threads and returns empty list."""
    dp = DataProcessor(records=[])
    with patch("data_processor.threading.Thread") as thread_ctor:
        results = dp.process_records_parallel(threshold=0.0)
        assert results == []
        thread_ctor.assert_not_called()