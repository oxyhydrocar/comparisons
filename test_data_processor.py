import pytest
from unittest.mock import patch, MagicMock
from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sample_sales_records():
    """Create a list of SalesRecord instances for testing."""
    return [
        SalesRecord(record_id=1, product="A", amount=100.0, date="2024-01-01", region="North"),
        SalesRecord(record_id=2, product="B", amount=50.5, date="2024-01-02", region="South"),
        SalesRecord(record_id=3, product="A", amount=200.75, date="2024-01-03", region="North"),
        SalesRecord(record_id=4, product="C", amount=10.0, date="2024-01-04", region="East"),
        SalesRecord(record_id=5, product="B", amount=150.25, date="2024-01-05", region="West"),
    ]


@pytest.fixture
def data_processor_instance(sample_sales_records):
    """Create a DataProcessor instance with sample records."""
    return DataProcessor(records=sample_sales_records)


# ---------------------- SalesRecord tests ----------------------


def test_SalesRecord_init_valid():
    """Test SalesRecord initialization with valid data."""
    record = SalesRecord(record_id=1, product="Widget", amount=123.45, date="2024-01-01", region="EMEA")
    assert record.record_id == 1
    assert record.product == "Widget"
    assert record.amount == pytest.approx(123.45)
    assert record.date == "2024-01-01"
    assert record.region == "EMEA"


def test_SalesRecord_to_dict_round_trip():
    """Test SalesRecord.to_dict returns correct dictionary representation."""
    record = SalesRecord(record_id=10, product="Gadget", amount=42.0, date="2024-02-01", region="NA")
    record_dict = record.to_dict()
    assert record_dict == {
        "record_id": 10,
        "product": "Gadget",
        "amount": 42.0,
        "date": "2024-02-01",
        "region": "NA",
    }


def test_SalesRecord_from_dict_uses_v_correctly():
    """Test SalesRecord.from_dict uses utils.v with correct parameters and values."""
    data = {
        "record_id": 7,
        "product": "Thing",
        "amount": 99.9,
        "date": "2024-03-01",
        "region": "APAC",
    }

    with patch("data_processor.v") as mock_v:
        # Configure side effects to return values in order of calls
        mock_v.side_effect = [7, "Thing", 99.9, "2024-03-01", "APAC"]

        record = SalesRecord.from_dict(data)

        # Ensure v was called with expected arguments
        expected_calls = [
            ((data, "record_id", "i"),),
            ((data, "product", "s"),),
            ((data, "amount", "f"),),
            ((data, "date", "s"),),
            ((data, "region", "s"),),
        ]
        actual_calls = mock_v.call_args_list
        assert len(actual_calls) == len(expected_calls)
        for actual, expected in zip(actual_calls, expected_calls):
            assert actual[0] == expected[0]

        assert isinstance(record, SalesRecord)
        assert record.record_id == 7
        assert record.product == "Thing"
        assert record.amount == pytest.approx(99.9)
        assert record.date == "2024-03-01"
        assert record.region == "APAC"


def test_SalesRecord_from_dict_exception_propagation():
    """Test SalesRecord.from_dict propagates exceptions raised by utils.v."""
    data = {"record_id": "bad"}

    with patch("data_processor.v") as mock_v:
        mock_v.side_effect = ValueError("Invalid type")

        with pytest.raises(ValueError):
            SalesRecord.from_dict(data)


# ---------------------- DataProcessor tests ----------------------


def test_DataProcessor_init_assigns_records(sample_sales_records):
    """Test DataProcessor initialization correctly assigns records."""
    processor = DataProcessor(records=sample_sales_records)
    assert processor.records is sample_sales_records


def test_DataProcessor_sort_by_amount_sorts_ascending(data_processor_instance):
    """Test sort_by_amount sorts records by amount in ascending order using bubble sort."""
    sorted_records = data_processor_instance.sort_by_amount()
    amounts = [r.amount for r in sorted_records]
    assert amounts == sorted(amounts)


def test_DataProcessor_sort_by_amount_stable_for_equal_amounts():
    """Test sort_by_amount stability when records have equal amounts."""
    records = [
        SalesRecord(1, "A", 10.0, "2024-01-01", "R1"),
        SalesRecord(2, "B", 10.0, "2024-01-02", "R2"),
        SalesRecord(3, "C", 10.0, "2024-01-03", "R3"),
    ]
    processor = DataProcessor(records)
    sorted_records = processor.sort_by_amount()
    ids = [r.record_id for r in sorted_records]
    assert ids == [1, 2, 3]


def test_DataProcessor_sort_by_amount_empty_list():
    """Test sort_by_amount returns empty list when there are no records."""
    processor = DataProcessor(records=[])
    sorted_records = processor.sort_by_amount()
    assert sorted_records == []


def test_DataProcessor_filter_by_region_existing(data_processor_instance):
    """Test filter_by_region returns only records matching specified region."""
    north_records = data_processor_instance.filter_by_region("North")
    assert len(north_records) == 2
    assert all(r.region == "North" for r in north_records)


def test_DataProcessor_filter_by_region_non_existing(data_processor_instance):
    """Test filter_by_region with a region that has no records returns empty list."""
    records = data_processor_instance.filter_by_region("NonExisting")
    assert records == []


def test_DataProcessor_filter_by_product_existing(data_processor_instance):
    """Test filter_by_product returns only records matching specified product."""
    product_a_records = data_processor_instance.filter_by_product("A")
    assert len(product_a_records) == 2
    assert all(r.product == "A" for r in product_a_records)


def test_DataProcessor_filter_by_product_non_existing(data_processor_instance):
    """Test filter_by_product with a product that has no records returns empty list."""
    records = data_processor_instance.filter_by_product("NonExistingProduct")
    assert records == []


def test_DataProcessor_get_total_sales_correct_sum(data_processor_instance):
    """Test get_total_sales returns the correct sum of all record amounts."""
    expected_total = sum(r.amount for r in data_processor_instance.records)
    total = data_processor_instance.get_total_sales()
    assert total == pytest.approx(expected_total)


def test_DataProcessor_get_total_sales_empty():
    """Test get_total_sales returns 0 when there are no records."""
    processor = DataProcessor(records=[])
    total = processor.get_total_sales()
    assert total == pytest.approx(0.0)


def test_DataProcessor_get_average_sale_non_empty(data_processor_instance):
    """Test get_average_sale returns correct average for non-empty records."""
    total = sum(r.amount for r in data_processor_instance.records)
    expected_average = total / len(data_processor_instance.records)
    avg = data_processor_instance.get_average_sale()
    assert avg == pytest.approx(expected_average)


def test_DataProcessor_get_average_sale_empty():
    """Test get_average_sale returns 0 for empty records list."""
    processor = DataProcessor(records=[])
    avg = processor.get_average_sale()
    assert avg == pytest.approx(0.0)


def test_DataProcessor_group_by_region_groups_correctly(data_processor_instance):
    """Test group_by_region groups records under their respective regions."""
    grouped = data_processor_instance.group_by_region()
    expected_regions = {r.region for r in data_processor_instance.records}
    assert set(grouped.keys()) == expected_regions
    for region, records in grouped.items():
        assert all(r.region == region for r in records)


def test_DataProcessor_group_by_region_empty():
    """Test group_by_region returns empty dict when there are no records."""
    processor = DataProcessor(records=[])
    grouped = processor.group_by_region()
    assert grouped == {}


def test_DataProcessor_get_top_products_default_limit(data_processor_instance):
    """Test get_top_products returns top 5 products by total amount (or fewer if less products)."""
    top_products = data_processor_instance.get_top_products()
    product_sales = {}
    for r in data_processor_instance.records:
        product_sales[r.product] = product_sales.get(r.product, 0) + r.amount
    expected_sorted = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    assert top_products == expected_sorted[:5]


def test_DataProcessor_get_top_products_custom_limit(data_processor_instance):
    """Test get_top_products respects the custom limit parameter."""
    limit = 2
    top_products = data_processor_instance.get_top_products(limit=limit)
    product_sales = {}
    for r in data_processor_instance.records:
        product_sales[r.product] = product_sales.get(r.product, 0) + r.amount
    expected_sorted = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    assert top_products == expected_sorted[:limit]
    assert len(top_products) <= limit


def test_DataProcessor_get_top_products_more_limit_than_products(data_processor_instance):
    """Test get_top_products when limit is greater than distinct products returns all products."""
    limit = 10
    top_products = data_processor_instance.get_top_products(limit=limit)
    product_sales = {}
    for r in data_processor_instance.records:
        product_sales[r.product] = product_sales.get(r.product, 0) + r.amount
    expected_sorted = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    assert top_products == expected_sorted
    assert len(top_products) == len(expected_sorted)


def test_DataProcessor_process_records_parallel_threshold_filtering(data_processor_instance):
    """Test process_records_parallel returns records above the given threshold."""
    threshold = 100.0
    results = data_processor_instance.process_records_parallel(threshold)
    assert all(r.amount > threshold for r in results)
    expected = [r for r in data_processor_instance.records if r.amount > threshold]
    result_ids = {r.record_id for r in results}
    expected_ids = {r.record_id for r in expected}
    assert result_ids == expected_ids


def test_DataProcessor_process_records_parallel_with_small_number_of_records():
    """Test process_records_parallel behavior when record count is less than 4."""
    records = [
        SalesRecord(1, "A", 5.0, "2024-01-01", "R1"),
        SalesRecord(2, "B", 15.0, "2024-01-02", "R2"),
        SalesRecord(3, "C", 25.0, "2024-01-03", "R3"),
    ]
    processor = DataProcessor(records)
    threshold = 10.0
    results = processor.process_records_parallel(threshold)
    expected = [r for r in records if r.amount > threshold]
    assert {r.record_id for r in results} == {r.record_id for r in expected}


def test_DataProcessor_process_records_parallel_empty_records():
    """Test process_records_parallel returns empty list when there are no records."""
    processor = DataProcessor(records=[])
    results = processor.process_records_parallel(threshold=10.0)
    assert results == []


def test_DataProcessor_process_records_parallel_threading_called():
    """Test process_records_parallel creates and starts threads."""
    records = [
        SalesRecord(1, "A", 100.0, "2024-01-01", "R1"),
        SalesRecord(2, "B", 200.0, "2024-01-02", "R2"),
        SalesRecord(3, "C", 300.0, "2024-01-03", "R3"),
        SalesRecord(4, "D", 400.0, "2024-01-04", "R4"),
    ]
    processor = DataProcessor(records)

    with patch("data_processor.threading.Thread") as mock_thread_cls:
        # Configure thread mock so that start and join don't do real threading
        thread_instance = MagicMock()
        mock_thread_cls.return_value = thread_instance

        processor.process_records_parallel(threshold=50.0)

        # There should be at least one thread started
        assert mock_thread_cls.call_count >= 1
        assert thread_instance.start.call_count == mock_thread_cls.call_count
        assert thread_instance.join.call_count == mock_thread_cls.call_count
