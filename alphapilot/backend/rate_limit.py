from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

from redis import Redis


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool:
        ...


@dataclass
class InMemoryRateLimiter:
    limit: int
    window_seconds: int
    _buckets: dict[str, tuple[int, float]] = field(default_factory=dict)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        count, reset_at = self._buckets.get(key, (0, now + self.window_seconds))
        if now >= reset_at:
            count = 0
            reset_at = now + self.window_seconds
        count += 1
        self._buckets[key] = (count, reset_at)
        return count <= self.limit


class RedisRateLimiter:
    def __init__(self, redis_url: str, *, limit: int, window_seconds: int, prefix: str = "alphapilot:rate") -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.limit = limit
        self.window_seconds = window_seconds
        self.prefix = prefix

    def allow(self, key: str) -> bool:
        redis_key = f"{self.prefix}:{key}"
        count = self.client.incr(redis_key)
        if count == 1:
            self.client.expire(redis_key, self.window_seconds)
        return count <= self.limit
