from __future__ import annotations

import json
from typing import Dict

from pydantic import BaseModel


class Payload(BaseModel):
    data: Dict[str, str]


def serialize_payload(payload: Payload) -> str:
    return json.dumps(payload.data)
