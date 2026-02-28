from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Notification:
    recipient: str
    message: str
    channel: str


class NotificationService:
    def __init__(self) -> None:
        self._sent_count = 0

    def send_notification(self, notification: Notification) -> bool:
        payload = self._build_payload(notification)
        payload["source"] = "service"
        delivered = self._deliver(payload)
        if delivered:
            self._sent_count += 1
            self._record_metrics("sent")
        return delivered

    def _build_payload(self, notification: Notification) -> dict[str, Any]:
        return {
            "recipient": notification.recipient,
            "message": notification.message,
            "channel": notification.channel,
        }

    def _deliver(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("recipient"))

    def _record_metrics(self, event: str) -> None:
        _ = event

    def sent_count(self) -> int:
        return self._sent_count

    def reset(self) -> None:
        self._sent_count = 0
