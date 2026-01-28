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
    """Fixture providing sample JSON-serializable data."""
    return [{"id": 1, "name": "Item1"}, {"id": 2, "name": "Item2"}]


@pytest.fixture
def sample_json_str(sample_json_data):
    """Fixture providing sample JSON string matching sample_json_data."""
    return json.dumps(sample_json_data)


class TestLoadDataFromFile:
    """Tests for load_data_from_file."""

    def test_load_data_from_file_nonexistent_path(self, tmp_path):
        """Test load_data_from_file returns empty list when file does not exist."""
        non_existent_file = tmp_path / "does_not_exist.json"
        result = load_data_from_file(str(non_existent_file))
        assert result == []

    def test_load_data_from_file_existing_file(self, tmp_path, sample_json_data):
        """Test load_data_from_file loads JSON content from existing file."""
        file_path = tmp_path / "data.json"
        file_path.write_text(json.dumps(sample_json_data))

        result = load_data_from_file(str(file_path))

        assert result == sample_json_data

    def test_load_data_from_file_uses_open_and_json_load(self, sample_json_str, sample_json_data):
        """Test load_data_from_file uses open and json.load correctly via mocks."""
        mock_file = mock_open(read_data=sample_json_str)
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("json.load", return_value=sample_json_data) as mock_json_load:
            result = load_data_from_file("fake/path/data.json")

        mock_file.assert_called_once_with("fake/path/data.json", "r")
        mock_json_load.assert_called_once()
        assert result == sample_json_data


class TestSaveDataToFile:
    """Tests for save_data_to_file."""

    def test_save_data_to_file_creates_directory_and_writes_data(
        self, tmp_path, sample_json_data
    ):
        """Test save_data_to_file creates directory and writes JSON data."""
        target_dir = tmp_path / "nested" / "dir"
        target_file = target_dir / "data.json"

        save_data_to_file(str(target_file), sample_json_data)

        assert target_file.exists()
        saved_content = json.loads(target_file.read_text())
        assert saved_content == sample_json_data

    def test_save_data_to_file_uses_os_makedirs_and_json_dump(self, sample_json_data):
        """Test save_data_to_file uses os.makedirs and json.dump via mocks."""
        mock_file = mock_open()
        with patch("os.makedirs") as mock_makedirs, patch(
            "builtins.open", mock_file
        ), patch("json.dump") as mock_json_dump:
            save_data_to_file("some/dir/data.json", sample_json_data)

        mock_makedirs.assert_called_once_with("some/dir", exist_ok=True)
        mock_file.assert_called_once_with("some/dir/data.json", "w")
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert args[0] == sample_json_data
        assert "indent" in kwargs and kwargs["indent"] == 2


class TestFormatCurrency:
    """Tests for format_currency."""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0, "$0.00"),
            (1, "$1.00"),
            (1234.5, "$1,234.50"),
            (1234.567, "$1,234.57"),
            (-42, "$-42.00"),
            (-1234.567, "$-1,234.57"),
        ],
    )
    def test_format_currency_various_amounts(self, amount, expected):
        """Test format_currency with various numeric amounts."""
        result = format_currency(amount)
        assert result == expected


class TestParseDate:
    """Tests for parse_date."""

    def test_parse_date_valid_string(self):
        """Test parse_date returns datetime for valid ISO date string."""
        date_str = "2023-01-15"
        result = parse_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    @pytest.mark.parametrize(
        "date_str",
        [
            "2023-13-01",  # invalid month
            "2023-00-10",  # invalid month
            "2023-02-30",  # invalid day
            "15-01-2023",  # wrong format
            "2023/01/15",  # wrong separator
            "",
            "not-a-date",
        ],
    )
    def test_parse_date_invalid_strings(self, date_str):
        """Test parse_date returns None for invalid date strings."""
        result = parse_date(date_str)
        assert result is None


class TestVFunction:
    """Tests for v helper function."""

    @pytest.mark.parametrize(
        "data,key,typ,expected",
        [
            ({"a": "10"}, "a", "i", 10),
            ({"a": 10}, "a", "i", 10),
            ({"a": "10.5"}, "a", "f", 10.5),
            ({"a": 10.5}, "a", "f", 10.5),
            ({"a": "text"}, "a", "s", "text"),
            ({"a": 100}, "a", "s", "100"),
            ({"a": "10"}, "a", "x", "10"),  # unknown type returns raw value
            ({}, "missing", "i", None),
            ({"a": None}, "a", "i", None),
        ],
    )
    def test_v_various_types_and_values(self, data, key, typ, expected):
        """Test v returns correctly converted values for various inputs."""
        result = v(data, key, typ)
        if isinstance(expected, float):
            assert result == pytest.approx(expected)
        else:
            assert result == expected

    @pytest.mark.parametrize(
        "data,key,typ",
        [
            ({"a": "not-int"}, "a", "i"),
            ({"a": "10.5.3"}, "a", "i"),
            ({"a": "not-float"}, "a", "f"),
            ({"a": "10,5"}, "a", "f"),
        ],
    )
    def test_v_invalid_conversions_return_none(self, data, key, typ):
        """Test v returns None when int/float conversion fails."""
        result = v(data, key, typ)
        assert result is None


class TestGetDateRange:
    """Tests for get_date_range."""

    def test_get_date_range_with_datetime_objects(self):
        """Test get_date_range computes difference when passed datetime objects."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 10)
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_with_string_dates(self):
        """Test get_date_range computes difference when passed date strings."""
        start = "2023-01-01"
        end = "2023-01-10"
        result = get_date_range(start, end)
        assert result == 9

    def test_get_date_range_mixed_types(self):
        """Test get_date_range handles mixed string and datetime inputs."""
        start = "2023-01-01"
        end = datetime(2023, 1, 15)
        result = get_date_range(start, end)
        assert result == 14

    def test_get_date_range_invalid_start_date_string(self):
        """Test get_date_range returns 0 when start_date string is invalid."""
        start = "invalid-date"
        end = "2023-01-10"
        result = get_date_range(start, end)
        assert result == 0

    def test_get_date_range_invalid_end_date_string(self):
        """Test get_date_range returns 0 when end_date string is invalid."""
        start = "2023-01-01"
        end = "invalid-date"
        result = get_date_range(start, end)
        assert result == 0

    def test_get_date_range_none_inputs(self):
        """Test get_date_range returns 0 when either date is None."""
        assert get_date_range(None, datetime(2023, 1, 1)) == 0
        assert get_date_range(datetime(2023, 1, 1), None) == 0
        assert get_date_range(None, None) == 0

    def test_get_date_range_end_before_start(self):
        """Test get_date_range returns negative difference when end is before start."""
        start = "2023-01-10"
        end = "2023-01-01"
        result = get_date_range(start, end)
        assert result == -9