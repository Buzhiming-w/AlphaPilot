from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage
from redis.exceptions import TimeoutError as RedisTimeoutError

from alphapilot.backend.app import create_app
from alphapilot.backend.queue import RedisAnalysisQueue
from alphapilot.backend.rate_limit import InMemoryRateLimiter
from alphapilot.backend.sqlalchemy_store import SqlAlchemyAlphaPilotStore
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
                "sections": {
                    "market": "English market report",
                    "final": "English final report",
                },
            },
            {"company_of_interest": ticker, "selected_analysts": selected_analysts or ["market"]},
        )


class LiveEngineWithLangChainMessages:
    def run_live(self, ticker: str, trade_date: str, selected_analysts: list[str] | None = None):
        return (
            {
                "ticker": ticker,
                "trade_date": trade_date,
                "decision": "Neutral",
                "sections": {"final": "serialized worker result"},
            },
            {
                "company_of_interest": ticker,
                "messages": [HumanMessage(content="Analyze this ticker", id="msg-1")],
            },
        )


class FailingLiveEngine:
    def run_live(self, *_args, **_kwargs):
        raise RuntimeError("provider timeout")


class StubReportTranslator:
    provider = "deepseek"
    model = "deepseek-v4-flash"

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list[str] = []

    def translate_final_report(self, report: str) -> str:
        self.calls.append(report)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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
    events = store.list_analysis_progress_events(job["id"])
    assert events[-1].stage_key == "queued"
    assert events[-1].status == "completed"


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
    assert result.normalized["sections"]["final"] == "English final report"
    assert usage_logs[-1].user_id == user.id
    assert usage_logs[-1].endpoint == "analysis.worker.live"
    assert usage_logs[-1].provider == "deepseek"
    assert usage_logs[-1].model == "deepseek-v4-pro"
    events = store.list_analysis_progress_events(job.id)
    assert [event.stage_key for event in events] == ["running", "market", "final"]
    assert events[-1].summary == "Analysis completed and final report persisted."


@pytest.mark.unit
def test_worker_generates_and_persists_chinese_report_after_full_english_report():
    store = AlphaPilotStore()
    user = store.create_user("translate-worker@example.com", "pass-1234", "Translate Worker")
    job = store.create_job(user.id, "nvda", "2024-05-10", "live", ["market"])
    translator = StubReportTranslator("中文完整报告")

    completed = process_analysis_job(
        store=store,
        engine=SuccessfulLiveEngine(),
        job_id=job.id,
        translator=translator,
    )

    result = store.get_result(completed.result_id)
    assert translator.calls == ["## Market report\n\nEnglish market report\n\n---\n\n## Final report\n\nEnglish final report"]
    assert result.normalized["localized_sections"]["zh"]["report"] == "中文完整报告"
    assert result.normalized["report_translations"]["zh"]["status"] == "completed"
    assert result.normalized["report_translations"]["zh"]["attempts"] == 1
    events = store.list_analysis_progress_events(job.id)
    assert events[-1].stage_key == "translation_zh"
    assert events[-1].status == "completed"


@pytest.mark.unit
def test_worker_does_not_regenerate_cached_chinese_report():
    store = AlphaPilotStore()
    user = store.create_user("cached-translation@example.com", "pass-1234", "Cached Translation")
    job = store.create_job(user.id, "nvda", "2024-05-10", "live", ["market"])
    completed = store.complete_job(
        job.id,
        {
            "sections": {"final": "worker result"},
            "localized_sections": {"zh": {"report": "已有中文完整报告"}},
            "report_translations": {"zh": {"status": "completed", "attempts": 1}},
        },
        {"company_of_interest": "NVDA"},
    )
    translator = StubReportTranslator("不应该调用")

    from alphapilot.backend.worker import ensure_chinese_report_translation

    ensure_chinese_report_translation(store=store, job=completed, translator=translator)

    result = store.get_result(completed.result_id)
    assert translator.calls == []
    assert result.normalized["localized_sections"]["zh"]["report"] == "已有中文完整报告"


@pytest.mark.unit
def test_worker_retries_chinese_report_translation_and_records_failed_status():
    store = AlphaPilotStore()
    user = store.create_user("failed-translation@example.com", "pass-1234", "Failed Translation")
    job = store.create_job(user.id, "nvda", "2024-05-10", "live", ["market"])
    translator = StubReportTranslator(
        RuntimeError("temporary provider error"),
        RuntimeError("provider still down"),
        RuntimeError("provider exhausted"),
    )

    completed = process_analysis_job(
        store=store,
        engine=SuccessfulLiveEngine(),
        job_id=job.id,
        translator=translator,
    )

    result = store.get_result(completed.result_id)
    assert completed.status == "completed"
    assert len(translator.calls) == 3
    assert result.normalized["sections"]["final"] == "English final report"
    assert result.normalized["report_translations"]["zh"]["status"] == "failed"
    assert result.normalized["report_translations"]["zh"]["attempts"] == 3
    assert "provider exhausted" in result.normalized["report_translations"]["zh"]["error"]
    events = store.list_analysis_progress_events(job.id)
    assert events[-1].stage_key == "translation_zh"
    assert events[-1].status == "failed"


@pytest.mark.unit
def test_worker_serializes_langchain_messages_before_persisting_live_result(tmp_path):
    store = SqlAlchemyAlphaPilotStore(database_url=f"sqlite:///{tmp_path / 'worker.db'}")
    user = store.create_user("json-worker@example.com", "pass-1234", "JSON Worker")
    job = store.create_job(user.id, "aapl", "2026-01-01", "live", ["market"])

    completed = process_analysis_job(
        store=store,
        engine=LiveEngineWithLangChainMessages(),
        job_id=job.id,
    )

    result = store.get_result(completed.result_id)
    assert completed.status == "completed"
    assert result.raw_state["messages"][0]["type"] == "human"
    assert result.raw_state["messages"][0]["content"] == "Analyze this ticker"


@pytest.mark.unit
def test_analysis_progress_endpoint_returns_owner_events():
    store = AlphaPilotStore()
    client = TestClient(create_app(store=store))
    token = _register_and_login(client, "progress@example.com")
    user = store.get_user_by_email("progress@example.com")
    job = store.create_job(user.id, "NVDA", "2024-05-10", "live", ["market"])
    store.create_analysis_progress_event(
        job_id=job.id,
        stage_key="market",
        stage_label="Market analyst",
        status="running",
        summary="Collecting price action and technical indicators.",
    )

    response = client.get(
        f"/analysis/{job.id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["stage_key"] == "market"
    assert response.json()[0]["stage_label"] == "Market analyst"
    assert response.json()[0]["summary"] == "Collecting price action and technical indicators."


@pytest.mark.unit
def test_delete_analysis_job_removes_queued_running_and_completed_jobs():
    store = AlphaPilotStore()
    client = TestClient(create_app(store=store))
    token = _register_and_login(client, "delete-jobs@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    user = store.get_user_by_email("delete-jobs@example.com")

    queued = store.create_job(user.id, "AAPL", "2026-06-10", "live", ["market"])
    running = store.create_job(user.id, "NVDA", "2026-06-10", "live", ["market"])
    store.mark_job_running(running.id)
    completed = store.create_job(user.id, "MSFT", "2026-06-10", "demo", ["market"])
    store.complete_job(completed.id, {"decision": "Neutral"}, {"company_of_interest": "MSFT"})

    for job_id in (queued.id, running.id, completed.id):
        deleted = client.delete(f"/analysis/{job_id}", headers=headers)
        assert deleted.status_code == 204
        missing = client.get(f"/analysis/{job_id}", headers=headers)
        assert missing.status_code == 404

    remaining = client.get("/analysis", headers=headers)
    assert remaining.status_code == 200
    assert remaining.json() == []


@pytest.mark.unit
def test_worker_skips_deleted_queued_job_without_crashing():
    store = AlphaPilotStore()
    user = store.create_user("deleted-worker@example.com", "pass-1234", "Deleted Worker")
    job = store.create_job(user.id, "aapl", "2026-06-10", "live", ["market"])
    store.delete_analysis_job(user.id, job.id)

    assert process_analysis_job(store=store, engine=SuccessfulLiveEngine(), job_id=job.id) is None


@pytest.mark.unit
def test_delete_compare_workflow_removes_history_item():
    store = AlphaPilotStore()
    client = TestClient(create_app(store=store))
    token = _register_and_login(client, "delete-compare@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/compare",
        headers=headers,
        json={
            "symbols": [
                {
                    "ticker": "LLY",
                    "company_name": "Eli Lilly and Company",
                    "market": "US",
                    "exchange": "NYSE",
                    "currency": "USD",
                },
                {
                    "ticker": "UNH",
                    "company_name": "UnitedHealth Group Incorporated",
                    "market": "US",
                    "exchange": "NYSE",
                    "currency": "USD",
                },
            ],
            "start_date": "2026-01-01",
            "end_date": "2026-06-15",
            "analysis_anchor": "2026-06-15",
        },
    )
    assert created.status_code == 201

    deleted = client.delete(f"/compare/{created.json()['id']}", headers=headers)

    assert deleted.status_code == 204
    assert client.get(f"/compare/{created.json()['id']}", headers=headers).status_code == 404
    assert client.get("/compare", headers=headers).json() == []


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
def test_worker_runs_security_master_sync_once_on_monday_midnight(monkeypatch):
    from datetime import datetime, timezone

    from alphapilot.backend.worker import maybe_run_scheduled_security_master_sync

    monkeypatch.setenv("ALPHAPILOT_SECURITY_MASTER_AUTO_SYNC_ENABLED", "true")
    store = AlphaPilotStore()
    calls = []

    def fake_sync(sync_store):
        calls.append(sync_store)
        return sync_store.create_security_master_sync_run(
            source="test",
            status="completed",
            started_at=datetime(2026, 6, 15, 0, 5, tzinfo=timezone.utc),
            finished_at=datetime(2026, 6, 15, 0, 5, tzinfo=timezone.utc),
        )

    monday = datetime(2026, 6, 15, 0, 5, tzinfo=timezone.utc)
    tuesday = datetime(2026, 6, 16, 0, 5, tzinfo=timezone.utc)

    assert maybe_run_scheduled_security_master_sync(store, now=monday, sync_func=fake_sync) is True
    assert maybe_run_scheduled_security_master_sync(store, now=monday, sync_func=fake_sync) is False
    assert maybe_run_scheduled_security_master_sync(store, now=tuesday, sync_func=fake_sync) is False
    assert calls == [store]


@pytest.mark.unit
def test_rate_limit_blocks_public_demo_after_threshold():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    client = TestClient(create_app(store=AlphaPilotStore(), rate_limiter=limiter))

    assert client.get("/demo/reference").status_code == 200
    assert client.get("/demo/reference").status_code == 200
    blocked = client.get("/demo/reference")

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Rate limit exceeded"
