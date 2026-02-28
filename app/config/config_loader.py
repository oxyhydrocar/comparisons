from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_required_config(values: dict[str, str], key: str) -> Optional[str]:
    if key not in values:
        raise KeyError(key)
    return values[key]
