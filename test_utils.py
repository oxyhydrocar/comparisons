import json
import os
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
    """Provide sample data for JSON operations."""
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


@pytest.fixture
def json_file_path(tmp_path, sample_data):
    """Create a temporary JSON file with sample_data and return its path."""
    d = tmp_path / "data"
    d.mkdir()
    p = d / "sample.json"
    with open(p, "w") as f:
        json.dump(sample_data, f)
    return p


def test_load_data_from_file_nonexistent_returns_empty_list(tmp_path):
    """load_data_from_file should return empty list when file does not exist."""
    fake_path = tmp_path / "nonexistent.json"
    with patch("utils.os.path.exists", return_value=False):
        result = load_data_from_file(str(fake_path))
    assert result == []


def test_load_data_from_file_reads_valid_json(json_file_path, sample_data):
    """load_data_from_file should read and return JSON content."""
    result = load_data_from_file(str(json_file_path))
    assert result == sample_data


def test_load_data_from_file_invalid_json_raises_json_decode_error(tmp_path):
    """load_data_from_file should propagate JSON decoding errors for invalid content."""
    p = tmp_path / "bad.json"
    p.write_text("{invalid json}")
    with pytest.raises(json.JSONDecodeError):
        load_data_from_file(str(p))


def test_save_data_to_file_writes_json_and_creates_directory(tmp_path, sample_data):
    """save_data_to_file should create directories and write JSON data."""
    dest_dir = tmp_path / "nested" / "path"
    dest_file = dest_dir / "out.json"
    with patch("utils.os.makedirs", wraps=os.makedirs) as makedirs_spy:
        save_data_to_file(str(dest_file), sample_data)
        makedirs_spy.assert_called_once()
        args, kwargs = makedirs_spy.call_args
        assert args[0] == str(dest_dir)
        assert kwargs.get("exist_ok") is True

    # Verify content was written correctly
    with open(dest_file, "r") as f:
        data = json.load(f)
    assert data == sample_data


def test_save_data_to_file_raises_on_permission_error(tmp_path, sample_data):
    """save_data_to_file should propagate exceptions from os.makedirs."""
    dest_file = tmp_path / "noaccess" / "out.json"
    with patch("utils.os.makedirs", side_effect=PermissionError("no permission")):
        with pytest.raises(PermissionError):
            save_data_to_file(str(dest_file), sample_data)


@pytest.mark.parametrize(
    "amount,expected",
    [
        (0, "$0.00"),
        (1234, "$1,234.00"),
        (1234.5, "$1,234.50"),
        (1000000.987, "$1,000,000.99"),
        (-5, "$-5.00"),
        (-1234.56, "$-1,234.56"),
    ],
)
def test_format_currency_various_inputs(amount, expected):
    """format_currency should format amounts with currency symbol, commas, and two decimals."""
    assert format_currency(amount) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("2023-01-31", datetime(2023, 1, 31)),
        ("1999-12-01", datetime(1999, 12, 1)),
    ],
)
def test_parse_date_valid_iso_yyyy_mm_dd(input_str, expected):
    """parse_date should parse valid YYYY-MM-DD date strings into datetime."""
    result = parse_date(input_str)
    assert isinstance(result, datetime)
    assert result == expected


@pytest.mark.parametrize(
    "input_str",
    [
        "31-01-2023",
        "2023/01/31",
        "invalid",
        "",
        "2023-02-30",
    ],
)
def test_parse_date_invalid_returns_none(input_str):
    """parse_date should return None for invalid or unsupported date strings."""
    assert parse_date(input_str) is None


@pytest.mark.parametrize(
    "d,k,t,expected",
    [
        ({"a": "123"}, "a", "i", 123),
        ({"a": "abc"}, "a", "i", None),
        ({"a": 1.23}, "a", "s", "1.23"),
        ({"a": "1.5"}, "a", "f", 1.5),
        ({"a": "abc"}, "a", "f", None),
        ({}, "missing", "s", None),
        ({"a": "value"}, "a", "x", "value"),
        ({"a": None}, "a", "i", None),
    ],
)
def test_v_extract_and_convert_types(d, k, t, expected):
    """v should extract values and convert to desired types, handling errors gracefully."""
    result = v(d, k, t)
    if isinstance(expected, float) and str(expected) == "nan":
        assert result != result  # NaN is not equal to itself
    else:
        assert result == expected


def test_get_date_range_with_valid_strings():
    """get_date_range should return the number of days between two valid dates."""
    assert get_date_range("2023-01-01", "2023-01-10") == 9


def test_get_date_range_same_day_returns_zero():
    """get_date_range should return zero when start and end are the same date."""
    assert get_date_range("2023-01-01", "2023-01-01") == 0


def test_get_date_range_reversed_dates_negative():
    """get_date_range should return negative number when start is after end."""
    assert get_date_range("2023-01-10", "2023-01-01") == -9


def test_get_date_range_with_datetime_objects():
    """get_date_range should work when datetime objects are provided."""
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 5)
    assert get_date_range(start, end) == 4


def test_get_date_range_with_invalid_inputs_returns_zero():
    """get_date_range should return zero when dates cannot be parsed."""
    assert get_date_range("invalid", "2023-01-01") == 0
    assert get_date_range("2023-01-01", "invalid") == 0
    assert get_date_range("invalid", "also invalid") == 0