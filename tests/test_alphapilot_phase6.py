from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import TimeoutError as RedisTimeoutError

from alphapilot.backend.app import create_app
from alphapilot.backend.queue import RedisAnalysisQueue
from alphapilot.backend.rate_limit import InMemoryRateLimiter
from alphapilot.backend.store import AlphaPilotStore
from alphapilot.backend.worker import process_analysis_job


class SpyQueue:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)


class TimeoutRedisClient:
    def blpop(self, *_args, **_kwargs):
        raise RedisTimeoutError("Timeout reading from socket")


class ExplodingLiveEngine:
    def run_demo(self):
        return {"decision": "Overweight", "sections": {"final": "demo"}}, {"demo": True}

    def run_live(self, *_args, **_kwargs):
        raise AssertionError("live analysis must run in the worker, not the request")


class SuccessfulLiveEngine:
    def run_live(self, ticker: str, trade_date: str, selected_analysts: list[str] | None = None):
        return (
            {
                "ticker": ticker,
                "trade_date": trade_date,
                "decision": "Overweight",
                "sections": {"final": "worker result"},
            },
            {"company_of_interest": ticker, "selected_analysts": selected_analysts or ["market"]},
        )


class FailingLiveEngine:
    def run_live(self, *_args, **_kwargs):
        raise RuntimeError("provider timeout")


def _register_and_login(client: TestClient, email: str = "phase6@example.com") -> str:
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "pass-1234", "display_name": "Phase 6 User"},
    )
    assert registered.status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": "pass-1234"})
    assert login.status_code == 200
    return login.json()["access_token"]


@pytest.mark.unit
def test_live_analysis_is_queued_without_running_engine_in_request():
    store = AlphaPilotStore()
    queue = SpyQueue()
    client = TestClient(create_app(store=store, engine=ExplodingLiveEngine(), queue=queue))
    token = _register_and_login(client)

    created = client.post(
        "/analysis",
        json={"ticker": "NVDA", "trade_date": "2024-05-10", "mode": "live"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert created.status_code == 201
    job = created.json()
    assert job["status"] == "queued"
    assert job["result_id"] is None
    assert queue.enqueued == [job["id"]]
    assert store.get_job(job["id"]).status == "queued"


@pytest.mark.unit
def test_worker_completes_live_job_and_records_usage_log(monkeypatch):
    monkeypatch.setenv("TRADINGAGENTS_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("TRADINGAGENTS_DEEP_THINK_LLM", "deepseek-v4-pro")
    store = AlphaPilotStore()
    user = store.create_user("worker@example.com", "pass-1234", "Worker User")
    job = store.create_job(user.id, "nvda", "2024-05-10", "live", ["market"])

    completed = process_analysis_job(store=store, engine=SuccessfulLiveEngine(), job_id=job.id)

    result = store.get_result(completed.result_id)
    usage_logs = store.list_usage_logs()
    assert completed.status == "completed"
    assert result.normalized["sections"]["final"] == "worker result"
    assert usage_logs[-1].user_id == user.id
    assert usage_logs[-1].endpoint == "analysis.worker.live"
    assert usage_logs[-1].provider == "deepseek"
    assert usage_logs[-1].model == "deepseek-v4-pro"


@pytest.mark.unit
def test_worker_marks_live_job_failed_and_records_failure_log():
    store = AlphaPilotStore()
    user = store.create_user("failed-worker@example.com", "pass-1234", "Failed Worker User")
    job = store.create_job(user.id, "aapl", "2024-05-10", "live", ["market"])

    failed = process_analysis_job(store=store, engine=FailingLiveEngine(), job_id=job.id)

    usage_logs = store.list_usage_logs()
    assert failed.status == "failed"
    assert failed.error == "provider timeout"
    assert failed.result_id is None
    assert usage_logs[-1].user_id == user.id
    assert usage_logs[-1].endpoint == "analysis.worker.failed"


@pytest.mark.unit
def test_redis_queue_dequeue_treats_timeout_as_empty_queue():
    queue = RedisAnalysisQueue.__new__(RedisAnalysisQueue)
    queue.client = TimeoutRedisClient()
    queue.queue_name = "alphapilot:analysis_jobs"

    assert queue.dequeue(timeout_seconds=1) is None


@pytest.mark.unit
def test_rate_limit_blocks_public_demo_after_threshold():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    client = TestClient(create_app(store=AlphaPilotStore(), rate_limiter=limiter))

    assert client.get("/demo/reference").status_code == 200
    assert client.get("/demo/reference").status_code == 200
    blocked = client.get("/demo/reference")

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Rate limit exceeded"
