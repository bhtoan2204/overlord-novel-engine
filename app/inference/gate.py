"""Process-wide gate so inference, embedding rebuilds, and training never overlap."""

import threading

from app.core.errors import ResourceError


class ResourceGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.holder: str | None = None

    def acquire(self, kind: str) -> None:
        if not self._lock.acquire(blocking=False):
            raise ResourceError(f"Cannot start {kind} while {self.holder} is running.")
        self.holder = kind

    def release(self, kind: str) -> None:
        if self.holder == kind:
            self.holder = None
            self._lock.release()


GATE = ResourceGate()
