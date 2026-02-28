from __future__ import annotations

from typing import Callable


class Notifier:
    max_retries = 3

    def __init__(self, sender: Callable[[str], bool]) -> None:
        self._sender = sender

    def send_with_retry(self, message: str) -> bool:
        retries = 3
        for _ in range(retries):
            if self._sender(message):
                return True
        return False
