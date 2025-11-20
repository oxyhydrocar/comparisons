import json
import os
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock

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
def sample_json_data():
    return {"name": "Alice", "age": 30, "active": True}


@pytest.fixture
def sample_json_list():
    return [{"id": 1}, {"id": 2}]


@pytest.fixture
def temp_json_file(tmp_path, sample_json_data):
    """Create a temporary JSON file with sample data."""
    file_path = tmp_path / "data.json"
    with open(file_path, "w") as f:
        json.dump(sample_json_data, f)
    return file_path


def test_load_data_from_file_nonexistent_returns_empty_list():
    """load_data_from_file should return an empty list when the file does not exist."""
    with patch("os.path.exists", return_value=False), patch("builtins.open", mock_open()) as m_open:
        result = load_data_from_file("nonexistent.json")
        assert result == []
        m_open.assert_not_called()


def test_load_data_from_file_valid_json_reads_content(temp_json_file, sample_json_data):
    """load_data_from_file should read and return JSON content from a valid file."""
    result = load_data_from_file(str(temp_json_file))
    assert result == sample_json_data


def test_load_data_from_file_invalid_json_raises(tmp_path):
    """load_data_from_file should raise JSONDecodeError when JSON is invalid."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{bad json")
    with pytest.raises(json.JSONDecodeError):
        load_data_from_file(str(bad_file))


def test_save_data_to_file_creates_directories_and_writes_json(tmp_path, sample_json_list):
    """save_data_to_file should create directories and write JSON content to file."""
    nested_dir = tmp_path / "a" / "b"
    file_path = nested_dir / "out.json"
    save_data_to_file(str(file_path), sample_json_list)

    assert file_path.exists()
    with open(file_path, "r") as f:
        data = json.load(f)
    assert data == sample_json_list


def test_save_data_to_file_uses_indent_and_open_mode(tmp_path, sample_json_data):
    """save_data_to_file should call json.dump with indent=2 and open file in write mode."""
    target_file = tmp_path / "target" / "file.json"

    with patch("os.makedirs") as m_makedirs, \
         patch("builtins.open", mock_open()) as m_open, \
         patch("json.dump") as m_dump:
        save_data_to_file(str(target_file), sample_json_data)

        # os.makedirs called with correct directory and exist_ok=True
        m_makedirs.assert_called_once()
        called_dir, called_kwargs = m_makedirs.call_args[0][0], m_makedirs.call_args[1]
        assert os.path.basename(called_dir) == "target"
        assert called_kwargs.get("exist_ok") is True

        # open called in write mode
        m_open.assert_called_once()
        assert m_open.call_args[0][1] == "w"

        # json.dump called with indent=2
        assert m_dump.call_count == 1
        _, dump_kwargs = m_dump.call_args
        assert dump_kwargs.get("indent") == 2


def test_save_data_to_file_non_serializable_raises(tmp_path):
    """save_data_to_file should raise TypeError when data is not JSON serializable."""
    file_path = tmp_path / "x" / "y.json"
    data = {"obj": object()}
    with pytest.raises(TypeError):
        save_data_to_file(str(file_path), data)


@pytest.mark.parametrize(
    "amount,expected",
    [
        (0, "$0.00"),
        (12, "$12.00"),
        (12.3, "$12.30"),
        (12.3456, "$12.35"),
        (1234.5, "$1,234.50"),
        (-1, "$-1.00"),
        (-1234567.89, "$-1,234,567.89"),
        (1000000.4, "$1,000,000.40"),
    ],
)
def test_format_currency_valid_values(amount, expected):
    """format_currency should format numbers with dollar sign, commas, and 2 decimals."""
    assert format_currency(amount) == expected


@pytest.mark.parametrize("bad_input", ["abc", "12x", None, object()])
def test_format_currency_invalid_input_raises(bad_input):
    """format_currency should raise ValueError or TypeError for non-numeric inputs."""
    with pytest.raises((ValueError, TypeError)):
        format_currency(bad_input)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "date_string,expected",
    [
        ("2020-01-02", datetime(2020, 1, 2)),
        ("1999-12-31", datetime(1999, 12, 31)),
    ],
)
def test_parse_date_valid_strings(date_string, expected):
    """parse_date should return a datetime object for valid YYYY-MM-DD strings."""
    assert parse_date(date_string) == expected


@pytest.mark.parametrize("invalid", ["2020/01/02", "02-01-2020", "", "not-a-date"])
def test_parse_date_invalid_strings_return_none(invalid):
    """parse_date should return None for invalid date strings."""
    assert parse_date(invalid) is None


@pytest.mark.parametrize(
    "data,key,t,expected",
    [
        ({"a": "5"}, "a", "i", 5),
        ({"a": 5}, "a", "i", 5),
        ({"a": "5.9"}, "a", "i", None),
        ({"a": "xyz"}, "a", "i", None),
        ({"a": 2.5}, "a", "f", 2.5),
        ({"a": "2.5"}, "a", "f", 2.5),
        ({"a": "x"}, "a", "f", None),
        ({"a": 7}, "a", "s", "7"),
        ({"a": None}, "a", "i", None),
        ({}, "missing", "i", None),
        ({"a": [1, 2, 3]}, "a", "x", [1, 2, 3]),
    ],
)
def test_v_type_conversion_various_cases(data, key, t, expected):
    """v should convert values based on type specifier or return None/unchanged appropriately."""
    assert v(data, key, t) == expected


@pytest.mark.parametrize(
    "start,end,expected_days",
    [
        ("2020-01-01", "2020-01-10", 9),
        ("2020-02-28", "2020-03-01", 2),
        ("2020-01-01", "2020-01-01", 0),
    ],
)
def test_get_date_range_valid_strings(start, end, expected_days):
    """get_date_range should compute difference in days for valid date strings."""
    assert get_date_range(start, end) == expected_days


def test_get_date_range_datetime_objects():
    """get_date_range should handle datetime objects directly."""
    s = datetime(2020, 1, 5)
    e = datetime(2020, 1, 10)
    assert get_date_range(s, e) == 5


def test_get_date_range_start_after_end_negative():
    """get_date_range should return negative days when start is after end."""
    assert get_date_range("2020-01-10", "2020-01-01") == -9


@pytest.mark.parametrize(
    "start,end",
    [
        ("invalid", "2020-01-01"),
        ("2020-01-01", "bad"),
        ("bad", "worse"),
    ],
)
def test_get_date_range_invalid_inputs_return_zero(start, end):
    """get_date_range should return 0 when either start or end is invalid."""
    assert get_date_range(start, end) == 0