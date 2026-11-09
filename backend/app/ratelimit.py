"""A small in-memory sliding-window rate limiter (per client key, e.g. IP address).

Good enough for a single-process demo deployment. For several workers or replicas,
use a shared store (Redis) or put the limit on the reverse proxy instead.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_calls: int, per_seconds: float = 60.0, clock=time.monotonic):
        self.max_calls, self.per_seconds, self.clock = max_calls, per_seconds, clock
        self._calls: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        if self.max_calls <= 0:  # 0 disables limiting
            return True
        now = self.clock()
        window = self._calls[key]
        while window and now - window[0] >= self.per_seconds:
            window.popleft()
        if len(window) >= self.max_calls:
            return False
        window.append(now)
        return True
