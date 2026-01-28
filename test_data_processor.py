import pytest
from unittest.mock import Mock, patch
from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sample_sales_records():
    """Create a list of sample SalesRecord instances for testing."""
    return [
        SalesRecord(record_id=1, product="Widget", amount=100.0, date="2024-01-01", region="North"),
        SalesRecord(record_id=2, product="Gadget", amount=50.5, date="2024-01-02", region="South"),
        SalesRecord(record_id=3, product="Widget", amount=75.25, date="2024-01-03", region="North"),
        SalesRecord(record_id=4, product="Thing", amount=200.0, date="2024-01-04", region="East"),
        SalesRecord(record_id=5, product="Widget", amount=10.0, date="2024-01-05", region="West"),
    ]


@pytest.fixture
def data_processor_instance(sample_sales_records):
    """Create a DataProcessor instance for testing."""
    return DataProcessor(records=sample_sales_records)


# ---- SalesRecord tests ----

def test_salesrecord_init_valid():
    """Test SalesRecord initialization with valid data."""
    record = SalesRecord(record_id=1, product="Widget", amount=123.45, date="2024-01-01", region="North")
    assert record.record_id == 1
    assert record.product == "Widget"
    assert record.amount == pytest.approx(123.45)
    assert record.date == "2024-01-01"
    assert record.region == "North"


def test_salesrecord_to_dict():
    """Test SalesRecord.to_dict returns a correct dictionary."""
    record = SalesRecord(record_id=10, product="Gizmo", amount=42.0, date="2024-02-01", region="South")
    result = record.to_dict()
    assert result == {
        "record_id": 10,
        "product": "Gizmo",
        "amount": 42.0,
        "date": "2024-02-01",
        "region": "South",
    }


def test_salesrecord_from_dict_uses_utils_v_success():
    """Test SalesRecord.from_dict uses utils.v correctly for all fields."""
    data = {
        "record_id": 7,
        "product": "Gadget",
        "amount": 12.34,
        "date": "2024-03-01",
        "region": "East",
    }

    # Side effect returns in the order of calls to v()
    with patch("data_processor.v") as mock_v:
        mock_v.side_effect = [7, "Gadget", 12.34, "2024-03-01", "East"]
        record = SalesRecord.from_dict(data)

        # Ensure v was called with correct arguments
        expected_calls = [
            ((data, "record_id", "i"),),
            ((data, "product", "s"),),
            ((data, "amount", "f"),),
            ((data, "date", "s"),),
            ((data, "region", "s"),),
        ]
        actual_calls = [(call.args,) for call in mock_v.call_args_list]
        assert actual_calls == expected_calls

        assert isinstance(record, SalesRecord)
        assert record.record_id == 7
        assert record.product == "Gadget"
        assert record.amount == pytest.approx(12.34)
        assert record.date == "2024-03-01"
        assert record.region == "East"


def test_salesrecord_from_dict_utils_v_raises():
    """Test SalesRecord.from_dict propagates exceptions raised by utils.v."""
    data = {"record_id": "invalid"}

    with patch("data_processor.v", side_effect=ValueError("bad value")) as mock_v:
        with pytest.raises(ValueError) as excinfo:
            SalesRecord.from_dict(data)

        assert "bad value" in str(excinfo.value)
        mock_v.assert_called_once()  # fails on first call


# ---- DataProcessor tests ----

def test_dataprocessor_init(sample_sales_records):
    """Test DataProcessor initialization stores records."""
    processor = DataProcessor(records=sample_sales_records)
    assert processor.records == sample_sales_records


def test_dataprocessor_sort_by_amount_sorted_ascending(data_processor_instance):
    """Test DataProcessor.sort_by_amount sorts records by amount ascending."""
    sorted_records = data_processor_instance.sort_by_amount()
    amounts = [r.amount for r in sorted_records]
    assert amounts == sorted(amounts)
    # Ensure original list is not mutated
    original_amounts = [r.amount for r in data_processor_instance.records]
    assert original_amounts != sorted(original_amounts) or len(original_amounts) == 0


def test_dataprocessor_sort_by_amount_stable_on_equal_amounts():
    """Test DataProcessor.sort_by_amount handles records with equal amounts."""
    r1 = SalesRecord(1, "A", 10.0, "2024-01-01", "X")
    r2 = SalesRecord(2, "B", 10.0, "2024-01-02", "Y")
    r3 = SalesRecord(3, "C", 5.0, "2024-01-03", "Z")
    processor = DataProcessor([r1, r2, r3])
    sorted_records = processor.sort_by_amount()
    amounts = [r.amount for r in sorted_records]
    assert amounts == [5.0, 10.0, 10.0]


def test_dataprocessor_sort_by_amount_empty_list():
    """Test DataProcessor.sort_by_amount returns empty list for no records."""
    processor = DataProcessor(records=[])
    sorted_records = processor.sort_by_amount()
    assert sorted_records == []


def test_dataprocessor_filter_by_region_matches(data_processor_instance):
    """Test DataProcessor.filter_by_region returns matching records."""
    north_records = data_processor_instance.filter_by_region("North")
    assert all(r.region == "North" for r in north_records)
    # From fixture: two North records
    assert len(north_records) == 2


def test_dataprocessor_filter_by_region_no_matches(data_processor_instance):
    """Test DataProcessor.filter_by_region returns empty when no region matches."""
    records = data_processor_instance.filter_by_region("Nonexistent")
    assert records == []


def test_dataprocessor_filter_by_product_matches(data_processor_instance):
    """Test DataProcessor.filter_by_product returns matching records."""
    widget_records = data_processor_instance.filter_by_product("Widget")
    assert all(r.product == "Widget" for r in widget_records)
    # From fixture: three Widget records
    assert len(widget_records) == 3


def test_dataprocessor_filter_by_product_no_matches(data_processor_instance):
    """Test DataProcessor.filter_by_product returns empty when no product matches."""
    records = data_processor_instance.filter_by_product("UnknownProduct")
    assert records == []


def test_dataprocessor_get_total_sales(data_processor_instance):
    """Test DataProcessor.get_total_sales sums amounts correctly."""
    total = data_processor_instance.get_total_sales()
    expected = sum(r.amount for r in data_processor_instance.records)
    assert total == pytest.approx(expected)


def test_dataprocessor_get_total_sales_empty():
    """Test DataProcessor.get_total_sales returns 0 for no records."""
    processor = DataProcessor(records=[])
    total = processor.get_total_sales()
    assert total == pytest.approx(0.0)


def test_dataprocessor_get_average_sale_non_empty(data_processor_instance):
    """Test DataProcessor.get_average_sale returns correct average."""
    avg = data_processor_instance.get_average_sale()
    expected = sum(r.amount for r in data_processor_instance.records) / len(
        data_processor_instance.records
    )
    assert avg == pytest.approx(expected)


def test_dataprocessor_get_average_sale_empty():
    """Test DataProcessor.get_average_sale returns 0 when there are no records."""
    processor = DataProcessor(records=[])
    avg = processor.get_average_sale()
    assert avg == pytest.approx(0.0)


def test_dataprocessor_group_by_region_groups_correctly(data_processor_instance):
    """Test DataProcessor.group_by_region groups records by region."""
    grouped = data_processor_instance.group_by_region()
    # Ensure all regions are present as keys
    regions = {r.region for r in data_processor_instance.records}
    assert regions == set(grouped.keys())

    # Ensure each record appears under its region
    for region, records in grouped.items():
        assert all(r.region == region for r in records)


def test_dataprocessor_group_by_region_empty():
    """Test DataProcessor.group_by_region with no records returns empty dict."""
    processor = DataProcessor(records=[])
    grouped = processor.group_by_region()
    assert grouped == {}


def test_dataprocessor_get_top_products_default_limit(data_processor_instance):
    """Test DataProcessor.get_top_products returns top products by total sales with default limit."""
    top_products = data_processor_instance.get_top_products()
    # Ensure sorted by total sales descending
    totals = dict()
    for r in data_processor_instance.records:
        totals[r.product] = totals.get(r.product, 0.0) + r.amount

    expected_sorted = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    # Only first 5 or fewer
    assert top_products == expected_sorted[:5]


def test_dataprocessor_get_top_products_custom_limit(data_processor_instance):
    """Test DataProcessor.get_top_products respects custom limit."""
    limit = 2
    top_products = data_processor_instance.get_top_products(limit=limit)
    assert len(top_products) <= limit


def test_dataprocessor_get_top_products_limit_exceeds_products(data_processor_instance):
    """Test DataProcessor.get_top_products when limit exceeds number of products."""
    total_unique_products = len({r.product for r in data_processor_instance.records})
    top_products = data_processor_instance.get_top_products(limit=total_unique_products + 10)
    assert len(top_products) == total_unique_products


def test_dataprocessor_get_top_products_empty():
    """Test DataProcessor.get_top_products returns empty list when no records."""
    processor = DataProcessor(records=[])
    top_products = processor.get_top_products()
    assert top_products == []


def test_dataprocessor_process_records_parallel_threshold_filters(sample_sales_records):
    """Test DataProcessor.process_records_parallel filters records over threshold."""
    processor = DataProcessor(records=sample_sales_records)
    threshold = 60.0
    results = processor.process_records_parallel(threshold=threshold)
    assert all(r.amount > threshold for r in results)
    expected = [r for r in sample_sales_records if r.amount > threshold]
    # Order is not guaranteed due to threading; compare as sets of ids
    assert {r.record_id for r in results} == {r.record_id for r in expected}


def test_dataprocessor_process_records_parallel_empty():
    """Test DataProcessor.process_records_parallel with no records returns empty list."""
    processor = DataProcessor(records=[])
    results = processor.process_records_parallel(threshold=10.0)
    assert results == []


def test_dataprocessor_process_records_parallel_chunk_size_lt_4():
    """Test DataProcessor.process_records_parallel uses chunk size 1 when len < 4."""
    records = [
        SalesRecord(1, "A", 5.0, "2024-01-01", "X"),
        SalesRecord(2, "B", 15.0, "2024-01-02", "Y"),
        SalesRecord(3, "C", 25.0, "2024-01-03", "Z"),
    ]
    processor = DataProcessor(records=records)
    results = processor.process_records_parallel(threshold=10.0)
    expected_ids = {2, 3}
    assert {r.record_id for r in results} == expected_ids


def test_dataprocessor_process_records_parallel_exception_in_thread():
    """Test DataProcessor.process_records_parallel propagates exceptions from thread target."""
    bad_record = SalesRecord(99, "Bad", 100.0, "2024-01-01", "X")
    processor = DataProcessor(records=[bad_record])

    original_thread = __import__("threading").Thread

    def failing_process_chunk(_chunk):
        raise RuntimeError("Processing failed")

    with patch("threading.Thread") as mock_thread_cls:
        thread_instance = Mock()
        # side_effect on start to simulate raising inside thread.run
        def start_side_effect():
            raise RuntimeError("Processing failed")

        thread_instance.start.side_effect = start_side_effect
        mock_thread_cls.return_value = thread_instance

        with pytest.raises(RuntimeError):
            processor.process_records_parallel(threshold=10.0)