import pytest
from unittest.mock import Mock, patch
from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sample_sales_record():
    """Create a sample SalesRecord instance for testing."""
    return SalesRecord(
        record_id=1,
        product="Widget",
        amount=100.5,
        date="2024-01-01",
        region="North",
    )


@pytest.fixture
def sample_sales_records():
    """Create a list of SalesRecord instances for DataProcessor tests."""
    return [
        SalesRecord(1, "Widget", 100.0, "2024-01-01", "North"),
        SalesRecord(2, "Gadget", 50.0, "2024-01-02", "South"),
        SalesRecord(3, "Widget", 150.0, "2024-01-03", "North"),
        SalesRecord(4, "Thing", 75.0, "2024-01-04", "East"),
        SalesRecord(5, "Widget", 200.0, "2024-01-05", "South"),
    ]


@pytest.fixture
def data_processor_instance(sample_sales_records):
    """Create a DataProcessor instance with sample records."""
    return DataProcessor(records=sample_sales_records)


# ---------- SalesRecord tests ----------


def test_salesrecord_init_valid(sample_sales_record):
    """Test SalesRecord initialization with valid data."""
    record = sample_sales_record
    assert record.record_id == 1
    assert record.product == "Widget"
    assert record.amount == pytest.approx(100.5)
    assert record.date == "2024-01-01"
    assert record.region == "North"


def test_salesrecord_to_dict(sample_sales_record):
    """Test SalesRecord.to_dict returns correct dictionary."""
    result = sample_sales_record.to_dict()
    assert result["record_id"] == 1
    assert result["product"] == "Widget"
    assert result["amount"] == pytest.approx(100.5)
    assert result["date"] == "2024-01-01"
    assert result["region"] == "North"


def test_salesrecord_from_dict_uses_v_correctly():
    """Test SalesRecord.from_dict uses utils.v with correct arguments."""
    data = {
        "record_id": 10,
        "product": "Gizmo",
        "amount": 300.75,
        "date": "2024-02-01",
        "region": "West",
    }

    with patch("data_processor.v") as mock_v:
        # Configure side effects to return appropriate values
        mock_v.side_effect = [
            data["record_id"],
            data["product"],
            data["amount"],
            data["date"],
            data["region"],
        ]

        record = SalesRecord.from_dict(data)

        # Check calls to v
        expected_calls = [
            ((data, "record_id", "i"),),
            ((data, "product", "s"),),
            ((data, "amount", "f"),),
            ((data, "date", "s"),),
            ((data, "region", "s"),),
        ]
        actual_calls = [call.args for call in mock_v.call_args_list]
        assert actual_calls == expected_calls

        # Check record fields
        assert record.record_id == 10
        assert record.product == "Gizmo"
        assert record.amount == pytest.approx(300.75)
        assert record.date == "2024-02-01"
        assert record.region == "West"


def test_salesrecord_from_dict_raises_from_v_error():
    """Test SalesRecord.from_dict propagates exceptions from utils.v."""
    data = {"record_id": "bad"}  # intentionally malformed

    with patch("data_processor.v") as mock_v:
        mock_v.side_effect = ValueError("invalid data")
        with pytest.raises(ValueError):
            SalesRecord.from_dict(data)


# ---------- DataProcessor __init__ ----------


def test_dataprocessor_init_with_records(sample_sales_records):
    """Test DataProcessor initialization stores records correctly."""
    processor = DataProcessor(records=sample_sales_records)
    assert processor.records is sample_sales_records
    assert len(processor.records) == 5


def test_dataprocessor_init_with_empty_list():
    """Test DataProcessor initialization with empty list of records."""
    processor = DataProcessor(records=[])
    assert processor.records == []


# ---------- DataProcessor.sort_by_amount ----------


def test_dataprocessor_sort_by_amount_sorted_order(data_processor_instance):
    """Test sort_by_amount returns records sorted ascending by amount."""
    sorted_records = data_processor_instance.sort_by_amount()
    amounts = [r.amount for r in sorted_records]
    assert amounts == sorted(amounts)


def test_dataprocessor_sort_by_amount_stable_for_equal_amounts():
    """Test sort_by_amount behavior when multiple records have equal amounts."""
    records = [
        SalesRecord(1, "A", 100.0, "2024-01-01", "North"),
        SalesRecord(2, "B", 100.0, "2024-01-02", "South"),
        SalesRecord(3, "C", 50.0, "2024-01-03", "East"),
    ]
    processor = DataProcessor(records=records)
    sorted_records = processor.sort_by_amount()
    amounts = [r.amount for r in sorted_records]
    assert amounts == [50.0, 100.0, 100.0]


def test_dataprocessor_sort_by_amount_does_not_modify_original(data_processor_instance):
    """Test sort_by_amount does not modify original records list."""
    original_ids = [r.record_id for r in data_processor_instance.records]
    _ = data_processor_instance.sort_by_amount()
    after_ids = [r.record_id for r in data_processor_instance.records]
    assert after_ids == original_ids


def test_dataprocessor_sort_by_amount_empty():
    """Test sort_by_amount on empty records list."""
    processor = DataProcessor(records=[])
    sorted_records = processor.sort_by_amount()
    assert sorted_records == []


# ---------- DataProcessor.filter_by_region ----------


def test_dataprocessor_filter_by_region_matches(data_processor_instance):
    """Test filter_by_region returns only records with matching region."""
    filtered = data_processor_instance.filter_by_region("North")
    assert all(r.region == "North" for r in filtered)
    assert len(filtered) == 2


def test_dataprocessor_filter_by_region_no_matches(data_processor_instance):
    """Test filter_by_region returns empty list when no region matches."""
    filtered = data_processor_instance.filter_by_region("NonExistent")
    assert filtered == []


# ---------- DataProcessor.filter_by_product ----------


def test_dataprocessor_filter_by_product_matches(data_processor_instance):
    """Test filter_by_product returns only records with matching product."""
    filtered = data_processor_instance.filter_by_product("Widget")
    assert all(r.product == "Widget" for r in filtered)
    assert len(filtered) == 3


def test_dataprocessor_filter_by_product_no_matches(data_processor_instance):
    """Test filter_by_product returns empty list when no product matches."""
    filtered = data_processor_instance.filter_by_product("NonExistentProduct")
    assert filtered == []


# ---------- DataProcessor.get_total_sales ----------


def test_dataprocessor_get_total_sales_correct_sum(data_processor_instance):
    """Test get_total_sales returns correct sum of amounts."""
    expected = sum(r.amount for r in data_processor_instance.records)
    total = data_processor_instance.get_total_sales()
    assert total == pytest.approx(expected)


def test_dataprocessor_get_total_sales_empty():
    """Test get_total_sales on empty records list returns 0."""
    processor = DataProcessor(records=[])
    total = processor.get_total_sales()
    assert total == pytest.approx(0.0)


# ---------- DataProcessor.get_average_sale ----------


def test_dataprocessor_get_average_sale_non_empty(data_processor_instance):
    """Test get_average_sale returns correct average for non-empty list."""
    total = sum(r.amount for r in data_processor_instance.records)
    expected_avg = total / len(data_processor_instance.records)
    avg = data_processor_instance.get_average_sale()
    assert avg == pytest.approx(expected_avg)


def test_dataprocessor_get_average_sale_empty():
    """Test get_average_sale returns 0 for empty records list."""
    processor = DataProcessor(records=[])
    avg = processor.get_average_sale()
    assert avg == pytest.approx(0.0)


# ---------- DataProcessor.group_by_region ----------


def test_dataprocessor_group_by_region_groups_correctly(data_processor_instance):
    """Test group_by_region returns dict keyed by region with correct records."""
    grouped = data_processor_instance.group_by_region()
    regions = {r.region for r in data_processor_instance.records}
    assert set(grouped.keys()) == regions
    for region, records in grouped.items():
        assert all(r.region == region for r in records)


def test_dataprocessor_group_by_region_empty():
    """Test group_by_region on empty records list returns empty dict."""
    processor = DataProcessor(records=[])
    grouped = processor.group_by_region()
    assert grouped == {}


# ---------- DataProcessor.get_top_products ----------


def test_dataprocessor_get_top_products_default_limit(data_processor_instance):
    """Test get_top_products returns top products sorted by total amount."""
    top_products = data_processor_instance.get_top_products()
    assert isinstance(top_products, list)
    assert all(isinstance(t, tuple) and len(t) == 2 for t in top_products)
    # Check that amounts are in descending order
    amounts = [t[1] for t in top_products]
    assert amounts == sorted(amounts, reverse=True)


def test_dataprocessor_get_top_products_custom_limit(data_processor_instance):
    """Test get_top_products respects custom limit."""
    top_two = data_processor_instance.get_top_products(limit=2)
    assert len(top_two) == 2


def test_dataprocessor_get_top_products_limit_greater_than_products(data_processor_instance):
    """Test get_top_products when limit exceeds number of unique products."""
    unique_products = {r.product for r in data_processor_instance.records}
    top = data_processor_instance.get_top_products(limit=10)
    assert len(top) == len(unique_products)


def test_dataprocessor_get_top_products_empty():
    """Test get_top_products on empty records list returns empty list."""
    processor = DataProcessor(records=[])
    top = processor.get_top_products()
    assert top == []


# ---------- DataProcessor.process_records_parallel ----------


def test_dataprocessor_process_records_parallel_threshold_middle(sample_sales_records):
    """Test process_records_parallel returns records above threshold."""
    processor = DataProcessor(records=sample_sales_records)
    threshold = 100.0
    results = processor.process_records_parallel(threshold)
    assert all(r.amount > threshold for r in results)
    # Check that expected records are present (amounts > 100)
    expected_ids = {r.record_id for r in sample_sales_records if r.amount > threshold}
    result_ids = {r.record_id for r in results}
    assert result_ids == expected_ids


def test_dataprocessor_process_records_parallel_threshold_high(sample_sales_records):
    """Test process_records_parallel returns empty list when no records exceed threshold."""
    processor = DataProcessor(records=sample_sales_records)
    threshold = 1000.0
    results = processor.process_records_parallel(threshold)
    assert results == []


def test_dataprocessor_process_records_parallel_single_record():
    """Test process_records_parallel behavior with a single record."""
    records = [SalesRecord(1, "A", 10.0, "2024-01-01", "North")]
    processor = DataProcessor(records=records)
    results = processor.process_records_parallel(threshold=5.0)
    assert len(results) == 1
    assert results[0].record_id == 1
    assert results[0].amount == pytest.approx(10.0)


def test_dataprocessor_process_records_parallel_empty():
    """Test process_records_parallel with empty records list returns empty list."""
    processor = DataProcessor(records=[])
    results = processor.process_records_parallel(threshold=0.0)
    assert results == []


def test_dataprocessor_process_records_parallel_chunk_size_less_than_four():
    """Test process_records_parallel when len(records) < 4 uses chunk_size 1."""
    records = [
        SalesRecord(1, "A", 10.0, "2024-01-01", "North"),
        SalesRecord(2, "B", 20.0, "2024-01-02", "South"),
        SalesRecord(3, "C", 30.0, "2024-01-03", "East"),
    ]
    processor = DataProcessor(records=records)
    results = processor.process_records_parallel(threshold=15.0)
    result_ids = {r.record_id for r in results}
    expected_ids = {2, 3}
    assert result_ids == expected_ids


def test_dataprocessor_process_records_parallel_uses_threading(sample_sales_records, monkeypatch):
    """Test process_records_parallel creates threads with correct targets and args."""
    processor = DataProcessor(records=sample_sales_records)

    created_threads = []

    class FakeThread:
        def __init__(self, target=None, args=None, kwargs=None):
            self.target = target
            self.args = args or ()
            self.kwargs = kwargs or {}
            created_threads.append(self)

        def start(self):
            # Directly run target instead of starting real thread
            if self.target:
                self.target(*self.args, **self.kwargs)

        def join(self):
            # No-op for fake thread
            pass

    monkeypatch.setattr("data_processor.threading.Thread", FakeThread)

    threshold = 75.0
    results = processor.process_records_parallel(threshold=threshold)

    # Ensure at least one fake thread was created
    assert len(created_threads) >= 1

    # Validate the results are still correct
    expected_ids = {r.record_id for r in sample_sales_records if r.amount > threshold}
    result_ids = {r.record_id for r in results}
    assert result_ids == expected_ids