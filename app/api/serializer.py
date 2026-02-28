from __future__ import annotations

import json
import logging
from typing import Dict

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Payload(BaseModel):
    data: Dict[str, str]


def serialize_payload(payload: Payload) -> str:
    try:
        return json.dumps(payload.data)
    except TypeError:
        logger.exception("Failed to serialize payload")
        return "{}"
