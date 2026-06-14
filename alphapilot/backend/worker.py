from __future__ import annotations

import os
import time

from .engine_service import AnalysisEngineService
from .queue import RedisAnalysisQueue
from .settings import get_database_url, get_redis_url
from .sqlalchemy_store import SqlAlchemyAlphaPilotStore


def process_analysis_job(*, store, engine: AnalysisEngineService, job_id: str):
    job = store.mark_job_running(job_id)
    try:
        if job.mode == "demo":
            normalized, raw_state = engine.run_demo()
            endpoint = "analysis.worker.demo"
        else:
            normalized, raw_state = engine.run_live(
                job.ticker,
                job.trade_date,
                job.selected_analysts,
            )
            endpoint = "analysis.worker.live"
        completed = store.complete_job(job.id, normalized, raw_state)
        store.log_api_usage(
            user_id=job.user_id,
            endpoint=endpoint,
            provider=os.getenv("TRADINGAGENTS_LLM_PROVIDER"),
            model=os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or os.getenv("TRADINGAGENTS_QUICK_THINK_LLM"),
        )
        return completed
    except Exception as exc:
        failed = store.fail_job(job.id, str(exc))
        store.log_api_usage(
            user_id=job.user_id,
            endpoint="analysis.worker.failed",
            provider=os.getenv("TRADINGAGENTS_LLM_PROVIDER"),
            model=os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or os.getenv("TRADINGAGENTS_QUICK_THINK_LLM"),
        )
        return failed


def run_worker_loop(*, poll_interval_seconds: float = 1.0) -> None:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("ALPHAPILOT_DATABASE_URL is required for the worker")
    store = SqlAlchemyAlphaPilotStore(database_url)
    engine = AnalysisEngineService()
    queue = RedisAnalysisQueue(get_redis_url())
    while True:
        job_id = queue.dequeue(timeout_seconds=5)
        if job_id:
            process_analysis_job(store=store, engine=engine, job_id=job_id)
        else:
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    run_worker_loop()
