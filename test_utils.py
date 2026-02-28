import json
import os
from datetime import datetime, date
from typing import Any, Optional, Union

__all__ = [
    "load_data_from_file",
    "save_data_to_file",
    "format_currency",
    "parse_date",
    "v",
    "get_date_range",
]


def _to_str_path(filepath: Union[str, os.PathLike]) -> str:
    return os.fspath(filepath)


def load_data_from_file(filepath: Union[str, os.PathLike]) -> list:
    path_str = _to_str_path(filepath)
    if not os.path.exists(path_str):
        return []
    with open(path_str, "r") as f:
        return json.load(f)


def save_data_to_file(filepath: Union[str, os.PathLike], data: Any) -> None:
    path_str = _to_str_path(filepath)
    dir_name = os.path.dirname(path_str)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path_str, "w") as f:
        json.dump(data, f, indent=2)


def format_currency(amount: Union[int, float]) -> str:
    return f"${amount:,.2f}"


def parse_date(date_string: Any) -> Optional[datetime]:
    if isinstance(date_string, datetime):
        return date_string
    if isinstance(date_string, date):
        return datetime(date_string.year, date_string.month, date_string.day)
    if not isinstance(date_string, str):
        return None
    date_string = date_string.strip()
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        return None


def v(d: dict, k: Any, t: str) -> Any:
    r = d.get(k)
    if r is None:
        return None
    if t == "i":
        try:
            return int(r)
        except Exception:
            return None
    elif t == "s":
        return str(r)
    elif t == "f":
        try:
            return float(r)
        except Exception:
            return None
    return r


def _ensure_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        return parse_date(value)
    return None


def get_date_range(start_date: Any, end_date: Any) -> int:
    start_dt = _ensure_datetime(start_date)
    end_dt = _ensure_datetime(end_date)
    if start_dt is None or end_dt is None:
        return 0
    return (end_dt - start_dt).days