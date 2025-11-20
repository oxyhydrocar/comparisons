import json
from datetime import datetime
from unittest.mock import patch

import pytest

from utils import (
    load_data_from_file,
    save_data_to_file,
    format_currency,
    parse_date,
    v,
    get_date_range,
)


@pytest.fixture
def sample_data():
    """Provide sample JSON-serializable data for tests."""
    return [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]


def test_load_data_from_file_nonexistent_returns_empty_with_mock():
    """load_data_from_file should return [] when file does not exist."""
    with patch("utils.os.path.exists", return_value=False) as exists_mock:
        result = load_data_from_file("does_not_exist.json")
        exists_mock.assert_called_once()
    assert result == []


def test_load_data_from_file_reads_json_from_tempfile(tmp_path, sample_data):
    """load_data_from_file should read and parse a JSON file successfully."""
    fp = tmp_path / "data.json"
    with fp.open("w") as f:
        json.dump(sample_data, f)

    result = load_data_from_file(str(fp))
    assert result == sample_data


def test_load_data_from_file_invalid_json_raises(tmp_path):
    """load_data_from_file should raise JSONDecodeError on invalid JSON content."""
    fp = tmp_path / "bad.json"
    fp.write_text("{invalid json}")

    with pytest.raises(json.JSONDecodeError):
        load_data_from_file(str(fp))


def test_save_data_to_file_calls_makedirs_and_writes_json(tmp_path, sample_data):
    """save_data_to_file should create directories, write JSON, and use indent=2."""
    target_dir = tmp_path / "nested"
    target_dir.mkdir(parents=True, exist_ok=True)
    fp = target_dir / "out.json"

    with patch("utils.os.makedirs") as makedirs_mock:
        save_data_to_file(str(fp), sample_data)
        # Assert makedirs called with directory path and exist_ok=True
        assert makedirs_mock.call_count == 1
        called_dir = makedirs_mock.call_args[0][0]
        called_kwargs = makedirs_mock.call_args.kwargs
        assert called_dir == str(target_dir)
        assert called_kwargs.get("exist_ok") is True

    # Verify file was written and content is valid JSON
    with fp.open("r") as f:
        content = f.read()
        # Indentation suggests pretty-printed JSON
        assert content.startswith("{\n") or content.startswith("[\n")
        loaded = json.loads(content)
        assert loaded == sample_data


@pytest.mark.parametrize(
    "amount,expected",
    [
        (0, "$0.00"),
        (1, "$1.00"),
        (1000, "$1,000.00"),
        (1234.5, "$1,234.50"),
        (-2.5, "$-2.50"),
        (1000000.125, "$1,000,000.12"),
    ],
)
def test_format_currency_various_values(amount, expected):
    """format_currency should format numbers with dollar sign, grouping, and 2 decimals."""
    assert format_currency(amount) == expected


def test_format_currency_raises_for_non_numeric_string():
    """format_currency should raise when given a non-numeric string."""
    with pytest.raises((TypeError, ValueError)):
        format_currency("not-a-number")


@pytest.mark.parametrize(
    "date_string,expected",
    [
        ("2021-03-15", datetime(2021, 3, 15)),
        ("1999-12-31", datetime(1999, 12, 31)),
        ("invalid-date", None),
        ("2021-02-30", None),
        ("", None),
    ],
)
def test_parse_date_various_inputs(date_string, expected):
    """parse_date should return datetime for valid YYYY-MM-DD strings, None otherwise."""
    result = parse_date(date_string)
    assert result == expected


@pytest.mark.parametrize(
    "data,key,type_code,expected",
    [
        ({"a": "10"}, "a", "i", 10),
        ({"a": "bad"}, "a", "i", None),
        ({"a": 3.5}, "a", "f", 3.5),
        ({"a": "3.14"}, "a", "f", 3.14),
        ({"a": None}, "a", "i", None),
        ({"a": 10}, "a", "s", "10"),
        ({"a": "x"}, "missing", "s", None),
        ({"a": 7}, "a", "x", 7),
    ],
)
def test_v_type_conversion_cases(data, key, type_code, expected):
    """v should convert values based on type code or return None/unchanged appropriately."""
    assert v(data, key, type_code) == expected


@pytest.mark.parametrize(
    "start,end,expected_days",
    [
        ("2020-01-01", "2020-01-10", 9),
        ("2020-01-10", "2020-01-01", -9),
        ("2020-01-01", "2020-01-01", 0),
    ],
)
def test_get_date_range_with_strings(start, end, expected_days):
    """get_date_range should compute day difference between parsed date strings."""
    assert get_date_range(start, end) == expected_days


def test_get_date_range_with_datetimes():
    """get_date_range should compute day difference between datetime objects."""
    start_dt = datetime(2020, 1, 1)
    end_dt = datetime(2020, 1, 2)
    assert get_date_range(start_dt, end_dt) == 1


@pytest.mark.parametrize(
    "start,end",
    [
        ("invalid", "2020-01-01"),
        ("2020-01-01", "invalid"),
        ("invalid", "also-bad"),
    ],
)
def test_get_date_range_returns_zero_when_unparseable(start, end):
    """get_date_range should return 0 when either start or end cannot be parsed."""
    assert get_date_range(start, end) == 0