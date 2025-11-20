import sys
import types
from unittest.mock import Mock, patch, call
import pytest

# Create a dummy 'utils' module with a v function to satisfy data_processor import
utils_module = types.ModuleType("utils")


def v(data, key, typ):
    # Minimal type conversion based on typ spec used in SalesRecord.from_dict
    val = data[key]
    if typ == 'i':
        return int(val)
    if typ == 'f':
        return float(val)
    if typ == 's':
        return str(val)
    return val


utils_module.v = v
sys.modules['utils'] = utils_module

from data_processor import SalesRecord, DataProcessor


@pytest.fixture
def sample_records():
    """Create a list of SalesRecord instances for testing."""
    return [
        SalesRecord(record_id=1, product="Widget", amount=100.0, date="2025-01-01", region="North"),
        SalesRecord(record_id=2, product="Gadget", amount=50.0, date="2025-01-02", region="South"),
        SalesRecord(record_id=3, product="Widget", amount=200.0, date="2025-01-03", region="East"),
        SalesRecord(record_id=4, product="Thingamajig", amount=150.0, date="2025-01-04", region="North"),
        SalesRecord(record_id=5, product="Gizmo", amount=75.0, date="2025-01-05", region="West"),
    ]


@pytest.fixture
def data_processor_all(sample_records):
    """Create a DataProcessor containing all sample records."""
    return DataProcessor(records=sample_records)


@pytest.fixture
def data_processor_empty():
    """Create a DataProcessor with no records."""
    return DataProcessor(records=[])


def test_salesrecord_init_and_to_dict():
    """Test SalesRecord initialization and to_dict output."""
    record = SalesRecord(record_id=42, product="Widget", amount=123.45, date="2025-10-10", region="EMEA")
    d = record.to_dict()
    assert d == {
        'record_id': 42,
        'product': "Widget",
        'amount': 123.45,
        'date': "2025-10-10",
        'region': "EMEA",
    }


def test_salesrecord_from_dict_parses_values_with_dummy_v():
    """Test SalesRecord.from_dict returns a SalesRecord with converted types using dummy utils.v."""
    data = {
        'record_id': "10",
        'product': 777,  # should be converted to str
        'amount': "99.9",
        'date': 20250101,  # should be converted to str
        'region': b"APAC",  # should be converted to str
    }
    record = SalesRecord.from_dict(data)
    assert isinstance(record, SalesRecord)
    assert record.record_id == 10
    assert record.product == "777"
    assert record.amount == pytest.approx(99.9)
    assert record.date == "20250101"
    assert record.region == "b'APAC'"  # str() of bytes in dummy v


@patch('data_processor.v')
def test_salesrecord_from_dict_uses_v_calls_and_order(mock_v):
    """Test SalesRecord.from_dict calls utils.v for each field with correct arguments and order."""
    # Configure mock to pass through values for simplicity
    def side_effect(data, key, typ):
        mapping = {
            'record_id': 123,
            'product': "Widget",
            'amount': 456.78,
            'date': "2025-02-02",
            'region': "North",
        }
        return mapping[key]

    mock_v.side_effect = side_effect
    payload = {'record_id': 'x', 'product': 'y', 'amount': 'z', 'date': 'd', 'region': 'r'}

    record = SalesRecord.from_dict(payload)

    # Verify call order and parameters
    expected_calls = [
        call(payload, 'record_id', 'i'),
        call(payload, 'product', 's'),
        call(payload, 'amount', 'f'),
        call(payload, 'date', 's'),
        call(payload, 'region', 's'),
    ]
    assert mock_v.call_args_list == expected_calls

    # Verify returned values are from mock
    assert record.record_id == 123
    assert record.product == "Widget"
    assert record.amount == pytest.approx(456.78)
    assert record.date == "2025-02-02"
    assert record.region == "North"


@patch('data_processor.v', side_effect=KeyError("amount"))
def test_salesrecord_from_dict_raises_when_v_fails(mock_v):
    """Test SalesRecord.from_dict propagates exceptions from utils.v (e.g., missing keys)."""
    payload = {'record_id': 1, 'product': 'Widget', 'amount': 100, 'date': '2025-01-01', 'region': 'North'}
    with pytest.raises(KeyError):
        SalesRecord.from_dict(payload)


def test_dataprocessor_init_and_records_property(sample_records):
    """Test DataProcessor initialization stores records."""
    dp = DataProcessor(records=sample_records)
    assert dp.records == sample_records
    assert len(dp.records) == 5


def test_dataprocessor_sort_by_amount_returns_new_sorted_list(data_processor_all, sample_records):
    """Test sort_by_amount returns ascending order without mutating original records."""
    original_ids = [r.record_id for r in data_processor_all.records]
    sorted_records = data_processor_all.sort_by_amount()
    sorted_amounts = [r.amount for r in sorted_records]

    assert sorted_amounts == sorted(sorted_amounts)
    # Original order unchanged
    assert [r.record_id for r in data_processor_all.records] == original_ids
    # Returned list is a different object
    assert sorted_records is not data_processor_all.records


def test_dataprocessor_filter_by_region_matches_exact(data_processor_all):
    """Test filter_by_region returns only records from the specified region."""
    north = data_processor_all.filter_by_region("North")
    assert all(r.region == "North" for r in north)
    # Count expected: record_id 1 and 4 in fixture
    assert sorted(r.record_id for r in north) == [1, 4]

    none = data_processor_all.filter_by_region("Nonexistent")
    assert none == []


def test_dataprocessor_filter_by_product_matches_exact(data_processor_all):
    """Test filter_by_product returns only records for the specified product."""
    widget = data_processor_all.filter_by_product("Widget")
    assert all(r.product == "Widget" for r in widget)
    assert sorted(r.record_id for r in widget) == [1, 3]


def test_dataprocessor_get_total_and_average(data_processor_all):
    """Test get_total_sales and get_average_sale return correct values."""
    total = data_processor_all.get_total_sales()
    avg = data_processor_all.get_average_sale()
    amounts = [100.0, 50.0, 200.0, 150.0, 75.0]
    assert total == pytest.approx(sum(amounts))
    assert avg == pytest.approx(sum(amounts) / len(amounts))


def test_dataprocessor_get_average_empty(data_processor_empty):
    """Test get_average_sale returns 0 for empty dataset."""
    assert data_processor_empty.get_average_sale() == 0


def test_dataprocessor_group_by_region_groups_correctly(data_processor_all):
    """Test group_by_region returns a dict of regions mapped to their records."""
    grouped = data_processor_all.group_by_region()
    assert set(grouped.keys()) == {"North", "South", "East", "West"}
    assert sorted(r.record_id for r in grouped["North"]) == [1, 4]
    assert [r.record_id for r in grouped["South"]] == [2]
    assert [r.record_id for r in grouped["East"]] == [3]
    assert [r.record_id for r in grouped["West"]] == [5]


def test_dataprocessor_get_top_products_aggregation_and_limit():
    """Test get_top_products aggregates sales by product and respects the limit."""
    records = [
        SalesRecord(1, "A", 100, "d", "R1"),
        SalesRecord(2, "B", 200, "d", "R1"),
        SalesRecord(3, "A", 150, "d", "R2"),
        SalesRecord(4, "C", 50, "d", "R2"),
        SalesRecord(5, "B", 25, "d", "R3"),
        SalesRecord(6, "D", 500, "d", "R3"),
    ]
    dp = DataProcessor(records)
    top3 = dp.get_top_products(limit=3)
    # Totals: A=250, B=225, C=50, D=500 => order D, A, B
    assert top3 == [("D", 500), ("A", 250), ("B", 225)]

    # Limit larger than unique products should return all sorted
    top10 = dp.get_top_products(limit=10)
    assert top10 == [("D", 500), ("A", 250), ("B", 225), ("C", 50)]


def test_dataprocessor_get_top_products_limit_zero():
    """Test get_top_products with limit 0 returns an empty list."""
    dp = DataProcessor([
        SalesRecord(1, "A", 10, "d", "R"),
        SalesRecord(2, "B", 20, "d", "R"),
    ])
    assert dp.get_top_products(limit=0) == []


def test_dataprocessor_process_records_parallel_returns_records_above_threshold():
    """Test process_records_parallel returns records with amount strictly greater than threshold using real threads."""
    records = [
        SalesRecord(1, "A", 10, "d", "R"),
        SalesRecord(2, "B", 20, "d", "R"),
        SalesRecord(3, "C", 30, "d", "R"),
        SalesRecord(4, "D", 40, "d", "R"),
        SalesRecord(5, "E", 50, "d", "R"),
    ]
    dp = DataProcessor(records)
    res = dp.process_records_parallel(threshold=30)
    # Expect amounts > 30 => 40 and 50
    assert set(r.record_id for r in res) == {4, 5}
    # Threshold equal to amount should not include
    res2 = dp.process_records_parallel(threshold=50)
    assert res2 == []


def test_dataprocessor_process_records_parallel_empty_and_threshold_edge(data_processor_empty):
    """Test process_records_parallel with empty records and threshold equal to amounts edge case."""
    assert data_processor_empty.process_records_parallel(threshold=0) == []

    records = [
        SalesRecord(1, "A", 100, "d", "R"),
        SalesRecord(2, "B", 100, "d", "R"),
        SalesRecord(3, "C", 99.99, "d", "R"),
    ]
    dp = DataProcessor(records)
    res = dp.process_records_parallel(threshold=100)
    # Strictly greater than threshold, so none with 100 included
    assert set(r.record_id for r in res) == set()


def test_dataprocessor_process_records_parallel_threads_are_used_and_chunks_processed():
    """Test process_records_parallel uses threading with expected chunking and processes each chunk."""
    # Use 8 records so that chunk_size = len // 4 = 2 => 4 threads
    records = [
        SalesRecord(i, f"P{i}", i * 10, "d", "R")
        for i in range(1, 9)
    ]  # amounts: 10..80
    dp = DataProcessor(records)

    created_threads = []

    class DummyThread:
        def __init__(self, target, args):
            self._target = target
            self._args = args
            created_threads.append(self)

        def start(self):
            # Immediately process to avoid real concurrency
            self._target(*self._args)

        def join(self):
            pass

    def thread_side_effect(target, args):
        return DummyThread(target, args)

    with patch('data_processor.threading.Thread', side_effect=thread_side_effect) as mock_thread_cls:
        result = dp.process_records_parallel(threshold=35)

        # Verify 4 threads created with correct chunk args
        assert mock_thread_cls.call_count == 4
        # Expected chunks: [1,2], [3,4], [5,6], [7,8] based on amounts 10..80
        expected_chunks = [
            records[0:2],
            records[2:4],
            records[4:6],
            records[6:8],
        ]
        actual_chunks = [args.kwargs.get('args', args.args)[0] if hasattr(args, 'kwargs') else call_args[1]['args'][0]
                         for call_args in []]  # placeholder to keep code structure consistent

        # Validate constructor calls captured arguments
        calls = mock_thread_cls.call_args_list
        for idx, c in enumerate(calls):
            # c is a call object; c.args is (target, args); args is tuple with (chunk,)
            _, ctor_args = c
            # In Python versions, call has .args attr; fall back to index access from tuple if needed
            if hasattr(c, 'args') and c.args:
                ctor_args_tuple = c.args
            else:
                # For compatibility with older pytest/mock versions
                ctor_args_tuple = ctor_args.get('args', ())
                if not ctor_args_tuple:
                    # direct parameter mapping
                    ctor_args_tuple = (ctor_args.get('target'), ctor_args.get('args'))

            chunk_passed = ctor_args_tuple[1][0]
            assert chunk_passed == expected_chunks[idx]

        # Verify results are amounts > 35 => record_id 4..8
        assert set(r.record_id for r in result) == {4, 5, 6, 7, 8}