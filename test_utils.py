import json
import os
from datetime import datetime
from unittest.mock import patch, mock_open

import pytest

from utils import load_data_from_file, save_data_to_file, format_currency, parse_date, v, get_date_range


@pytest.fixture
def sample_json_data():
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


def test_load_data_from_file_nonexistent_returns_empty_list():
    """load_data_from_file should return an empty list when the file does not exist."""
    with patch("utils.os.path.exists", return_value=False):
        result = load_data_from_file("nonexistent.json")
        assert result == []


def test_load_data_from_file_reads_valid_json(tmp_path, sample_json_data):
    """load_data_from_file should return parsed JSON content for an existing file."""
    p = tmp_path / "data.json"
    p.write_text(json.dumps(sample_json_data), encoding="utf-8")

    result = load_data_from_file(str(p))
    assert result == sample_json_data


def test_load_data_from_file_raises_on_invalid_json(tmp_path):
    """load_data_from_file should propagate json.JSONDecodeError on invalid JSON content."""
    p = tmp_path / "bad.json"
    p.write_text("{ invalid json ", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_data_from_file(str(p))


def test_save_data_to_file_creates_directories_and_writes_json(tmp_path, sample_json_data):
    """save_data_to_file should create directories and write the given JSON content."""
    nested_dir = tmp_path / "nested" / "deeper"
    filepath = nested_dir / "output.json"

    save_data_to_file(str(filepath), sample_json_data)

    assert filepath.exists()
    content = json.loads(filepath.read_text(encoding="utf-8"))
    assert content == sample_json_data


def test_save_data_to_file_calls_makedirs_and_json_dump():
    """save_data_to_file should call os.makedirs with exist_ok=True and json.dump with indent=2."""
    data = {"x": 1}
    path = "dir/file.json"

    with patch("utils.os.makedirs") as makedirs_mock, \
         patch("utils.open", mock_open()) as mopen, \
         patch("utils.json.dump") as json_dump_mock:
        save_data_to_file(path, data)

        makedirs_mock.assert_called_once_with(os.path.dirname(path), exist_ok=True)
        mopen.assert_called_once_with(path, "w")
        # Ensure json.dump called with indent=2
        assert json_dump_mock.call_args.kwargs.get("indent") == 2
        # Ensure data passed through
        assert json_dump_mock.call_args.args[0] == data


@pytest.mark.parametrize(
    "amount,expected",
    [
        (0, "$0.00"),
        (12, "$12.00"),
        (12.3, "$12.30"),
        (1234.5, "$1,234.50"),
        (-9876.543, "$-9,876.54"),
        (1000000, "$1,000,000.00"),
    ],
)
def test_format_currency_various(amount, expected):
    """format_currency should format amounts with dollar sign, thousands separator, and two decimals."""
    assert format_currency(amount) == expected


@pytest.mark.parametrize(
    "date_string,expected",
    [
        ("2024-01-31", datetime(2024, 1, 31)),
        ("2020-02-29", datetime(2020, 2, 29)),  # leap year
    ],
)
def test_parse_date_valid_strings(date_string, expected):
    """parse_date should parse valid YYYY-MM-DD strings and return a datetime object."""
    result = parse_date(date_string)
    assert isinstance(result, datetime)
    assert result.year == expected.year
    assert result.month == expected.month
    assert result.day == expected.day


@pytest.mark.parametrize("date_string", ["31-01-2024", "2024/01/31", "invalid", ""])
def test_parse_date_invalid_strings_return_none(date_string):
    """parse_date should return None for invalid date strings."""
    assert parse_date(date_string) is None


@pytest.mark.parametrize(
    "start,end,expected_days",
    [
        ("2024-01-01", "2024-01-10", 9),
        ("2024-01-10", "2024-01-01", -9),
        ("2024-01-01", "2024-01-01", 0),
    ],
)
def test_get_date_range_string_inputs(start, end, expected_days):
    """get_date_range should return day difference for date strings."""
    assert get_date_range(start, end) == expected_days


@pytest.mark.parametrize(
    "start,end",
    [
        ("invalid", "2024-01-10"),
        ("2024-01-01", "invalid"),
        ("invalid", "invalid"),
    ],
)
def test_get_date_range_returns_zero_when_dates_invalid(start, end):
    """get_date_range should return 0 when either date fails to parse."""
    assert get_date_range(start, end) == 0


def test_get_date_range_with_datetime_objects():
    """get_date_range should work with datetime objects directly."""
    start = datetime(2024, 3, 1)
    end = datetime(2024, 3, 5)
    assert get_date_range(start, end) == 4


@pytest.mark.parametrize(
    "data,key,typ,expected,approx",
    [
        ({"a": "1"}, "a", "i", 1, False),
        ({"a": "x"}, "a", "i", None, False),
        ({"a": 3.14}, "a", "f", 3.14, True),
        ({"a": "3.14"}, "a", "f", 3.14, True),
        ({"a": None}, "a", "i", None, False),
        ({"a": "text"}, "a", "s", "text", False),
        ({"a": 42}, "a", "s", "42", False),
        ({"a": 10}, "a", "other", 10, False),
        ({}, "missing", "i", None, False),
    ],
)
def test_v_type_conversion_and_fallback(data, key, typ, expected, approx):
    """v should convert values based on the type flag and handle None/missing keys gracefully."""
    result = v(data, key, typ)
    if approx and isinstance(expected, float):
        assert result == pytest.approx(expected)
    else:
        assert result == expected


def test_load_data_from_file_uses_json_load_when_exists():
    """load_data_from_file should invoke json.load when the file exists."""
    fake_file = "exists.json"
    fake_data = {"k": "v"}

    m = mock_open(read_data=json.dumps(fake_data))
    with patch("utils.os.path.exists", return_value=True), \
         patch("utils.open", m), \
         patch("utils.json.load", wraps=json.load) as json_load_spy:
        result = load_data_from_file(fake_file)
        assert result == fake_data
        assert json_load_spy.called is True