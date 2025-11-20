import pytest
from unittest.mock import Mock, patch, call
from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sales_records():
    """Create a list of SalesRecord instances for testing."""
    return [
        SalesRecord(record_id=1, product="Widget", amount=100.0, date="2025-01-01", region="EMEA"),
        SalesRecord(record_id=2, product="Gadget", amount=50.0, date="2025-01-02", region="APAC"),
        SalesRecord(record_id=3, product="Widget", amount=75.0, date="2025-01-03", region="Americas"),
        SalesRecord(record_id=4, product="Thing", amount=50.0, date="2025-01-04", region="EMEA"),
        SalesRecord(record_id=5, product="Widget", amount=50.0, date="2025-01-05", region="APAC"),
    ]


@pytest.fixture
def data_processor_instance(sales_records):
    """Create a DataProcessor instance for testing."""
    return DataProcessor(records=sales_records)


def test_salesrecord_init_and_to_dict():
    """Test SalesRecord initialization and to_dict output."""
    record = SalesRecord(record_id=10, product="Widget", amount=123.45, date="2025-01-01", region="EMEA")
    data = record.to_dict()
    assert data["record_id"] == 10
    assert data["product"] == "Widget"
    assert data["amount"] == 123.45
    assert data["date"] == "2025-01-01"
    assert data["region"] == "EMEA"


def test_salesrecord_from_dict_success():
    """Test SalesRecord.from_dict parses fields using utils.v correctly."""
    sample_data = {
        "record_id": "10",
        "product": "Widget",
        "amount": "123.45",
        "date": "2025-01-01",
        "region": "EMEA",
    }
    with patch("data_processor.v") as mock_v:
        mock_v.side_effect = [10, "Widget", 123.45, "2025-01-01", "EMEA"]
        record = SalesRecord.from_dict(sample_data)

        # Validate call order and arguments to v
        assert mock_v.call_args_list == [
            call(sample_data, "record_id", "i"),
            call(sample_data, "product", "s"),
            call(sample_data, "amount", "f"),
            call(sample_data, "date", "s"),
            call(sample_data, "region", "s"),
        ]

        # Validate resulting SalesRecord
        assert record.record_id == 10
        assert record.product == "Widget"
        assert record.amount == 123.45
        assert record.date == "2025-01-01"
        assert record.region == "EMEA"


def test_salesrecord_from_dict_raises_on_error():
    """Test SalesRecord.from_dict propagates exceptions from utils.v."""
    sample_data = {
        "record_id": "bad",
        "product": "Widget",
        "amount": "123.45",
        "date": "2025-01-01",
        "region": "EMEA",
    }
    with patch("data_processor.v") as mock_v:
        # Simulate failure when parsing record_id
        mock_v.side_effect = ValueError("invalid integer")
        with pytest.raises(ValueError):
            SalesRecord.from_dict(sample_data)


def test_dataprocessor_init_preserves_records_list(sales_records):
    """Test DataProcessor initialization stores records as provided."""
    dp = DataProcessor(records=sales_records)
    assert dp.records is sales_records
    assert len(dp.records) == 5


def test_dataprocessor_sort_by_amount_sorted_and_original_unchanged(data_processor_instance, sales_records):
    """Test sort_by_amount returns a new list sorted by amount ascending and does not mutate original."""
    original_order_ids = [r.record_id for r in sales_records]
    sorted_records = data_processor_instance.sort_by_amount()
    sorted_amounts = [r.amount for r in sorted_records]
    assert sorted_amounts == sorted(sorted_amounts)
    # Ensure original list order unchanged
    assert [r.record_id for r in sales_records] == original_order_ids


def test_dataprocessor_sort_by_amount_stability(sales_records):
    """Test sort_by_amount is stable when amounts are equal."""
    # Records 2, 4, 5 all have amount 50.0 in the provided fixture order
    dp = DataProcessor(records=sales_records)
    sorted_records = dp.sort_by_amount()
    equal_amount_ids_in_sorted = [r.record_id for r in sorted_records if r.amount == 50.0]
    assert equal_amount_ids_in_sorted == [2, 4, 5]


def test_dataprocessor_filter_by_region(data_processor_instance):
    """Test filter_by_region returns records matching the region."""
    results = data_processor_instance.filter_by_region("EMEA")
    assert [r.record_id for r in results] == [1, 4]


def test_dataprocessor_filter_by_product(data_processor_instance):
    """Test filter_by_product returns records matching the product."""
    results = data_processor_instance.filter_by_product("Widget")
    assert [r.record_id for r in results] == [1, 3, 5]


def test_dataprocessor_get_total_sales(data_processor_instance):
    """Test get_total_sales computes the sum of amounts."""
    assert data_processor_instance.get_total_sales() == 325.0


def test_dataprocessor_get_average_sale_non_empty(data_processor_instance):
    """Test get_average_sale returns average for non-empty records."""
    assert data_processor_instance.get_average_sale() == 65.0


def test_dataprocessor_get_average_sale_empty():
    """Test get_average_sale returns 0 for empty dataset."""
    dp = DataProcessor(records=[])
    assert dp.get_average_sale() == 0


def test_dataprocessor_group_by_region(data_processor_instance):
    """Test group_by_region returns a mapping of region to list of records."""
    groups = data_processor_instance.group_by_region()
    assert set(groups.keys()) == {"EMEA", "APAC", "Americas"}
    assert [r.record_id for r in groups["EMEA"]] == [1, 4]
    assert [r.record_id for r in groups["APAC"]] == [2, 5]
    assert [r.record_id for r in groups["Americas"]] == [3]


def test_dataprocessor_get_top_products_limit_and_order(data_processor_instance):
    """Test get_top_products returns top products by total sales with limit applied."""
    # Product totals: Widget=225, Gadget=50, Thing=50
    top1 = data_processor_instance.get_top_products(limit=1)
    assert top1 == [("Widget", 225.0)]

    top2 = data_processor_instance.get_top_products(limit=2)
    assert top2[0] == ("Widget", 225.0)
    assert len(top2) == 2
    assert top2[1][0] in {"Gadget", "Thing"}
    assert top2[1][1] == 50.0

    top10 = data_processor_instance.get_top_products(limit=10)
    assert len(top10) == 3


def test_dataprocessor_process_records_parallel_threshold_filtering():
    """Test process_records_parallel filters records above threshold across threads."""
    records = [
        SalesRecord(1, "A", 10.0, "d1", "R1"),
        SalesRecord(2, "B", 20.0, "d2", "R2"),
        SalesRecord(3, "C", 30.0, "d3", "R3"),
        SalesRecord(4, "D", 40.0, "d4", "R4"),
        SalesRecord(5, "E", 50.0, "d5", "R5"),
        SalesRecord(6, "F", 60.0, "d6", "R6"),
        SalesRecord(7, "G", 70.0, "d7", "R7"),
        SalesRecord(8, "H", 80.0, "d8", "R8"),
    ]
    dp = DataProcessor(records=records)
    threshold = 50.0
    results = dp.process_records_parallel(threshold=threshold)
    result_ids = sorted(r.record_id for r in results)
    # Strictly greater than threshold
    assert result_ids == [6, 7, 8]


def test_dataprocessor_process_records_parallel_empty_records_uses_no_threads():
    """Test process_records_parallel with empty records returns empty list and creates no threads."""
    dp = DataProcessor(records=[])

    class FakeThread:
        created = 0

        def __init__(self, target=None, args=(), kwargs=None):
            FakeThread.created += 1
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}

        def start(self):
            if self._target:
                self._target(*self._args, **self._kwargs)

        def join(self):
            return

    with patch("data_processor.threading.Thread", new=FakeThread):
        results = dp.process_records_parallel(threshold=10.0)
        assert results == []
        assert FakeThread.created == 0


def test_dataprocessor_process_records_parallel_thread_chunking_and_execution(sales_records):
    """Test process_records_parallel creates expected number of threads based on chunking and processes data."""
    # 10 records -> chunk_size = 10 // 4 = 2 -> expected 5 threads
    records = sales_records + [
        SalesRecord(6, "X", 10.0, "d6", "R1"),
        SalesRecord(7, "Y", 20.0, "d7", "R2"),
        SalesRecord(8, "Z", 30.0, "d8", "R3"),
        SalesRecord(9, "W", 40.0, "d9", "R4"),
        SalesRecord(10, "V", 60.0, "d10", "R5"),
    ]
    dp = DataProcessor(records=records)

    class FakeThread:
        """A fake Thread that runs target synchronously and counts instances."""
        instances = []

        def __init__(self, target=None, args=(), kwargs=None):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}
            FakeThread.instances.append(self)

        def start(self):
            if self._target:
                self._target(*self._args, **self._kwargs)

        def join(self):
            return

    with patch("data_processor.threading.Thread", new=FakeThread):
        results = dp.process_records_parallel(threshold=50.0)
        # Expect 5 threads for 10 records with chunk_size 2
        assert len(FakeThread.instances) == 5
        # Results include records strictly greater than 50.0
        result_ids = sorted(r.record_id for r in results)
        assert result_ids == [1, 10]  # from fixtures: id 1 is 100.0; id 10 is 60.0


def test_dataprocessor_get_top_products_empty():
    """Test get_top_products on empty records returns an empty list."""
    dp = DataProcessor(records=[])
    assert dp.get_top_products() == []