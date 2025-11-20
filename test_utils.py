import json
import os
from datetime import datetime
from typing import Any, Iterable, Optional, Union


def load_data_from_file(filepath: str) -> Any:
    """
    Load JSON data from a file. If the file does not exist, return an empty list.
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r") as f:
        return json.load(f)


def save_data_to_file(filepath: str, data: Any) -> None:
    """
    Save data to a JSON file, ensuring the directory exists. Uses indent=2.
    """
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def format_currency(amount: Any) -> str:
    """
    Format a numeric amount as currency with a dollar sign, commas, and 2 decimals.
    Raises ValueError or TypeError for non-numeric inputs.
    """
    return f"${amount:,.2f}"


def parse_date(date_string: str) -> Optional[datetime]:
    """
    Parse a date string in YYYY-MM-DD format into a datetime object.
    Returns None for invalid formats.
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def v(d: dict, k: str, t: str) -> Any:
    """
    Retrieve and convert a value from dict d by key k according to type t:
    - 'i': integer
    - 'f': float
    - 's': string
    Unknown type returns the value unchanged.
    None values return None.
    """
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


def get_date_range(
    start_date: Union[str, datetime], end_date: Union[str, datetime]
) -> int:
    """
    Compute the difference in days between two dates.
    Accepts strings in YYYY-MM-DD format or datetime objects.
    Returns 0 if either date is invalid.
    """
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    if start_date and end_date:
        return (end_date - start_date).days
    return 0