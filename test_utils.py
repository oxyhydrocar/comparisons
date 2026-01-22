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
    """Provide sample JSON-serializable data for tests."""
    return {"key": "value", "number": 123}


@pytest.fixture
def sample_json_str(sample_json_data):
    """Provide a JSON string representation of the sample data."""
    return json.dumps(sample_json_data)


class TestLoadDataFromFile:
    """Tests for load_data_from_file."""

    def test_load_data_from_file_nonexistent_path(self, tmp_path):
        """Return empty list when file does not exist."""
        nonexistent_file = tmp_path / "does_not_exist.json"
        result = load_data_from_file(str(nonexistent_file))
        assert result == []

    def test_load_data_from_file_happy_path(self, sample_json_data, sample_json_str):
        """Load JSON data correctly from an existing file."""
        m = mock_open(read_data=sample_json_str)
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", m
        ):
            result = load_data_from_file("some/path/file.json")

        assert result == sample_json_data
        m.assert_called_once_with("some/path/file.json", "r")

    def test_load_data_from_file_invalid_json(self):
        """Propagate json.JSONDecodeError when file content is invalid JSON."""
        m = mock_open(read_data="not-valid-json")
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", m
        ):
            with pytest.raises(json.JSONDecodeError):
                load_data_from_file("file.json")


class TestSaveDataToFile:
    """Tests for save_data_to_file."""

    def test_save_data_to_file_creates_directory_and_writes(
        self, sample_json_data
    ):
        """Create directories as needed and write JSON data."""
        m = mock_open()
        with patch("os.makedirs") as makedirs_mock, patch(
            "builtins.open", m
        ):
            save_data_to_file("some/dir/file.json", sample_json_data)

        makedirs_mock.assert_called_once_with("some/dir", exist_ok=True)
        m.assert_called_once_with("some/dir/file.json", "w")
        handle = m()
        handle.write.assert_called()

        written = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written) == sample_json_data

    def test_save_data_to_file_root_directory(self, sample_json_data):
        """Handle saving to a file in the current directory (no parent dir)."""
        m = mock_open()
        with patch("os.makedirs") as makedirs_mock, patch(
            "builtins.open", m
        ):
            save_data_to_file("file.json", sample_json_data)

        # os.path.dirname('file.json') == ''
        makedirs_mock.assert_called_once_with("", exist_ok=True)
        m.assert_called_once_with("file.json", "w")


class TestFormatCurrency:
    """Tests for format_currency."""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0, "$0.00"),
            (1, "$1.00"),
            (1.2, "$1.20"),
            (1234.5, "$1,234.50"),
            (1234567.891, "$1,234,567.89"),
            (-50, "$-50.00"),
        ],
    )
    def test_format_currency_various_values(self, amount, expected):
        """Format various amounts as currency with two decimals and commas."""
        result = format_currency(amount)
        assert result == expected


class TestParseDate:
    """Tests for parse_date."""

    @pytest.mark.parametrize(
        "date_string,expected",
        [
            ("2024-01-01", datetime(2024, 1, 1)),
            ("1999-12-31", datetime(1999, 12, 31)),
        ],
    )
    def test_parse_date_valid_dates(self, date_string, expected):
        """Return datetime object for valid ISO date strings."""
        result = parse_date(date_string)
        assert result == expected

    @pytest.mark.parametrize(
        "date_string",
        [
            "2024-13-01",  # invalid month
            "2024-00-10",  # invalid month
            "2024-02-30",  # invalid day
            "not-a-date",
            "",
        ],
    )
    def test_parse_date_invalid_dates(self, date_string):
        """Return None for invalid date strings."""
        result = parse_date(date_string)
        assert result is None


class TestVFunction:
    """Tests for v (value conversion) helper."""

    @pytest.fixture
    def base_dict(self):
        """Provide a sample dictionary for v function tests."""
        return {
            "int_str": "10",
            "int_val": 20,
            "float_str": "3.14",
            "float_val": 2.718,
            "str_val": "hello",
            "none_val": None,
            "bad_int": "abc",
            "bad_float": "xyz",
        }

    def test_v_missing_key_returns_none(self, base_dict):
        """Return None when key is not present in dictionary."""
        result = v(base_dict, "missing", "i")
        assert result is None

    def test_v_none_value_returns_none(self, base_dict):
        """Return None when value is explicitly None."""
        result = v(base_dict, "none_val", "s")
        assert result is None

    @pytest.mark.parametrize(
        "key,type_code,expected",
        [
            ("int_str", "i", 10),
            ("int_val", "i", 20),
        ],
    )
    def test_v_integer_conversion_success(self, base_dict, key, type_code, expected):
        """Convert values to int when possible."""
        result = v(base_dict, key, type_code)
        assert result == expected

    @pytest.mark.parametrize(
        "key,type_code",
        [
            ("bad_int", "i"),
            ("str_val", "i"),
        ],
    )
    def test_v_integer_conversion_failure_returns_none(
        self, base_dict, key, type_code
    ):
        """Return None when integer conversion fails."""
        result = v(base_dict, key, type_code)
        assert result is None

    @pytest.mark.parametrize(
        "key,type_code,expected",
        [
            ("float_str", "f", 3.14),
            ("float_val", "f", 2.718),
            ("int_val", "f", 20.0),
        ],
    )
    def test_v_float_conversion_success(self, base_dict, key, type_code, expected):
        """Convert values to float when possible."""
        result = v(base_dict, key, type_code)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "key,type_code",
        [
            ("bad_float", "f"),
            ("str_val", "f"),
        ],
    )
    def test_v_float_conversion_failure_returns_none(
        self, base_dict, key, type_code
    ):
        """Return None when float conversion fails."""
        result = v(base_dict, key, type_code)
        assert result is None

    @pytest.mark.parametrize(
        "key,type_code,expected",
        [
            ("str_val", "s", "hello"),
            ("int_val", "s", "20"),
            ("float_val", "s", "2.718"),
        ],
    )
    def test_v_string_conversion(self, base_dict, key, type_code, expected):
        """Convert values to string when type code is 's'."""
        result = v(base_dict, key, type_code)
        assert result == expected

    def test_v_unknown_type_code_returns_raw_value(self, base_dict):
        """Return raw dictionary value when type code is unknown."""
        result = v(base_dict, "int_val", "unknown")
        assert result == 20


class TestGetDateRange:
    """Tests for get_date_range."""

    def test_get_date_range_with_datetime_objects(self):
        """Compute difference in days when given datetime objects."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_with_string_dates(self):
        """Compute difference in days when given date strings."""
        result = get_date_range("2024-01-01", "2024-01-10")
        assert result == 9

    def test_get_date_range_mixed_types(self):
        """Accept mixed string and datetime inputs."""
        start = "2024-01-01"
        end = datetime(2024, 1, 05)
        result = get_date_range(start, end)
        assert result == 4

    @pytest.mark.parametrize(
        "start_date,end_date",
        [
            ("invalid", "2024-01-10"),
            ("2024-01-01", "invalid"),
            ("invalid", "also-invalid"),
            (None, datetime(2024, 1, 10)),
            (datetime(2024, 1, 1), None),
        ],
    )
    def test_get_date_range_invalid_or_missing_dates_returns_zero(
        self, start_date, end_date
    ):
        """Return 0 when dates cannot be parsed or are missing."""
        result = get_date_range(start_date, end_date)
        assert result == 0

    def test_get_date_range_end_before_start_negative_days(self):
        """Return negative difference when end date is before start date."""
        result = get_date_range("2024-01-10", "2024-01-01")
        assert result == -9