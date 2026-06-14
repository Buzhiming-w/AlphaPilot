from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from redis import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError


class AnalysisQueue(Protocol):
    def enqueue(self, job_id: str) -> None:
        ...


@dataclass
class InlineAnalysisQueue:
    enqueued: list[str] = field(default_factory=list)

    def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)


class RedisAnalysisQueue:
    def __init__(self, redis_url: str, *, queue_name: str = "alphapilot:analysis_jobs") -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.queue_name = queue_name

    def enqueue(self, job_id: str) -> None:
        self.client.rpush(self.queue_name, job_id)

    def dequeue(self, *, timeout_seconds: int = 5) -> str | None:
        try:
            item = self.client.blpop(self.queue_name, timeout=timeout_seconds)
        except RedisTimeoutError:
            return None
        return item[1] if item else None
