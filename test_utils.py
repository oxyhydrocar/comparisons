import json
import os
from datetime import datetime


def load_data_from_file(filepath):
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data_to_file(filepath, data):
    # Ensure directory part is handled even when there is no parent directory.
    directory = os.path.dirname(filepath)
    os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def format_currency(amount):
    return f"${amount:,.2f}"


def parse_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def v(d, k, t):
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


def get_date_range(start_date, end_date):
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        return (end_date - start_date).days
    return 0