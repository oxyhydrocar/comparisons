import json
import os
from datetime import datetime
from unittest.mock import mock_open, patch

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
    """Provide sample JSON-serializable data."""
    return {"key": "value", "number": 123}


@pytest.fixture
def sample_json_string(sample_json_data):
    """Provide sample JSON string corresponding to sample_json_data."""
    return json.dumps(sample_json_data)


class TestLoadDataFromFile:
    """Tests for load_data_from_file."""

    def test_load_data_from_file_nonexistent_path(self, tmp_path):
        """Return empty list when file does not exist."""
        nonexistent_file = tmp_path / "does_not_exist.json"
        result = load_data_from_file(str(nonexistent_file))
        assert result == []

    def test_load_data_from_file_existing_file(self, sample_json_data, sample_json_string):
        """Load JSON data from an existing file."""
        m = mock_open(read_data=sample_json_string)
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", m
        ):
            result = load_data_from_file("dummy_path.json")
        assert result == sample_json_data

    def test_load_data_from_file_invalid_json(self):
        """Propagate JSONDecodeError when file contains invalid JSON."""
        m = mock_open(read_data="not valid json")
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", m
        ):
            with pytest.raises(json.JSONDecodeError):
                load_data_from_file("dummy_path.json")


class TestSaveDataToFile:
    """Tests for save_data_to_file."""

    def test_save_data_to_file_creates_directory_and_writes(
        self, tmp_path, sample_json_data
    ):
        """Create directories and write JSON data to file."""
        file_path = tmp_path / "nested" / "file.json"
        with patch("os.makedirs") as makedirs_mock, patch(
            "builtins.open", mock_open()
        ) as m:
            save_data_to_file(str(file_path), sample_json_data)

        makedirs_mock.assert_called_once_with(
            os.path.dirname(str(file_path)), exist_ok=True
        )
        m.assert_called_once_with(str(file_path), "w")
        handle = m()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        loaded = json.loads(written)
        assert loaded == sample_json_data

    def test_save_data_to_file_overwrites_existing_file(
        self, tmp_path, sample_json_data
    ):
        """Overwrite existing file content."""
        file_path = tmp_path / "file.json"
        file_path.write_text(json.dumps({"old": "data"}))

        save_data_to_file(str(file_path), sample_json_data)

        content = json.loads(file_path.read_text())
        assert content == sample_json_data


class TestFormatCurrency:
    """Tests for format_currency."""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0, "$0.00"),
            (1, "$1.00"),
            (1234.5, "$1,234.50"),
            (1234.567, "$1,234.57"),
            (-10, "$-10.00"),
            (1000000, "$1,000,000.00"),
        ],
    )
    def test_format_currency_various_values(self, amount, expected):
        """Format various numeric values as currency strings."""
        result = format_currency(amount)
        assert result == expected


class TestParseDate:
    """Tests for parse_date."""

    def test_parse_date_valid_string(self):
        """Parse a valid date string into datetime."""
        date_str = "2024-01-15"
        result = parse_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    @pytest.mark.parametrize(
        "date_str",
        [
            "2024-13-01",  # invalid month
            "2024-00-10",  # invalid month
            "2024-02-30",  # invalid day
            "not-a-date",
            "",
        ],
    )
    def test_parse_date_invalid_strings(self, date_str):
        """Return None for invalid date strings."""
        result = parse_date(date_str)
        assert result is None


class TestVFunction:
    """Tests for v helper function."""

    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"a": "1"}, "a", 1),
            ({"a": 1}, "a", 1),
            ({"a": 1.9}, "a", 1),
            ({"a": "not-int"}, "a", None),
            ({}, "missing", None),
            ({"a": None}, "a", None),
        ],
    )
    def test_v_integer_conversion(self, data, key, expected):
        """Convert values to int when type specifier is 'i'."""
        result = v(data, key, "i")
        assert result == expected

    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"a": "text"}, "a", "text"),
            ({"a": 123}, "a", "123"),
            ({"a": 1.23}, "a", "1.23"),
            ({}, "missing", None),
            ({"a": None}, "a", None),
        ],
    )
    def test_v_string_conversion(self, data, key, expected):
        """Convert values to str when type specifier is 's'."""
        result = v(data, key, "s")
        assert result == expected

    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"a": "1.5"}, "a", 1.5),
            ({"a": 1}, "a", 1.0),
            ({"a": 1.23}, "a", 1.23),
            ({"a": "not-float"}, "a", None),
            ({}, "missing", None),
            ({"a": None}, "a", None),
        ],
    )
    def test_v_float_conversion(self, data, key, expected):
        """Convert values to float when type specifier is 'f'."""
        result = v(data, key, "f")
        if expected is None:
            assert result is None
        else:
            assert result == pytest.approx(expected)

    def test_v_unknown_type_returns_raw_value(self):
        """Return raw value when type specifier is unknown."""
        data = {"a": "123"}
        result = v(data, "a", "unknown")
        assert result == "123"

    def test_v_missing_key_returns_none(self):
        """Return None when key is missing regardless of type."""
        data = {}
        result = v(data, "missing", "i")
        assert result is None


class TestGetDateRange:
    """Tests for get_date_range."""

    def test_get_date_range_with_datetime_objects(self):
        """Calculate day difference when given datetime objects."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_with_string_dates(self):
        """Calculate day difference when given date strings."""
        result = get_date_range("2024-01-01", "2024-01-10")
        assert result == 9

    def test_get_date_range_mixed_types(self):
        """Calculate day difference when given mixed types."""
        start = datetime(2024, 1, 1)
        end = "2024-01-05"
        result = get_date_range(start, end)
        assert result == 4

    @pytest.mark.parametrize(
        "start,end",
        [
            ("invalid", "2024-01-10"),
            ("2024-01-01", "invalid"),
            ("invalid", "also-invalid"),
            (None, datetime(2024, 1, 10)),
            (datetime(2024, 1, 1), None),
        ],
    )
    def test_get_date_range_invalid_inputs(self, start, end):
        """Return 0 when either date cannot be parsed or is falsy."""
        result = get_date_range(start, end)
        assert result == 0

    def test_get_date_range_end_before_start(self):
        """Allow negative differences when end date is before start date."""
        result = get_date_range("2024-01-10", "2024-01-01")
        assert result == -9