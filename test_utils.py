import json
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
    """Provide a JSON string corresponding to sample_json_data."""
    return json.dumps(sample_json_data)


class TestLoadDataFromFile:
    """Tests for load_data_from_file."""

    def test_load_data_from_file_nonexistent_path(self, tmp_path):
        """Return empty list when file does not exist."""
        non_existent_file = tmp_path / "nope.json"
        result = load_data_from_file(str(non_existent_file))
        assert result == []

    def test_load_data_from_file_existing_file(self, tmp_path, sample_json_data):
        """Load JSON data correctly from an existing file."""
        file_path = tmp_path / "data.json"
        file_path.write_text(json.dumps(sample_json_data))

        result = load_data_from_file(str(file_path))
        assert result == sample_json_data

    def test_load_data_from_file_uses_os_path_exists_and_open(self, sample_json_string):
        """Ensure os.path.exists and open are used as expected."""
        with patch("os.path.exists", return_value=True) as mock_exists, patch(
            "builtins.open", mock_open(read_data=sample_json_string)
        ) as mocked_file:
            result = load_data_from_file("dummy/path.json")

        assert result == json.loads(sample_json_string)
        mock_exists.assert_called_once_with("dummy/path.json")
        mocked_file.assert_called_once_with("dummy/path.json", "r")


class TestSaveDataToFile:
    """Tests for save_data_to_file."""

    def test_save_data_to_file_creates_directory_and_writes(self, sample_json_data):
        """Create directories and write JSON data to file."""
        m = mock_open()
        with patch("os.makedirs") as mock_makedirs, patch(
            "builtins.open", m
        ) as mocked_file:
            save_data_to_file("some/dir/file.json", sample_json_data)

        mock_makedirs.assert_called_once()
        # First arg is directory, so check dirname
        args, kwargs = mock_makedirs.call_args
        assert args[0] == "some/dir"
        assert kwargs.get("exist_ok") is True

        mocked_file.assert_called_once_with("some/dir/file.json", "w")
        handle = mocked_file()
        handle.write.assert_called()  # json.dump should have written something

        # Verify written content is valid JSON and matches the data
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        # json.dump with indent=2 may write in multiple chunks, so reassemble
        assert json.loads(written_content) == sample_json_data

    def test_save_data_to_file_with_root_directory(self, sample_json_data):
        """Handle file path without an explicit directory (dirname is '')."""
        m = mock_open()
        with patch("os.makedirs") as mock_makedirs, patch(
            "builtins.open", m
        ) as mocked_file:
            save_data_to_file("file.json", sample_json_data)

        # os.path.dirname("file.json") is '', so makedirs is called with ''
        mock_makedirs.assert_called_once()
        args, kwargs = mock_makedirs.call_args
        assert args[0] == ""
        assert kwargs.get("exist_ok") is True
        mocked_file.assert_called_once_with("file.json", "w")


class TestFormatCurrency:
    """Tests for format_currency."""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0, "$0.00"),
            (1, "$1.00"),
            (12.5, "$12.50"),
            (1234.567, "$1,234.57"),
            (-5, "$-5.00"),
            (1000000, "$1,000,000.00"),
        ],
    )
    def test_format_currency_various_values(self, amount, expected):
        """Format different numeric values as currency."""
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
            "15-01-2024",
            "2024/01/15",
            "2024-13-01",
            "invalid",
            "",
            "2024-02-30",
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
            ({"a": 1}, "a", 1),
            ({"a": "2"}, "a", 2),
            ({"a": 1.9}, "a", 1),  # int(1.9) == 1
        ],
    )
    def test_v_type_int_valid(self, data, key, expected):
        """Return integer value when type is 'i' and conversion is valid."""
        result = v(data, key, "i")
        assert result == expected

    @pytest.mark.parametrize(
        "data,key",
        [
            ({}, "missing"),
            ({"a": None}, "a"),
        ],
    )
    def test_v_missing_or_none_key_returns_none(self, data, key):
        """Return None when key is missing or value is None."""
        result = v(data, key, "i")
        assert result is None

    @pytest.mark.parametrize(
        "value",
        ["not-an-int", {}, [], "123.45"],
    )
    def test_v_type_int_invalid_conversion(self, value):
        """Return None when int conversion fails."""
        data = {"a": value}
        result = v(data, "a", "i")
        assert result is None

    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"a": "text"}, "a", "text"),
            ({"a": 123}, "a", "123"),
            ({"a": 12.34}, "a", "12.34"),
        ],
    )
    def test_v_type_str(self, data, key, expected):
        """Return string representation when type is 's'."""
        result = v(data, key, "s")
        assert result == expected

    @pytest.mark.parametrize(
        "data,key,expected",
        [
            ({"a": 1}, "a", 1.0),
            ({"a": "2.5"}, "a", 2.5),
            ({"a": 3.14159}, "a", 3.14159),
        ],
    )
    def test_v_type_float_valid(self, data, key, expected):
        """Return float value when type is 'f' and conversion is valid."""
        result = v(data, key, "f")
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "value",
        ["not-a-float", {}, []],
    )
    def test_v_type_float_invalid_conversion(self, value):
        """Return None when float conversion fails."""
        data = {"a": value}
        result = v(data, "a", "f")
        assert result is None

    def test_v_unknown_type_returns_raw_value(self):
        """Return raw value when type is not recognized."""
        data = {"a": 10}
        result = v(data, "a", "unknown")
        assert result == 10


class TestGetDateRange:
    """Tests for get_date_range."""

    def test_get_date_range_with_datetime_objects(self):
        """Compute date range when given datetime objects."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_with_string_dates(self):
        """Compute date range when given string date representations."""
        start = "2024-01-01"
        end = "2024-01-10"
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_mixed_types(self):
        """Compute date range when mixing string and datetime inputs."""
        start = "2024-01-01"
        end = datetime(2024, 1, 5)
        result = get_date_range(start, end)
        assert result == 4

    @pytest.mark.parametrize(
        "start,end",
        [
            ("invalid", "2024-01-01"),
            ("2024-01-01", "invalid"),
            ("invalid", "also-invalid"),
        ],
    )
    def test_get_date_range_invalid_strings(self, start, end):
        """Return 0 when either parsed date is invalid."""
        result = get_date_range(start, end)
        assert result == 0

    def test_get_date_range_none_inputs(self):
        """Return 0 when inputs are None."""
        result = get_date_range(None, None)
        assert result == 0

    def test_get_date_range_start_after_end(self):
        """Return negative days when start_date is after end_date."""
        start = "2024-01-10"
        end = "2024-01-01"
        result = get_date_range(start, end)
        assert result == -9